import numpy as np
from matplotlib import pyplot as plt

from YardBlock import YardBlock
from scipy.stats import expon
import seaborn as sns

def simulate(data):
    # Simulation period (months)
    period = 1

    # Converting the yard storage blocks dataframe into a list of objects
    yard_block_list = data['YARDSTORAGEBLOCKS'].astype({'Capacity': 'int'}).values.tolist()
    yard_blocks = []
    for x in yard_block_list:
        yard_blocks.append(YardBlock(x[0], x[1], x[2], x[3], 0, x[4], x[5]))

    # Sampling CG inter-arrival times
    get_inter_arrival_time_sample()


def get_inter_arrival_time_sample():
    # Todo: find the right distribution (for now we use an exponential distribution but it's to steep)
    return round(expon.rvs(scale=3, loc=0))

