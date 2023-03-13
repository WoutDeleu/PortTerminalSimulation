import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from Data.CONST import WEEKDAYS, WEEKDAYS_NUMERIC, SORTED_WEEKDAYS, DAY_BASED, HIST
from Data.DataParser import cleanData, filterDayOfWeek, reorderCols, format_import_export, shift_time, reformat_index


# TODO fixen histogrammen => JEF


def sort(normals, reefers):
    if DAY_BASED:
        indices = WEEKDAYS_NUMERIC.argsort()
        normals = np.array(normals)[indices]
        reefers = np.array(reefers)[indices]
    else:
        normals = reformat_index(normals)
        reefers = reformat_index(reefers)
    return normals, reefers


def calculate_reefer_capacity(yardStorageBlocks):
    yardStorageBlocks = yardStorageBlocks[yardStorageBlocks['ContainerType'] == 'FULL']
    return yardStorageBlocks['Capacity'].sum()


def calculate_normal_capacity(yardStorageBlocks):
    yardStorageBlocks = yardStorageBlocks[yardStorageBlocks['ContainerType'] == 'REEFER']
    return yardStorageBlocks['Capacity'].sum()


def visualise_data(data):
    yardStorageBlocks = data['YARDSTORAGEBLOCKS'].astype({'Capacity': 'int'})

    # Replaces the 0 index with the actual indexes
    schedule = data['VESSELSCHEDULE'].set_index('VESSEL')

    # Cleanup and format import-data
    localImport = cleanData(data['LocalImportNormal'])
    localImportReefer = cleanData(data['LocalImportReefer'])
    importNormals, importReefer = format_import_export(localImport, localImportReefer, schedule)
    # Cleanup and format export-data
    localExport = cleanData(data['LocalExportNormal'])
    localExportReefer = cleanData(data['LocalExportReefer'])
    exportNormals, exportReefer = format_import_export(localExport, localExportReefer, schedule)

    # Cleanup and format transhipments-data
    tranNormal = reorderCols(cleanData(data['TransshipmentsNormal']))
    tranReefer = reorderCols(cleanData(data['TransshipmentsReefer']))

    visualise_normals_reefers(importNormals, importReefer, 'Import')
    visualise_normals_reefers(exportNormals, exportReefer, 'Export')
    visualise_transhipments(tranNormal, tranReefer, schedule)

    calculate_flow(importNormals, importReefer, exportNormals, exportReefer)
    # visualise_occupancy(yardStorageBlocks, importNormals, importReefer, exportNormals, exportReefer)
    if HIST and DAY_BASED:
        visualise_normals_reefers_hist('Import', importNormals, importReefer)


def visualise_normals_reefers(normals, reefer, title):
    normals, reefer = sort(normals, reefer)
    if DAY_BASED:
        plt.xticks(np.arange(len(SORTED_WEEKDAYS)), SORTED_WEEKDAYS)
    plt.plot(normals, label='#Normal containers')
    plt.plot(reefer, label='#Reefer containers')
    plt.title('Local {}'.format(title))
    plt.legend()
    plt.show()


# TODO make it work for hours
def visualise_normals_reefers_hist(title, normals, reefer):
    normals, reefer = sort(normals, reefer)
    fig, ax = plt.subplots()

    ax.bar(SORTED_WEEKDAYS, normals, align='center', alpha=0.5, label="#Normal containers")
    ax.bar(SORTED_WEEKDAYS, reefer, align='center', alpha=0.5, label="#Reefer containers")

    ax.set_xlabel('Days of the week')
    ax.set_ylabel('# of containers')
    ax.set_title(title)

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


def shift_time_series(flow, offset_hours):
    flow = flow.reset_index()
    flow['Arrival'] = flow.apply(lambda x: shift_time(x.Arrival, offset_hours), axis=1)
    return flow.set_index('Arrival')[list(flow.columns)[1]]


def visualise_flow(title, inFlow, outFlow):
    normals, reefer = sort(inFlow, outFlow)
    if DAY_BASED:
        plt.xticks(np.arange(len(SORTED_WEEKDAYS)), SORTED_WEEKDAYS)
    plt.plot(normals, label='#inFlow')
    plt.plot(reefer, label='#outFlow')
    plt.title('{} Flow'.format(title))
    plt.legend()
    plt.show()


def calculate_flow(importNormals_inFlow, importReefer_inFlow, exportNormals_outFlow,
                   exportReefer_outFlow):
    exportNormals_inFlow = shift_time_series(exportNormals_outFlow, -48)
    exportReefer_inFlow = shift_time_series(exportReefer_outFlow, -48)
    importNormals_outFlow = shift_time_series(importNormals_inFlow, -48)
    importReefer_outFlow = shift_time_series(importReefer_inFlow, -48)

    # incoming = import + incoming transhipments + (local export - 48u)
    totalExport_outFlow = exportNormals_outFlow.add(exportReefer_outFlow)
    totalImport_inFlow = importNormals_inFlow.add(importReefer_inFlow)
    totalExport_inFlow = shift_time_series(totalExport_outFlow, -48)
    totalImport_outFlow = shift_time_series(totalImport_inFlow, 48)
    # Visualise
    visualise_flow('import', totalImport_inFlow, totalImport_outFlow)
    visualise_flow('export', totalExport_inFlow, totalImport_outFlow)

    totalNormal_inFlow = exportNormals_inFlow.add(importNormals_inFlow)
    totalReefer_inFlow = exportReefer_inFlow.add(importReefer_inFlow)
    totalNormal_outFlow = shift_time_series(totalNormal_inFlow, -48)
    totalReefer_outFlow = shift_time_series(totalReefer_inFlow, 48)
    # Visualise

    # Todo: transhipment flow
    transhipments_inFlow = 0
    transhipments_outFlow = 0

    total_inFlow = totalExport_inFlow.add(totalImport_inFlow)
    total_inFlow = total_inFlow.add(transhipments_inFlow)
    total_outFlow = totalExport_outFlow.add(totalImport_outFlow)
    total_outFlow = total_outFlow.add(transhipments_outFlow)

    return total_inFlow, total_outFlow


def visualise_occupancy(yardStorageBlocks, importNormals, importReefer, exportNormals, exportReefer):
    yardStorageBlocks = yardStorageBlocks

    total_capacity = yardStorageBlocks['Capacity'].sum()
    reefer_capacity = calculate_reefer_capacity(yardStorageBlocks)
    normal_capacity = calculate_normal_capacity(yardStorageBlocks)

    total_inFlow, total_outFlow = calculate_flow(importNormals, importReefer, exportNormals, exportReefer)
    if DAY_BASED:
        pass

    else:
        # Formateer index string
        pass