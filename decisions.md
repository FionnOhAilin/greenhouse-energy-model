## 2026-10-27: Unit conversions in their own module
- Why: the 8760-hour conversion sat inside `calculate_supplies`. Testing it there meant building the whole optimiser with the full demand data, which is slow and fragile.
- Effect: the conversion is now a small function in `units.py` that a test can call with plain numbers.
- Open question: whether the performance ratio belongs in `SolarSupply` or in the input data.