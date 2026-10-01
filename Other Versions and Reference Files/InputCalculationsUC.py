def calculate_inputs():
    import pandas as pd
    import math
    import numpy as np
    from joblib import dump
    import os
    from uncertainties import ufloat, umath, unumpy

    date_files = ("Climate.csv", "Crop.csv", "Operation_TemperatureHourly")  # Defining files with date indexes

    def read_csv(file_name):
        # Get the base directory (Lib folder)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_dir, r"Lib\\CSV Inputs", os.path.basename(file_name))

        parse_dates = file_name in date_files
        x = pd.read_csv(full_path, index_col=0, parse_dates=parse_dates, skip_blank_lines=True)
        return x.dropna(how="all")

    def rad(x):
        z = math.radians(x)
        return z

    # Reading in all CSV files
    gm_d = read_csv("CSV Inputs/GreenhouseModel_Dimensions.csv")
    gm_r = read_csv("CSV Inputs/GreenhouseModel_Roof.csv")
    gm_south = read_csv("CSV Inputs/GreenhouseModel_SouthWall.csv")
    gm_side = read_csv("CSV Inputs/GreenhouseModel_SideWall.csv")
    gm_north = read_csv("CSV Inputs/GreenhouseModel_NorthWall.csv")

    climate = read_csv("CSV Inputs/Climate.csv")

    crop_co2 = read_csv("CSV Inputs/Crop_CO2.csv")
    crop = read_csv("CSV Inputs/Crop.csv")

    op_enviro = read_csv("CSV Inputs/Operation_Enviromental.csv")
    op_temp = read_csv("CSV Inputs/Operation_Temperature.csv")
    op_temp_sp = read_csv("CSV Inputs/Operation_TemperatureHourly.csv")
    op_light = read_csv("CSV Inputs/Operation_Lighting.csv")
    op_co2 = read_csv("CSV Inputs/Operation_CO2.csv")

    global_assump = read_csv("CSV Inputs/GlobalAssumptions.csv")

    # Greenhouse Model inter dependant calcs
    gm_r.loc["Characteristic Length Surface", "Value"] = gm_d.loc["South Roof Area", "Value"] / (
            2 * ((gm_d.loc["Width", "Value"] / 2) / math.cos(rad(gm_d.loc["Roof angle", "Value"]))) + 2 * gm_d.loc[
        "Length", "Value"])

    gm_r.loc["Characteristic Length", "Value"] = gm_r.loc["Material Thickness", "Value"]

    gm_r.loc["View Factor", "Value"] = (1 + math.cos(rad(gm_d.loc["Roof angle", "Value"]))) / 2

    gm_south.loc["Characteristic Length Surface", "Value"] = gm_d.loc["South Wall Area", "Value"] / (
            2 * gm_d.loc["Length", "Value"] + 2 * gm_d.loc["Wall height", "Value"])

    gm_south.loc["Characteristic Length", "Value"] = gm_south.loc["Material Thickness", "Value"]

    gm_side.loc["Characteristic Length Surface", "Value"] = gm_d.loc["East Wall Area", "Value"] / (
            2 * ((gm_d.loc["Width", "Value"] / 2) / math.cos(rad(gm_d.loc["Roof angle", "Value"]))) + (
            2 * gm_d.loc["Wall height", "Value"]) + gm_d.loc["Width", "Value"])

    gm_side.loc["Characteristic Length", "Value"] = gm_side.loc["Material Thickness", "Value"]

    gm_north.loc["Characteristic Length Surface", "Value"] = gm_d.loc["South Wall Area", "Value"] / (
            2 * gm_d.loc["Length", "Value"] + 2 * gm_d.loc["Wall height", "Value"])

    gm_north.loc["Characteristic Length", "Value"] = gm_north.loc["Total Material Thickness", "Value"]

    # Climate Calculations
    print("\n"
          "Please visit Met Eireann website for climate data:"
          "\n 1. Click Hourly Data, and select the station closest to your location"
          "\n 2. Click \"Download the full data series\" highlighted in blue"
          "\n https://www.met.ie/climate/available-data/historical-data"
          "\n\n Next visit The European Commission's PVGIS website for solar radiation data:"
          "\n 1. Select the location of your greenhouse"
          "\n 2. Click Hourly Data"
          "\n 3. Change the Start Year to 2005 and the end year to 2023"
          "\n 4. Click Download CSV"
          "\n https://re.jrc.ec.europa.eu/pvg_tools/en/"
          "\n Save both csv files in the CSV inputs folder"
          "\n Rename the climate data file to \"ClimateData.csv\" and the solar radiation data file to \"SolarRadiation.csv\"")
    input("\nPress Enter when you have downloaded and saved the files...")

    climate_data = pd.read_csv("CSV Inputs/ClimateData.csv", index_col=0, parse_dates=True,
                               skip_blank_lines=True, skiprows=23)
    # After reading the solar radiation files
    solar_radiation_nr = pd.read_csv("CSV Inputs/SolarRadiationNR.csv", skiprows=10, skip_blank_lines=True)
    solar_radiation_sr = pd.read_csv("CSV Inputs/SolarRadiationSR.csv", skiprows=10, skip_blank_lines=True)
    solar_radiation_nw = pd.read_csv("CSV Inputs/SolarRadiationNW.csv", skiprows=10, skip_blank_lines=True)
    solar_radiation_ew = pd.read_csv("CSV Inputs/SolarRadiationEW.csv", skiprows=10, skip_blank_lines=True)
    solar_radiation_sw = pd.read_csv("CSV Inputs/SolarRadiationSW.csv", skiprows=10, skip_blank_lines=True)
    solar_radiation_ww = pd.read_csv("CSV Inputs/SolarRadiationWW.csv", skiprows=10, skip_blank_lines=True)

    # Make sure the solar radiation DataFrames have the same length as climate_data
    if len(solar_radiation_nr) == len(climate_data):
        # Copy the datetime index from climate_data to the solar radiation DataFrames
        solar_radiation_nr.index = climate_data.index.copy()
        solar_radiation_sr.index = climate_data.index.copy()
        solar_radiation_nw.index = climate_data.index.copy()
        solar_radiation_ew.index = climate_data.index.copy()
        solar_radiation_sw.index = climate_data.index.copy()
        solar_radiation_ww.index = climate_data.index.copy()
    else:
        print(
            f"Warning: Index length mismatch. Climate data has {len(climate_data)} entries, but solar radiation has {len(solar_radiation_nr)} entries.")
        # You might need fallback logic here

    def calculate_hourly_statistics(df, start_year=2005, end_year=2023):
        """
        Calculate hourly averages and standard deviations for weather data
        filtered for years 2005-2023.
        """
        # Filter data for years 2005-2023 only
        if isinstance(df.index, pd.DatetimeIndex):
            print(f"Filtering data for years {start_year}-{end_year}...")
            filtered_df = df[(df.index.year >= start_year) & (df.index.year <= end_year)]
            print(f"Filtered data has {len(filtered_df)} rows (from original {len(df)} rows)")
        else:
            print("Warning: Index is not a DatetimeIndex, attempting to convert...")
            df.index = pd.to_datetime(df.index)
            filtered_df = df[(df.index.year >= start_year) & (df.index.year <= end_year)]

        # Extract time components
        filtered_df = filtered_df.copy()  # To avoid SettingWithCopyWarning
        filtered_df['hour'] = filtered_df.index.hour
        filtered_df['month'] = filtered_df.index.month
        filtered_df['day'] = filtered_df.index.day

        # Ensure all potentially numeric columns are converted to numeric type
        for col in filtered_df.columns:
            if filtered_df[col].dtype == 'object':
                filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce')

        # Get numeric columns (skipping any non-numeric data)
        numeric_columns = filtered_df.select_dtypes(include=['number']).columns.tolist()
        # Remove the hour, month, day columns we just added
        numeric_columns = [col for col in numeric_columns if col not in ['hour', 'month', 'day']]

        print(f"Calculating statistics for columns: {numeric_columns}")

        # Group by month, day, hour
        grouped = filtered_df.groupby(['month', 'day', 'hour'])

        # Calculate averages and standard deviations
        avg_values = grouped[numeric_columns].mean()
        std_values = grouped[numeric_columns].std().fillna(0)  # Replace NaN with 0

        print(f"Calculated statistics for {len(avg_values)} unique hour-day combinations")

        return avg_values, std_values, numeric_columns

    # Enhanced function to create dataframe with ufloat values
    def create_ufloat_dataframe(avg_df, std_df):
        """
        Create a DataFrame where each value is a ufloat combining the average and standard deviation.
        Also ensure values are accessible for numpy operations.
        """
        result = pd.DataFrame(index=avg_df.index)

        for column in avg_df.columns:
            # Create a series of ufloat objects
            values = [ufloat(avg, std) for avg, std in zip(avg_df[column], std_df[column])]
            result[column] = values

            # Also store nominal values to facilitate numpy operations
            result[f"{column}_nominal"] = [val.nominal_value for val in values]
            result[f"{column}_std"] = [val.std_dev for val in values]

        return result

    # Calculate hourly statistics for climate data
    avg_climate, std_climate, climate_columns = calculate_hourly_statistics(climate_data)
    ufloat_climate = create_ufloat_dataframe(avg_climate, std_climate)

    avg_solar_nr, std_solar_nr, solar_columns_nr = calculate_hourly_statistics(solar_radiation_nr)
    ufloat_solar_nr = create_ufloat_dataframe(avg_solar_nr, std_solar_nr)

    avg_solar_sr, std_solar_sr, solar_columns_sr = calculate_hourly_statistics(solar_radiation_sr)
    ufloat_solar_sr = create_ufloat_dataframe(avg_solar_sr, std_solar_sr)

    avg_solar_nw, std_solar_nw, solar_columns_nw = calculate_hourly_statistics(solar_radiation_nw)
    ufloat_solarNW = create_ufloat_dataframe(avg_solar_nw, std_solar_nw)

    avg_solar_ew, std_solar_ew, solar_columns_ew = calculate_hourly_statistics(solar_radiation_ew)
    ufloat_solarEW = create_ufloat_dataframe(avg_solar_ew, std_solar_ew)

    avg_solar_sw, std_solar_sw, solar_columns_sw = calculate_hourly_statistics(solar_radiation_sw)
    ufloat_solarSW = create_ufloat_dataframe(avg_solar_sw, std_solar_sw)

    avg_solar_ww, std_solar_ww, solar_columns_ww = calculate_hourly_statistics(solar_radiation_ww)
    ufloat_solarWW = create_ufloat_dataframe(avg_solar_ww, std_solar_ww)

    # Store the statistical results
    climate_statistics = {
        'averages': avg_climate,
        'std_deviations': std_climate,
        'ufloat_values': ufloat_climate
    }
    ufloat_climate.to_csv("CSV Inputs/ClimateStatistics.csv")

    # Create new climate DataFrame with both ufloat and nominal values
    climate = pd.DataFrame(index=climate_statistics['averages'].index)

    # Store the ufloat objects
    climate["Temperature C (ufloat)"] = climate_statistics["ufloat_values"]["temp"]
    climate["Temperature K (ufloat)"] = climate_statistics["ufloat_values"]["temp"].apply(lambda x: x + 273.15)
    climate["TDP (ufloat)"] = climate_statistics["ufloat_values"]["dewpt"]
    climate["Wind Speed (ufloat)"] = climate_statistics["ufloat_values"]["wdsp"].apply(
        lambda x: x * 0.514444)  # Convert from knots to m/s
    climate["Relative Humidity (ufloat)"] = climate_statistics["ufloat_values"]["rhum"]
    climate["CF (ufloat)"] = climate_statistics["ufloat_values"]["clamt"]

    # Also store nominal values for use with numpy functions
    climate["Temperature C"] = climate_statistics["averages"]["temp"]
    climate["Temperature K"] = climate_statistics["averages"]["temp"] + 273.15
    climate["TDP"] = climate_statistics["averages"]["dewpt"]
    climate["Wind Speed"] = climate_statistics["averages"]["wdsp"] * 0.514444
    climate["Relative Humidity"] = climate_statistics["averages"]["rhum"]
    climate["CF"] = climate_statistics["averages"]["clamt"]

    # Store ufloat solar radiation with error propagation
    # Combined radiation calculation for each surface
    for surface_name, data in [
        ("South Roof", ufloat_solar_sr),
        ("North Roof", ufloat_solar_nr),
        ("North Wall", ufloat_solarNW),
        ("East Wall", ufloat_solarEW),
        ("South Wall", ufloat_solarSW),
        ("West Wall", ufloat_solarWW)
    ]:
        # Store the ufloat objects with uncertainty
        climate[f"Solar Radiation ({surface_name}) (ufloat)"] = data["Gb(i)"] + data["Gd(i)"] + data["Gr(i)"]

        # Also store the nominal values for numpy operations
        climate[f"Solar Radiation ({surface_name})"] = (
                data["Gb(i)_nominal"] + data["Gd(i)_nominal"] + data["Gr(i)_nominal"]
        )

    # Calculate sky emissivity with uncertainty propagation
    # Use nominal values for numpy operations
    climate["Clear Sky Emissivity"] = 0.787 + 0.7641 * np.log(climate["Temperature K"] / 273)
    climate["Cloud Sky Emissivity"] = (1 + (0.0224 * climate["CF"]) - (0.0035 * climate["CF"] ** 2)
                                       + (0.00028 * climate["CF"] ** 3)) * climate["Clear Sky Emissivity"]
    climate["Tsky"] = climate["Temperature K"] * (climate["Cloud Sky Emissivity"] ** 0.25)

    # Also store uncertainty versions where possible
    try:
        climate["Clear Sky Emissivity (ufloat)"] = 0.787 + 0.7641 * climate["Temperature K (ufloat)"].apply(
            lambda x: umath.log(x / 273))

        # Store these attempts in a try block as they may be complex to calculate with ufloat
        cf_vals = climate["CF (ufloat)"]
        climate["Cloud Sky Emissivity (ufloat)"] = climate["Clear Sky Emissivity (ufloat)"] * (
                1 + (0.0224 * cf_vals) - (0.0035 * cf_vals ** 2) + (0.00028 * cf_vals ** 3))

        climate["Tsky (ufloat)"] = climate["Temperature K (ufloat)"] * climate["Cloud Sky Emissivity (ufloat)"].apply(
            lambda x: x ** 0.25)
    except Exception as e:
        print(f"Could not calculate sky emissivity with uncertainty: {e}")
        print("Continuing with nominal values only for these parameters.")

    # Crop inter dependant calcs
    crop["Solar Radiation in Greenhouse"] = (
            climate["Solar Radiation (South Roof)"] + climate["Solar Radiation (North Roof)"]
    )

    # Also store with uncertainty if available
    try:
        crop["Solar Radiation in Greenhouse (ufloat)"] = (
                climate["Solar Radiation (South Roof) (ufloat)"] + climate["Solar Radiation (North Roof) (ufloat)"]
        )
    except Exception as e:
        print(f"Could not calculate greenhouse solar radiation with uncertainty: {e}")

    crop["Photosynthetically Active Solar Radiation"] = crop["Solar Radiation in Greenhouse"] * 0.5 * 0.7 / 2
    avg_list = []

    for i in range(len(crop)):
        if i < 166:
            avg = crop["Photosynthetically Active Solar Radiation"][:167].mean()
        else:
            avg = crop["Photosynthetically Active Solar Radiation"][i - 167:i].mean()

        avg_list.append(avg)

    crop["I StomCond"] = avg_list
    crop["Saturation Temperature of Water Vapour"] = 0.61078 * (
        np.exp((17.27 * op_temp_sp["Temperature C"]) / (op_temp_sp["Temperature C"] + 237.3))) * 1000
    crop["Partial Pressure of Water Vapour"] = crop["Saturation Temperature of Water Vapour"] * (
                climate["Relative Humidity"] / 100)
    crop["Plant Surface Area"] = crop["Leaf Area Index"] * gm_d.loc["Floor Area", "Value"]
    crop["Saturated Humidity Ratio"] = 0.6219 * (crop["Saturation Temperature of Water Vapour"] / (
                global_assump.loc["Atmospheric Pressure", "Value"] - crop["Saturation Temperature of Water Vapour"]))
    crop["Humidity Ratio"] = 0.6219 * (crop["Partial Pressure of Water Vapour"] / (
                global_assump.loc["Atmospheric Pressure", "Value"] - crop["Partial Pressure of Water Vapour"]))
    crop["Aerodynamic Resistance"] = 220 * (
                (crop["Characteristic Length of leaf"] ** 0.2) / (op_enviro.loc["Indoor air Velocity", "Value"] ** 0.8))

    t = gm_r.loc["Solar Transmissivity", "Value"]
    i = (climate["Solar Radiation (South Roof)"] + climate["Solar Radiation (North Roof)"]) / 2
    crop["Stomatal Resistance"] = 200 * (1 + (1 / np.exp(0.05 * (t * i - 50))))
    crop["Moisture Transfer Rate"] = crop["Plant Surface Area"] * global_assump.loc["Air density", "Value"] * (
                (crop["Saturated Humidity Ratio"] - crop["Humidity Ratio"]) / (
                    crop["Aerodynamic Resistance"] + crop["Stomatal Resistance"]))

    # Operational Controls inter dependant
    start_hour = op_temp.loc["Daytime Start Hour", "Value"]
    end_hour = op_temp.loc["Nighttime Start Hour", "Value"]
    value_if_true = op_temp.loc["Set-point Daytime Temperature", "Value"]
    value_if_false = op_temp.loc["Set-point Nighttime Temperature", "Value"]

    op_temp_sp.index = pd.to_datetime(op_temp_sp.index, dayfirst=True)
    op_temp_sp["Temperature C"] = np.where(
        (op_temp_sp.index.hour > start_hour) & (op_temp_sp.index.hour < end_hour),
        value_if_true,
        value_if_false
    )
    op_temp_sp["Temperature K"] = op_temp_sp["Temperature C"] + 273.15

    # Global Assumptions inter dependant calcs
    x = (gm_d.loc["South Roof Area", "Value"] + gm_d.loc["North Roof Area", "Value"]) * gm_r.loc[
        "Long-wave Transmissivity", "Value"]
    y = gm_d.loc["South Wall Area", "Value"] * gm_south.loc["Long-wave Transmissivity", "Value"]
    z = (gm_d.loc["East Wall Area", "Value"] + gm_d.loc["West Wall Area", "Value"]) * gm_side.loc[
        "Long-wave Transmissivity", "Value"]
    a = gm_d.loc["South Wall Area", "Value"] + gm_d.loc["East Wall Area", "Value"] + gm_d.loc[
        "West Wall Area", "Value"] + gm_d.loc["South Roof Area", "Value"] + gm_d.loc["North Roof Area", "Value"]
    global_assump.loc["Avg Transmissivity LW Radiation", "Value"] = (x + y + z) / a

    # Add a flag to indicate uncertainty is enabled
    climate.attrs['has_uncertainty'] = True
    crop.attrs['has_uncertainty'] = True

    # Saving dataframes for use in other files
    inputs_dataframe = {
        "gm_d": gm_d,
        "gm_r": gm_r,
        "gm_south": gm_south,
        "gm_side": gm_side,
        "gm_north": gm_north,
        "climate": climate,
        "crop": crop,
        "crop_co2": crop_co2,
        "op_enviro": op_enviro,
        "op_temp": op_temp,
        "op_temp_sp": op_temp_sp,
        "op_light": op_light,
        "op_co2": op_co2,
        "global_assump": global_assump,
        "climate_data": climate_data,
    }

    return inputs_dataframe


if __name__ == "__main__":
    inputs_data = calculate_inputs()