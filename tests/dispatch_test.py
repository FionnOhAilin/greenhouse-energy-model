import numpy as np
from greenhouse_model.dispatch import merit_order_dispatch

def test_enough_capacity():
    # Demand set to 1, 3, 5 MW. Cheap source set as 2MW and Expensive source set as 4MW.
    outputs, unmet = merit_order_dispatch([1,3,5], [2,4])


    np.testing.assert_allclose(outputs[0],[1, 2, 2]) # cheap source fills first, capped at 2MW
    np.testing.assert_allclose(outputs[1],[0, 1, 3]) # expensive source only covers the rest
    np.testing.assert_allclose(unmet, [0, 0 , 0]) # total 6MW > than peak demand of 5MW, should be nothing 


def test_not_enough_capacity():
    # Demand set to 1, 3, 5 MW. Now only 2 + 2 = 4MW, installed, below the 5MW peak

    outputs, unmet = merit_order_dispatch([1, 3, 5], [2, 2])

    np.testing.assert_allclose(outputs[0], [1, 2, 2])
    np.testing.assert_allclose(outputs[1], [0, 1, 2])
    np.testing.assert_allclose(unmet, [0, 0, 1])


def test_energy_balance():
    # Every MW of demand must end up either being supplied by a source or counted as unmet.

    demand = np.array([0.5, 2.0, 4.5, 6.0, 1.2])

    outputs, unmet = merit_order_dispatch(demand, [1.5, 2.0, 1.0])
    np.testing.assert_allclose(sum(outputs) + unmet, demand)

