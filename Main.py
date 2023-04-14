import os

import pandas as pd
from progress.bar import Bar

from Data.DataParser import parse_data, array_to_string
from Simulation import Simulation

AMOUNT_SIMULATIONS = 10

# LATEX formats table to copy paste in Latex-doc
LATEX = True
OVERVIEW = True


def format_stats(stats):
    names = []
    avg = []
    for col in stats.columns:
        names.append(col)
        if col == 'Max_Occupancy' or col == 'AVG_Daily_Individual_Occupancy':
            tmp_serie = []
            for i in range(len(stats[col].iloc[0])):
                tmp_avg = 0
                for row in stats[col]:
                    tmp_avg += row[i]
                tmp_serie.append(tmp_avg / len(stats[col]))
            avg.append(array_to_string(tmp_serie))
        else:
            avg.append(str(stats[col].mean()))
    return names, avg


def show_result(title, stats):
    names, avg = format_stats(stats)
    print("*********************** " + title + " ***********************")
    print()
    if LATEX:
        print_stats_latex(names, avg)
    if OVERVIEW:
        print_stats(names, avg)
    print()
    print("****************************************************")


# prints stats of the simulation in overview
def print_stats(colnames, values):
    mean_series = pd.Series(values)
    for name, value in zip(colnames, mean_series):
        print(f"{name}: average = {value}")


# formats table to copy paste in Latex-doc
def format_yb_table(data):
    data = data.strip('[]')
    values = data.split(';')
    num_columns = len(values)
    num_tables = (num_columns + 8) // 9
    latex_tables = []
    for i in range(num_tables):
        start_index = i * 9
        end_index = min(start_index + 9, num_columns)
        latex_table = '\\begin{table}[h]\n\\centering\n\\begin{tabular}{|' + '|'.join(
            ['c'] * (end_index - start_index)) + '|}\n'
        latex_table += '\\hline\n'
        for j in range(start_index + 1, end_index + 1):
            latex_table += 'YB' + str(j) + ' & '
        latex_table = latex_table.rstrip('& ') + '\\\\\n'
        latex_table += '\\hline\n'
        for k in range(start_index, end_index):
            latex_table += values[k].strip() + ' & '
        latex_table = latex_table.rstrip('& ') + '\\\\\n'
        latex_table += '\\hline\n'
        latex_table += '\\end{tabular}\n\\caption{...}\n\\end{table}'
        latex_tables.append(latex_table)
    return latex_tables


def print_stats_latex(colnames, values):
    mean_series = pd.Series(values)
    # Creëer de Latex-tabel
    latex_table = "\\begin{table}[h]\n\\centering\n\\begin{tabular}{|c|c|}\n\\hline\n"
    for name, value in zip(colnames, mean_series):
        # Voeg de kolomnaam en gemiddelde waarde toe als een rij in de tabel
        if name == 'Max_Occupancy':
            avg_occ_latex = format_yb_table(value)
        elif name == 'AVG_Daily_Individual_Occupancy':
            avg_daily_occ_latex = format_yb_table(value)
        else:
            latex_table += f"{name} & {value} \\\\ \\hline\n"
    latex_table += "\\end{tabular}\n\\caption{...}\n\\end{table}"

    # Print de Latex-tabel
    print(latex_table)
    print(avg_occ_latex)
    print(avg_daily_occ_latex)


def load_data(folder):
    # find all plugins available and initialize them
    data = {}
    for f in os.listdir(folder):
        if '.py' in f or '__pycache__' in f:
            continue
        data[f.replace('.csv', '')] = parse_data(f)
    return data


def simulate_fifo_closest_departure(stats_fifo, data):
    sim = Simulation(data)
    sim.fifo(arrival_based=True)
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
    return stats_fifo


def main():
    data = load_data('./Data/')
    # visualise_data(data)
    stats_fifo = pd.DataFrame(
        columns=['Containers_Rejected', 'CG_Rejected', 'Normal_Rejected', 'Reefer_Rejected', 'Total_Travel_Distance',
                 'AVG_Travel_Distance_Containers', 'Max_Occupancy', 'AVG_Daily_Individual_Occupancy',
                 'AVG_daily_total_Occupancy'])

    i = 1
    # Progressbar - Only when using emulate in prompt
    with Bar('Simulating', fill='#', empty_fill='.', bar_prefix=' [',
             bar_suffix='] ', max=AMOUNT_SIMULATIONS) as bar:
        while i <= AMOUNT_SIMULATIONS:
            stats_fifo = simulate_fifo_closest_departure(stats_fifo, data)
            bar.next()
            i += 1
    print('\n')
    show_result('FIFO', stats_fifo)
    # print('\n\n\n\n')


if __name__ == '__main__':
    main()