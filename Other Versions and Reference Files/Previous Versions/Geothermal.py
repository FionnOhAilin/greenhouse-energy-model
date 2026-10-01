def geothermal():

    import pandas as pd
    import numpy as np
    from InputCalculations import inputs
    from HTCoefficients import calculate_htc
    from HeatDemand import calculate_heatdemand
    from LightDemandOriginal import calculate_lightdemand
    from CO2Demand import calculate_co2demand

    inputs_data = inputs()
    htc_data = calculate_htc(inputs_data)
    heat_demand = calculate_heatdemand(inputs_data, htc_data)["Q_net,MWh"].astype(float)
    light_demand = calculate_lightdemand(inputs_data, htc_data, heat_demand)["MWh"].astype(float)
    co2_demand = calculate_co2demand(inputs_data, htc_data, heat_demand, light_demand)["Total CO2 Demand"].astype(float)

    cop = 5.5  # Coefficient of Performance (COP) of deep geothermal system from GSI used in Excel model

    geothermal_results = pd.DataFrame(index=heat_demand.index)

    geothermal_results["Electricity for Heat"] = heat_demand / cop  # Electricity required to run geothermal system

    return geothermal_results


if __name__ == "__main__":
    geothermal_results = geothermal()
