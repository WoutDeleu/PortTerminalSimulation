import matplotlib.pyplot as plt
import numpy as np

from Data.DataParser import cleanData, WEEKDAYS, filterDayOfWeek, WEEKDAYS_NUMERIC, SORTED_WEEKDAYS, reorderCols, \
    format_import_export

# TODO fixen histogrammen
HIST = False
DAY_BASED = True


def sort_weekdays(normals, reefers):
    if DAY_BASED:
        indices = WEEKDAYS_NUMERIC.argsort()
        normals = np.array(normals)[indices]
        reefers = np.array(reefers)[indices]
    return normals, reefers


def visualise_data(data):
    # Replaces the 0 index with the actual indexes
    schedule = data['VESSELSCHEDULE'].set_index('VESSEL')

    # Cleanup and format import-data
    localImport = cleanData(data['LocalImportNormal'])
    localImportReefer = cleanData(data['LocalImportReefer'])
    importNormals, importReefer = format_import_export(localImport, localImportReefer, schedule)
    totalImport = importNormals.add(importReefer)

    # Cleanup and format export-data
    localExport = cleanData(data['LocalExportNormal'])
    localExportReefer = cleanData(data['LocalExportReefer'])
    exportNormals, exportReefer = format_import_export(localExport, localExportReefer, schedule)
    totalExport = exportNormals.add(exportReefer)

    # Cleanup and format transhipments-data
    tranNormal = reorderCols(cleanData(data['TransshipmentsNormal']))
    tranReefer = reorderCols(cleanData(data['TransshipmentsReefer']))

    visualise_normals_reefers(importNormals, importReefer, 'Import')
    visualise_normals_reefers(exportNormals, exportReefer, 'Export')
    visualise_transhipments(tranNormal, tranReefer, schedule)


def visualise_normals_reefers(normals, reefer, title):
    normals, reefer = sort_weekdays(normals, reefer)
    if DAY_BASED:
        plt.xticks(np.arange(len(SORTED_WEEKDAYS)), SORTED_WEEKDAYS)
    plt.plot(normals, label='#Normal containers')
    plt.plot(reefer, label='#Reefer containers')
    plt.title('Local {}'.format(title))
    plt.legend()
    plt.show()


def visualise_transhipments(tranNormal, tranReefer, schedule):
    # Visualize the amount of containers transferring between ships per hour

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

# def Visualization_TotalOccupancy(yardStorageBlocks, localImport, localImportReefer, localExport, localExportReefer,
#                                  schedule):
#     yardStorageBlocks = yardStorageBlocks.astype({'Capacity': 'int'})
#     total_capacity = calculate_full_capacity(yardStorageBlocks)
#     reefer_capacity = calculate_reefer_capacity(yardStorageBlocks)
#     normal_capacity = calculate_normal_capacity(yardStorageBlocks)
#
#     sumSchedule_export = schedule.merge(localExport, left_index=True, right_index=True)
#     sumSchedule_export = sumSchedule_export.merge(localExportReefer, left_index=True, right_index=True)
#
#     sumSchedule_import = schedule.merge(localImport, left_index=True, right_index=True)
#     sumSchedule_import = sumSchedule_import.merge(localImportReefer, left_index=True, right_index=True)
#
#     if DAY_BASED:
#         sumSchedule_import['Arrival'] = sumSchedule_import.apply(lambda x: filterDayOfWeek(x.Arrival), axis=1)
#         sumSchedule_export['Arrival'] = sumSchedule_export.apply(lambda x: filterDayOfWeek(x.Arrival), axis=1)
#
#         exportNormals = sumSchedule_export.groupby(['Arrival'])['Containers_x'].sum()
#         exportNormals = sort_weekdays(exportNormals)
#
#         exportReefer = sumSchedule_export.groupby(['Arrival'])['Containers_y'].sum()
#         exportReefer = sort_weekdays(exportReefer)
#
#         totalExport = exportNormals.add(exportReefer)
#         totalExport = sort_weekdays(totalExport)
#
#         arrivalNormals = sumSchedule_import.groupby(['Arrival'])['Containers_x'].sum()
#         arrivalNormals = sort_weekdays(arrivalNormals)
#
#         arrivalReefer = sumSchedule_import.groupby(['Arrival'])['Containers_y'].sum()
#         arrivalReefer = sort_weekdays(arrivalReefer)
#
#         totalImport = arrivalNormals.add(arrivalReefer)
#         totalImport = sort_weekdays(totalImport)
#
#         totalNormals = calculate_normalOccupancy_byDay(exportNormals, arrivalNormals)
#         totalNormals_percentage = totalNormals.div(normal_capacity) * 100
#         totalReefer = calculate_reeferOccupancy_byDay(exportReefer, arrivalReefer)
#         totalReefer_percentage = totalReefer.div(reefer_capacity) * 100
#
#         total = totalNormals + totalReefer
#         total_percentage = total.div(total_capacity) * 100
#
#         # Maak de grafiek
#         plt.plot(WEEKDAYS, totalNormals_percentage, label='Normal Occupancy')
#         plt.plot(WEEKDAYS, totalReefer_percentage, label='Reefer Occupancy')
#         plt.plot(WEEKDAYS, total_percentage, label='Total Occupancy')
#
#         # Voeg labels en titel toe aan de grafiek
#         plt.xlabel('Day of the Week')
#         plt.ylabel('Occupancy (%)')
#         plt.title('Occupancy')
#         # Voeg een legenda toe
#         plt.legend()
#
#         # Toon de grafiek
#         plt.show()