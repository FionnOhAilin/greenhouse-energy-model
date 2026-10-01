import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution
from joblib import load
import EnergyDemand
import Cost
import time
from datetime import timedelta, datetime


class OptimizeEnergySources:
    def __init__(self, heat_demand, light_demand, co2_demand):
        self.heat_demand = heat_demand
        self.light_demand = light_demand
        self.co2_demand = co2_demand

        # Store demand calculations and max powers
        self.chp = EnergyDemand.CHP(heat_demand, light_demand, co2_demand)
        self.chp_demand, self.chp_max_power = self.chp.calculate_demand()

        self.geo = EnergyDemand.Geothermal(heat_demand, light_demand, co2_demand)
        self.geo_demand, self.geo_max_power = self.geo.calculate_demand()

        self.gshp = EnergyDemand.GSHP(heat_demand, light_demand, co2_demand)
        self.gshp_demand, self.gshp_max_power = self.gshp.calculate_demand()

        self.solar = EnergyDemand.SolarPV(heat_demand, light_demand, co2_demand)
        self.solar_demand, self.solar_max_power = self.solar.calculate_demand()

        self.wasteheat = EnergyDemand.WasteHeat(heat_demand, light_demand, co2_demand)
        self.wasteheat_demand, self.wasteheat_max_power = self.wasteheat.calculate_demand()

        self.grid = EnergyDemand.Grid(heat_demand, light_demand, co2_demand)
        self.grid_demand, self.grid_max_power = self.grid.calculate_demand()

        self.boiler = EnergyDemand.Boiler(heat_demand, light_demand, co2_demand)
        self.boiler_demand, self.boiler_max_power = self.boiler.calculate_demand()

        self.co2 = EnergyDemand.CO2Import(heat_demand, light_demand, co2_demand)
        self.co2_demand, self.co2_max_power = self.co2.calculate_demand()

        # Store maximum demands
        self.max_heat = heat_demand["QnetMWh"].max()
        self.max_light = light_demand["MWh"].max()
        self.max_co2 = co2_demand["Total CO2 Demand"].max()
        self.best_solution = None
        self.best_cost = float('inf')

        print(f"\nMaximum demands:")
        print(f"Heat: {self.max_heat:.4f} MW")
        print(f"Light: {self.max_light:.4f} MW")
        print(f"CO2: {self.max_co2:.4f} kg/h")

        print(f"\nMaximum technology powers:")
        print(f"CHP: {self.chp_max_power:.4f} MW")
        print(f"Geothermal: {self.geo_max_power:.4f} MW")
        print(f"GSHP: {self.gshp_max_power:.4f} MW")
        print(f"Solar: {self.solar_max_power:.4f} MW")
        print(f"Waste Heat: {self.wasteheat_max_power:.4f} MW")
        print(f"Grid: {self.grid_max_power:.4f} MW")
        print(f"Boiler: {self.boiler_max_power:.4f} MW")
        print(f"CO2: {self.co2_max_power:.4f} kg/h")

        self.iteration_data = []
        self.current_minimum = float('inf')
        self.local_minima = []
        self.iteration_count = 0
        self.convergence_window = 10  # Number of minima to check for improvement
        self.improvement_threshold = 0.005  # 0.5% improvement threshold
        self.converged = False

        self.best_cost_components = {
            'CHP': {'capex': 0, 'opex': 0, 'fuel': 0},
            'Geothermal': {'capex': 0, 'opex': 0, 'fuel': 0},
            'GSHP': {'capex': 0, 'opex': 0, 'fuel': 0},
            'Solar': {'capex': 0, 'opex': 0, 'fuel': 0},
            'WasteHeat': {'capex': 0, 'opex': 0, 'fuel': 0},
            'Grid': {'capex': 0, 'opex': 0, 'fuel': 0},
            'Boiler': {'capex': 0, 'opex': 0, 'fuel': 0},
            'CO2': {'capex': 0, 'opex': 0, 'fuel': 0}
        }

    def calculate_supplies(self, x):
        """Calculate supply of heat, light, and CO2 from given capacities"""
        chp, geo, gshp, solar, waste, grid, boiler, co2 = x

        # Calculate heat supply
        heat_supply = (
                chp * self.chp.heat_to_electric_ratio +
                geo +
                gshp +
                waste +
                boiler
        )

        # Calculate light supply
        light_supply = (
                chp * (1 - self.chp.cc_power) +
                solar * self.solar.capacity_factor +
                grid
        )

        # Calculate CO2 capture
        co2_supply = (
                chp / self.chp.fuel_to_electric_efficiency * self.chp.gas_co2_per_Mwh * self.chp.cc_efficiency +
                boiler * self.boiler.gas_co2_per_Mwh * self.boiler.fuel_to_heat_efficiency +
                co2
        )

        return heat_supply, light_supply, co2_supply

    def calculate_total_cost(self, x):
        """Calculate total annual cost for all technologies"""
        chp, geo, gshp, solar, waste, grid, boiler, co2 = x
        total_cost = 0

        current_cost_components = dict(self.best_cost_components)

        try:
            # CHP costs
            if chp > 0:
                chp_cost = Cost.CHP(
                    capital_cost=900000,
                    base_capex=0,
                    operational_cost=11,
                    fuel_cost=90.1,
                    power=chp,
                    energy_output=self.chp_demand["Yearly Electricity Output"].sum() * (chp / self.chp_max_power),
                    fuel_requirement=self.chp_demand["Fuel Requirement"].sum() * (chp / self.chp_max_power),
                    cc_power=0.16,
                    lifetime=20,
                    loan_term=20
                )
                capex, opex, fuel, annual_cost, _ = chp_cost.constant_cost()
                current_cost_components['CHP'] = {'capex': capex, 'opex': opex, 'fuel': fuel}
                total_cost += annual_cost

            # Geothermal costs
            if geo > 0:
                geo_cost = Cost.Geothermal(
                    capital_cost=2890000,
                    base_capex=0,
                    operational_cost=11000 * self.geo_max_power /
                                     (self.geo_demand["Yearly Heat Output"].sum() * (geo / self.geo_max_power)),
                    fuel_cost=228.1,
                    power=geo,
                    energy_output=self.geo_demand["Yearly Heat Output"].sum() * (geo / self.geo_max_power),
                    fuel_requirement=self.geo_demand["Electricity for Heat"].sum() * (geo / self.geo_max_power),
                    cc_power=0,
                    lifetime=20,
                    loan_term=20
                )
                capex, opex, fuel, annual_cost, _ = geo_cost.constant_cost()
                current_cost_components['Geothermal'] = {'capex': capex, 'opex': opex, 'fuel': fuel}
                total_cost += annual_cost

            # GSHP costs
            if gshp > 0:
                gshp_cost = Cost.GSHP(
                    capital_cost=1297000,
                    base_capex=0,
                    operational_cost=8000 * self.gshp_max_power /
                                     (self.gshp_demand["Yearly Heat Output"].sum() * (gshp / self.gshp_max_power)),
                    fuel_cost=228.1,
                    power=gshp,
                    energy_output=self.gshp_demand["Yearly Heat Output"].sum() * (gshp / self.gshp_max_power),
                    fuel_requirement=self.gshp_demand["Electricity for Heat"].sum() * (gshp / self.gshp_max_power),
                    cc_power=0,
                    lifetime=20,
                    loan_term=20
                )
                capex, opex, fuel, annual_cost, _ = gshp_cost.constant_cost()
                current_cost_components['GSHP'] = {'capex': capex, 'opex': opex, 'fuel': fuel}
                total_cost += annual_cost

            # Solar costs
            if solar > 0:
                solar_cost = Cost.SolarPV(
                    capital_cost=1780000,
                    base_capex=0,
                    operational_cost=26450 * self.solar_max_power /
                                     (self.solar_demand["Yearly Electricity Output"].sum() *
                                      (solar / self.solar_max_power)),
                    fuel_cost=0,
                    power=solar,
                    energy_output=self.solar_demand["Yearly Electricity Output"].sum() * (solar / self.solar_max_power),
                    fuel_requirement=0,
                    cc_power=0,
                    lifetime=20,
                    loan_term=20
                )
                capex, opex, fuel, annual_cost, _ = solar_cost.constant_cost()
                current_cost_components['Solar'] = {'capex': capex, 'opex': opex, 'fuel': fuel}
                total_cost += annual_cost

            # Waste Heat costs
            if waste > 0:
                waste_cost = Cost.WasteHeat(
                    capital_cost=0,
                    base_capex=0,
                    operational_cost=0,
                    fuel_cost=100,
                    power=waste,
                    energy_output=self.wasteheat_demand["Yearly Heat Output"].sum() * (
                            waste / self.wasteheat_max_power),
                    fuel_requirement=self.wasteheat_demand["Steam Required"].sum() * (waste / self.wasteheat_max_power),
                    cc_power=0,
                    lifetime=20,
                    loan_term=20
                )
                capex, opex, fuel, annual_cost, _ = waste_cost.constant_cost()
                current_cost_components['WasteHeat'] = {'capex': capex, 'opex': opex, 'fuel': fuel}
                total_cost += annual_cost

            # Grid costs
            if grid > 0:
                grid_cost = Cost.Grid(
                    capital_cost=0,
                    base_capex=0,
                    operational_cost=0,
                    fuel_cost=228.1,
                    power=grid,
                    energy_output=self.grid_demand["Yearly Electricity Output"].sum() * (grid / self.grid_max_power),
                    fuel_requirement=self.grid_demand["Electricity for Light"].sum() * (grid / self.grid_max_power),
                    cc_power=0,
                    lifetime=20,
                    loan_term=20
                )
                capex, opex, fuel, annual_cost, _ = grid_cost.constant_cost()
                current_cost_components['Grid'] = {'capex': capex, 'opex': opex, 'fuel': fuel}
                total_cost += annual_cost

            if boiler > 0:
                boiler_cost = Cost.Boiler(
                    capital_cost=130000,
                    base_capex=0,
                    operational_cost=3900 * self.boiler_max_power /
                                     (self.boiler_demand["Yearly Heat Output"].sum() * (
                                             boiler / self.boiler_max_power)),
                    fuel_cost=0.27,
                    power=boiler,
                    energy_output=self.boiler_demand["Yearly Heat Output"].sum() * (boiler / self.boiler_max_power),
                    fuel_requirement=self.boiler_demand["Fuel Requirement"].sum() * (boiler / self.boiler_max_power),
                    cc_power=0,
                    lifetime=20,
                    loan_term=20
                )
                capex, opex, fuel, annual_cost, _ = boiler_cost.constant_cost()
                current_cost_components['Boiler'] = {'capex': capex, 'opex': opex, 'fuel': fuel}
                total_cost += annual_cost

            if co2 > 0:
                co2_cost = Cost.CO2Import(
                    capital_cost=0,
                    base_capex=0,
                    operational_cost=0,
                    fuel_cost=0.14678,
                    power=co2,
                    energy_output=0,
                    fuel_requirement=self.co2_demand["CO2 Requirement"].sum() * (co2 / self.co2_max_power),
                    cc_power=0,
                    lifetime=20,
                    loan_term=20
                )
                capex, opex, fuel, annual_cost, _ = co2_cost.constant_cost()
                current_cost_components['CO2'] = {'capex': capex, 'opex': opex, 'fuel': fuel}
                total_cost += annual_cost

            if total_cost < self.best_cost:
                self.best_cost_components = current_cost_components

            return total_cost
        except Exception as e:
            print(f"Error in calculate_total_cost: {e}")
            return 1e10  # Return high cost instead of None

    def check_convergence(self):
        """Check if optimization has converged based on improvements between discovered minima"""
        if len(self.local_minima) < self.convergence_window:
            return False

        # Look at the most recent X minima discoveries, where X is the convergence window
        recent_minima = self.local_minima[-self.convergence_window:]

        # Calculate the best cost from the start of this window and the best cost now
        best_cost_start = recent_minima[0]['cost']
        best_cost_now = recent_minima[-1]['cost']

        # Calculate relative improvement from best discovered solution at window start to now
        relative_improvement = (best_cost_start - best_cost_now) / best_cost_start

        if relative_improvement < self.improvement_threshold:
            print(f"\nConvergence detected:")
            print(
                f"Best solution improved by only {relative_improvement:.4%} over last {self.convergence_window} discovered minima")
            print(f"Below threshold of {self.improvement_threshold:.1%}")
            self.converged = True
            # Set the current minimum to the best cost when convergence is detected
            self.current_minimum = self.best_cost
            return True

        return False

    def objective(self, x):
        """Modified objective function that tracks local minima"""
        if self.converged:
            return self.current_minimum

        cost = self._calculate_objective(x)  # This contains the original objective function logic

        # Update best solution if this is better
        if cost < self.best_cost:
            self.best_cost = cost
            self.best_solution = x.copy()  # Store a copy of the best solution

            # Print only significant improvements (e.g., more than 1% better)
            if len(self.local_minima) == 0 or cost < self.local_minima[-1]['cost'] * 0.99:
                print(f"\nNew better solution found: £{cost:,.2f}")
                techs = ['CHP', 'Geothermal', 'GSHP', 'Solar', 'Waste Heat', 'Grid', 'Boiler', 'CO2']
                for tech, cap in zip(techs, x):
                    if cap > 0.0001:
                        unit = "kg/h" if tech == "CO2" else "MW"
                        print(f"{tech}: {cap:.4f} {unit}")

            self.local_minima.append({
                'iteration': self.iteration_count,
                'cost': cost,
                'capacities': list(x)
            })

            # Check for convergence after updating local_minima
            self.check_convergence()

        self.iteration_count += 1
        return cost

    def _calculate_objective(self, x):
        """Objective function with cost breakdown tracking"""
        chp, geo, gshp, solar, waste, grid, boiler, co2 = x
        try:
            heat_supply, light_supply, co2_supply = self.calculate_supplies(x)
            base_cost = self.calculate_total_cost(x)

            # Calculate violations
            heat_undersupply = max(0, self.max_heat - heat_supply)
            light_undersupply = max(0, self.max_light - light_supply)
            co2_undersupply = max(0, self.max_co2 - co2_supply)

            # Calculate undersupply penalties
            heat_undersupply_penalty = 1e12 * heat_undersupply ** 2
            light_undersupply_penalty = 1e12 * light_undersupply ** 2
            co2_undersupply_penalty = 1e10 * co2_undersupply ** 2
            undersupply_penalty = heat_undersupply_penalty + light_undersupply_penalty + co2_undersupply_penalty

            tolerance = 0.05
            heat_oversupply = max(0, heat_supply - self.max_heat * (1 + tolerance))
            light_oversupply = max(0, light_supply - self.max_light * (1 + tolerance))
            co2_oversupply = (
                    self.chp_demand["Fuel Requirement"].sum() * self.chp.gas_co2_per_Mwh * self.chp.cc_efficiency * (
                    chp / self.chp_max_power) +
                    self.boiler_demand[
                        "Fuel Requirement"].sum() * self.boiler.gas_co2_per_Mwh * self.boiler.cc_efficiency * (
                            boiler / self.boiler_max_power) +
                    self.co2_demand["CO2 Requirement"].sum() * (co2 / self.co2_max_power) -
                    self.co2_demand["CO2 Requirement"].sum()
            )

            # Calculate oversupply penalties
            co2_oversupply_penalty = co2_oversupply * 0.056  # £56 per tonne of CO2
            oversupply_penalty = co2_oversupply_penalty

            total_cost = base_cost + undersupply_penalty + oversupply_penalty

            # Store the iteration data
            self.iteration_data.append({
                'CHP': chp,
                'Geothermal': geo,
                'GSHP': gshp,
                'Solar': solar,
                'Waste Heat': waste,
                'Grid': grid,
                'Boiler': boiler,
                'CO2': co2,
                'Total Cost': total_cost
            })

            # Store cost breakdown for this iteration
            self.current_cost_breakdown = {
                'base_cost': base_cost,
                'undersupply_penalty': undersupply_penalty,
                'oversupply_penalty': oversupply_penalty,
                'total_cost': total_cost,
                'undersupply_breakdown': {
                    'heat': heat_undersupply_penalty,
                    'light': light_undersupply_penalty,
                    'co2': co2_undersupply_penalty
                },
                'oversupply_breakdown': {
                    'co2': co2_oversupply_penalty
                }
            }

            # Detailed debugging output
            if undersupply_penalty > 0 or oversupply_penalty > 1000:
                print(f"\nCost Breakdown at CHP = {x[0]:.4f} MW:"
                      f"\nGeothermal = {x[1]:.4f} MW "
                      f"\nGSHP = {x[2]:.4f} MW "
                      f"\nSolar = {x[3]:.4f} MW"
                      f"\nWaste Heat = {x[4]:.4f} MW"
                      f"\nGrid = {x[5]:.4f} MW"
                      f"\nBoiler = {x[6]:.4f} MW"
                      f"\nCO2 = {x[7]:.4f} kg/h")
                print(f"Base Cost: £{base_cost:,.2f}")
                print(f"Undersupply Penalty: £{undersupply_penalty:,.2f}")
                print(f"  Heat: £{heat_undersupply_penalty:,.2f}")
                print(f"  Light: £{light_undersupply_penalty:,.2f}")
                print(f"  CO2: £{co2_undersupply_penalty:,.2f}")
                print(f"Oversupply Penalty: £{oversupply_penalty:,.2f}")
                print(f"  CO2: £{co2_oversupply_penalty:,.2f}")
                print(f"Total Cost: £{total_cost:,.2f}")

            return float(total_cost)

        except Exception as e:
            print(f"Error in objective function: {e}")
            return 1e10

    def callback_function(self, xk, convergence=None):
        """Callback function for differential evolution"""
        # Check if we've already converged and should stop
        return self.converged

    def optimize(self):
        """Run optimization using differential evolution with convergence tracking"""
        print("\nStarting differential evolution optimization...")

        self.best_solution = None
        self.best_cost = float('inf')
        self.local_minima = []
        self.iteration_count = 0
        self.converged = False

        bounds = [
            (0, self.chp_max_power),
            (0, self.geo_max_power),
            (0, self.gshp_max_power),
            (0, self.solar_max_power),
            (0, self.wasteheat_max_power),
            (0, self.grid_max_power),
            (0, self.boiler_max_power),
            (0, self.co2_max_power)
        ]

        # Calculate minimum CHP capacity needed for constraints
        min_chp_heat = self.max_heat / self.chp.fuel_to_heat_efficiency
        min_chp_light = self.max_light / (self.chp.fuel_to_electric_efficiency * (1 - self.chp.cc_power))
        min_chp_co2 = self.max_co2 / (self.chp.gas_co2_per_Mwh * self.chp.cc_efficiency)

        min_chp = max(min_chp_heat, min_chp_light, min_chp_co2)

        print(f"\nMinimum CHP requirements:")
        print(f"For heat: {min_chp_heat:.4f} MW")
        print(f"For light: {min_chp_light:.4f} MW")
        print(f"For CO2: {min_chp_co2:.4f} MW")
        print(f"Overall minimum: {min_chp:.4f} MW")

        results = []

        initial_points = [
            [min_chp, 0, 0, 0, 0, 0, 0, 0]
        ]

        # Create an initial population that includes our initial points
        # This serves a similar purpose to the x0 parameter in dual_annealing
        init_pop = None
        if initial_points:
            # Create initial population for differential evolution
            # We'll make a population that includes our key initial points
            popsize = 15  # Default popsize for differential_evolution
            init_pop = np.zeros((popsize * len(bounds), len(bounds)))

            # Fill the first rows with our initial points
            for i, point in enumerate(initial_points):
                if i < len(init_pop):
                    init_pop[i] = point

            # Fill the rest with random points within bounds
            for i in range(len(initial_points), len(init_pop)):
                for j in range(len(bounds)):
                    init_pop[i, j] = np.random.uniform(bounds[j][0], bounds[j][1])

        for i, x0 in enumerate(initial_points):
            print(f"\nStarting optimization run {i + 1} with initial CHP power: {x0[0]:.2f} MW")

            result = differential_evolution(
                self.objective,
                bounds=bounds,
                strategy='best1bin',  # Good balance between exploration and exploitation
                maxiter=100,  # Maximum number of generations
                popsize=15,  # Population size multiplier
                tol=0.01,  # Relative tolerance for convergence
                mutation=(0.5, 1.0),  # Mutation constant boundaries
                recombination=0.7,  # Recombination probability (crossover)
                seed=42 + i,  # Random seed for reproducibility
                callback=self.callback_function,  # Early stopping callback
                init=init_pop if i == 0 else None,  # Use custom initial population only for first run
                workers=-1,  # Use all available CPU cores
                updating='deferred',  # Update fitness values once per generation
                polish=True  # Local optimization on the best population member
            )

            results.append(result)

        best_result = min(results, key=lambda r: r.fun)

        # Override the result with our best found solution
        if self.best_solution is not None and self.best_cost < best_result.fun:
            best_result.x = self.best_solution
            best_result.fun = self.best_cost

        minima_df = pd.DataFrame(self.local_minima)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"optimization_minima_{timestamp}.csv"
        minima_df.to_csv(filename, index=False)

        if self.converged:
            print("\nOptimization stopped early due to convergence")
        print(f"\nLocal minima history saved to {filename}")
        print(f"Best solution found: £{self.best_cost:,.2f}")

        return best_result


def main():
    # Start timing
    start_time = time.time()

    print("Loading demand data...")
    heat_demand = load("heat_demand.joblib")
    light_demand = load("light_demand.joblib")
    co2_demand = load("co2_demand.joblib")

    # Time for data loading
    data_load_time = time.time()
    print(f"Data loading time: {timedelta(seconds=data_load_time - start_time)}")

    # Initialize optimizer
    optimizer = OptimizeEnergySources(heat_demand, light_demand, co2_demand)

    # Time for initialization
    init_time = time.time()
    print(f"Initialization time: {timedelta(seconds=init_time - data_load_time)}")

    # Run optimization
    print("\nStarting optimization...")
    opt_start_time = time.time()
    result = optimizer.optimize()
    opt_end_time = time.time()

    # Calculate optimization time
    opt_duration = opt_end_time - opt_start_time
    print(f"\nOptimization time: {timedelta(seconds=opt_duration)}")

    if result.success:
        print("\nOptimization successful!")
        print("\nOptimal capacities (MW):")
        technologies = ['CHP', 'Geothermal', 'GSHP', 'Solar PV', 'Waste Heat', 'Grid', 'Boiler', 'CO2 Import']
        for tech, capacity in zip(technologies, result.x):
            print(f"{tech}: {capacity:.4f}")

        print(f"\nMinimum annual cost: £{result.fun:,.2f}")

        # Verify constraints are met
        heat_supply, light_supply, co2_supply = optimizer.calculate_supplies(result.x)

        print("\nConstraint Verification:")
        print(f"Heat Supply:")
        print(f"Required: {optimizer.max_heat:.4f} MW")
        print(f"Supplied: {heat_supply:.4f} MW")

        print(f"\nLight Supply:")
        print(f"Required: {optimizer.max_light:.4f} MW")
        print(f"Supplied: {light_supply:.4f} MW")

        print(f"\nCO2 Supply:")
        print(f"Required: {optimizer.max_co2:.4f} kg/h")
        print(f"Supplied: {co2_supply:.4f} kg/h")

        # Print optimization statistics
        print("\nOptimization Statistics:")
        print(f"Number of iterations: {result.nit}")
        print(f"Number of function evaluations: {result.nfev}")
        print(f"Average time per iteration: {timedelta(seconds=opt_duration / result.nit)}")

        # Get final cost breakdown
        optimizer.objective(result.x)  # This will update the cost breakdown
        cost_breakdown = optimizer.current_cost_breakdown

        print("\nFinal Cost Breakdown:")
        print(f"Base Cost: £{cost_breakdown['base_cost']:,.2f}")
        print("\nUndersupply Penalties:")
        print(f"  Heat: £{cost_breakdown['undersupply_breakdown']['heat']:,.2f}")
        print(f"  Light: £{cost_breakdown['undersupply_breakdown']['light']:,.2f}")
        print(f"  CO2: £{cost_breakdown['undersupply_breakdown']['co2']:,.2f}")
        print(f"Total Undersupply Penalty: £{cost_breakdown['undersupply_penalty']:,.2f}")
        print("\nOversupply Penalties:")
        print(f"  CO2: £{cost_breakdown['oversupply_breakdown']['co2']:,.2f}")
        print(f"\nTotal Cost: £{cost_breakdown['total_cost']:,.2f}")

    else:
        print("\nOptimization failed:", result.message)

    # Total runtime
    end_time = time.time()
    total_duration = end_time - start_time

    # Detailed timing breakdown
    print("\nTiming Breakdown:")
    print(f"Total:          {timedelta(seconds=total_duration)}")


if __name__ == "__main__":
    main()