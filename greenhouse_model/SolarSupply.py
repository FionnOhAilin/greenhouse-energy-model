import pandas as pd


class SolarSupply:
    """
    Solar PV Supply - calculates hourly electricity output based on climate data.
    """

    def __init__(self, climate_data, surface="Solar Radiation (South Roof)"):
        self.irradiance = climate_data[surface].astype(float)
        self.time_index = climate_data.index
        """
        Initialise with hourly climate data from PVGIS

        climate_data: DataFrame with hourly solar radiation coloumn
        surface: coloumn name for irradiance data (W/m^2)
        """
    def calculate_supply(self, capacity_kw):
        """
        Calculate hourly PV electricity output.

        capacity_kw: installed system capacity in kilowatts

        returns DataFrame with:
        - Electricity Output (MWh): hourly generation
        - Yearly Total (MWh): annual sum of generation
        """

        df = pd.DataFrame(index=self.time_index)

        #Calculate hourly power output
        #Power (kW) = Irradiance (W/m^2) x Capacity (kW) / 1000 W/m^2
        hourly_power_kw = self.irradiance * capacity_kw / 1000 
    

        #Convert to energy: MWh = kW / 1000 
        df["Electricity Output (MWh)"] = hourly_power_kw / 1000

        #Yearly total
        yearly_mwh = df["Electricity Output (MWh)"].sum()
        df["Yearly Total (MWh)"] = yearly_mwh

        return df

if __name__ == "__main__":
    from InputCalculations import calculate_inputs
    inputs = calculate_inputs()
    climate = inputs["climate"]

    #Test 50 kW south roof
    solar = SolarSupply(climate)
    supply = solar.calculate_supply(capacity_kw=50)

    annual = supply["Yearly Total (MWh)"].iloc[0]
    print(f"50 kW South Roof: {annual:.2f} MWh/year")
    print(f"Capacity factor: {annual / (50 * 8.76):.3f}")