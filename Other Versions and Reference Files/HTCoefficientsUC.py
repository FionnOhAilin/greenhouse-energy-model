def calculate_htc(inputs_data):
    from joblib import load
    import pandas as pd
    import numpy as np
    from joblib import dump
    from uncertainties import ufloat, umath, unumpy

    # Check if input data has uncertainty
    has_uncertainty = hasattr(inputs_data["climate"], 'attrs') and inputs_data["climate"].attrs.get('has_uncertainty',
                                                                                                    False)

    # gm_d = inputs_data["gm_d"]
    gm_r = inputs_data["gm_r"]
    gm_south = inputs_data["gm_south"]
    gm_side = inputs_data["gm_side"]
    gm_north = inputs_data["gm_north"]

    climate = inputs_data["climate"]
    # crop_co2 = inputs_data["crop_co2"]
    crop = inputs_data["crop"]
    # op_enviro = inputs_data["op_enviro"]
    # op_temp = inputs_data["op_temp"]
    op_temp_sp = inputs_data["op_temp_sp"]
    # op_light = inputs_data["op_light"]
    # op_co2 = inputs_data["op_co2"]

    global_assump = inputs_data["global_assump"]

    climate.index = pd.to_datetime(climate.index, dayfirst=True)
    op_temp_sp.index = pd.to_datetime(op_temp_sp.index, dayfirst=True)
    crop.index = pd.to_datetime(crop.index, dayfirst=True)

    # Create helper functions for working with uncertainty
    def get_value(series, col_name):
        """Get value from a series, using uncertainty if available"""
        if has_uncertainty and f"{col_name} (ufloat)" in series:
            return series[f"{col_name} (ufloat)"]
        return series[col_name]

    def calculate_with_uncertainty(func, *args):
        """Try to calculate with uncertainty, fall back to nominal if needed"""
        try:
            # First try with uncertainty
            return func(*args)
        except Exception as e:
            print(f"Falling back to nominal calculation: {e}")
            # Fall back to nominal values
            nominal_args = [arg.nominal_value if hasattr(arg, 'nominal_value') else arg for arg in args]
            return func(*nominal_args)

    # Heat Transfer Coefficients calculations
    htc = pd.DataFrame(index=climate.index)

    # Standard calculation using nominal values
    htc["Cover Temp"] = (2 / 3) * climate["Temperature K"] + (1 / 3) * op_temp_sp["Temperature K"]
    htc["Prandtl No"] = (global_assump.loc["Dynamic Viscosity of Air", "Value"] *
                         global_assump.loc["Specific Heat of Air", "Value"] /
                         global_assump.loc["Thermal Conductivity of air", "Value"])

    # Uncertainty calculation if available
    if has_uncertainty:
        try:
            htc["Cover Temp (ufloat)"] = (2 / 3) * get_value(climate, "Temperature K") + (1 / 3) * op_temp_sp[
                "Temperature K"]

            # Calculate Prandtl number with uncertainty if possible
            dynamic_viscosity = ufloat(global_assump.loc["Dynamic Viscosity of Air", "Value"],
                                       global_assump.loc[
                                           "Dynamic Viscosity of Air", "Value"] * 0.05)  # Assume 5% uncertainty
            specific_heat = ufloat(global_assump.loc["Specific Heat of Air", "Value"],
                                   global_assump.loc["Specific Heat of Air", "Value"] * 0.05)
            thermal_conductivity = ufloat(global_assump.loc["Thermal Conductivity of air", "Value"],
                                          global_assump.loc["Thermal Conductivity of air", "Value"] * 0.05)

            htc["Prandtl No (ufloat)"] = dynamic_viscosity * specific_heat / thermal_conductivity
        except Exception as e:
            print(f"Could not calculate Cover Temp with uncertainty: {e}")

    variable = ["re_no", "H_i", "H_o", "U-Value"]
    structure = ["Roof_", "South_Wall", "Side_Wall", "North_Wall"]

    # Roof H/T calculations
    # Standard calculation with nominal values
    htc["Roof Re No"] = (global_assump.loc["Air density", "Value"] *
                         climate["Wind Speed"] *
                         gm_r.loc["Characteristic Length Surface", "Value"] /
                         global_assump.loc["Dynamic Viscosity of Air", "Value"])

    htc["Roof h_i"] = 1.86 * (np.abs(op_temp_sp["Temperature K"] - htc["Cover Temp"])) ** 0.33

    htc["Roof h_o"] = ((global_assump.loc["Thermal Conductivity of air", "Value"] /
                        gm_r.loc["Characteristic Length Surface", "Value"]) *
                       0.037 * (htc["Roof Re No"] ** 0.8) * (htc["Prandtl No"] ** 0.33))

    x = ((1 / htc["Roof h_i"]) +
         (gm_r.loc["Number of Layers in Cover", "Value"] *
          (gm_r.loc["Characteristic Length", "Value"] /
           gm_r.loc["Material Thermal Conductivity", "Value"])))

    y = ((gm_r.loc["Number of Layers in Cover", "Value"] - 1) *
         (1 / gm_r.loc["Thermal Air Conductance", "Value"]) +
         (1 / htc["Roof h_o"]))

    htc["Roof U-Value"] = (x + y) ** -1

    # Uncertainty calculations for Roof H/T if available
    if has_uncertainty:
        try:
            air_density = ufloat(global_assump.loc["Air density", "Value"],
                                 global_assump.loc["Air density", "Value"] * 0.05)

            htc["Roof Re No (ufloat)"] = (air_density *
                                          get_value(climate, "Wind Speed") *
                                          gm_r.loc["Characteristic Length Surface", "Value"] /
                                          dynamic_viscosity)

            htc["Roof h_i (ufloat)"] = 1.86 * (abs(op_temp_sp["Temperature K"] - htc["Cover Temp (ufloat)"])) ** 0.33

            htc["Roof h_o (ufloat)"] = ((thermal_conductivity /
                                         gm_r.loc["Characteristic Length Surface", "Value"]) *
                                        0.037 * (htc["Roof Re No (ufloat)"] ** 0.8) *
                                        (htc["Prandtl No (ufloat)"] ** 0.33))

            x_ufloat = ((1 / htc["Roof h_i (ufloat)"]) +
                        (gm_r.loc["Number of Layers in Cover", "Value"] *
                         (gm_r.loc["Characteristic Length", "Value"] /
                          gm_r.loc["Material Thermal Conductivity", "Value"])))

            y_ufloat = ((gm_r.loc["Number of Layers in Cover", "Value"] - 1) *
                        (1 / gm_r.loc["Thermal Air Conductance", "Value"]) +
                        (1 / htc["Roof h_o (ufloat)"]))

            htc["Roof U-Value (ufloat)"] = (x_ufloat + y_ufloat) ** -1
        except Exception as e:
            print(f"Could not calculate Roof U-Value with uncertainty: {e}")

    # South wall H/T with nominal values
    htc["South Wall Re No"] = (global_assump.loc["Air density", "Value"] *
                               climate["Wind Speed"] *
                               gm_south.loc["Characteristic Length Surface", "Value"] /
                               global_assump.loc["Dynamic Viscosity of Air", "Value"])

    htc["South Wall h_i"] = 1.86 * (np.abs(op_temp_sp["Temperature K"] - htc["Cover Temp"])) ** 0.33

    htc["South Wall h_o"] = ((global_assump.loc["Thermal Conductivity of air", "Value"] /
                              gm_south.loc["Characteristic Length Surface", "Value"]) *
                             0.037 * (htc["South Wall Re No"] ** 0.8) * (htc["Prandtl No"] ** 0.33))

    x = ((1 / htc["South Wall h_i"]) +
         (gm_south.loc["Number of Layers in Cover", "Value"] *
          (gm_south.loc["Characteristic Length", "Value"] /
           gm_south.loc["Material Thermal Conductivity", "Value"])))

    y = ((gm_south.loc["Number of Layers in Cover", "Value"] - 1) *
         (1 / gm_south.loc["Thermal Air Conductance", "Value"]) +
         (1 / htc["South Wall h_o"]))

    htc["South Wall U-Value"] = (x + y) ** -1

    # South Wall with uncertainty if available
    if has_uncertainty:
        try:
            htc["South Wall Re No (ufloat)"] = (air_density *
                                                get_value(climate, "Wind Speed") *
                                                gm_south.loc["Characteristic Length Surface", "Value"] /
                                                dynamic_viscosity)

            htc["South Wall h_i (ufloat)"] = 1.86 * (
                abs(op_temp_sp["Temperature K"] - htc["Cover Temp (ufloat)"])) ** 0.33

            htc["South Wall h_o (ufloat)"] = ((thermal_conductivity /
                                               gm_south.loc["Characteristic Length Surface", "Value"]) *
                                              0.037 * (htc["South Wall Re No (ufloat)"] ** 0.8) *
                                              (htc["Prandtl No (ufloat)"] ** 0.33))

            x_ufloat = ((1 / htc["South Wall h_i (ufloat)"]) +
                        (gm_south.loc["Number of Layers in Cover", "Value"] *
                         (gm_south.loc["Characteristic Length", "Value"] /
                          gm_south.loc["Material Thermal Conductivity", "Value"])))

            y_ufloat = ((gm_south.loc["Number of Layers in Cover", "Value"] - 1) *
                        (1 / gm_south.loc["Thermal Air Conductance", "Value"]) +
                        (1 / htc["South Wall h_o (ufloat)"]))

            htc["South Wall U-Value (ufloat)"] = (x_ufloat + y_ufloat) ** -1
        except Exception as e:
            print(f"Could not calculate South Wall U-Value with uncertainty: {e}")

    # Side wall H/T with nominal values
    htc["Side Wall Re No"] = (global_assump.loc["Air density", "Value"] *
                              climate["Wind Speed"] *
                              gm_side.loc["Characteristic Length Surface", "Value"] /
                              global_assump.loc["Dynamic Viscosity of Air", "Value"])

    htc["Side Wall h_i"] = 1.86 * (np.abs(op_temp_sp["Temperature K"] - htc["Cover Temp"])) ** 0.33

    htc["Side Wall h_o"] = ((global_assump.loc["Thermal Conductivity of air", "Value"] /
                             gm_side.loc["Characteristic Length Surface", "Value"]) *
                            0.037 * (htc["Side Wall Re No"] ** 0.8) * (htc["Prandtl No"] ** 0.33))

    x = ((1 / htc["Side Wall h_i"]) +
         (gm_side.loc["Number of Layers in Cover", "Value"] *
          (gm_side.loc["Characteristic Length", "Value"] /
           gm_side.loc["Material Thermal Conductivity", "Value"])))

    y = ((gm_side.loc["Number of Layers in Cover", "Value"] - 1) *
         (1 / gm_side.loc["Thermal Air Conductance", "Value"]) +
         (1 / htc["Side Wall h_o"]))

    htc["Side Wall U-Value"] = (x + y) ** -1

    # Side Wall with uncertainty if available
    if has_uncertainty:
        try:
            htc["Side Wall Re No (ufloat)"] = (air_density *
                                               get_value(climate, "Wind Speed") *
                                               gm_side.loc["Characteristic Length Surface", "Value"] /
                                               dynamic_viscosity)

            htc["Side Wall h_i (ufloat)"] = 1.86 * (
                abs(op_temp_sp["Temperature K"] - htc["Cover Temp (ufloat)"])) ** 0.33

            htc["Side Wall h_o (ufloat)"] = ((thermal_conductivity /
                                              gm_side.loc["Characteristic Length Surface", "Value"]) *
                                             0.037 * (htc["Side Wall Re No (ufloat)"] ** 0.8) *
                                             (htc["Prandtl No (ufloat)"] ** 0.33))

            x_ufloat = ((1 / htc["Side Wall h_i (ufloat)"]) +
                        (gm_side.loc["Number of Layers in Cover", "Value"] *
                         (gm_side.loc["Characteristic Length", "Value"] /
                          gm_side.loc["Material Thermal Conductivity", "Value"])))

            y_ufloat = ((gm_side.loc["Number of Layers in Cover", "Value"] - 1) *
                        (1 / gm_side.loc["Thermal Air Conductance", "Value"]) +
                        (1 / htc["Side Wall h_o (ufloat)"]))

            htc["Side Wall U-Value (ufloat)"] = (x_ufloat + y_ufloat) ** -1
        except Exception as e:
            print(f"Could not calculate Side Wall U-Value with uncertainty: {e}")

    # North wall H/T with nominal values
    htc["North Wall Re No"] = (global_assump.loc["Air density", "Value"] *
                               climate["Wind Speed"] *
                               gm_north.loc["Characteristic Length Surface", "Value"] /
                               global_assump.loc["Dynamic Viscosity of Air", "Value"])

    htc["North Wall h_i"] = 1.247 * (np.abs(op_temp_sp["Temperature K"] - htc["Cover Temp"])) ** 0.33

    htc["North Wall h_o"] = ((global_assump.loc["Thermal Conductivity of air", "Value"] /
                              gm_north.loc["Characteristic Length Surface", "Value"]) *
                             0.037 * (htc["North Wall Re No"] ** 0.8) * (htc["Prandtl No"] ** 0.33))

    gm_north.loc["Characteristic Length", "Value"] = float(gm_north.loc["Characteristic Length", "Value"])
    gm_north.loc["Material 2 Thermal Conductivity", "Value"] = float(
        gm_north.loc["Material 2 Thermal Conductivity", "Value"])
    gm_north.loc["Number of Layers in Cover", "Value"] = float(gm_north.loc["Number of Layers in Cover", "Value"])
    gm_north.loc["Thermal Air Conductance", "Value"] = float(gm_north.loc["Thermal Air Conductance", "Value"])
    gm_north.loc["Material 1 Thickness", "Value"] = float(gm_north.loc["Material 1 Thickness", "Value"])
    gm_north.loc["Material 1 Thermal Conductivity", "Value"] = float(
        gm_north.loc["Material 1 Thermal Conductivity", "Value"])
    gm_north.loc["Material 2 Thickness", "Value"] = float(gm_north.loc["Material 2 Thickness", "Value"])
    gm_north.loc["Material 2 Thermal Conductivity", "Value"] = float(
        gm_north.loc["Material 2 Thermal Conductivity", "Value"])

    x = ((1 / htc["North Wall h_i"]) +
         (gm_north.loc["Material 1 Thickness", "Value"] /
          gm_north.loc["Material 1 Thermal Conductivity", "Value"]))

    y = ((gm_north.loc["Material 2 Thickness", "Value"] /
          gm_north.loc["Material 2 Thermal Conductivity", "Value"]) +
         (1 / htc["North Wall h_o"]))

    htc["North Wall U-Value"] = (x + y) ** -1

    # North Wall with uncertainty if available
    if has_uncertainty:
        try:
            htc["North Wall Re No (ufloat)"] = (air_density *
                                                get_value(climate, "Wind Speed") *
                                                gm_north.loc["Characteristic Length Surface", "Value"] /
                                                dynamic_viscosity)

            htc["North Wall h_i (ufloat)"] = 1.247 * (
                abs(op_temp_sp["Temperature K"] - htc["Cover Temp (ufloat)"])) ** 0.33

            htc["North Wall h_o (ufloat)"] = ((thermal_conductivity /
                                               gm_north.loc["Characteristic Length Surface", "Value"]) *
                                              0.037 * (htc["North Wall Re No (ufloat)"] ** 0.8) *
                                              (htc["Prandtl No (ufloat)"] ** 0.33))

            # Convert material values to ufloat with estimated uncertainty
            m1_thickness = ufloat(gm_north.loc["Material 1 Thickness", "Value"],
                                  gm_north.loc["Material 1 Thickness", "Value"] * 0.05)
            m1_conductivity = ufloat(gm_north.loc["Material 1 Thermal Conductivity", "Value"],
                                     gm_north.loc["Material 1 Thermal Conductivity", "Value"] * 0.05)
            m2_thickness = ufloat(gm_north.loc["Material 2 Thickness", "Value"],
                                  gm_north.loc["Material 2 Thickness", "Value"] * 0.05)
            m2_conductivity = ufloat(gm_north.loc["Material 2 Thermal Conductivity", "Value"],
                                     gm_north.loc["Material 2 Thermal Conductivity", "Value"] * 0.05)

            x_ufloat = (1 / htc["North Wall h_i (ufloat)"]) + (m1_thickness / m1_conductivity)
            y_ufloat = (m2_thickness / m2_conductivity) + (1 / htc["North Wall h_o (ufloat)"])

            htc["North Wall U-Value (ufloat)"] = (x_ufloat + y_ufloat) ** -1
        except Exception as e:
            print(f"Could not calculate North Wall U-Value with uncertainty: {e}")

    # Mark the dataframe as having uncertainty data
    if has_uncertainty:
        htc.attrs['has_uncertainty'] = True

    return htc


if __name__ == "__main__":
    from InputCalculationsUC import calculate_inputs

    inputs_data = calculate_inputs()
    htc = calculate_htc(inputs_data)