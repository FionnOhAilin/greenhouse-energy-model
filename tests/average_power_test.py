import pytest

from greenhouse_model.units import annual_mwh_to_average_mw


def test_average_power():

    # Test that this logic holds up:
    # 8.76 MWh spread over 8760 hours is 0.001 MW or 1 kW

    assert annual_mwh_to_average_mw(8.76) == pytest.approx(0.001)

