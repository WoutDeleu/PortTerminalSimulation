# formats table to copy paste in Latex-doc

import pandas as pd

from Data.DataParser import array_to_string


def format_yb_tables(data):
    data = data.strip('[]')
    values = data.split(';')
    num_columns = len(values)
    num_tables = (num_columns + 8) // 9
    latex_tables = []
    for i in range(num_tables):
        start_index = i * 9
        end_index = min(start_index + 9, num_columns)
        latex_table = "\\begin{table}[h]\n\\centering\n\\begin{tabular}{|" + "|".join(
            ["c"] * (end_index - start_index)) + "|}\n"
        latex_table += "\\hline\n"
        for j in range(start_index + 1, end_index + 1):
            latex_table += "YB" + str(j) + " & "
        latex_table = latex_table.rstrip("& ") + "\\\\\n"
        latex_table += "\\hline\n"
        for k in range(start_index, end_index):
            latex_table += str(round(float(values[k].strip()), 2)) + " & "
        latex_table = latex_table.rstrip("& ") + "\\\\\n"
        latex_table += "\\hline\n"
        latex_table += "\\end{tabular}\n\\caption{...}\n\\end{table}"
        latex_tables.append(latex_table)
    return latex_tables


def print_stats_latex(colnames, values, title):
    mean_series = pd.Series(values)
    # Creëer de Latex-tabel
    latex_table = "\\begin{table}[h]\n\\centering\n\\begin{tabular}{|c|c|}\n\\hline\n"
    for name, value in zip(colnames, mean_series):
        # Voeg de kolomnaam en gemiddelde waarde toe als een rij in de tabel
        if name == 'Max_Occupancy':
            avg_occ_latex = format_yb_tables(value)
        elif name == 'AVG_Daily_Individual_Occupancy':
            avg_daily_occ_latex = format_yb_tables(value)
        else:
            name = name.replace("_", " ")
            latex_table += f"{name} & {round(float(value),3)} \\\\ \\hline\n"
    latex_table += "\\end{tabular}\n\\caption{"+title+"}\n\\end{table}"

    # Print de Latex-tabel
    # print("*********************** AVG occ ***********************")
    # for s in avg_occ_latex:
    #     print(s)
    # print("*********************** AVG daily occ ***********************")
    # for s in avg_daily_occ_latex:
    #     print(s)
    print(latex_table)


def get_avg_serie(name, values):
    if name == 'Max_Occupancy' or name == 'AVG_Daily_Individual_Occupancy':
        avg_serie = []
        for i in range(len(values.iloc[0])):
            tmp = 0
            for row in values:
                tmp += row[i]
            avg_serie.append(tmp / len(values))
        return avg_serie
    else:
        return None


def format_stats_individual_YB(stats):
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


def count_over_90(avg_serie):
    count = 0
    for v in avg_serie:
        if v > 0.9:
            count += 1
    return count


def count_never_used(avg_serie):
    count = 0
    for v in avg_serie:
        if v < 0.05:
            count += 1
    return count


def format_stats(stats):
    names = []
    avg = []
    # names.append("Amount of YB's")
    # avg.append(len(stats['Max_Occupancy'].iloc[0]))
    for col in stats.columns:
        avg_serie = get_avg_serie(col, stats[col])
        if col == 'Max_Occupancy':
            names.append("Portion of YB close to full (at some point)")
            avg.append(count_over_90(avg_serie) / len(avg_serie))
            names.append("Portion of YB never used")
            avg.append(count_never_used(avg_serie) / len(avg_serie))
        elif col == 'AVG_Daily_Individual_Occupancy':
            names.append("Portion of YB close to full (average)")
            avg.append(count_over_90(avg_serie) / len(avg_serie))
        else:
            names.append(col)
            avg.append(str(stats[col].mean()))
    return names, avg


def show_result(stats, ARRIVAL_BASED, DEPARTURE_BASED, CLOSEST, LOWEST_OCCUPANCY, MIXED_RULE, SPLIT_UP, LATEX, OVERVIEW):
    print()
    if ARRIVAL_BASED:
        title = 'ARRIVAL-BASED'
    elif DEPARTURE_BASED:
        title = 'DEPARTURE-BASED'

    if CLOSEST:
        title = 'FIFO ' + title
    if LOWEST_OCCUPANCY:
        title = 'LOWEST OCCUPANCY ' + title
    if MIXED_RULE:
        title = 'MIXED RULE ' + title
    if SPLIT_UP:
        title = 'SPLIT UP ' + title

    names, avg = format_stats(stats)
    if LATEX:
        print_stats_latex(names, avg, title)
    if OVERVIEW:
        print_stats_overview(names, avg)


# prints stats of the simulation in overview
def print_stats_overview(colnames, values):
    mean_series = pd.Series(values)
    for name, value in zip(colnames, mean_series):
        print(f"{name}: average = {value}")