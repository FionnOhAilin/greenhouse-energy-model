## 2026-10-27: Unit conversions in their own module
- Why: the 8760-hour conversion sat inside `calculate_supplies`. Testing it there meant building the whole optimiser with the full demand data, which is slow and fragile.
- Effect: the conversion is now a small function in `units.py` that a test can call with plain numbers.
- Open question: whether the performance ratio belongs in `SolarSupply` or in the input data.


## 2026-11-05: CHP set to 'must-run' in the merit order for heating sources
- Why: CHP can support lighting and CO2 demand as well as heat. lighting does not yet have a profile the same way the heat does, so its value in the merit order would be undermined by that
- Effect: It's gonna be kept as 'must-run' until there is a lighting profile then moved in the merit order when lighting is time-resolved