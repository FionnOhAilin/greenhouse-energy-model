import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import ScalarFormatter
import matplotlib.ticker as mticker
from matplotlib.dates import MonthLocator, DateFormatter
from datetime import datetime

"""Heat Demand Chart"""
heat_demand = pd.read_json("heat_demand.json")
light_demand = pd.read_json("light_demand.json")
co2_demand = pd.read_json("co2_demand.json")
climate_data = pd.read_json("climateDF.json")
crop_data = pd.read_json("cropDF.json")


def plot_monthly_heat_demand(heat_demand):
    """
    Create a bar chart of average daily heat demand by month with average temperature line.
    """
    # Check inputs
    if not isinstance(heat_demand.index, pd.DatetimeIndex):
        raise ValueError("Heat demand data index must be in datetime format.")

    if 'QnetMWh' not in heat_demand.columns:
        raise ValueError("Heat demand DataFrame must contain 'QnetMWh' column.")

    # Create a copy to avoid modifying the original
    heat_demand_processed = heat_demand.copy()

    # Create month and year columns
    heat_demand_processed['Month'] = heat_demand_processed.index.strftime('%b')
    heat_demand_processed['MonthNum'] = heat_demand_processed.index.year * 100 + heat_demand_processed.index.month

    avg_month_temp = climate_data['Temperature C'].resample('M').mean()

    # Group by month and calculate daily averages
    daily_avg_by_month = heat_demand_processed.groupby(['Month', 'MonthNum']).agg(
        AvgDailyHeatDemand=('QnetMWh', lambda x: x.sum() / (len(x) / 24))
    ).reset_index()

    # Sort chronologically
    daily_avg_by_month = daily_avg_by_month.sort_values('MonthNum')

    # Create figure and axis
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Create the bar chart on primary y-axis
    bars = ax1.bar(
        daily_avg_by_month['Month'],
        daily_avg_by_month['AvgDailyHeatDemand'],
        color='#C70039',
        width=0.7,
        label='Heat Demand'
    )

    # Format primary y-axis
    ax1.set_ylabel('Heat Demand (MWh/day)', fontsize=20, fontweight='bold')
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.1f}'))
    ax1.tick_params(axis='y', labelsize=18)

    # Create secondary y-axis and plot temperature
    ax2 = ax1.twinx()
    line = ax2.plot(range(len(avg_month_temp)), avg_month_temp.values,
                    color='blue', linewidth=3, label='Average Temperature')
    ax2.set_ylabel('Temperature (°C)', fontsize=20, fontweight='bold')
    ax2.tick_params(axis='y', labelsize=18)
    ax2.set_ylim(bottom=0)  # Set minimum temperature to 0

    # Combine legends from both axes
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2, fontsize=18)
    # Add grid for primary y-axis only
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    ax1.set_axisbelow(True)

    # Rotate x-axis labels
    ax1.set_xticklabels(ax1.get_xticklabels(), fontsize=18)

    # Ensure tight layout
    plt.tight_layout()

    # Show the plot
    plt.show()

    return daily_avg_by_month


"""Heat Demand Chart"""
plot_monthly_heat_demand(heat_demand)


def plot_monthly_light_demand(light_demand):
    """
    Create a bar chart of average daily light demand by month with solar radiation line.

    Args:
        light_demand (pd.DataFrame): DataFrame with light demand data and 'MWh' column
                                   Must have a datetime index.
        crop (pd.DataFrame): DataFrame with crop data including 'Solar Radiation in Greenhouse'
                           Must have a datetime index matching light_demand.
    """
    # Check inputs
    if not isinstance(light_demand.index, pd.DatetimeIndex):
        raise ValueError("Light demand data index must be in datetime format.")

    if 'MWh' not in light_demand.columns:
        raise ValueError("Light demand DataFrame must contain 'MWh' column.")

    # Create a copy to avoid modifying the original
    light_demand_processed = light_demand.copy()

    # Create month and year columns
    light_demand_processed['Month'] = light_demand_processed.index.strftime('%b')
    light_demand_processed['MonthNum'] = light_demand_processed.index.year * 100 + light_demand_processed.index.month

    crop = pd.read_json("cropDF.json")

    # Calculate monthly average solar radiation

    # Group by month and calculate daily averages for light demand
    daily_avg_by_month = light_demand_processed.groupby(['Month', 'MonthNum']).agg(
        AvgDailyLightDemand=('MWh', lambda x: x.sum() / (len(x) / 24))
    ).reset_index()

    # Sort chronologically
    daily_avg_by_month = daily_avg_by_month.sort_values('MonthNum')

    daily_avg_by_month.to_json("monthly_light_demand24hr.json")

    # Create figure and axis
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Create the bar chart on primary y-axis
    bars = ax1.bar(
        daily_avg_by_month['Month'],
        daily_avg_by_month['AvgDailyLightDemand'],
        color='#3498db',
        width=0.7,
        label='Light Demand'
    )

    # Format primary y-axis
    ax1.set_ylabel('Light Demand (MWh/day)', fontsize=20, fontweight='bold')
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.1f}'))
    ax1.tick_params(axis='y', labelsize=16)


    # Combine legends from both axes
    lines, labels = ax1.get_legend_handles_labels()


    # Add grid for primary y-axis only
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    ax1.set_axisbelow(True)

    # Set x-axis labels
    plt.xticks(fontsize=18)

    # Ensure tight layout
    plt.tight_layout()

    # Show the plot
    plt.show()

    return daily_avg_by_month


"""Light Demand Chart"""
# plot_monthly_light_demand(light_demand)


def plot_monthly_co2_demand(co2_demand):
    """
    Create a bar chart of average daily CO2 demand by month with solar radiation line overlay.

    Args:
        co2_demand (pd.DataFrame): DataFrame with CO2 demand data and 'Total CO2 Demand' column
                                  Must have a datetime index.
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    import numpy as np

    # Check inputs
    if not isinstance(co2_demand.index, pd.DatetimeIndex):
        raise ValueError("CO2 demand data index must be in datetime format.")

    if 'Total CO2 Demand' not in co2_demand.columns:
        raise ValueError("CO2 demand DataFrame must contain 'Total CO2 Demand' column.")

    # Create a copy to avoid modifying the original
    co2_demand_processed = co2_demand.copy()

    # Create month and year columns
    co2_demand_processed['Month'] = co2_demand_processed.index.strftime('%b')
    co2_demand_processed['MonthNum'] = co2_demand_processed.index.month

    # Group by month and calculate daily averages
    daily_avg_by_month = co2_demand_processed.groupby(['Month', 'MonthNum']).agg(
        AvgDailyCO2Demand=('Total CO2 Demand', lambda x: x.sum() / (len(x) / 24))
    ).reset_index()

    # Sort chronologically by month number
    daily_avg_by_month = daily_avg_by_month.sort_values('MonthNum')

    # Load crop data for solar radiation
    crop_data = pd.read_json("cropDF.json")

    # Calculate monthly average solar radiation
    crop_data['Month'] = crop_data.index.strftime('%b')
    crop_data['MonthNum'] = crop_data.index.month

    # Calculate average daily solar radiation by month
    solar_by_month = crop_data.groupby('MonthNum')['Solar Radiation in Greenhouse'].mean().reset_index()

    # Sort by month number
    solar_by_month = solar_by_month.sort_values('MonthNum')

    # Create figure and axes - use primary for CO2 demand, secondary for solar radiation
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Create the bar chart for CO2 demand on primary y-axis - USING DARKER GREEN #196f3d
    bars = ax1.bar(
        daily_avg_by_month['Month'],
        daily_avg_by_month['AvgDailyCO2Demand'],
        color='#196f3d',  # Darker green color for CO2
        width=0.7,
        label='CO₂ Demand'
    )

    # Format primary y-axis for CO2 demand
    ax1.set_ylabel('CO₂ Demand (kg/day)', fontsize=20, fontweight='bold')
    ax1.tick_params(axis='y', labelsize=18)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))

    # Create secondary y-axis for solar radiation
    ax2 = ax1.twinx()

    # Plot solar radiation line on secondary y-axis
    line = ax2.plot(
        daily_avg_by_month['Month'],
        solar_by_month['Solar Radiation in Greenhouse'],
        color='#c0392b',  # Red color for solar radiation
        linewidth=3,
        label='Solar Radiation'
    )

    # Format secondary y-axis for solar radiation
    ax2.set_ylabel('Solar Radiation (W/m²)', fontsize=20, fontweight='bold')
    ax2.tick_params(axis='y', labelsize=18)

    # Add grid for better readability (on primary axis only)
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    ax1.set_axisbelow(True)

    # Explicitly set the x-axis tick labels and their font size
    ax1.set_xticks(range(len(daily_avg_by_month['Month'])))
    ax1.set_xticklabels(daily_avg_by_month['Month'], fontsize=18)

    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center',
               bbox_to_anchor=(0.5, 1.15), ncol=2, fontsize=18)

    # Ensure tight layout with space for the legend
    plt.tight_layout()
    plt.subplots_adjust(top=0.88)

    # Show the plot
    plt.show()

    return daily_avg_by_month


"""CO2 Demand Chart"""
# plot_monthly_co2_demand(co2_demand)


def plot_co2_emissions(heat_demand, light_demand, co2_demand):
    """
    Create a bar chart comparing CO2 emissions from different energy sources with non-zero capacities.

    Args:
        heat_demand (pd.DataFrame): DataFrame with heat demand data
        light_demand (pd.DataFrame): DataFrame with light demand data
        co2_demand (pd.DataFrame): DataFrame with CO2 demand data

    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Import the EnergyDemand classes
    from EnergyDemand import CHP, Geothermal, GSHP, WasteHeat, SolarPV, Grid, Boiler, CO2Import

    # Define source capacities directly in the function
    source_capacities = {
        'CHP': 17.596773176324433,  # Example capacity for CHP in MW
        'Geothermal': 0.0,  # Example capacity for Geothermal in MW
        'GSHP': 0.0,  # Example capacity for GSHP in MW
        'WasteHeat': 0.0,  # Example capacity for WasteHeat in MW
        'Solar': 0.0,  # Example capacity for Solar in MW
        'Grid': 0.0,  # Example capacity for Grid in MW
        'Boiler': 40.953451086040346,  # Example capacity for Boiler in MW
        'CO2': 9334.2162578557  # Example capacity for CO2 in kg/h
    }

    # Map source names to their respective classes
    source_classes = {
        'CHP': CHP,
        'Geothermal': Geothermal,
        'GSHP': GSHP,
        'WasteHeat': WasteHeat,
        'Solar': SolarPV,
        'Grid': Grid,
        'Boiler': Boiler,
        'CO2': CO2Import
    }

    # Filter for sources with non-zero capacities
    active_sources = [source for source, capacity in source_capacities.items()
                      if capacity > 0 and source in source_classes]

    if not active_sources:
        # If no sources have capacity, return an empty figure with a message
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No energy sources with capacity > 0",
                ha='center', va='center', fontsize=14)
        ax.set_axis_off()
        return fig

    # Initialize lists for plotting
    sources_labels = []
    direct_emissions = []
    related_emissions = []
    net_emissions = []

    # Calculate emissions for each active source
    for source in active_sources:
        # Get the class for this source
        source_class = source_classes[source]

        # Create an instance of the source class
        source_instance = source_class(heat_demand, light_demand, co2_demand)

        # Get the capacity for this source
        capacity = source_capacities[source]

        # Calculate max supply and get demand data
        source_demand, max_power = source_instance.calculate_max_supply()

        # Calculate supply based on the source type
        if source in ['CHP', 'Boiler']:
            source_supply = source_instance.calculate_supply(capacity, max_power, source_demand)

            # Override direct emissions for CHP and Boiler as specified
            if source == 'CHP':
                # Direct CO2 emissions from Fuel for CO2
                direct_co2 = source_demand["Fuel for CO2"].sum() * CHP.gas_co2_per_Mwh
                related_co2 = source_supply["Related CO2 Emissions"].sum()
                net_co2 = direct_co2 + related_co2 - co2_demand["Net Photosynthesis"].sum()
            elif source == 'Boiler':
                # Direct CO2 emissions from Fuel for CO2
                direct_co2 = source_demand["Fuel for CO2"].sum() * Boiler.gas_co2_per_Mwh
                related_co2 = source_supply["Related CO2 Emissions"].sum()
                net_co2 = direct_co2 + related_co2 - co2_demand["Net Photosynthesis"].sum()
        else:
            source_supply = source_instance.calculate_supply(capacity, max_power)
            direct_co2 = source_supply["Direct CO2 Emissions"].sum()
            related_co2 = source_supply["Related CO2 Emissions"].sum()
            net_co2 = source_supply["Net CO2 Emissions"].sum()

        # Add the source name to the labels
        sources_labels.append(source)

        # Add the emissions data
        direct_emissions.append(direct_co2)
        related_emissions.append(related_co2)
        net_emissions.append(net_co2)

    # Create figure and axes
    fig, ax = plt.subplots(figsize=(10, 6))

    # Set width of bars
    bar_width = 0.35

    # Set positions of the bars on x-axis
    r1 = np.arange(len(sources_labels))
    r2 = [x + bar_width + 0.05 for x in r1]

    # Create bars - stack direct and related emissions for group 1
    p1 = ax.bar(r1, direct_emissions, bar_width, label='Direct Emissions', color='#E57373')
    p2 = ax.bar(r1, related_emissions, bar_width, bottom=direct_emissions, label='Related Emissions', color='#81C784')

    # Create bars for net emissions (group 2)
    p3 = ax.bar(r2, net_emissions, bar_width, label='Net Emissions', color='#5C6BC0')

    # Add labels, title and custom x-axis tick labels
    ax.set_ylabel('Annual CO₂ Emissions (kg)', fontsize=20)
    ax.set_xticks([r + bar_width / 2 for r in range(len(sources_labels))])
    ax.set_xticklabels(sources_labels, rotation=0, fontsize=14)
    ax.tick_params(axis='y', labelsize=14)

    # Calculate the maximum height needed for y-axis
    max_stacked_height = max([a + b for a, b in zip(direct_emissions, related_emissions)])
    y_max = 3e7  # Add 10% margin
    ax.set_ylim(0, y_max)

    # Format y-axis with commas for thousands
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))

    # Add legend
    ax.legend(loc='upper center', ncol=3, fontsize=14)

    # Add grid for better readability
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)

    # Adjust layout to make room for legend and rotated labels
    plt.tight_layout(rect=[0, 0, 1, 0.9])

    # Show the plot
    plt.show()

    return fig


"""CO2 Emissions Chart"""
# plot_co2_emissions(heat_demand, light_demand, co2_demand)


def plot_co2_emissions2(heat_demand, light_demand, co2_demand):
    """
    Create a bar chart comparing CO2 emissions from different energy sources with non-zero capacities.

    Args:
        heat_demand (pd.DataFrame): DataFrame with heat demand data
        light_demand (pd.DataFrame): DataFrame with light demand data
        co2_demand (pd.DataFrame): DataFrame with CO2 demand data

    Returns:
        matplotlib.figure.Figure: The created figure
    """
    # Import the EnergyDemand classes
    from EnergyDemand import CHP, Geothermal, GSHP, WasteHeat, SolarPV, Grid, Boiler, CO2Import

    # Define source capacities directly in the function
    source_capacities = {
        'CHP': 0.05698438687087806,  # Example capacity for CHP in MW
        'Geothermal': 0,  # Example capacity for Geothermal in MW
        'GSHP': 0,  # Example capacity for GSHP in MW
        'WasteHeat': 0,  # Example capacity for WasteHeat in MW
        'Solar': 0,  # Example capacity for Solar in MW
        'Grid': 0,  # Example capacity for Grid in MW
        'Boiler': 0.13262132079558708,  # Example capacity for Boiler in MW
        'CO2': 30.2273936843  # Example capacity for CO2 in kg/h
    }

    # Map source names to their respective classes
    source_classes = {
        'CHP': CHP,
        'Geothermal': Geothermal,
        'GSHP': GSHP,
        'WasteHeat': WasteHeat,
        'Solar': SolarPV,
        'Grid': Grid,
        'Boiler': Boiler,
        'CO2': CO2Import
    }

    # Filter for sources with non-zero capacities
    active_sources = [source for source, capacity in source_capacities.items()
                      if capacity > 0 and source in source_classes]

    if not active_sources:
        # If no sources have capacity, return an empty figure with a message
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "No energy sources with capacity > 0",
                ha='center', va='center', fontsize=14)
        ax.set_axis_off()
        return fig

    # Initialize lists for plotting
    sources_labels = []
    direct_emissions = []
    related_emissions = []
    net_emissions = []

    # Calculate emissions for each active source
    for source in active_sources:
        # Get the class for this source
        source_class = source_classes[source]

        # Create an instance of the source class
        source_instance = source_class(heat_demand, light_demand, co2_demand)

        # Get the capacity for this source
        capacity = source_capacities[source]

        # Calculate max supply and get demand data
        source_demand, max_power = source_instance.calculate_max_supply()

        # Calculate supply based on the source type
        if source in ['CHP', 'Boiler']:
            source_supply = source_instance.calculate_supply(capacity, max_power, source_demand)

            # Override direct emissions for CHP and Boiler as specified
            if source == 'CHP':
                # Direct CO2 emissions from Fuel for CO2
                direct_co2 = source_supply["Direct CO2 Emissions"].sum()
                related_co2 = source_supply["Related CO2 Emissions"].sum()
                net_co2 = source_supply["Net CO2 Emissions"].sum()
            elif source == 'Boiler':
                # Direct CO2 emissions from Fuel for CO2
                direct_co2 = source_supply["Direct CO2 Emissions"].sum()
                related_co2 = source_supply["Related CO2 Emissions"].sum()
                net_co2 = source_supply["Net CO2 Emissions"].sum()
        else:
            source_supply = source_instance.calculate_supply(capacity, max_power)
            direct_co2 = source_supply["Direct CO2 Emissions"].sum()
            related_co2 = source_supply["Related CO2 Emissions"].sum()
            net_co2 = source_supply["Net CO2 Emissions"].sum()

        # Add the source name to the labels
        sources_labels.append(source)

        # Add the emissions data
        direct_emissions.append(direct_co2)
        related_emissions.append(related_co2)
        net_emissions.append(net_co2)

    # Create figure and axes
    fig, ax = plt.subplots(figsize=(10, 6))

    # Set width of bars
    bar_width = 0.35

    # Set positions of the bars on x-axis
    r1 = np.arange(len(sources_labels))
    r2 = [x + bar_width + 0.05 for x in r1]

    # Create bars - stack direct and related emissions for group 1
    p1 = ax.bar(r1, direct_emissions, bar_width, label='Direct Emissions', color='#E57373')
    p2 = ax.bar(r1, related_emissions, bar_width, bottom=direct_emissions, label='Related Emissions', color='#81C784')

    # Create bars for net emissions (group 2)
    p3 = ax.bar(r2, net_emissions, bar_width, label='Net Emissions', color='#5C6BC0')

    # Add labels, title and custom x-axis tick labels
    ax.set_ylabel('Annual CO₂ Emissions (kg)', fontsize=20)
    ax.tick_params(axis='y', labelsize=14)
    ax.set_xticks([r + bar_width / 2 for r in range(len(sources_labels))])
    ax.set_xticklabels(sources_labels, rotation=45, fontsize=14)

    # Calculate the maximum height needed for y-axis
    max_stacked_height = max([a + b for a, b in zip(direct_emissions, related_emissions)])
    y_max = 12e4  # Add 10% margin
    ax.set_ylim(0, y_max)

    # Format y-axis with commas for thousands
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))

    # Add legend
    ax.legend(loc='upper right', ncol=3, fontsize=14)

    # Add grid for better readability
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)

    # Adjust layout to make room for legend and rotated labels
    plt.tight_layout(rect=[0, 0, 1, 0.9])

    # Show the plot
    plt.show()

    return fig

"""CO2 Emissions Chart for cost effective operation"""
# plot_co2_emissions2(heat_demand, light_demand, co2_demand)

def crop_yield_chart():
    """
    Create a horizontal bar chart comparing field crop yield vs greenhouse crop yield,
    with text labels to the right of the bars.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    # Data for the comparison
    categories = ['Greenhouse Crop Yield', 'Field Crop Yield']
    values = [0.45, 1.1]  # kg/plant

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(15, 3))

    # Set bar colors - blue for field, orange for greenhouse
    colors = ['#f6ab52', '#4a90e2']

    # Create the horizontal bar chart (note: plt.barh reverses the order)
    bars = ax.barh(
        [0.8, 0],  # Reverse order for top-to-bottom layout
        values,
        color=colors,
        height=0.6
    )

    # Add labels with different positioning for each bar
    for i, bar in enumerate(bars):
        width = bar.get_width()
        category = categories[1 - i]
        value = values[i]

        # Different positioning for Field Crop Yield (index 0) vs Greenhouse Crop Yield (index 1)
        if i == 0:  # Field Crop Yield (blue bar)
            ax.text(
                width + 0.05,  # Position text to the right of the bar
                bar.get_y() + bar.get_height() / 2,
                f'{category}: {value} kg/plant',
                ha='left',  # Left alignment for text outside
                va='center',
                color='black',
                fontsize=24,
                fontweight='bold'
            )
        else:  # Greenhouse Crop Yield (orange bar)
            ax.text(
                width / 2,  # Position text in the middle of the bar
                bar.get_y() + bar.get_height() / 2,
                f'{category}: {value} kg/plant',
                ha='center',  # Center alignment for text inside
                va='center',
                color='black',
                fontsize=24,
                fontweight='bold'
            )

    # Remove all axes, spines, ticks, etc.
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(bottom=False, left=False)
    ax.set_xticks([])
    ax.set_yticks([])

    # Set a larger x-limit to make room for the labels
    ax.set_xlim(0, max(values) + 0.2)

    # Set a tight layout with minimal margins
    plt.tight_layout()

    # Show the plot
    plt.show()

    return fig


"""Crop Yield Chart"""
#crop_yield_chart()

def chp_capital_scalling():

    capacities = np.arange(0.01,0.5,0.01)

    capex = 1.2e6 * capacities ** -0.4

    plt.figure(figsize=(10, 4))

    # Plot the fitted curve as a solid line
    plt.plot(capacities, capex, '-', color='blue', linewidth=2,
             label='1.2e6 * CHP Capacity^-0.4')

    # Add labels and title
    plt.xlabel('CHP Capacity (MW)', fontsize=20)
    plt.ylabel('Capital Cost (€/MW)', fontsize=20)

    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)

    ax = plt.gca()
    from matplotlib.ticker import FuncFormatter
    def millions_formatter(x, pos):
        return f'{x / 1e6:.1f}'

    ax.yaxis.set_major_formatter(FuncFormatter(millions_formatter))
    plt.ylabel('Capital Cost (M€/MW)', fontsize=20)  # Update label to reflect scaling

    # Add a legend
    plt.legend(fontsize=16)

    # Ensure tight layout
    plt.tight_layout()

    # Show the plot
    plt.show()


"""CHP Capital Scaling"""
# chp_capital_scalling()

def geothermal_capital_scalling():

    capacities = np.arange(0.1,150,0.1)

    capex = 2.89e6 * capacities ** -0.45 + 2.1e6

    capacities_2 = [5, 10, 15, 30, 75, 100, 125, 150]
    costs_per_mw = [3.29e6, 3.24e6, 3.14e6, 3.05e6, 2.66e6, 2.47e6, 2.29e6, 2.13e6]


    plt.figure(figsize=(10, 6))

    # Plot the fitted curve as a solid line
    plt.plot(capacities, capex, '-', color='blue', linewidth=2,
             label='2.89e6 * Geothermal Capacity^-0.45 + 2.1e6')

    plt.scatter(capacities_2, costs_per_mw, color='red', marker='x', s=60, label='Actual data points')

    # Add labels and title
    plt.xlabel('Geothermal Capacity (MW)', fontsize=20)
    plt.ylabel('Capital Cost (€/MW)', fontsize=20)

    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)

    ax = plt.gca()
    from matplotlib.ticker import FuncFormatter
    def millions_formatter(x, pos):
        return f'{x / 1e6:.1f}'

    ax.yaxis.set_major_formatter(FuncFormatter(millions_formatter))
    plt.ylabel('Capital Cost (Million €/MW)', fontsize=20)  # Update label to reflect scaling

    # Add a legend
    plt.legend(fontsize=16)

    # Ensure tight layout
    plt.tight_layout()

    # Show the plot
    plt.show()


"""Geothermal Capital Scaling"""
# geothermal_capital_scalling()

def gshp_capital_scalling():

    capacities = np.arange(0.01,5,0.01)

    capacities_2 = np.arange(0.1,5,0.2)

    capex = 1.297e6 * capacities ** -0.21557

    capex_2 = (1.297e6 * (capacities_2/1) ** 0.78443) / capacities_2

    plt.figure(figsize=(10, 6))

    # Plot the fitted curve as a solid line
    plt.plot(capacities, capex, '-', color='blue', linewidth=2,
             label='1.297e6 * GSHP Capacity^-0.21557')

    plt.plot(capacities_2, capex_2, 'x', color='red', linewidth=2,
             label='Vannoni et al (2023)')

    # Add labels and title
    plt.xlabel('GSHP Capacity (MW)', fontsize=20)
    plt.ylabel('Capital Cost (€/MW)', fontsize=20)

    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)

    ax = plt.gca()
    from matplotlib.ticker import FuncFormatter
    def millions_formatter(x, pos):
        return f'{x / 1e6:.1f}'

    ax.yaxis.set_major_formatter(FuncFormatter(millions_formatter))
    plt.ylabel('Capital Cost (M€/MW)', fontsize=20)  # Update label to reflect scaling

    # Add a legend
    plt.legend(fontsize=16)

    # Ensure tight layout
    plt.tight_layout()

    # Show the plot
    plt.show()


"""GSHP Capital Scaling"""
# gshp_capital_scalling()

def solar_capital_scalling():
    capacities_2 = [0.06, 0.1, 0.25, 0.235, 0.625, 0.999, 4, 0.005, 0.03, 0.15, 0.625, 1, 5]
    costs_per_mw = [1600000, 1500000, 1200000, 1200000, 1200000, 1575000, 1050000, 1950000, 2124000, 1860000, 1776000, 1572000,
                    1171000]

    capacities = np.arange(0.1, 5, 0.01)

    capex = 1572000*capacities**-0.15 - 150000

    plt.figure(figsize=(10, 6))

    # Plot the fitted curve as a solid line
    plt.plot(capacities, capex, '-', color='blue', linewidth=2,
             label='1572000 * Solar Capacity^-0.15 - 150000')

    plt.scatter(capacities_2, costs_per_mw, color='red', marker='x', s=60, label='Actual data points')

    # Add labels and title
    plt.xlabel('Solar Capacity (MW)', fontsize=20)
    plt.ylabel('Capital Cost (€/MW)', fontsize=20)

    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)

    ax = plt.gca()
    from matplotlib.ticker import FuncFormatter
    def millions_formatter(x, pos):
        return f'{x / 1e6:.1f}'

    ax.yaxis.set_major_formatter(FuncFormatter(millions_formatter))
    plt.ylabel('Capital Cost (Million €/MW)', fontsize=20)  # Update label to reflect scaling

    # Add a legend
    plt.legend(fontsize=16)

    # Ensure tight layout
    plt.tight_layout()

    # Show the plot
    plt.show()


"""Solar Capital Scaling"""
# solar_capital_scalling()

def boiler_capital_scalling():

    capacities = np.arange(0.01, 5, 0.01)

    capex = 1.03e5 * capacities ** -0.17

    capacities_2 = [0.007, 0.03, 0.1, 0.3, 1, 3]

    costs_per_mw = [215000, 182000, 155000, 130000, 103000, 78000]

    plt.figure(figsize=(10, 6))

    # Plot the fitted curve as a solid line
    plt.plot(capacities, capex, '-', color='blue', linewidth=2,
             label='1.03e5 * Boiler Capacity^-0.17')

    plt.scatter(capacities_2, costs_per_mw, color='red', marker='x', s=60, label='Actual data points')

    # Add labels and title
    plt.xlabel('Boiler Capacity (MW)', fontsize=20)
    plt.ylabel('Capital Cost (€/MW)', fontsize=20)

    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)

    ax = plt.gca()
    from matplotlib.ticker import FuncFormatter
    def millions_formatter(x, pos):
        return f'{x / 1e6:.1f}'

    ax.yaxis.set_major_formatter(FuncFormatter(millions_formatter))
    plt.ylabel('Capital Cost (M€/MW)', fontsize=20)  # Update label to reflect scaling

    # Add a legend
    plt.legend(fontsize=16)

    # Ensure tight layout
    plt.tight_layout()

    # Show the plot
    plt.show()

"""Boiler Capital Scaling"""
# boiler_capital_scalling()

def climate_data_plot():
    from matplotlib.dates import MonthLocator, DateFormatter

    climate = pd.read_json("climateDF.json")

    climate["Temperature SP"] = 20

    daily_avg_temp = climate['Temperature C'].resample('W').mean()

    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot the temperature data
    ax.plot(climate.index, climate['Temperature C'], label='Hourly Temperature', color='blue', linewidth=0.75)

    # Plot the average temperature
    ax.plot(daily_avg_temp.index, daily_avg_temp, label='Daily Avg Temperature', color='orange', linewidth=3)

    ax.plot(climate.index, climate['Temperature SP'], label='Temperature Setpoint', color='red', linewidth=2)

    ax.xaxis.set_major_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%b'))
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    ax.set_xlim(start_date, end_date)
    ax.tick_params(axis='x', labelsize=14)
    ax.tick_params(axis='y', labelsize=14)


    ax.set_ylabel('Temperature (°C)', fontsize=16, fontweight='bold')
    ax.legend(fontsize=14)


    plt.show()


"""Climate Data Plot"""
# climate_data_plot()

def plot_heat_sinks():
    # Resample to month start and get mean values
    cond_conv = heat_demand["Q_t"].resample('MS').mean()
    infiltration = heat_demand["Q_i"].resample('MS').mean()
    perimeter = heat_demand["Q_p"].resample('MS').mean()
    radiation = heat_demand["Q_r,total"].resample('MS').mean()
    evapotranspiration = heat_demand["Q_e"].resample('MS').mean()

    # Create a DataFrame with all components for easier stacking
    heat_losses = pd.DataFrame({
        'Convective': cond_conv,
        'Infiltration': infiltration,
        'Perimeter': perimeter,
        'Radiation': radiation,
        'Evapotranspiration': evapotranspiration
    })

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))

    # Create the stacked area chart
    ax.stackplot(heat_losses.index,
                 heat_losses['Convective'],
                 heat_losses['Infiltration'],
                 heat_losses['Perimeter'],
                 heat_losses['Radiation'],
                 heat_losses['Evapotranspiration'],
                 labels=['Conv/Cond Heat Loss', 'Infiltration Heat Loss',
                         'Perimeter Heat Loss', 'Radiation Heat Loss',
                         'Evapotranspiration Heat Loss'],
                 colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
                 alpha=0.7)

    # Calculate and plot the total heat loss
    total_loss = heat_losses.sum(axis=1)
    ax.plot(heat_losses.index, total_loss, color='black', linewidth=2.5,
            label='Total Heat Loss', linestyle='-')

    # Format the x-axis
    ax.xaxis.set_major_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%b'))
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 1)
    ax.set_xlim(start_date, end_date)

    # Add labels and styling
    ax.tick_params(axis='x', labelsize=14)
    ax.tick_params(axis='y', labelsize=14)
    ax.set_ylabel('Heat Loss (MJ/Day)', fontsize=16, fontweight='bold')

    # Add grid for better readability
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)

    # Format y-axis to show commas in thousands
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))

    # Add legend with better positioning
    ax.legend(fontsize=12, bbox_to_anchor=(0.5, 1.09),
              loc='center', ncol=3, frameon=True, facecolor='white', edgecolor='gray')

    # Ensure tight layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)  # Make room for the legend

    plt.show()

"""Heat Sinks Plot"""
# plot_heat_sinks()

def plot_heat_sources_with_demand(heat_demand):
    # Resample to month start and get mean values for heat sources

    solar = heat_demand["Q_s"].resample('D').sum().resample('MS').mean() * 3600 / 1e6 # Convert from W to MWh
    lighting = heat_demand["Q_sl"].resample('D').sum().resample('MS').mean() * 3600 / 1e6 # Convert from W to MWh
    motors = heat_demand["Q_m"].resample('D').sum().resample('MS').mean() * 3600 / 1e6 # Convert from W to MWh

    # Calculate daily average heat demand by month (convert from hourly to daily)
    # We're using the QnetMWh column, which represents the hourly heat demand in MWh
    daily_heat_demand = heat_demand["Q_net,MJ"].resample('D').sum().resample('MS').mean()

    # Create a DataFrame with all components for easier stacking
    heat_gains = pd.DataFrame({
        'Solar Radiation': solar,
        'Lighting': lighting,
        'Motors': motors,
    })

    # Create figure and axis
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Create the stacked area chart for heat sources
    ax1.stackplot(heat_gains.index,
                  heat_gains['Solar Radiation'],
                  heat_gains['Lighting'],
                  heat_gains['Motors'],
                  labels=['Solar Radiation', 'Lighting', 'Motors'],
                  colors=['#1f77b4', '#ff7f0e', '#2ca02c'],
                  alpha=0.7)

    # Calculate and plot the total heat gain
    total_gain = heat_gains.sum(axis=1)
    ax1.plot(heat_gains.index, total_gain, color='black', linewidth=2.5,
             label='Total Heat Gain', linestyle='-')

    # Format the primary y-axis
    ax1.set_ylabel('Heat Gain (MJ/Day)', fontsize=16, fontweight='bold')
    ax1.tick_params(axis='y', labelsize=14)
    ax1.grid(axis='y', linestyle='--', alpha=0.7)
    ax1.set_axisbelow(True)
    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))

    # Create secondary y-axis for heat demand
    ax2 = ax1.twinx()
    ax2.plot(daily_heat_demand.index, daily_heat_demand, color='red', linewidth=2.5,
             label='Heat Demand', linestyle='-')
    ax2.set_ylabel('Heat Demand (MJ/Day)', fontsize=16, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='red', labelsize=14)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.0f}'))

    # Format the x-axis
    ax1.xaxis.set_major_locator(MonthLocator())
    ax1.xaxis.set_major_formatter(DateFormatter('%b'))
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 1)
    ax1.set_xlim(start_date, end_date)
    ax1.tick_params(axis='x', labelsize=14)

    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               loc='upper center', bbox_to_anchor=(0.5, 1.15),
               ncol=5, frameon=True, fontsize=12)

    # Ensure tight layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)  # Make room for the legend

    plt.show()

    return fig

"""Heat Ources Plot"""
# plot_heat_sources_with_demand(heat_demand)

def plot_solar_radiation():
    """
    Create a plot comparing winter day and summer day solar radiation with lighting setpoint.
    """
    crop = pd.read_json("cropDF.json")

    # Filter data for winter and summer days
    # Looking at data for January 1st and July 1st
    winter_data = crop[crop.index.strftime('%m-%d') == '01-01']
    summer_data = crop[crop.index.strftime('%m-%d') == '07-01']

    # Extract the column for solar radiation
    winter_radiation = winter_data['Solar Radiation in Greenhouse']
    summer_radiation = summer_data['Solar Radiation in Greenhouse']

    # Get hour of day for x-axis
    winter_hours = [dt.hour for dt in winter_radiation.index]
    summer_hours = [dt.hour for dt in summer_radiation.index]

    # Light setpoint value
    hours = range(24)
    light_setpoint = pd.DataFrame({'hour': hours})

    # Set the light setpoint value: 250 between 7am and 10pm, 0 otherwise
    light_setpoint['setpoint'] = [250 if 7 <= h <= 21 else 0 for h in hours]    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot the solar radiation data
    ax.plot(winter_hours, winter_radiation.values,
            label='Winter Day (15th Jan)', color='#3498db', linewidth=2.5)
    ax.plot(summer_hours, summer_radiation.values,
            label='Summer Day (15th Jul)', color='#f39c12', linewidth=2.5)

    # Add horizontal line for light setpoint
    ax.plot(light_setpoint['hour'], light_setpoint['setpoint'],
            color='#e74c3c', linestyle='--', linewidth=2, label='Light Setpoint',
            drawstyle='steps-post')

    # Shade areas where winter radiation is below setpoint


    # Add labels and styling
    ax.set_xlabel('Hour of Day', fontsize=16, fontweight='bold')
    ax.set_ylabel('Solar Radiation (W/m²)', fontsize=16, fontweight='bold')


    # Set x-axis limits and ticks
    ax.set_xlim(0, 23)
    ax.set_xticks(range(0, 24, 1))

    # Add grid for better readability
    ax.set_axisbelow(True)

    # Add legend with better positioning
    ax.legend(fontsize=14, loc='upper center', bbox_to_anchor=(0.5, 1.13),
              ncol=3, frameon=True, facecolor='white', edgecolor='gray')


    # Customize tick labels
    ax.tick_params(axis='both', labelsize=14)

    # Ensure tight layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)  # Make room for the legend

    plt.show()

    return fig

# Call the function
# plot_solar_radiation()

def plot_light_operation_comparison():
    """
    Create a bar chart comparing lighting demand between 24hr operation and 7am-10pm operation.
    """
    # Load the JSON data
    light_demand_7_to_10 = pd.read_json("monthly_light_demand.json")
    light_demand_24hr = pd.read_json("monthly_light_demand24hr.json")

    # Merge the two datasets
    merged_data = pd.DataFrame({
        'Month': light_demand_7_to_10['Month'],
        'MonthNum': light_demand_7_to_10['MonthNum'],
        '7am-10pm Operation': light_demand_7_to_10['AvgDailyLightDemand'],
        '24hr Operation': light_demand_24hr['AvgDailyLightDemand']
    })

    # Sort by month number
    merged_data = merged_data.sort_values('MonthNum')

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(14, 8))

    # Set the width of bars
    bar_width = 0.4

    # Set positions of bars on x-axis
    months = merged_data['Month']
    x_pos = np.arange(len(months))

    # Create bars
    bar1 = ax.bar(x_pos - bar_width / 2, merged_data['7am-10pm Operation'],
                  bar_width, label='7am-10pm Operation', color='#3498db')
    bar2 = ax.bar(x_pos + bar_width / 2, merged_data['24hr Operation'],
                  bar_width, label='24hr Operation', color='#e74c3c')

    # Add labels, title and custom x-axis tick labels
    ax.set_ylabel('Light Demand (MWh/day)', fontsize=20, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(months, fontsize=18)
    ax.tick_params(axis='y', labelsize=18)

    # Add grid for y-axis only
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)

    # Format y-axis to show commas and one decimal place
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.1f}'))

    # Add legend
    ax.legend(fontsize=16, loc='upper center', bbox_to_anchor=(0.5, 1.1),
              ncol=2, frameon=True, facecolor='white', edgecolor='gray')

    # Ensure tight layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.9)  # Make room for the title and legend

    # Show the plot
    plt.show()

    return fig


# Call the function
# plot_light_operation_comparison()

def plot_infiltration_photosynthesis():
    """
    Create a stacked area chart showing CO2 loss rate (infiltration) below and net photosynthesis
    above it over the year.
    """
    # Resample to monthly averages of daily sums
    photosynthesis = co2_demand["Net Photosynthesis"].resample('D').sum().resample('MS').mean()
    infiltration = co2_demand["CO2 Loss Rate"].resample('D').sum().resample('MS').mean()

    # Create a DataFrame for easier plotting
    co2_data = pd.DataFrame({
        'Photosynthesis': photosynthesis.values,
        'Infiltration': infiltration.values
    }, index=photosynthesis.index)

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))

    # Create the stacked area chart - REVERSED ORDER!
    # Put Infiltration first (bottom layer) and Photosynthesis second (top layer)
    ax.stackplot(co2_data.index,
                 co2_data['Infiltration'],  # First (bottom) layer
                 co2_data['Photosynthesis'],  # Second (top) layer
                 labels=['Infiltration', 'Photosynthesis'],  # Match the order!
                 colors=['#c0392b', '#196f3d'],  # Match the order of colours too
                 alpha=0.7)

    # Add a line for the total (sum of both)
    total = co2_data['Photosynthesis'] + co2_data['Infiltration']
    ax.plot(co2_data.index, total, color='black', linewidth=2.5,
            label='CO₂ Demand', linestyle='-')

    # Format the x-axis
    ax.xaxis.set_major_locator(MonthLocator())
    ax.xaxis.set_major_formatter(DateFormatter('%b'))
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 1)
    ax.set_xlim(start_date, end_date)

    # Add labels and styling
    ax.set_ylabel('CO₂ (kg/day)', fontsize=20, fontweight='bold')
    ax.tick_params(axis='x', labelsize=18)
    ax.tick_params(axis='y', labelsize=18)

    # Format y-axis to show commas in thousands
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))

    # Add legend
    ax.legend(fontsize=18, loc='upper center', bbox_to_anchor=(0.5, 1.15),
              ncol=3, frameon=True, facecolor='white', edgecolor='gray')

    # Set title

    # Ensure tight layout with space for the legend and title
    plt.tight_layout()
    plt.subplots_adjust(top=0.85)

    # Show the plot
    plt.show()

    return fig


# Call the function
# plot_infiltration_photosynthesis()

def plot_cost_breakdown():
    """
    Create a stacked bar chart showing the cost breakdown (CAPEX, OPEX, Fuel Cost, CO2 Tax)
    for each energy source.
    """
    # Load the cost data
    costs_df = pd.read_json("costsDF_case2.json", lines=True)

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(14, 8))

    # Set the width of bars
    bar_width = 0.7

    # Set positions of bars on x-axis
    sources = costs_df['Energy Source']
    x_pos = np.arange(len(sources))

    # Extract cost components
    capex = costs_df['CAPEX']
    opex = costs_df['OPEX']
    fuel_cost = costs_df['Fuel Cost']
    co2_tax = costs_df['CO2 Tax']

    # Create the stacked bars
    p1 = ax.bar(x_pos, capex, bar_width, label='Capital Cost', color='#1f77b4')
    p2 = ax.bar(x_pos, opex, bar_width, bottom=capex, label='Operational Cost', color='#ff7f0e')

    # Calculate the bottom position for fuel cost (CAPEX + OPEX)
    bottom_fuel = capex + opex
    p3 = ax.bar(x_pos, fuel_cost, bar_width, bottom=bottom_fuel, label='Fuel Cost', color='#2ca02c')

    # Calculate the bottom position for CO2 tax (CAPEX + OPEX + Fuel Cost)
    bottom_co2 = capex + opex + fuel_cost
    p4 = ax.bar(x_pos, co2_tax, bar_width, bottom=bottom_co2, label='CO₂ Tax', color='#d62728')

    # Add labels, title, and custom x-axis tick labels
    ax.set_ylabel('Equivalent Annual Cost (€ x 10$^{6}$)', fontsize=20, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(sources, rotation=45, ha='right', fontsize=16)

    # Format y-axis with commas for thousands and K for thousands
    def thousands_formatter(x, pos):
        return f'€{x / 1e6:.0f}'

    ax.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    ax.tick_params(axis='y', labelsize=16)

    # Add legend
    ax.legend(fontsize=16, loc='upper right')

    # Add cost values on top of each stacked bar
    for i, source in enumerate(sources):
        total = costs_df.iloc[i]['Total Cost']
        ax.annotate(f'€{total / 1e6:.2f}',
                    (x_pos[i], total + 2000),
                    ha='center', va='bottom',
                    fontsize=14, fontweight='bold')

    # Ensure tight layout
    plt.tight_layout()

    # Show the plot
    plt.show()

    return fig


# Call the function
# plot_cost_breakdown()

import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter


def plot_optimized_cost_breakdown():
    """
    Create a stacked bar chart showing the cost breakdown (CAPEX, OPEX, Fuel Cost, CO2 Tax)
    for the optimized energy sources from optimization_results.json.
    """
    # Load the optimization results
    with open("optimization_results.json", "r") as f:
        optimization_results = json.load(f)

    # Extract optimized cost components
    opt_costs = optimization_results["optimised_cost_components"]

    # Filter out sources with zero total cost
    active_sources = [source for source, costs in opt_costs.items() if costs["total"] > 0]

    if not active_sources:
        print("No active sources found with costs > 0")
        return None

    # Create a DataFrame to hold the cost data
    data = []
    for source in active_sources:
        # Get cost components, handling potentially missing keys
        costs = opt_costs[source]
        capex = costs.get("capex", 0)
        opex = costs.get("opex", 0)
        fuel = costs.get("fuel", 0)
        co2_tax = costs.get("co2_tax", 0)
        total = costs.get("total", 0)

        data.append({
            "Energy Source": source,
            "CAPEX": capex,
            "OPEX": opex,
            "Fuel Cost": fuel,
            "CO2 Tax": co2_tax,
            "Total Cost": total
        })

    costs_df = pd.DataFrame(data)

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 14))

    # Set the width of bars
    bar_width = 0.7

    # Set positions of bars on x-axis
    sources = costs_df['Energy Source']
    x_pos = np.arange(len(sources))

    # Extract cost components
    capex = costs_df['CAPEX']
    opex = costs_df['OPEX']
    fuel_cost = costs_df['Fuel Cost']
    co2_tax = costs_df['CO2 Tax']

    # Create the stacked bars
    p1 = ax.bar(x_pos, capex, bar_width, label='Capital Cost', color='#1f77b4')
    p2 = ax.bar(x_pos, opex, bar_width, bottom=capex, label='Operational Cost', color='#ff7f0e')

    # Calculate the bottom position for fuel cost (CAPEX + OPEX)
    bottom_fuel = capex + opex
    p3 = ax.bar(x_pos, fuel_cost, bar_width, bottom=bottom_fuel, label='Fuel Cost', color='#2ca02c')

    # Calculate the bottom position for CO2 tax (CAPEX + OPEX + Fuel Cost)
    bottom_co2 = capex + opex + fuel_cost
    p4 = ax.bar(x_pos, co2_tax, bar_width, bottom=bottom_co2, label='CO₂ Tax', color='#d62728')

    # Add labels, title, and custom x-axis tick labels
    ax.set_ylabel('Equivalent Annual Cost (€ x 10$^{6}$)', fontsize=30, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(sources, rotation=45, ha='right', fontsize=26)
    max_stacked_height = max(costs_df['Total Cost'])
    y_max = max_stacked_height * 1.2  # Add 20% margin instead of a fixed value
    ax.set_ylim(0, y_max)

    # Format y-axis with thousands separator
    def thousands_formatter(x, pos):
        if x >= 1e6:
            return f'€{x / 1e6:.1f}'
        elif x >= 1e3:
            return f'€{x / 1e3:.0f}'
        else:
            return f'€{x:.0f}'

    ax.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))
    ax.tick_params(axis='y', labelsize=26)

    # Add legend
    # Add legend
    ax.legend(fontsize=26,
              loc='upper center',  # Center the legend at the top
              bbox_to_anchor=(0.5, 1.15),  # Adjust the vertical position
              ncol=2,  # Set the number of columns to 2
              frameon=True,  # Optional: add a frame to the legend
              facecolor='white',  # Optional: set legend background color
              edgecolor='gray')  # Optional: set legend border color

    # Add cost values on top of each stacked bar
    for i, source in enumerate(sources):
        total = costs_df.iloc[i]['Total Cost']
        if total >= 1e6:
            label = f'€{total / 1e6:.2f}'
        elif total >= 1e3:
            label = f'€{total / 1e3:.1f}'
        else:
            label = f'€{total:.0f}'

        ax.annotate(label,
                    (x_pos[i], total + (max(costs_df['Total Cost']) * 0.02)),  # Add small percentage of max for padding
                    ha='center', va='bottom',
                    fontsize=26, fontweight='bold')

    # Ensure tight layout
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])  # Make room for the total cost text

    # Show the plot
    plt.show()

    return fig, costs_df

# Example usage:
# plot_optimized_cost_breakdown()
