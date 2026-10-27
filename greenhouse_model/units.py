HOURS_PER_YEAR = 8760

def annual_mwh_to_average_mw(annual_mwh, hours= HOURS_PER_YEAR):
    """
    This converts a yearly energy total in MWh into the average power in MW over a year.
    Average Power = energy / hours.

    """

    return annual_mwh / hours 