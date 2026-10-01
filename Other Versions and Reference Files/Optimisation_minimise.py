import numpy as np
from scipy.optimize import minimize
from joblib import load
import EnergyDemand
import Cost
import pandas as pd


class OptimizeEnergySources:
    def __init__(self, heat_demand, light_demand, co2_demand):
        self.heat_demand = heat_demand
        self.light_demand = light_demand
        self.co2_demand = co2_demand

        # Get constants from EnergyDemand.CHP
        self.fuel_to_electric = 0.333
        self.heat_to_electric = 1.51
        self.fuel_to_heat = self.heat_to_electric / (1 / self.fuel_to_electric)
        self.gas_co2_per_mwh = 184
        self.cc_power = 0.16  # Additional power needed for carbon capture
        self.co2_capture_efficiency = 0.96  # 96% CO2 capture efficiency

        # Calculate hourly fuel requirements
        print("\nCalculating hourly demands...")
        self.hourly_demands = self._calculate_hourly_demands()

        # Get maximum fuel requirement
        self.max_fuel = self.hourly_demands["Fuel Requirement"].max() * 1.1  # 10% safety margin
        print(f"\nMaximum fuel requirement: {self.max_fuel:.4f} MW")
        print(f"Primary drivers summary:\n{self.hourly_demands['Primary Driver'].value_counts()}")

    def _safe_divide(self, numerator, denominator):
        """Replicate the safe divide function from EnergyDemand"""
        numerator, denominator = np.broadcast_arrays(numerator, denominator)
        result = np.zeros_like(numerator, dtype=float)
        mask = denominator != 0
        result[mask] = numerator[mask] / denominator[mask]
        return result

    def _calculate_hourly_demands(self):
        """Replicate the CHP demand calculations from EnergyDemand with corrected CO2 capture"""
        df = pd.DataFrame(index=self.heat_demand.index)

        # Calculate fuel required for each demand
        df["Fuel for Light"] = self._safe_divide(
            self.light_demand["MWh"],
            self.fuel_to_electric
        )

        df["Fuel for Heat"] = self._safe_divide(
            self.heat_demand["QnetMWh"],
            self.fuel_to_heat
        )

        # CO2 capture calculation considering 96% capture efficiency
        df["Fuel for CO2"] = self._safe_divide(
            self.co2_demand["Total CO2 Demand"],
            (self.gas_co2_per_mwh * self.co2_capture_efficiency)
        )

        # Find driving demand for each hour
        df["Fuel Requirement"] = df[["Fuel for Light", "Fuel for Heat", "Fuel for CO2"]].max(axis=1)
        # Add extra fuel for carbon capture power requirement
        df["Fuel Requirement"] *= (1 + self.cc_power)

        # Identify primary driver
        df["Primary Driver"] = df[["Fuel for Light", "Fuel for Heat", "Fuel for CO2"]].idxmax(axis=1)

        return df

    def objective(self, x):
        """Calculate total annual cost using Cost.py"""
        try:
            if x[0] > 0:  # CHP capacity
                # Calculate actual fuel requirement based on capacity
                fuel_requirement = self.hourly_demands["Fuel Requirement"].sum() * x[0]
                energy_output = fuel_requirement * self.fuel_to_electric * (
                            1 - self.cc_power)  # Account for CC power usage

                chp = Cost.CHP(
                    capital_cost=900000,
                    base_capex=0,
                    operational_cost=11,
                    fuel_cost=90.1,
                    power=x[0],
                    energy_output=energy_output,
                    fuel_requirement=fuel_requirement,
                    cc_power=self.cc_power,
                    lifetime=20,
                    loan_term=20
                )
                _, _, _, annual_cost, _ = chp.constant_cost()
                return annual_cost
            return np.inf

        except Exception as e:
            print(f"Error in objective function: {e}")
            return np.inf

    def check_demands(self, capacity):
        """Verify all demands are met at every hour"""
        # Calculate actual outputs
        fuel = self.hourly_demands["Fuel Requirement"] * capacity
        heat_output = fuel * self.fuel_to_heat
        power_output = fuel * self.fuel_to_electric * (1 - self.cc_power)  # Account for CC power usage
        co2_capture = fuel * self.gas_co2_per_mwh * self.co2_capture_efficiency

        # Check if any demand is unmet
        heat_unmet = (heat_output < self.heat_demand["QnetMWh"]).any()
        power_unmet = (power_output < self.light_demand["MWh"]).any()
        co2_unmet = (co2_capture < self.co2_demand["Total CO2 Demand"]).any()

        print("\nDemand Check:")
        print(f"Heat demand always met: {not heat_unmet}")
        print(f"Power demand always met: {not power_unmet}")
        print(f"CO2 demand always met: {not co2_unmet}")

        # Calculate oversupply statistics
        heat_oversupply = ((heat_output - self.heat_demand["QnetMWh"]) / self.heat_demand["QnetMWh"] * 100)
        power_oversupply = ((power_output - self.light_demand["MWh"]) / self.light_demand["MWh"] * 100)
        co2_oversupply = (
                    (co2_capture - self.co2_demand["Total CO2 Demand"]) / self.co2_demand["Total CO2 Demand"] * 100)

        print("\nOversupply Statistics:")
        print(f"Heat - Mean: {heat_oversupply.mean():.1f}%, Max: {heat_oversupply.max():.1f}%")
        print(f"Power - Mean: {power_oversupply.mean():.1f}%, Max: {power_oversupply.max():.1f}%")
        print(f"CO2 - Mean: {co2_oversupply.mean():.1f}%, Max: {co2_oversupply.max():.1f}%")

        return not (heat_unmet or power_unmet or co2_unmet)

    def optimize(self):
        print("\nStarting optimization...")

        # Initial capacity based on maximum fuel requirement
        x0 = np.array([self.max_fuel])

        # Calculate and print initial cost
        initial_cost = self.objective(x0)
        print(f"\nInitial solution:")
        print(f"CHP Capacity: {x0[0]:.4f} MW")
        print(f"Annual Cost: £{initial_cost:,.2f}")

        # Verify demands are met
        if not self.check_demands(x0[0]):
            print("WARNING: Initial solution does not meet all demands!")
            return None

        # Define bounds
        bounds = [(self.max_fuel * 0.9, self.max_fuel * 1.2)]  # Allow some variation around max fuel

        # Run optimization
        result = minimize(
            self.objective,
            x0,
            method='Nelder-Mead',
            bounds=bounds,
            options={'maxiter': 1000, 'xatol': 1e-6, 'fatol': 1e-6}
        )

        # Create full result vector
        full_result = np.zeros(5)
        full_result[0] = result.x[0]

        return full_result, result.fun


def main():
    print("Loading demand data...")
    heat_demand = load("heat_demand.joblib")
    light_demand = load("light_demand.joblib")
    co2_demand = load("co2_demand.joblib")

    optimizer = OptimizeEnergySources(heat_demand, light_demand, co2_demand)
    result = optimizer.optimize()

    if result is not None:
        capacities, cost = result
        print("\nOptimization complete!")
        print("\nOptimal capacities (MW):")
        technologies = ['CHP', 'Geothermal', 'GSHP', 'Solar PV', 'Waste Heat']
        for tech, capacity in zip(technologies, capacities):
            print(f"{tech}: {capacity:.4f}")

        print(f"\nMinimum annual cost: £{cost:,.2f}")

        # Final verification
        optimizer.check_demands(capacities[0])
    else:
        print("\nOptimization failed to find valid solution")


if __name__ == "__main__":
    main()