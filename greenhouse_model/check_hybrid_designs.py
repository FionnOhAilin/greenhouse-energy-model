import numpy as np
import pandas as pd
from InputCalculations import calculate_inputs
from greenhouse_model.Optimise_dual_anealling import OptimiseEnergySources

# Same data loading as the optimiser's main()
heat_demand = pd.read_json("heat_demand.json")
light_demand = pd.read_json("light_demand.json")
co2_demand = pd.read_json("co2_demand.json")
climate_data = calculate_inputs()["climate"]

optimiser = OptimiseEnergySources(heat_demand, light_demand, co2_demand, climate_data)

peak_heat = optimiser.max_heat        # 0.2071 MW, to full precision
grid = optimiser.max_light            # lighting grid connection, same as the optimum
co2_pump = optimiser.co2_max_power    # pump sized to peak CO2, so no CO2 shortfall

print("\nGSHP + boiler designs (no waste heat), each sized to meet the heat peak exactly:")
for gshp_share in [0.40, 0.35, 0.30, 0.25, 0.20, 0.15, 0.10, 0.05]:
    gshp = gshp_share * peak_heat
    boiler = peak_heat - gshp
    #             chp geo gshp solar waste grid  boiler  co2
    x = np.array([0,  0,  gshp, 0,   0,    grid, boiler, co2_pump])
    cost = optimiser._calculate_objective(x)
    print(f"  GSHP {gshp:.4f} MW + boiler {boiler:.4f} MW: £{cost:,.0f}")