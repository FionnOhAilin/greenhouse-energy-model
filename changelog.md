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
