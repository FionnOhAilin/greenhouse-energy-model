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


### 09/11/2026

### Added:
- ``WasteHeat.Calculate_supply_from_dispatch():`` waste heat is now costed on its hourly dispatched output; steam drawn = heat delivered / 0.93. Optimium solution didnt change.
- ``Boiler.Calculate_supply_from_dispatch():`` The boiler is now costed on its dispatched heat ouput (fuel = heat / 0.775). It is heat led onl. Added a zero-output guard to boiler opex.
- Added ``calculate_exhaust_co2()``: to the optimiser, boiler exhaust now follows the dispatched gas use.
- `Report_heat_dispatch():` prints annual heat in MWh and running hours for each source and an hourly energy balance check. Called from both the optimisers Main() and MainScript.py so it doesnt matter which i run.
- Added `check_hybrid_designs.py`: costs GSHP + boiler splits (no waste heat) directly through `_calculate_objective`, without the optimiser. Cheapest: 35% GSHP (0.0725 MW GSHP + 0.1346 MW boiler) at £109,682. The optimiser's no-waste-heat answer (GSHP alone, £120,735) is 9.2% more expensive and was the worst of all splits tested. Cost curve is flat between 30% and 40% GSHP (<£300). Target for optimiser tuning: £109,682 or lower.


### Fixed
- With only the boiler cost converted, the CO2 balance still credited the boiler with having exhaust from its old full-year profile. The optimiser exploited this and used a boiler capacity of 0.1993 MW to supply CO2, even though it wasn't counted as burning any gas (basically got free CO2). Adding `calculate_exhaust_CO2` fixed this. 


### Optimiser Investigation (optimiser-tuning)

### 1. Finding a target using direct search
- No-waste-heat case --> the optimiser returned GSHP alone at 0.2071 MW (grid 0.0792 MW, CO2 pump 30.2274 kg/h): £120,734.63
- `check_hybrid_designs.py` costs GSHP and boiler splits directly through the `_calculate_objective` where gshp covers a certain base load and boiler covers peak. 
- Best Split was 35% GSHP 65% Boiler = €109,682. Boiler alone and GSHP alone were the most expensive splits so that proves the optimiser is missing out. It is a search problem not a model problem. 

### 2. Experiment: visit 1.01 -> 2.62 
- Changed `visit` from 1.01 to 2.62 (default) with no waste heat and maxiter = 50. Result unchanged. This design is one of the hardcoded starting points and the search never improved on it.

### 3. First Diagnosis
 - My current explanation is that the optimimum lies on the edges of the constraints, and single-variable move always either breaks a constraint or makes it more expensive, random all-variable moves are never landing on a feasible, cheap design.  

### 4. Evidence from output files
- `optimisation_evaluations.csv` showed that almost every annealing design had all eight technologies switched on at small sizes.
- `optimisation_minima.csv` shows each new improvement, so the annealing did improve the design over 50 times and single variable moves can make real improvements.
- But each design still had nearly all technologies active. The overall winner was the hand picked starting point, ie it never improved over the setpoint.
- Unreachable Zeros: the search continuously tries random values, which rarely end up being exact zero. Capex scales as size^(scaling factor) so for example if a technology was only 10W capacity it could still cost >€100/yr. 
- Constraint coupling: removing one unit only helps a solution if another grows by the right amount in the same evaluation.

### 5. Bug found in the starting points
- Starting points 1 and 2 put `self.grid_max_power` in position 5 (waste heat) instead of position 6 (grid). Start 3 has 0.0319 in the waste heat slot (a commented-out line suggests grid was intended). Row 1 of the minima file shows the effect: no lighting supply and a £982M light penalty. Not yet fixed, to keep experiments separate.

### 6. Experiment: snap capacities below 2% of their upper bound to exactly zero
- `snap_to_zero()` sets any capacity below 2% of its upper bound to exactly 0. It is applied in `objective()` and to the final result. 
- Result: €120,607.53 from €120,734.63 but the design changed:
 - The annealing found a GSHP + boiler hybrid by itself for the first time: GSHP 0.0673 MW (6,056 h, base load) + boiler 0.1243 MW (2,194 h, peaks), close to the best split from direct search (0.0725 + 0.1346).
  - It also kept CHP 0.0106 MW and solar 0.0949 MW, with grid reduced to 0.0590 MW. These add roughly £11k vs the target.
- Interpretation: snapping fixed the unreachable-zeros problem; the heat side reached the hybrid. Constraint coupling remains on the light side: removing CHP and solar needs the grid to rise back to 0.0792 MW in the same move.
