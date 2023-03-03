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

    tranR = tranR.rename(columns={'VESSELfrom_VESSELto': 'VESSEL'})  # Rename column for later merge
    tranR = tranR.set_index('VESSEL')  # Replaces the 0 index with the actual indexes
    tranR = tranR.replace('', 0)  # Replaces empty fields with 0
    tranR = tranR.astype(int)  # Changes the type of the parameters to 'int' instead of 'object'
    tranR = tranR.reindex(columns=sorted)  # Sort columns
    tranR = tranR.reindex(sorted)  # Sort rows

    schedule = schedule.set_index('VESSEL')  # Replaces the 0 index with the actual indexes

    # Calculating sum of unloaded containers (incoming)
    unloadedSumN = tranN.sum(axis=1)
    unloadedSumR = tranR.sum(axis=1)

    # Calculating sum of loaded containers per vessel (outgoing)
    loadedSumN = tranN.sum()
    loadedSumR = tranR.sum()

    # Linking vessels with schedule:
    # This dataframe shows when and how many containers are loaded/unloaded per Vessel
    sumSchedule = schedule.merge(unloadedSumN.to_frame(), left_index=True, right_index=True)
    sumSchedule = sumSchedule.rename(columns={0: 'unloadedContainersN'})
    sumSchedule = sumSchedule.merge(loadedSumN.to_frame(), left_index=True, right_index=True)
    sumSchedule = sumSchedule.rename(columns={0: 'loadedContainersN'})
    sumSchedule = sumSchedule.merge(unloadedSumR.to_frame(), left_index=True, right_index=True)
    sumSchedule = sumSchedule.rename(columns={0: 'unloadedContainersR'})
    sumSchedule = sumSchedule.merge(loadedSumR.to_frame(), left_index=True, right_index=True)
    sumSchedule = sumSchedule.rename(columns={0: 'loadedContainersR'})

    # Showing different graphs
    dayList = ['Mo ', 'Tu ', 'We ', 'Th ', 'Fr ', 'Sa ', 'Su ']
    arrivalNormals = sumSchedule.groupby(['Arrival'])['unloadedContainersN'].sum()
    departureNormals = sumSchedule.groupby(['Arrival'])['loadedContainersN'].sum()
    arrivalReefers = sumSchedule.groupby(['Arrival'])['unloadedContainersR'].sum()
    departureReefers = sumSchedule.groupby(['Arrival'])['loadedContainersR'].sum()

    # Plotting
    plt.title('Transshipments')
    plt.plot(arrivalNormals, label='#Normal containers arriving')
    plt.plot(departureNormals, label='#Normal containers departing')
    plt.plot(arrivalReefers, label='#Reefer containers arriving')
    plt.plot(departureReefers, label='#Reefer containers departing')
    plt.legend()
    plt.show()



