import os

import Visualisation
from Data.DataParser import parse_data


# todo: end ; verwijderen in columns
# todo: in forloop inlezen

def load_data(folder):
    # find all plugins available and initialize them
    data = {}
    for f in os.listdir(folder):
        if '.py' in f or '__pycache__' in f:
            continue
        data[f.replace('.csv', '')] = parse_data(f)

    return data


data = load_data('./Data/')
Visualisation.Visualisation_Export(data['LocalExportNormal'], data['LocalExportReefer'], data['VESSELSCHEDULE'])
Visualisation.Visualisation_Import(data['LocalImportNormal'], data['LocalImportReefer'], data['VESSELSCHEDULE'])

