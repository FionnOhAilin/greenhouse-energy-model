import pandas as pd
import pytest

from greenhouse_model.SolarSupply import SolarSupply

def make_climate(irradiance_w_m2, hours=8760):
    """Build one year of hourly climate data with constant irradiance"""
    index = pd.date_range("2023-01-01", periods=hours, freq= "h")
    return pd.DataFrame(
        {"Solar Radiation (South Roof)": [irradiance_w_m2] * hours},
        index = index,
    )

def test_1kw_array_production():
    # to test that a 1kw array of PV panels at full sun (1000W/m2 every hour) results in 8.76 MWh

    climate = make_climate(irradiance_w_m2=1000)

    supply = SolarSupply(climate).calculate_supply(capacity_kw=1)
    annual_mwh = supply["Yearly Total (MWh)"].iloc[0]

    assert annual_mwh == pytest.approx(8.76) 
