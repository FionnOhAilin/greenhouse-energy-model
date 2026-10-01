import Lib.Cost
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import Lib.EnergyDemand

heat_demand = pd.read_json("heat_demand.json")
light_demand = pd.read_json("light_demand.json")
co2_demand = pd.read_json("co2_demand.json")

def plot_heat_cost_scale():
    # Define capacity ranges for each heat source in MW
    gshp_scale = np.linspace(0.207, 53, 100)
    geothermal_scale = np.linspace(0.207, 53, 100)
    wasteheat_scale = np.linspace(0.223, 56.99, 100)

    # Initialize lists to store EAC for each capacity
    gshp_eac = []
    geothermal_eac = []
    wasteheat_eac = []

    gshp_demand, gshp_max_power = Lib.EnergyDemand.GSHP(heat_demand, light_demand, co2_demand).calculate_max_supply()
    gshp_supply = Lib.EnergyDemand.GSHP(heat_demand, light_demand, co2_demand).calculate_supply(gshp_max_power,
                                                                                                gshp_max_power)
    gshp_fuel = gshp_supply["Electricity for Heat"].sum()
    gshp_energy_output = gshp_supply["Yearly Heat Output"].sum()
    co2_emissions = gshp_supply["Direct CO2 Emissions"].sum()

    geo_demand, geo_max_power = Lib.EnergyDemand.Geothermal(heat_demand, light_demand, co2_demand).calculate_max_supply()
    geo_supply = Lib.EnergyDemand.Geothermal(heat_demand, light_demand, co2_demand).calculate_supply(geo_max_power,
                                                                                                      geo_max_power)
    geo_fuel = geo_supply["Electricity for Heat"].sum()
    geo_energy_output = geo_supply["Yearly Heat Output"].sum()

    wh_demand, wh_max_power = Lib.EnergyDemand.WasteHeat(heat_demand, light_demand, co2_demand).calculate_max_supply()
    wh_supply = Lib.EnergyDemand.WasteHeat(heat_demand, light_demand, co2_demand).calculate_supply(wh_max_power,
                                                                                                    wh_max_power)
    wh_fuel = wh_supply["Steam Required"].sum()
    wh_energy_output = wh_supply["Yearly Heat Output"].sum()

    # Calculate EAC for GSHP at different capacities
    for capacity in gshp_scale:
        # Create GSHP instance with appropriate parameters for this capacity
        # Scaling energy output and fuel requirement proportionally with capacity
        gshp = Lib.Cost.GSHP(
            capital_cost=1297000 * capacity ** -0.21557,  # CAPEX formula from original code
            operational_cost=8000 * capacity / (gshp_energy_output*capacity/53),  # Estimated capacity factor of 0.4
            fuel_cost=228.1,  # Grid electricity price
            lifetime=25,
            power=capacity,
            energy_output=gshp_energy_output*capacity/53,  # Estimated capacity factor of 0.4
            fuel_requirement=gshp_fuel*capacity/53,  # Assuming COP of 3.5
            base_capex=0,
            cc_power=0,
            loan_term=20,
            co2_emissions=(capacity * 8760 * 0.4 / 3.5) * 234  # Grid emissions factor of 234 kg/MWh
        )

        # Calculate costs and get EAC
        _, _, _, _, _, _, eac = gshp.constant_cost()
        gshp_eac.append(eac)

    # Calculate EAC for Geothermal at different capacities
    for capacity in geothermal_scale:
        # Create Geothermal instance
        geothermal = Lib.Cost.Geothermal(
            capital_cost=2.89e6 * capacity ** -0.45 + 2.1e6,  # CAPEX formula from original code
            operational_cost=11000 * capacity / (geo_energy_output* capacity/53),  # Estimated capacity factor of 0.7
            fuel_cost=228.1,  # Grid electricity price
            lifetime=30,
            power=capacity,
            energy_output=geo_energy_output*capacity/53,  # Estimated capacity factor of 0.7
            base_capex=0,
            fuel_requirement=geo_fuel*capacity/53,  # Assuming COP of 5.5
            cc_power=0,
            loan_term=20,
            co2_emissions=(capacity * 8760 * 0.7 / 5.5) * 234  # Grid emissions factor
        )

        # Calculate costs and get EAC
        _, _, _, _, _, _, eac = geothermal.constant_cost()
        geothermal_eac.append(eac)

    # Calculate EAC for Waste Heat at different capacities
    for capacity in wasteheat_scale:
        # Create Waste Heat instance
        wasteheat = Lib.Cost.WasteHeat(
            capital_cost=0,  # Assuming no capital cost for waste heat
            operational_cost=0,  # Assuming no operational cost for the system
            fuel_cost=90.1 * 0.9,  # Using price from original code (90% of natural gas)
            lifetime=50,
            power=capacity,
            energy_output=wh_energy_output*capacity/56.99,  # Estimated capacity factor of 0.6
            fuel_requirement=wh_fuel*capacity/56.99,  # Assuming heat exchanger efficiency of 93%
            base_capex=0,
            cc_power=0,
            loan_term=20,
            co2_emissions=(capacity * 8760 * 0.6) * 55  # Estimated emissions for waste heat
        )

        # Calculate costs and get EAC
        _, _, _, _, _, _, eac = wasteheat.constant_cost()
        wasteheat_eac.append(eac)

    # Create plot
    plt.figure(figsize=(12, 8))
    plt.plot(gshp_scale, gshp_eac, label='GSHP', linewidth=2)
    plt.plot(geothermal_scale, geothermal_eac, label='Geothermal', linewidth=2)
    plt.plot(wasteheat_scale, wasteheat_eac, label='Waste Heat', linewidth=2)

    plt.xlabel('Capacity (MW)', fontsize=14)
    plt.ylabel('Equivalent Annual Cost (€)', fontsize=14)
    plt.title('Comparison of Heat Source Costs Across Different Capacities', fontsize=16)
    plt.legend(fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)

    # Add vertical line at 1 MW for reference
    plt.axvline(x=1, color='gray', linestyle='--', alpha=0.5)
    plt.text(1.05, max(max(gshp_eac), max(geothermal_eac), max(wasteheat_eac)) * 0.95, '1 MW',
             fontsize=10, color='gray')

    # Format y-axis with thousand separators
    plt.gca().get_yaxis().set_major_formatter(plt.matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

    # Calculate crossover points and annotate them
    find_and_annotate_crossovers(plt, gshp_scale, gshp_eac, geothermal_scale, geothermal_eac,
                                 'GSHP', 'Geothermal')
    find_and_annotate_crossovers(plt, gshp_scale, gshp_eac, wasteheat_scale, wasteheat_eac,
                                 'GSHP', 'Waste Heat')
    find_and_annotate_crossovers(plt, geothermal_scale, geothermal_eac, wasteheat_scale, wasteheat_eac,
                                 'Geothermal', 'Waste Heat')

    plt.tight_layout()
    plt.savefig('heat_cost_comparison.png', dpi=300)
    plt.show()

    # Create a dataframe with the results
    results = pd.DataFrame({
        'Capacity (MW)': gshp_scale,
        'GSHP EAC (€)': gshp_eac,
        'Geothermal EAC (€)': geothermal_eac,
        'Waste Heat EAC (€)': wasteheat_eac
    })

    # Save results to CSV
    results.to_csv('heat_cost_comparison_data.csv', index=False)

    print("Plot and data saved successfully.")
    return results


def find_and_annotate_crossovers(plt, x1, y1, x2, y2, label1, label2):
    """Find and annotate crossover points between two curves"""
    # Interpolate to find crossovers
    for i in range(1, len(x1)):
        if (y1[i - 1] > y2[i - 1] and y1[i] < y2[i]) or (y1[i - 1] < y2[i - 1] and y1[i] > y2[i]):
            # Linear interpolation to find crossover point
            x_cross = x1[i - 1] + (x1[i] - x1[i - 1]) * (y2[i - 1] - y1[i - 1]) / (
                        (y1[i] - y1[i - 1]) - (y2[i] - y2[i - 1]))
            y_cross = y1[i - 1] + (y1[i] - y1[i - 1]) * (x_cross - x1[i - 1]) / (x1[i] - x1[i - 1])

            # Annotate crossover
            plt.plot(x_cross, y_cross, 'ro', markersize=5)
            plt.annotate(f'{label1}/{label2} crossover\n{x_cross:.2f} MW, €{int(y_cross):,}',
                         xy=(x_cross, y_cross),
                         xytext=(x_cross + 2, y_cross + 100000),
                         arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8),
                         fontsize=9)


if __name__ == "__main__":
    # Run the plotting function
    data = plot_heat_cost_scale()
    print(f"Data points: {len(data)}")
    print(f"Capacity range: {data['Capacity (MW)'].min():.3f} - {data['Capacity (MW)'].max():.3f} MW")