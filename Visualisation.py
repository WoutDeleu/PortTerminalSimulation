import pandas as pd
import matplotlib.pyplot as plt

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
    tranN = tranN.rename(columns={'VESSELfrom_VESSELto': 'VESSEL'})  # Rename column for later merge
    tranN = tranN.set_index('VESSEL')  # Replaces the 0 index with the actual indexes
    tranN = tranN.replace('', 0)  # Replaces empty fields with 0
    tranN = tranN.astype(int)  # Changes the type of the parameters to 'int' instead of 'object'
    tranNRows, tranNColumns = tranN.shape
    sorted = []
    for x in range(tranNColumns):
        sorted.append('V' + str(x))
    tranN = tranN.reindex(columns=sorted)  # Sort columns
    tranN = tranN.reindex(sorted)  # Sort rows

    schedule = schedule.set_index('VESSEL')  # Replaces the 0 index with the actual indexes

    # Calculating sum of unloaded containers (incoming)
    unloadedSumPerVessel = tranN.sum(axis=1)

    # Calculating sum of loaded containers per vessel (outgoing)
    loadedSumPerVessel = tranN.sum()

    # Linking vessels with schedule:
    # This dataframe shows how many containers are loaded/unloaded per Vessel and when
    unloadedLink = schedule.merge(unloadedSumPerVessel.to_frame(), left_index=True, right_index=True)
    unloadedLink = unloadedLink.rename(columns={0: 'unloadedContainers'})
    link = unloadedLink.merge(loadedSumPerVessel.to_frame(), left_index=True, right_index=True)
    link = link.rename(columns={0: 'loadedContainers'})

    # Changing day names to numbers
    #link = link.replace(['Mo ', 'Tu ', 'We ', 'Th ', 'Fr ', 'Sa ', 'Su ', ':'], ['0', '1', '2', '3', '4', '5', '6', ''], regex=True)
    link = link.groupby(['Arrival'])['unloadedContainers'].sum()
    print(link)

    # Plotting

    plt.plot(link)
    plt.show()


