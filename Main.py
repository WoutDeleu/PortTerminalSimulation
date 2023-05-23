import time

import pandas as pd
from progress.bar import Bar

from Data.DataParser import load_data
from Result_Parser import show_result
from Simulation import simulate

simulation_data = ['Containers_Rejected', 'CG_Rejected', 'Normal_Rejected', 'Reefer_Rejected', 'Total_Travel_Distance',
                   'AVG_Travel_Distance_Containers', 'Max_Occupancy', 'AVG_Daily_Individual_Occupancy',
                   'AVG_daily_total_Occupancy']

# Distance base scenarios
ARRIVAL_BASED = True
DEPARTURE_BASED = False

# Scenarios
CLOSEST = False
LOWEST_OCCUPANCY = False
MIXED_RULE = False
SPLIT_UP = True

# LATEX formats table to copy paste in Latex-doc
LATEX = True
OVERVIEW = True

# 120 results in proper runs
AMOUNT_SIMULATIONS = 250

SIMULATION_MONTHS = 12
SIMULATION_DAYS = SIMULATION_MONTHS * 30
SIMULATION_HOURS = SIMULATION_DAYS * 24


def main():
    data = load_data('./Data/')
    # visualise_data(data)
    stats = pd.DataFrame(columns=simulation_data)
    times = []
    if SPLIT_UP:
        split_ups = []

    i = 1
    # Progressbar - Only when using emulate in prompt
    with Bar('Simulating', fill='#', empty_fill='.', bar_prefix=' [',
             bar_suffix='] ', max=AMOUNT_SIMULATIONS) as bar:
        while i <= AMOUNT_SIMULATIONS:
            start = time.time()
            if SPLIT_UP:
                stats, amount_of_splitups = simulate(stats, data, SIMULATION_HOURS, ARRIVAL_BASED, DEPARTURE_BASED,
                                                     MIXED_RULE, CLOSEST,
                                                     LOWEST_OCCUPANCY,
                                                     SPLIT_UP)
                split_ups.append(amount_of_splitups)
            else:
                stats = simulate(stats, data, SIMULATION_HOURS, ARRIVAL_BASED, DEPARTURE_BASED, MIXED_RULE, CLOSEST,
                                 LOWEST_OCCUPANCY, SPLIT_UP)
            end = time.time()
            times.append(end - start)
            bar.next()
            i += 1
    show_result(stats, ARRIVAL_BASED, DEPARTURE_BASED, CLOSEST, LOWEST_OCCUPANCY, MIXED_RULE, SPLIT_UP, LATEX, OVERVIEW)
    if SPLIT_UP:
        print("Average amount of split ups: " + str(sum(split_ups) / len(split_ups)))
    print("Average time per simulation: " + str(sum(times) / len(times)) + " seconds")


if __name__ == '__main__':
    main()