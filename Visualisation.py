import pandas as pd


def Visualisation_Import(localImport, localImportReefer, schedule):
    print()



def Visualisation_Export(localExport, localExportReefer, schedule):
    arivals = schedule['Arrival']
    departure = schedule['Departure']
    print(schedule)
    for v in schedule:
        print(v)

def Visualization_Transshipments(tranN, tranR, schedule):
    # Visualize the amount of containers transferring between ships per hour

    # Cleaning data
    tranN = tranN.set_index('VESSELfrom_VESSELto') # Replaces the 0 index with the actual indexes
    tranN = tranN.replace('', 0) # Replaces empty fields with 0
    tranN = tranN.astype(int) # Changes the type of the parameters to 'int' instead of 'object'

    # Calculating sum of unloaded containers per vessel
    print(tranN)

    # Calculating sum of loaded containers per vessel
    tranNrows, tranNcolumns = tranN.shape
