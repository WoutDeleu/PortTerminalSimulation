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
CLOSEST = True
LOWEST_OCCUPANCY = False
MIXED_RULE = False
SPLIT_UP = False

# LATEX formats table to copy paste in Latex-doc
LATEX = False
OVERVIEW = True

# 120 results in proper runs
AMOUNT_SIMULATIONS = 10

SIMULATION_MONTHS = 12
SIMULATION_DAYS = SIMULATION_MONTHS * 30
SIMULATION_HOURS = SIMULATION_DAYS * 24


def main():
    data = load_data('./Data/')
    stats = pd.DataFrame(
        columns=simulation_data)

    i = 1
    # Progressbar - Only when using emulate in prompt
    with Bar('Simulating', fill='#', empty_fill='.', bar_prefix=' [',
             bar_suffix='] ', max=AMOUNT_SIMULATIONS) as bar:
        while i <= AMOUNT_SIMULATIONS:
            stats = simulate(stats, data, SIMULATION_HOURS, ARRIVAL_BASED, DEPARTURE_BASED, MIXED_RULE, CLOSEST,
                             LOWEST_OCCUPANCY,
                             SPLIT_UP)
            bar.next()
            i += 1
    show_result(stats, ARRIVAL_BASED, DEPARTURE_BASED, CLOSEST, LOWEST_OCCUPANCY, LATEX, OVERVIEW)


if __name__ == '__main__':
    main()