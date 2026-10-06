import pandas as pd
import numpy as np

def calculate_solar_supply(climate, pv_efficiency=0.22, pv_area=1000):
    """
    Calculate the solar energy supply based on climate data.

    Args:
        climate (DataFrame):  A pandas DataFrame containing climate data with  solar_radiation columns (in W/m²).
        pv_efficiency (float): The efficiency of the photovoltaic panels (default: 0.22).
        pv_area (float): The area of the photovoltaic panels (in m²).

    Returns:
        DataFrame: Hourly electricity output in MWh 

    """

    # TODO: Implement the solar supply calculation based on the provided climate data.
    pass