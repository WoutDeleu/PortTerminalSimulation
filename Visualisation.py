import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import Counter

from Data.CONST import SORTED_WEEKDAYS, DAY_BASED, HIST, WEEKDAYS_DIC
from Data.DataParser import cleanData, filterDayOfWeek, reorderCols, format_import_export, shift_time, sort, \
    sum_by_index, add_series, subtract_series


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

    calculate_flow(yardStorageBlocks, importNormals, importReefer, exportNormals, exportReefer, tranNormal, tranReefer,
                   schedule)

    visualise_average_cg_size(localExport, localExportReefer, localImport, localImportReefer, tranNormal, tranReefer)
    if HIST and DAY_BASED:
        visualise_normals_reefers_hist('Import', importNormals, importReefer)

def calculate_capacity(yardStorageBlocks, type):
    yardStorageBlocks = yardStorageBlocks[yardStorageBlocks['ContainerType'] == type]
    return yardStorageBlocks['Capacity'].sum()


def visualise_normals_reefers(normals, reefer, title):
    reefer = sort(reefer)
    normals = sort(normals)
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


def calculate_transshipment_flow(flow_type, tranData, schedule):
    # Calculate sum of containers
    tranSum = 0
    match flow_type:
        case 'inflow':
            tranSum = tranData.sum(axis=1)
        case 'outflow':
            tranSum = tranData.sum()

    # Linking vessels with schedule:
    # This dataframe shows when and how many containers are loaded/unloaded per Vessel
    tranSchedule = schedule.merge(tranSum.to_frame(), left_index=True, right_index=True)
    tranSchedule = tranSchedule.rename(columns={0: 'Containers'})

    if DAY_BASED:
        tranSchedule['Arrival'] = tranSchedule.apply(lambda x: filterDayOfWeek(x.Arrival), axis=1)

    # Summing containers per arrival/departure time
    tranSum = tranSchedule.groupby(['Arrival'])['Containers'].sum()

    return sort(tranSum)


def shift_time_series(flow, offset_hours):
    flow = flow.reset_index()
    if DAY_BASED:
        flow['Arrival'] = flow.apply(lambda x: shift_time(x.Arrival, offset_hours), axis=1)
        result = flow.set_index('Arrival')[list(flow.columns)[1]]
        return sum_by_index(result)
    else:
        flow['Arrival'] = flow.apply(lambda x: shift_time(x['index'], offset_hours), axis=1)
        return flow.set_index('Arrival')[list(flow.columns)[1]]


def visualise_flow(title, inFlow, outFlow):
    inFlow = sort(inFlow)
    outFlow = sort(outFlow)
    if DAY_BASED:
        plt.xticks(np.arange(len(SORTED_WEEKDAYS)), SORTED_WEEKDAYS)
    plt.plot(inFlow, label='#inFlow')
    plt.plot(outFlow, label='#outFlow')
    plt.title('{} Flow'.format(title))
    plt.legend()
    plt.show()


def calculate_flow(yardStorageBlocks, importNormals_inFlow, importReefer_inFlow, exportNormals_outFlow,
                   exportReefer_outFlow, tranNormal, tranReefer, schedule):
    exportNormals_inFlow = shift_time_series(exportNormals_outFlow, -48)
    exportReefer_inFlow = shift_time_series(exportReefer_outFlow, -48)
    importNormals_outFlow = shift_time_series(importNormals_inFlow, -48)
    importReefer_outFlow = shift_time_series(importReefer_inFlow, -48)

    # incoming = import + incoming transhipments + (local export - 48u)
    totalExport_outFlow = add_series(exportReefer_outFlow, exportNormals_outFlow)
    totalImport_inFlow = add_series(importReefer_inFlow, importNormals_inFlow)
    totalExport_inFlow = shift_time_series(totalExport_outFlow, -48)
    totalImport_outFlow = shift_time_series(totalImport_inFlow, 48)
    # Visualise
    visualise_flow('Import', totalImport_inFlow, totalImport_outFlow)
    visualise_flow('Export', totalExport_inFlow, totalImport_outFlow)

    totalNormal_inFlow = add_series(exportNormals_inFlow, importNormals_inFlow)
    totalReefer_inFlow = add_series(importReefer_inFlow, exportReefer_inFlow)
    totalNormal_outFlow = add_series(exportNormals_outFlow, importNormals_outFlow)
    totalReefer_outFlow = add_series(exportReefer_outFlow, importReefer_outFlow)
    # Visualise
    visualise_flow('Normal', totalImport_inFlow, totalImport_outFlow)
    visualise_flow('Reefer', totalNormal_outFlow, totalReefer_outFlow)

    # Transhipments
    transhipments_inFlow = calculate_transshipment_flow('inflow', tranNormal, schedule) + calculate_transshipment_flow(
        'inflow', tranReefer, schedule)
    transhipments_outFlow = calculate_transshipment_flow('outflow', tranNormal,
                                                         schedule) + calculate_transshipment_flow('outflow', tranReefer,
                                                                                                  schedule)

    total_inFlow = add_series(totalImport_inFlow, totalExport_inFlow)
    total_inFlow = add_series(transhipments_inFlow, total_inFlow)
    total_outFlow = add_series(totalImport_outFlow, totalExport_outFlow)
    total_outFlow = total_outFlow.add(transhipments_outFlow)

    calculate_full_occupancy(yardStorageBlocks, total_inFlow, total_outFlow, totalNormal_inFlow, totalReefer_inFlow,
                             totalNormal_outFlow, totalReefer_outFlow)


def calculate_full_occupancy(yardStorageBlocks, total_inFlow, total_outFlow, totalNormal_inFlow, totalReefer_inFlow,
                             totalNormal_outFlow, totalReefer_outFlow):
    total_capacity = yardStorageBlocks['Capacity'].sum()
    reefer_capacity = calculate_capacity(yardStorageBlocks, 'REEFER')
    normal_capacity = calculate_capacity(yardStorageBlocks, 'FULL')

    visualise_occupancy('Total', total_capacity, total_inFlow, total_outFlow)
    visualise_occupancy('Normal', normal_capacity, totalNormal_inFlow, totalNormal_outFlow)
    visualise_occupancy('Reefer', reefer_capacity, totalReefer_inFlow, totalReefer_outFlow)


def visualise_occupancy(title, capacity, inflow, outflow):
    # Subtract flow -> Calculate absolute flow
    total_inFlow = sort(inflow).fillna(0)
    total_outFlow = sort(outflow).fillna(0)
    absolute_flow = subtract_series(total_inFlow, total_outFlow)

    # cummulative = occupancy
    absolute_occupancy = absolute_flow.cumsum()
    occupancy = (absolute_occupancy / capacity) * 100

    if DAY_BASED:
        plt.xticks(np.arange(len(SORTED_WEEKDAYS)), SORTED_WEEKDAYS)
    plt.plot(occupancy, label='#occupancy')
    plt.title('{} Occupancy'.format(title))
    plt.ylabel('%')
    plt.xlabel('Date')
    plt.legend()
    plt.show()


def visualise_innerInterval(total_inFlow):
    resulting = pd.Series()
    previous_index = 0
    for index, value in total_inFlow.items():
        if previous_index != 0:
            if DAY_BASED:
                value = abs(WEEKDAYS_DIC[index] - WEEKDAYS_DIC[previous_index])
            else:
                value = index - previous_index
            resulting = pd.concat([resulting, pd.Series(value)])
        previous_index = index
    if DAY_BASED:
        # Note: not very informative with days...
        pass
    else:
        timedelta = [td.total_seconds() / 60 for td in resulting]
        timedelta = [round(td, 1) for td in timedelta]

        # Sorteer de waarden
        timedelta_minutes_sorted = np.sort(timedelta)

        # Bereken de cumulatieve frequenties en normeer ze tot een CDF
        cdf = np.cumsum(np.ones_like(timedelta_minutes_sorted)) / len(timedelta_minutes_sorted)

        # Maak een plot van de CDF
        fig, ax = plt.subplots()
        ax.plot(timedelta_minutes_sorted, cdf)
        ax.set_xlabel('Minuten')
        ax.set_ylabel('Cumulatieve frequentie')
        ax.set_title('Cumulatieve distributiefunctie')

        plt.show()
def visualise_average_cg_size(localExport, localExportReefer, localImport, localImportReefer, tranNormal, tranReefer):
    # Calculating occurences of eacht cg_size
    cg_sizes = [Counter(d['Containers']) for d in [localExport, localExportReefer, localImport, localImportReefer]]
    res = sum(cg_sizes, Counter())
    cg_sizes = [Counter(d.stack()) for d in [tranNormal, tranReefer]]
    res = res + sum(cg_sizes, Counter())
    del res[0] # cg's of size 0 are no cg's and can be thrown away

    # Visualise

    print(res)
