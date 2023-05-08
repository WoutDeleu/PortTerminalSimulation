import os

import pandas as pd
from progress.bar import Bar

from Data.DataParser import parse_data
from Parameters import AMOUNT_SIMULATIONS, check_parameters
from Result_Parser import show_result
from Simulation import simulate


def load_data(folder):
    # find all plugins available and initialize them
    data = {}
    for f in os.listdir(folder):
        if '.py' in f or '__pycache__' in f:
            continue
        data[f.replace('.csv', '')] = parse_data(f)
    return data


def main():
    check_parameters()
    data = load_data('./Data/')
    stats = pd.DataFrame(
        columns=['Containers_Rejected', 'CG_Rejected', 'Normal_Rejected', 'Reefer_Rejected', 'Total_Travel_Distance',
                 'AVG_Travel_Distance_Containers', 'Max_Occupancy', 'AVG_Daily_Individual_Occupancy',
                 'AVG_daily_total_Occupancy'])

    i = 1
    # Progressbar - Only when using emulate in prompt
    with Bar('Simulating', fill='#', empty_fill='.', bar_prefix=' [',
             bar_suffix='] ', max=AMOUNT_SIMULATIONS) as bar:
        while i <= AMOUNT_SIMULATIONS:
            stats = simulate(stats, data)
            bar.next()
            i += 1
    show_result(stats)


if __name__ == '__main__':
    main()