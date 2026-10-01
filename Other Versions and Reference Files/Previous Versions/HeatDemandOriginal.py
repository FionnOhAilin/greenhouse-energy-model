from InputCalculations import inputs
from HTCoefficients import calculate_htc


def calculate_heatdemand(inputs_dataframe, htc):

    from joblib import load
    import pandas as pd
    import numpy as np
    from joblib import dump

    dataframes = load("input_dataframes.joblib")
    htc_dataframes = load("htc_dataframes.joblib")

    gm_d = dataframes["gm_d"]
    gm_r = dataframes["gm_r"]
    gm_south = dataframes["gm_south"]
    gm_side = dataframes["gm_side"]
    gm_north = dataframes["gm_north"]

    climate = dataframes["climate"]

    crop_co2 = dataframes["crop_co2"]
    crop = dataframes["crop"]

    op_enviro = dataframes["op_enviro"]
    op_temp = dataframes["op_temp"]
    op_temp_sp = dataframes["op_temp_sp"]
    op_light = dataframes["op_light"]
    op_co2 = dataframes["op_co2"]

    global_assump = dataframes["global_assump"]

    htc = htc_dataframes["htc"]

    climate.index = pd.to_datetime(climate.index, dayfirst=True)
    op_temp_sp.index = pd.to_datetime(op_temp_sp.index, dayfirst=True)
    crop.index = pd.to_datetime(crop.index, dayfirst=True)
    htc.index = pd.to_datetime(htc.index, dayfirst=True)

    heat_demand = pd.DataFrame(index=climate.index)

    # Solar heat gain (Q_s)
    a = gm_r.loc["Solar Heat Gain Coefficient", "Value"] * ((gm_r.loc["Solar Transmissivity", "Value"] * gm_d.loc[
        "South Roof Area", "Value"] * climate["Solar Radiation (South Roof)"]) + (
                                                                        gm_r.loc["Solar Transmissivity", "Value"] *
                                                                        gm_d.loc["North Roof Area", "Value"] * climate[
                                                                            "Solar Radiation (North Roof)"]))
    b = gm_south.loc["Solar Heat Gain Coefficient", "Value"] * gm_south.loc["Solar Transmissivity", "Value"] * gm_d.loc[
        "South Wall Area", "Value"] * climate["Solar Radiation (South Wall)"]
    c = gm_side.loc["Solar Heat Gain Coefficient", "Value"] * ((gm_side.loc["Solar Transmissivity", "Value"] * gm_d.loc[
        "East Wall Area", "Value"] * climate["Solar Radiation (East Wall)"]) + (
                                                                           gm_side.loc["Solar Transmissivity", "Value"] *
                                                                           gm_d.loc["West Wall Area", "Value"] * climate[
                                                                               "Solar Radiation (West Wall)"]))

    gm_north.loc["Solar Heat Gain Coefficient", "Value"] = float(gm_north.loc["Solar Heat Gain Coefficient", "Value"])
    gm_north.loc["Solar Transmissivity", "Value"] = float(gm_north.loc["Solar Transmissivity", "Value"])
    d = gm_north.loc["Solar Heat Gain Coefficient", "Value"] * gm_north.loc["Solar Transmissivity", "Value"] * gm_d.loc[
        "North Wall Area", "Value"] * climate["Solar Radiation (North Wall)"]

    heat_demand["Q_s"] = a + b + c + d

    # Lighting Heat Gain (Q_sl)
    is_lighting_on = (
            (crop["Solar Radiation in Greenhouse"] < op_light.loc[
                "Switch off if solar radiation is greater than:", "Value"])
            & (climate.index.hour > op_light.loc["Time lighting is switched on", "Value"])
            & (climate.index.hour <= op_light.loc["Time lighting is switched off", "Value"])
    )

    heat_demand["Q_sl"] = np.where(
        is_lighting_on,
        op_light.loc["Installed Power of lamp", "Value"]
        * op_light.loc["Lighting Heat Conversion Factor", "Value"]
        * op_light.loc["Lighting Allowance Factor", "Value"]
        * gm_d.loc["Floor Area", "Value"],
        0,
    )

    # Motors Heat Gain (Q_m)
    heat_demand["Q_m"] = op_enviro.loc["No. of Air Recirculation Fans", "Value"] * (
                op_enviro.loc["Motor Power Rating", "Value"] / op_enviro.loc["Recirculation Motor Efficiency", "Value"]) * \
                         op_enviro.loc["Recirculation Motor Load Factor", "Value"] * op_enviro.loc[
                             "Recirculation Motor Use Factor", "Value"]

    # CO2 Heat Gain (Q_CO2)
    heat_demand["Q_co2"] = 0  # Assumed zero in excel

    # Total Heat Sources
    heat_demand["Sources"] = heat_demand["Q_m"] + heat_demand["Q_s"] + heat_demand["Q_sl"] + heat_demand["Q_co2"]

    # Conduction/Convection Heat Loss (Q_t), Air Exchange Heat Loss (Q_i), Perimeter Heat Loss (Q_p)
    for i in heat_demand.index:
        if (op_temp_sp.loc[i, "Temperature C"] - climate.loc[i, "Temperature C"]) > 0:
            a = htc["Roof U-Value"] * gm_d.loc["North Roof Area", "Value"]
            b = htc["Roof U-Value"] * gm_d.loc["South Roof Area", "Value"]
            c = htc["North Wall U-Value"] * gm_d.loc["North Wall Area", "Value"]
            d = htc["South Wall U-Value"] * gm_d.loc["South Wall Area", "Value"]
            e = htc["Side Wall U-Value"] * gm_d.loc["East Wall Area", "Value"]
            f = htc["Side Wall U-Value"] * gm_d.loc["West Wall Area", "Value"]
            heat_demand["Q_t"] = (a + b + c + d + e + f) * (op_temp_sp["Temperature C"] - climate["Temperature C"])

            heat_demand["Q_i"] = 0.33 * op_enviro.loc["Number of Air Exchanges per hour", "Value"] * gm_d.loc[
                "Greenhouse Volume", "Value"] * (op_temp_sp["Temperature C"] - climate["Temperature C"])

            heat_demand["Q_p"] = gm_south.loc["Perimeter Heat Loss Factor", "Value"] * gm_d.loc[
                "Greenhouse Perimeter", "Value"] * (op_temp_sp["Temperature C"] - climate["Temperature C"])

        else:
            heat_demand["Q_t"] = 0

            heat_demand["Q_i"] = 0

            heat_demand["Q_p"] = 0

        if (op_temp_sp.loc[i, "Temperature C"] - climate.loc[i, "Temperature C"]) > 0 and op_light.loc[
            "Time lighting is switched on", "Value"] < i.hour <= op_light.loc["Time lighting is switched off", "Value"]:
            heat_demand.loc[i, "Q_r,sr"] = global_assump.loc["Stefan-Boltzmann Constant", "Value"] * gm_r.loc[
                "Emissivity", "Value"] * gm_d.loc["South Roof Area", "Value"] * gm_r.loc["View Factor", "Value"] * (
                                                       (op_temp_sp.loc[i, "Temperature K"] ** 4) - (
                                                           htc.loc[i, "Cover Temp"] ** 4))

            heat_demand.loc[i, "Q_r,nr"] = global_assump.loc["Stefan-Boltzmann Constant", "Value"] * gm_r.loc[
                "Emissivity", "Value"] * gm_d.loc["North Roof Area", "Value"] * gm_r.loc["View Factor", "Value"] * (
                                                   (op_temp_sp.loc[i, "Temperature K"] ** 4) - (
                                                   htc.loc[i, "Cover Temp"] ** 4))

            heat_demand.loc[i, "Q_r,sw"] = global_assump.loc["Stefan-Boltzmann Constant", "Value"] * gm_south.loc[
                "Emissivity", "Value"] * gm_d.loc["South Wall Area", "Value"] * gm_south.loc["View Factor", "Value"] * (
                                                   (op_temp_sp.loc[i, "Temperature K"] ** 4) - (
                                                   htc.loc[i, "Cover Temp"] ** 4))

            heat_demand.loc[i, "Q_r,ew"] = global_assump.loc["Stefan-Boltzmann Constant", "Value"] * gm_side.loc[
                "Emissivity", "Value"] * gm_d.loc["East Wall Area", "Value"] * gm_side.loc["View Factor", "Value"] * (
                                                   (op_temp_sp.loc[i, "Temperature K"] ** 4) - (
                                                   htc.loc[i, "Cover Temp"] ** 4))

            heat_demand.loc[i, "Q_r,ww"] = global_assump.loc["Stefan-Boltzmann Constant", "Value"] * gm_side.loc[
                "Emissivity", "Value"] * gm_d.loc["West Wall Area", "Value"] * gm_side.loc["View Factor", "Value"] * (
                                                   (op_temp_sp.loc[i, "Temperature K"] ** 4) - (
                                                   htc.loc[i, "Cover Temp"] ** 4))

            heat_demand.loc[i, "Q_r,i"] = global_assump.loc["Stefan-Boltzmann Constant", "Value"] * global_assump.loc[
                "Emissivity of plants", "Value"] * global_assump.loc["Avg Transmissivity LW Radiation", "Value"] * \
                                          global_assump.loc["Sky View Factor", "Value"] * gm_d.loc[
                                              "Floor Area", "Value"] * ((op_temp_sp.loc[i, "Temperature K"] ** 4) - (
                        climate.loc[i, "Tsky"] ** 4))

        else:
            heat_demand.loc[i, "Q_r,sr"] = 0
            heat_demand.loc[i, "Q_r,nr"] = 0
            heat_demand.loc[i, "Q_r,sw"] = 0
            heat_demand.loc[i, "Q_r,ew"] = 0
            heat_demand.loc[i, "Q_r,ww"] = 0
            heat_demand.loc[i, "Q_r,i"] = 0

    # Ground Heat Loss (Q_g) ??not sure about this from excel??
    heat_demand["Q_g"] = 0

    # Total Radiative Heat Loss
    heat_demand["Q_r,total"] = heat_demand["Q_r,sr"] + heat_demand["Q_r,nr"] + heat_demand["Q_r,sw"] + heat_demand[
        "Q_r,ew"] + heat_demand["Q_r,ww"] + heat_demand["Q_r,i"] + heat_demand["Q_g"]

    # Evaporative Heat Loss (Q_e)
    heat_demand["Q_e"] = crop["Moisture Transfer Rate"] * global_assump.loc["Latent Heat of Water Vaporisation", "Value"]

    # Total Heat "Sinks
    heat_demand["Sinks"] = heat_demand["Q_t"] + heat_demand["Q_i"] + heat_demand["Q_p"] + heat_demand["Q_r,total"] + \
                           heat_demand["Q_e"]

    # Net Heat Requirement (Q_net,W) W
    for i in heat_demand.index:
        if (heat_demand.loc[i, "Sinks"] - heat_demand.loc[i, "Sources"]) > 0:
            heat_demand.loc[i, "Q_net,W"] = heat_demand.loc[i, "Sinks"] - heat_demand.loc[i, "Sources"]

        else:
            heat_demand.loc[i, "Q_net,W"] = 0

    # Net Heat Requirement (Q_net) MJ
    heat_demand["Q_net,MJ"] = heat_demand["Q_net,W"] * 3600 / 1e6

    # Net Heat Requirement (Q_net) kWh
    heat_demand["Q_net,MWh"] = heat_demand["Q_net,MJ"] / 3600
    heat_demand["Q_net,MWh2"] = heat_demand["Q_net,W"] / 1e6

    dump(dataframes, "HeatDemand_dataframes.joblib")

    return heat_demand


if __name__ == "__main__":
    inputs = inputs()
    htc = calculate_htc(inputs)
    heat_demand_og = calculate_heatdemand(inputs, htc)

