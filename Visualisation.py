import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from Data.DataParser import cleanData, WEEKDAYS, filterDayOfWeek, WEEKDAYS_NUMERIC, reorderCols

# TODO fixen histogrammen
HIST = False
DAY_BASED = True


def sort_weekdays(data):
    data = data.loc[pd.Categorical(data.index, categories=WEEKDAYS, ordered=True)]
    data = data.reset_index(drop=False)
    return data.set_index('Arrival').reindex(WEEKDAYS)


def calculate_normalOccupancy_byDay(export, arrival):
    total_containers = {}

    # loop door alle tijdseenheden en bereken de totale hoeveelheid containers
    for index in range(0, 7):
        current_index = WEEKDAYS[index]
        previous_index = WEEKDAYS[index - 1]
        if index == 0:
            previous_total = 0
        else:
            previous_total = total_containers.get(previous_index, 0)
        total = previous_total + arrival.loc[current_index].at['Containers_x'] - export.loc[current_index].at[
            'Containers_x']
        total_containers[current_index] = total

    # maak een Pandas Series aan met de berekende waarden
    return pd.Series(total_containers)


def calculate_reeferOccupancy_byDay(export, arrival):
    total_containers = {}

    # loop door alle tijdseenheden en bereken de totale hoeveelheid containers
    for index in range(0, 7):
        current_index = WEEKDAYS[index]
        previous_index = WEEKDAYS[index - 1]
        if index == 0:
            previous_total = 0
        else:
            previous_total = total_containers.get(previous_index, 0)
        total = previous_total + arrival.loc[current_index].at['Containers_y'] - export.loc[current_index].at[
            'Containers_y']
        total_containers[current_index] = total

    # maak een Pandas Series aan met de berekende waarden
    return pd.Series(total_containers)


def calculate_full_capacity(yardStorageBlocks):
    return yardStorageBlocks['Capacity'].sum()


def calculate_reefer_capacity(yardStorageBlocks):
    yardStorageBlocks = yardStorageBlocks[yardStorageBlocks['ContainerType'] == 'FULL']
    return yardStorageBlocks['Capacity'].sum()


def calculate_normal_capacity(yardStorageBlocks):
    yardStorageBlocks = yardStorageBlocks[yardStorageBlocks['ContainerType'] == 'REEFER']
    return yardStorageBlocks['Capacity'].sum()


def Visualisation_Import(localImport, localImportReefer, schedule):
    localImport = cleanData(localImport)
    localImportReefer = cleanData(localImportReefer)

    schedule = schedule.set_index('VESSEL')

    sumSchedule = schedule.merge(localImport, left_index=True, right_index=True)
    sumSchedule = sumSchedule.merge(localImportReefer, left_index=True, right_index=True)
    if DAY_BASED:
        sumSchedule['Arrival'] = sumSchedule.apply(lambda x: filterDayOfWeek(x.Arrival), axis=1)

    arrivalNormals = sumSchedule.groupby(['Arrival'])['Containers_x'].sum()
    arrivalReefer = sumSchedule.groupby(['Arrival'])['Containers_y'].sum()
    totalImport = arrivalNormals.add(arrivalReefer)

    if HIST:
        pass

    else:
        if DAY_BASED:
            indices = WEEKDAYS_NUMERIC.argsort()
            sorted_weekdays = np.array(WEEKDAYS)[indices]
            sorted_exportNormals = np.array(arrivalNormals)[indices]
            sorted_exportReefer = np.array(arrivalReefer)[indices]
            plt.plot(sorted_exportNormals, label='#Normal containers arriving')
            plt.plot(sorted_exportReefer, label='#Reefer containers arriving')
            plt.xticks(np.arange(len(sorted_weekdays)), sorted_weekdays)
            plt.title('Local Export')
            plt.legend()
            plt.show()
        else:
            plt.plot(arrivalNormals, label='#Normal containers arriving')
            plt.plot(arrivalReefer, label='#Reefer containers arriving')
            plt.title('Local import')
            plt.legend()
            plt.show()


def Visualisation_Export(localExport, localExportReefer, schedule):
    localExport = cleanData(localExport)
    localExportReefer = cleanData(localExportReefer)

    schedule = schedule.set_index('VESSEL')

    sumSchedule = schedule.merge(localExport, left_index=True, right_index=True)
    sumSchedule = sumSchedule.merge(localExportReefer, left_index=True, right_index=True)
    if DAY_BASED:
        sumSchedule['Arrival'] = sumSchedule.apply(lambda x: filterDayOfWeek(x.Arrival), axis=1)

    exportNormals = sumSchedule.groupby(['Arrival'])['Containers_x'].sum()
    exportReefer = sumSchedule.groupby(['Arrival'])['Containers_y'].sum()
    totalExport = exportNormals.add(exportReefer)

    if HIST:
        # fig, ax = plt.subplots()
        # width = 0.8
        #
        # ax.hist(WEEKDAYS_NUMERIC - width / 2, weights=exportNormals, label='#Normal containers leaving',
        #         bins=7, width=width, histtype='bar')
        # ax.hist(WEEKDAYS_NUMERIC + width / 2, weights=exportReefer, label='#Reefer containers leaving',
        #         bins=7, width=width, histtype='bar')
        #
        # ax.set_xticks(np.arange(7))
        # ax.set_xticklabels(WEEKDAYS, rotation=45)
        #
        # plt.plot(np.arange(7), totalExport, label='#Total export', color='red')
        # plt.title('Local Export')
        # plt.legend()
        # plt.show()
        pass
    else:
        indices = WEEKDAYS_NUMERIC.argsort()
        sorted_weekdays = np.array(WEEKDAYS)[indices]
        sorted_exportNormals = np.array(exportNormals)[indices]
        sorted_exportReefer = np.array(exportReefer)[indices]

        if DAY_BASED:
            plt.plot(sorted_exportNormals, label='#Normal containers arriving')
            plt.plot(sorted_exportReefer, label='#Reefer containers arriving')
            plt.xticks(np.arange(len(sorted_weekdays)), sorted_weekdays)

        else:
            plt.plot(exportNormals, label='#Normal containers arriving')
            plt.plot(exportReefer, label='#Reefer containers arriving')
        plt.title('Local Export')
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

    if DAY_BASED:
        sumSchedule['Arrival'] = sumSchedule.apply(lambda x: filterDayOfWeek(x.Arrival), axis=1)

    # Showing different graphs
    arrivalNormals = sumSchedule.groupby(['Arrival'])['unloadedContainersN'].sum()
    departureNormals = sumSchedule.groupby(['Arrival'])['loadedContainersN'].sum()
    arrivalReefers = sumSchedule.groupby(['Arrival'])['unloadedContainersR'].sum()
    departureReefers = sumSchedule.groupby(['Arrival'])['loadedContainersR'].sum()

    indices = WEEKDAYS_NUMERIC.argsort()
    sorted_weekdays = np.array(WEEKDAYS)[indices]
    sorted_arrivalNormals = np.array(arrivalNormals)[indices]
    sorted_departureNormals = np.array(departureNormals)[indices]
    sorted_arrivalReefers = np.array(arrivalReefers)[indices]
    sorted_departureReefers = np.array(departureReefers)[indices]

    # Plotting
    plt.title('Transshipments')
    if DAY_BASED:
        plt.plot(sorted_arrivalNormals, label='#Normal containers arriving')
        plt.plot(sorted_departureNormals, label='#Normal containers departing')
        plt.plot(sorted_arrivalReefers, label='#Reefer containers arriving')
        plt.plot(sorted_departureReefers, label='#Reefer containers departing')
        plt.xticks(np.arange(len(sorted_weekdays)), sorted_weekdays)
    else:
        plt.plot(arrivalNormals, label='#Normal containers arriving')
        plt.plot(departureNormals, label='#Normal containers departing')
        plt.plot(arrivalReefers, label='#Reefer containers arriving')
        plt.plot(departureReefers, label='#Reefer containers departing')
    plt.legend()
    plt.show()


def Visualization_TotalOccupancy(yardStorageBlocks, localImport, localImportReefer, localExport, localExportReefer,
                                 schedule):
    yardStorageBlocks = yardStorageBlocks.astype({'Capacity': 'int'})
    total_capacity = calculate_full_capacity(yardStorageBlocks)
    reefer_capacity = calculate_reefer_capacity(yardStorageBlocks)
    normal_capacity = calculate_normal_capacity(yardStorageBlocks)

    localExport = cleanData(localExport)
    localExportReefer = cleanData(localExportReefer)

    localImport = cleanData(localImport)
    localImportReefer = cleanData(localImportReefer)

    schedule = schedule.set_index('VESSEL')

    sumSchedule_export = schedule.merge(localExport, left_index=True, right_index=True)
    sumSchedule_export = sumSchedule_export.merge(localExportReefer, left_index=True, right_index=True)

    sumSchedule_import = schedule.merge(localImport, left_index=True, right_index=True)
    sumSchedule_import = sumSchedule_import.merge(localImportReefer, left_index=True, right_index=True)

    if DAY_BASED:
        sumSchedule_import['Arrival'] = sumSchedule_import.apply(lambda x: filterDayOfWeek(x.Arrival), axis=1)
        sumSchedule_export['Arrival'] = sumSchedule_export.apply(lambda x: filterDayOfWeek(x.Arrival), axis=1)

        exportNormals = sumSchedule_export.groupby(['Arrival'])['Containers_x'].sum()
        exportNormals = sort_weekdays(exportNormals)

        exportReefer = sumSchedule_export.groupby(['Arrival'])['Containers_y'].sum()
        exportReefer = sort_weekdays(exportReefer)

        totalExport = exportNormals.add(exportReefer)
        totalExport = sort_weekdays(totalExport)

        arrivalNormals = sumSchedule_import.groupby(['Arrival'])['Containers_x'].sum()
        arrivalNormals = sort_weekdays(arrivalNormals)

        arrivalReefer = sumSchedule_import.groupby(['Arrival'])['Containers_y'].sum()
        arrivalReefer = sort_weekdays(arrivalReefer)

        totalImport = arrivalNormals.add(arrivalReefer)
        totalImport = sort_weekdays(totalImport)

        totalNormals = calculate_normalOccupancy_byDay(exportNormals, arrivalNormals)
        totalNormals_percentage = totalNormals.div(normal_capacity) * 100
        totalReefer = calculate_reeferOccupancy_byDay(exportReefer, arrivalReefer)
        totalReefer_percentage = totalReefer.div(reefer_capacity) * 100

        total = totalNormals + totalReefer
        total_percentage = total.div(total_capacity) * 100

        # Maak de grafiek
        plt.plot(WEEKDAYS, totalNormals_percentage, label='Normal Occupancy')
        plt.plot(WEEKDAYS, totalReefer_percentage, label='Reefer Occupancy')
        plt.plot(WEEKDAYS, total_percentage, label='Total Occupancy')

        # Voeg labels en titel toe aan de grafiek
        plt.xlabel('Day of the Week')
        plt.ylabel('Occupancy')

        # Voeg een legenda toe
        plt.legend()

        # Toon de grafiek
        plt.show()
