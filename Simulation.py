import numpy as np
from matplotlib import pyplot as plt

from ContainerGroup import ContainerGroup
from YardBlock import YardBlock
import scipy.stats as scipyst
import random
import seaborn as sns


def simulate(data):
    # Simulation period (months)
    period = 1
    period_in_hours = period * 24 * 30

    # Converting the yard storage blocks dataframe into a list of objects
    yard_block_list = data['YARDSTORAGEBLOCKS'].astype({'Capacity': 'int'}).values.tolist()
    yard_blocks = []
    for x in yard_block_list:
        yard_blocks.append(YardBlock(x[0], x[1], x[2], x[3], 0, x[4], x[5]))

    # Simulating the arrival of containers
    time = 0  # Simulation clock
    container_groups = []  # List of all container groups in the yard block
    while time < period_in_hours:  # Stop the simulation after the given period
        # Todo: find better sampling distributions (current ones are representative but probably not the best)
        time += get_inter_arrival_time_sample()
        a = get_container_type_sample()
        b = get_number_of_containers_sample()
        c = get_service_time_sample()
        d = get_arrival_point_sample()
        e = get_departure_point_sample()
        container_groups.append(ContainerGroup(a, b, time, c, d, e))  # New container arrived


def get_inter_arrival_time_sample():
    return round(scipyst.expon.rvs(scale=3, loc=0))


def get_container_type_sample():
    return random.choices(["normal", "reefer"], weights=[69, 31], k=1)


def get_number_of_containers_sample():
    return round(scipyst.expon.rvs(scale=5, loc=0))


def get_service_time_sample():
    return round(random.uniform(0, 166))


def get_arrival_point_sample():
    return 0


def get_departure_point_sample():
    return 0