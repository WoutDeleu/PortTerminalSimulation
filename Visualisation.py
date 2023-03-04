import pandas as pd
import matplotlib.pyplot as plt


def Visualisation_Import(localImport, localImportReefer, schedule):
    localImport = cleanData(localImport)
    localImportReefer = cleanData(localImportReefer)

    schedule = schedule.set_index('VESSEL')

    sumSchedule = schedule.merge(localImport, left_index=True, right_index=True)
    sumSchedule = sumSchedule.merge(localImportReefer, left_index=True, right_index=True)

    arrivalNormals = sumSchedule.groupby(['Arrival'])['Containers_x'].sum()
    arrivalReefer = sumSchedule.groupby(['Arrival'])['Containers_y'].sum()

    plt.title('Local Export')
    plt.plot(arrivalNormals, label='#Normal containers arriving')
    plt.plot(arrivalReefer, label='#Reefer containers arriving')
    plt.legend()
    plt.show()



def Visualisation_Export(localExport, localExportReefer, schedule):
    localExport = cleanData(localExport)
    localExportReefer = cleanData(localExportReefer)

    schedule = schedule.set_index('VESSEL')

    sumSchedule = schedule.merge(localExport, left_index=True, right_index=True)
    sumSchedule = sumSchedule.merge(localExportReefer, left_index=True, right_index=True)

    arrivalNormals = sumSchedule.groupby(['Arrival'])['Containers_x'].sum()
    arrivalReefer = sumSchedule.groupby(['Arrival'])['Containers_y'].sum()


    plt.title('Local Export')
    plt.plot(arrivalNormals, label='#Normal containers arriving')
    plt.plot(arrivalReefer, label='#Reefer containers arriving')
    plt.legend()
    plt.show()


def Visualization_Transshipments(tranNormal, tranReefer, schedule):
    # Visualize the amount of containers transferring between ships per hour

    # Cleaning data
    tranNormal = cleanData(tranNormal)
    tranNormal = reorderCols(tranNormal)
    tranReefer = cleanData(tranReefer)
    tranReefer = reorderCols(tranReefer)

    schedule = schedule.set_index('VESSEL')  # Replaces the 0 index with the actual indexes

    # Calculating sum of unloaded containers (incoming)
    unloadedSumN = tranNormal.sum(axis=1)
    unloadedSumR = tranReefer.sum(axis=1)

    # Calculating sum of loaded containers per vessel (outgoing)
    loadedSumN = tranNormal.sum()
    loadedSumR = tranReefer.sum()

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


def cleanData(dataframe):
    # Cleaning data

    dataframe = dataframe.rename(columns={'VESSELfrom_VESSELto': 'VESSEL'})  # Rename column for later merge
    dataframe = dataframe.set_index('VESSEL')  # Replaces the 0 index with the actual indexes
    dataframe = dataframe.replace('', 0)  # Replaces empty fields with 0
    dataframe = dataframe.astype(int)  # Changes the type of the parameters to 'int' instead of 'object'

    return dataframe


def reorderCols(dataframe):
    rows, cols = dataframe.shape


    vesselKeys = []
    for x in range(cols):
        vesselKeys.append('V' + str(x))

    dataframe = dataframe.reindex(columns=vesselKeys)  # Sort columns
    return dataframe.reindex(vesselKeys)
