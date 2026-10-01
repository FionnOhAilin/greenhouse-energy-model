def chp():
    import pandas as pd
    import numpy as np
    from InputCalculations import inputs
    from HTCoefficients import calculate_htc
    from HeatDemand import calculate_heatdemand
    from LightDemandOriginal import calculate_lightdemand
    from CO2Demand import calculate_co2demand

    # Constants
    gas_co2_per_Mwh = 184  # kgCO₂ per MWh of natural gas
    heat_to_electric_ratio = 1.51  # Taken from SEAI CHP in ireland 2020
    fuel_to_electric_efficiency = 0.333  # Taken from Excel model
    fuel_to_heat_efficiency = heat_to_electric_ratio / (1 / fuel_to_electric_efficiency)
    print(fuel_to_heat_efficiency)

    # calculate data for heat, light, and CO2 demand functions
    inputs_data = inputs()
    htc_data = calculate_htc(inputs_data)
    heat_demand = calculate_heatdemand(inputs_data, htc_data)["Q_net,MWh"].astype(float)
    light_demand = calculate_lightdemand(inputs_data, htc_data, heat_demand)["MWh"].astype(float)
    co2_demand = calculate_co2demand(inputs_data, htc_data, heat_demand, light_demand)["Total CO2 Demand"].astype(float)

    # Create DataFrame to store chp results
    chp_results = pd.DataFrame(index=heat_demand.index)

    # Calculate chp fuel requirements for light, heat, and CO2
    def safe_divide(numerator, denominator):
        numerator, denominator = np.broadcast_arrays(numerator, denominator)
        result = np.zeros_like(numerator, dtype=float)
        mask = denominator != 0
        result[mask] = numerator[mask] / denominator[mask]
        return result

    chp_results["Fuel for Light"] = safe_divide(light_demand.values, fuel_to_electric_efficiency)
    chp_results["Fuel for Heat"] = safe_divide(
        heat_demand,
        fuel_to_heat_efficiency
    )
    chp_results["Fuel for CO2"] = safe_divide(co2_demand.values, gas_co2_per_Mwh)

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

    chp_results["CO2 Emissions"] = gas_co2_per_Mwh * chp_results["Fuel requirement"]  # kg CO2 per hour

    return chp_results


if __name__ == "__main__":
    chp_results = chp()
    print(chp_results.head(24))  # Display the first 24 hours as an example
