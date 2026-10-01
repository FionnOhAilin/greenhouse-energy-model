import pandas as pd
import numpy as np
from InputCalculations import inputs
from HTCoefficients import calculate_htc
from HeatDemand import calculate_heatdemand
from LightDemandOriginal import calculate_lightdemand
from CO2Demand import calculate_co2demand


class EnergySource:

    def __init__(self, heat_demand, light_demand, co2_demand):
        self.heat_demand = heat_demand
        self.light_demand = light_demand
        self.co2_demand = co2_demand
        self.grid_emissions = 332  # kgCO₂ per MWh of electricity


class CHP(EnergySource):

    def chp_demand(self):
        gas_co2_per_Mwh = 184  # kgCO₂ per MWh of natural gas
        heat_to_electric_ratio = 1.51  # Taken from SEAI CHP in ireland 2020
        fuel_to_electric_efficiency = 0.333  # Taken from Excel model
        fuel_to_heat_efficiency = heat_to_electric_ratio / (1 / fuel_to_electric_efficiency)

        # Create DataFrame to store chp results
        chp_results = pd.DataFrame(index=self.heat_demand.index)

        # Calculate chp fuel requirements for light, heat, and CO2
        def safe_divide(numerator, denominator):
            numerator, denominator = np.broadcast_arrays(numerator, denominator)
            result = np.zeros_like(numerator, dtype=float)
            mask = denominator != 0
            result[mask] = numerator[mask] / denominator[mask]
            return result

        # Calculates the fuel required to meet the light, heat, and CO2 loads
        chp_results["Fuel for Light"] = safe_divide(self.light_demand.values, fuel_to_electric_efficiency)
        chp_results["Fuel for Heat"] = safe_divide(
            self.heat_demand,
            fuel_to_heat_efficiency
        )
        chp_results["Fuel for CO2"] = safe_divide(self.co2_demand.values, gas_co2_per_Mwh)

        # Determine primary driver for each hour
        def determine_driver(row):
            if row["Fuel for Heat"] > row["Fuel for Light"] and row["Fuel for Heat"] > row["Fuel for CO2"]:
                return "Heat"
            elif row["Fuel for Light"] > row["Fuel for Heat"] and row["Fuel for Light"] > row["Fuel for CO2"]:
                return "Light"
            elif row["Fuel for CO2"] > row["Fuel for Heat"] and row["Fuel for CO2"] > row["Fuel for Light"]:
                return "CO₂"
            else:
                return "None"

        chp_results["Primary Driver"] = chp_results.apply(determine_driver, axis=1)

        chp_results["Fuel requirement"] = chp_results[["Fuel for Light", "Fuel for Heat", "Fuel for CO2"]].max(axis=1)

        chp_results["CO2 Emissions"] = gas_co2_per_Mwh * chp_results["Fuel requirement"] - co2_demand  # kg CO2 per hour

        return chp_results


class GEOTHERMAL(EnergySource):

    def geothermal_demand(self):
        cop = 5.5

        geothermal_results = pd.DataFrame(index=heat_demand.index)

        geothermal_results["Electricity for Heat"] = heat_demand / cop  # Electricity required to run geothermal system

        geothermal_results["CO2 Emissions"] = self.grid_emissions * geothermal_results["Electricity for Heat"]

        return geothermal_results


class WasteHeat(EnergySource):

    def wasteheat_demand(self):

        exchanger_efficiency = 0.85 # Assumption, this needs to be confirmed

        waste_heat_results = pd.DataFrame(index=heat_demand.index)

        waste_heat_results["Steam Required"] = heat_demand / exchanger_efficiency

        waste_heat_results["CO2 Emissions"] = 0  # No CO2 emissions from waste heat
        return waste_heat_results


class GSHP(EnergySource):

    def gshp_demand(self):

        cop = 3.5

        gshp_results = pd.DataFrame(index=heat_demand.index)

        gshp_results["Electricity for Heat"] = heat_demand / cop

        gshp_results["CO2 Emissions"] = self.grid_emissions * gshp_results["Electricity for Heat"]

        return gshp_results


class SolarPV(EnergySource):

    def solarpv_demand(self):

        solarpv_results = pd.DataFrame(index=heat_demand.index)

        solarpv_results["Electricity for Light"] = light_demand

        solarpv_results["CO2 Emissions"] = 0  # No CO2 emissions from solar PV

        return solarpv_results


class Grid(EnergySource):

    def grid_demand(self):

        grid_results = pd.DataFrame(index=heat_demand.index)

        grid_results["Electricity for Light"] = light_demand

        grid_results["CO2 Emissions"] = self.grid_emissions * grid_results["Electricity for Light"]

        return grid_results


class CarbonCapture(EnergySource):

    def carboncapture_demand(self):

        carboncapture_results = pd.DataFrame(index=heat_demand.index)

        carboncapture_results["CO2 Emissions"] = co2_demand

        return carboncapture_results


if __name__ == "__main__":
    inputs = inputs()
    htc_data = calculate_htc(inputs)
    heat_demand = calculate_heatdemand(inputs, htc_data)["Q_net,MWh"].astype(float)
    light_demand = calculate_lightdemand(inputs, htc_data, heat_demand)["MWh"].astype(float)
    co2_demand = calculate_co2demand(inputs, htc_data, heat_demand, light_demand)["Total CO2 Demand"].astype(float)

    energy_source = EnergySource(heat_demand, light_demand, co2_demand)

    chp = CHP(heat_demand, light_demand, co2_demand)
    chp_results = chp.chp_demand()

    geothermal = GEOTHERMAL(heat_demand, light_demand, co2_demand)
    geothermal_results = geothermal.geothermal_demand()

    wasteheat = WasteHeat(heat_demand, light_demand, co2_demand)
    wasteheat_results = wasteheat.wasteheat_demand()

    gshp = GSHP(heat_demand, light_demand, co2_demand)
    gshp_results = gshp.gshp_demand()

    solarpv = SolarPV(heat_demand, light_demand, co2_demand)
    solarpv_results = solarpv.solarpv_demand()

    grid = Grid(heat_demand, light_demand, co2_demand)
    grid_results = grid.grid_demand()

    print(chp_results)
