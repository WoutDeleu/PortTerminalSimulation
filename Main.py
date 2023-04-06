import os

import pandas as pd
from progress.bar import Bar

from Data.DataParser import parse_data
from Simulation import Simulation

AMOUNT_SIMULATIONS = 1


def show_result(title, stats_fifo, LATEX=False, OVERVIEW=True):
    names = []
    avg = []
    for col in stats_fifo.columns:
        names.append(col)
        avg.append(stats_fifo[col].mean())

    print("*********************** " + title + " ***********************")
    print()
    if LATEX:
        print_stats_latex(names, avg)
    if OVERVIEW:
        print_stats(names, avg)
    print()
    print("****************************************************")


def print_stats(colnames, values):
    mean_series = pd.Series(values)
    for name, value in zip(colnames, mean_series):
        print(f"{name}: average = {value:.2f}")


def print_stats_latex(colnames, values):
    mean_series = pd.Series(values)
    # Creëer de Latex-tabel
    latex_table = "\\begin{tabular}{|c|c|}\n\\hline\n"
    for name, value in zip(colnames, mean_series):
        # Voeg de kolomnaam en gemiddelde waarde toe als een rij in de tabel
        latex_table += f"{name} & {value:.2f} \\\\ \\hline\n"
    latex_table += "\\end{tabular}"

    # Print de Latex-tabel
    print(latex_table)


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

stats_fifo = pd.DataFrame(
    columns=['Containers_Rejected', 'CG_Rejected', 'Normal_Rejected', 'Reefer_Rejected', 'Total_Travel_Distance',
             'AVG_Travel_Distance_Containers', 'Max_Occupancy', 'AVG_Daily_Individual_Occupancy',
             'AVG_daily_total_Occupancy'])

i = 1
# Progressbar - Only when using emulate in prompt
with Bar('Processing', fill='#', max=AMOUNT_SIMULATIONS) as bar:
    while i <= AMOUNT_SIMULATIONS:
        sim = Simulation(data)
        sim.simulate_fifo()
        stats_fifo = pd.concat(
            [stats_fifo,
             pd.DataFrame([{'Containers_Rejected': sim.rejected_containers, 'CG_Rejected': sim.rejected_groups,
                            'Normal_Rejected': sim.rejected_per_type["normal"],
                            'Reefer_Rejected': sim.rejected_per_type["reefer"],
                            'Total_Travel_Distance': sim.total_travel_distance_containers,
                            'AVG_Travel_Distance_Containers': sim.getAvgTravel_Containers(),
                            'Max_Occupancy': sim.getMaxOccupancy(),
                            'AVG_Daily_Individual_Occupancy': sim.getAvgOccupancy_individual(),
                            'AVG_daily_total_Occupancy': sim.getDailyTotalOccupancy()}])
             ])
        bar.next()
        i += 1
print('\n')
show_result('FIFO', stats_fifo, LATEX=False, OVERVIEW=True)
# print('\n\n\n\n')