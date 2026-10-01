import pandas as pd
import numpy as np
from InputCalculations import inputs
from HTCoefficients import calculate_htc
from HeatDemand import calculate_heatdemand
from LightDemand import calculate_lightdemand
from CO2Demand import calculate_co2demand


class EnergySource:
    """
    Base class for different energy sources.
    """
    grid_emissions = 332  # kgCO₂ per MWh of electricity

    def __init__(self, heat_demand, light_demand, co2_demand):
        self._heat_demand = heat_demand["QnetMWh"].astype(float)
        self._light_demand = light_demand["MWh"].astype(float)
        self._co2_demand = co2_demand["Total CO2 Demand"].astype(float)

    def calculate_demand(self):
        raise NotImplementedError("Subclasses must implement demand calculations")


class CHP(EnergySource):
    gas_co2_per_Mwh = 184  # kgCO₂ per MWh of natural gas
    heat_to_electric_ratio = 1.51
    fuel_to_electric_efficiency = 0.333
    fuel_to_heat_efficiency = heat_to_electric_ratio / (1 / fuel_to_electric_efficiency)

    def calculate_demand(self):
        df = pd.DataFrame(index=self._heat_demand.index)
        df["Fuel for Light"] = self._safe_divide(self._light_demand, self.fuel_to_electric_efficiency)
        df["Fuel for Heat"] = self._safe_divide(self._heat_demand, self.fuel_to_heat_efficiency)
        df["Fuel for CO2"] = self._safe_divide(self._co2_demand, self.gas_co2_per_Mwh)
        df["Fuel Requirement"] = df.max(axis=1)
        df["CO2 Emissions"] = df["Fuel Requirement"] * self.gas_co2_per_Mwh - self._co2_demand
        df["Primary Driver"] = df[["Fuel for Light", "Fuel for Heat", "Fuel for CO2"]].idxmax(axis=1)
        return df

    @staticmethod
    def _safe_divide(numerator, denominator):
        numerator, denominator = np.broadcast_arrays(numerator, denominator)
        result = np.zeros_like(numerator, dtype=float)
        mask = denominator != 0
        result[mask] = numerator[mask] / denominator[mask]
        return result


class Geothermal(EnergySource):
    cop = 5.5

    def calculate_demand(self):
        df = pd.DataFrame(index=self._heat_demand.index)
        df["Electricity for Heat"] = self._heat_demand / self.cop
        df["CO2 Emissions"] = self.grid_emissions * df["Electricity for Heat"]
        return df


class GSHP(EnergySource):
    cop = 3.5

    def calculate_demand(self):
        df = pd.DataFrame(index=self._heat_demand.index)
        df["Electricity for Heat"] = self._heat_demand / self.cop
        df["CO2 Emissions"] = self.grid_emissions * df["Electricity for Heat"]
        return df


class WasteHeat(EnergySource):
    exchanger_efficiency = 0.85

    def calculate_demand(self):
        df = pd.DataFrame(index=self._heat_demand.index)
        df["Steam Required"] = self._heat_demand / self.exchanger_efficiency
        df["CO2 Emissions"] = 0
        return df


class SolarPV(EnergySource):
    def calculate_demand(self):
        df = pd.DataFrame(index=self._heat_demand.index)
        df["Electricity for Light"] = self._light_demand
        df["CO2 Emissions"] = 0
        return df


class Grid(EnergySource):
    def calculate_demand(self):
        df = pd.DataFrame(index=self._heat_demand.index)
        df["Electricity for Light"] = self._light_demand
        df["CO2 Emissions"] = self.grid_emissions * df["Electricity for Light"]
        return df


if __name__ == "__main__":
    input_data = inputs()
    htc_data = calculate_htc(input_data)
    heat_demand = calculate_heatdemand(input_data, htc_data)
    light_demand = calculate_lightdemand(input_data, htc_data, heat_demand)
    co2_demand = calculate_co2demand(input_data, htc_data, heat_demand, light_demand)

    chp = CHP(heat_demand, light_demand, co2_demand).calculate_demand()
    geothermal = Geothermal(heat_demand, light_demand, co2_demand).calculate_demand()
    gshp = GSHP(heat_demand, light_demand, co2_demand).calculate_demand()
    wasteheat = WasteHeat(heat_demand, light_demand, co2_demand).calculate_demand()
    solar = SolarPV(heat_demand, light_demand, co2_demand).calculate_demand()
    grid = Grid(heat_demand, light_demand, co2_demand).calculate_demand()

    print("Running EnergyDemand.py")
    print("Heat demand columns:", heat_demand.columns)