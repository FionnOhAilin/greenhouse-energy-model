import numpy as np

def merit_order_dispatch(demand, capacities):
    """
    Dispatch heat sources in a merit order, meaning the cheapest running costs first, for every hour.

    demand: hourly heat demand in MW - one value for each hour

    capacities: heat output capacity of each source in MW, cheapest first.
                convert to heat output before calling

    returns: 
        outputs: a list of hourly output arrays in MW, one per source in the same order as capacities
        unmet: hourly demand no source could cover, in MW
    
    """

    remaining = np.asarray(demand, dtype=float).copy() #turns the demand input to a numpy array
    outputs = [] # empty list to store each source's hourly output


    for capacity in capacities:
        output = np.minimum(remaining, capacity) # for every hour at once, take the smaller of what's left to cover and the source's capacity
        outputs.append(output) # add this source's hourly output to the end of the list
        remaining = remaining - output # subtract what was covered by this source, hour by hour, the next source in the loop only sees whats left to cover.

    return outputs, remaining 