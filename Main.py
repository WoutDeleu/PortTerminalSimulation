import os

from Data.DataParser import parse_data
from Visualisation import Visualisation_Export, Visualisation_Import, Visualization_Transshipments, \
    Visualization_TotalOccupancy


def load_data(folder):
    # find all plugins available and initialize them
    data = {}
    for f in os.listdir(folder):
        if '.py' in f or '__pycache__' in f:
            continue
        data[f.replace('.csv', '')] = parse_data(f)

    return data


data = load_data('./Data/')
Visualisation_Export(data['LocalExportNormal'], data['LocalExportReefer'], data['VESSELSCHEDULE'])
Visualisation_Import(data['LocalImportNormal'], data['LocalImportReefer'], data['VESSELSCHEDULE'])
Visualization_Transshipments(data['TransshipmentsNormal'], data['TransshipmentsReefer'], data['VESSELSCHEDULE'])
Visualization_TotalOccupancy(data['YARDSTORAGEBLOCKS'], data['LocalImportNormal'], data['LocalImportReefer'],
                             data['LocalExportNormal'], data['LocalExportReefer'], data['VESSELSCHEDULE'])
