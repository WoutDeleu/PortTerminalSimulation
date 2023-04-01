import os

from Data.DataParser import parse_data
from Data.Simulation import simulate
from Visualisation import visualise_data
from YardBlock import YardBlock


def load_data(folder):
    # find all plugins available and initialize them
    data = {}
    for f in os.listdir(folder):
        if '.py' in f or '__pycache__' in f:
            continue
        data[f.replace('.csv', '')] = parse_data(f)
    return data


data = load_data('./Data/')
# visualise_data(data)
simulate(data)


