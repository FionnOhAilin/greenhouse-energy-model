import numpy as np
import pandas as pd
from greenhouse_model import EnergyDemand
from greenhouse_model.dispatch import merit_order_dispatch

heat_demand = pd.read_json("heat_demand.json")
light_demand = pd.read_json("light_demand.json")
co2_demand = pd.read_json("co2_demand.json")

geo = EnergyDemand.Geothermal(heat_demand, light_demand, co2_demand)
_, geo_max_power = geo.calculate_max_supply()

# Check 1: full size. Old and new must match exactly.
old = geo.calculate_supply(geo_max_power, geo_max_power)
outputs, unmet = merit_order_dispatch(heat_demand["QnetMWh"], [geo_max_power])
new = geo.calculate_supply_from_dispatch(outputs[0])

print(f"Unmet demand: {unmet.sum():,.2f} MWh")
for column in ["Yearly Heat Output", "Electricity for Heat", "Related CO2 Emissions"]:
    print(f"{column}: old {old[column].sum():,.2f}  new {new[column].sum():,.2f}")
    np.testing.assert_allclose(new[column], old[column])
print("Check 1 passed: old and new match at full size.\n")

# Check 2: half size. The methods should now differ.
half = 0.5 * geo_max_power
old_half = geo.calculate_supply(half, geo_max_power)
outputs_half, _ = merit_order_dispatch(heat_demand["QnetMWh"], [half])
new_half = geo.calculate_supply_from_dispatch(outputs_half[0])

total_heat = heat_demand["QnetMWh"].sum()
print(f"Half-size geothermal covers this share of annual heat:")
print(f"  Old (proportional split): {old_half['Yearly Heat Output'].sum() / total_heat:.0%}")
print(f"  New (merit order):        {new_half['Yearly Heat Output'].sum() / total_heat:.0%}")