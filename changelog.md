# Changelog

### 27/10/2026

### Fixed
- Average solar power: the MWh to MW conversion now lives inside a new module called units.py. This was decided because the conversion sat inside the optimiser where tests would be more fragile. The error that was made previously where 8.76 was used instead of 8760 is covered by a test.

### Added
- Solar Supply Test: for solar yield to test that 1kW of a solar array at max irradiation for a year (1000W/m2) results in 8.76MWh. 
- Average Power Test: tests that 8.76 MWh spread over 8760 hours is 0.001 MW or 1 kW
- GitHub actions workflow so any new tests I add run on every push and pull - required a new folder structure .github/workflows/tests.yml

### Changed
- `Optimise_dual_anealling.py` imports 'SolarSupply', from the package, not from the top level path.


### 04/11/2026

### Fixed
### Added
- dispatch.py: a script that takes the hourly heat demand and capacity of each source and loops over each source, cheapest first so each source covers what's left of the demand that it's capacity allows. 

- Added `tests/dispatch_test.py`: three unit tests for `merit_order_dispatch`.
  - Enough capacity: the cheapest source fills first and is capped at its capacity; the next source covers only the rest.
  - Not enough capacity: unmet demand appears only in hours where demand is above total installed capacity.
  - Energy balance: total supply plus unmet demand equals demand in every hour (no energy created or lost).
### Changed

### 05/11/2026 
### Added:
- `calculate_heat_dispatch()` to the optimiser: CHP runs first as must-run (surplus heat dumped), then geothermal, GSHP, waste heat and boiler are dispatched in merit order.
- `Geothermal.calculate_supply_from_dispatch()`: costs geothermal on its dispatched hourly output instead of a proportional share of demand. Geothermal now uses this in `calculate_total_cost`.
-`GSHP.calculate_supply_from_dispatch()`: cost GSHP on its dispatched hourly output instead of proportional demand. 

### Verified
- at full size, old and new methods give identical heat (402.14 MWh), electricity (73.12 MWh) and CO2 (24,274 kg). At half size, merit order gives 93% of annual heat vs 50% under the proportional split (heat load factor 22%).