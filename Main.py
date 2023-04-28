import math
import os

import matplotlib.pyplot as plt
import pandas as pd
from progress.bar import Bar

from Data.DataParser import parse_data
from Result_Parser import show_result
from Simulation import simulate_fifo

AMOUNT_SIMULATIONS = 1000

# LATEX formats table to copy paste in Latex-doc
LATEX = False
OVERVIEW = True


def load_data(folder):
    # find all plugins available and initialize them
    data = {}
    for f in os.listdir(folder):
        if '.py' in f or '__pycache__' in f:
            continue
        data[f.replace('.csv', '')] = parse_data(f)
    return data


def main():
    # startGUI()
    data = load_data('./Data/')
    # visualise_data(data)
    stats_fifo_closest_departure = pd.DataFrame(
        columns=['Containers_Rejected', 'CG_Rejected', 'Normal_Rejected', 'Reefer_Rejected', 'Total_Travel_Distance',
                 'AVG_Travel_Distance_Containers', 'Max_Occupancy', 'AVG_Daily_Individual_Occupancy',
                 'AVG_daily_total_Occupancy'])
    stats_fifo_closest_arrival = pd.DataFrame(
        columns=['Containers_Rejected', 'CG_Rejected', 'Normal_Rejected', 'Reefer_Rejected', 'Total_Travel_Distance',
                 'AVG_Travel_Distance_Containers', 'Max_Occupancy', 'AVG_Daily_Individual_Occupancy',
                 'AVG_daily_total_Occupancy'])

    i = 1
    d = 0.1
    deviations = []
    feature = 'AVG_Travel_Distance_Containers'
    # Progressbar - Only when using emulate in prompt
    with Bar('Simulating', fill='#', empty_fill='.', bar_prefix=' [',
             bar_suffix='] ', max=AMOUNT_SIMULATIONS) as bar:
        while i <= AMOUNT_SIMULATIONS:
            stats_fifo_closest_arrival = simulate_fifo(stats_fifo_closest_arrival, data, arrival_based=True)
            stats_fifo_closest_departure = simulate_fifo(stats_fifo_closest_departure, data, departure_based=True)
            sample_variance = calculate_sample_variance(stats_fifo_closest_arrival, feature)
            deviation = sample_variance/i
            print('\n')
            print(deviation)
            deviations.append(deviation)
            if deviation < d and i > 100:
                break
            bar.next()
            i += 1
    print(i)
    print('\n')

    plt.plot(range(0, len(deviations)), deviations)
    plt.ylim((0,round(max(deviations[1:]))))
    plt.xlabel("Number of runs")
    plt.ylabel(feature + " Deviation")
    plt.title("Deviation based on " + feature)
    plt.show()
    show_result('FIFO ARRIVAL-BASED', stats_fifo_closest_arrival, LATEX=LATEX, OVERVIEW=OVERVIEW)
    show_result('FIFO DEPARTURE-BASED', stats_fifo_closest_departure, LATEX=LATEX, OVERVIEW=OVERVIEW)


def calculate_sample_variance(stats_fifo, feature):
    average = stats_fifo[feature].mean()
    sum = 0
    for x in stats_fifo[feature]:
        sum += math.pow(x - average, 2)
    if len(stats_fifo[feature]) == 1:
        return 99999999
    return math.sqrt(sum / (len(stats_fifo[feature]) -1))

if __name__ == '__main__':
    main()