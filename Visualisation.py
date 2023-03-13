import matplotlib.pyplot as plt
import numpy as np

from Data.CONST import WEEKDAYS, WEEKDAYS_NUMERIC, SORTED_WEEKDAYS, DAY_BASED, HIST
from Data.DataParser import cleanData, filterDayOfWeek, reorderCols, format_import_export, shift_time, reformat_index


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

    calculate_flow(yardStorageBlocks, importNormals, importReefer, exportNormals, exportReefer, tranNormal, tranReefer, schedule)
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
def calculate_transshipment_flow(flow_type, tranData, schedule):
    #Calculate sum of containers
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

    #Summing containers per arrival/departure time
    tranSum = tranSchedule.groupby(['Arrival'])['Containers']

    indices = WEEKDAYS_NUMERIC.argsort()

    return np.array(tranSum)[indices]
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


def calculate_flow(yardStorageBlocks,importNormals_inFlow, importReefer_inFlow, exportNormals_outFlow,
                   exportReefer_outFlow, tranNormal, tranReefer,schedule):
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
    transhipments_inFlow = calculate_transshipment_flow('inflow',tranNormal,schedule) + calculate_transshipment_flow('inflow',tranReefer,schedule)
    transhipments_outFlow = calculate_transshipment_flow('outflow',tranNormal,schedule) + calculate_transshipment_flow('outflow',tranReefer,schedule)

    total_inFlow = totalExport_inFlow.add(totalImport_inFlow)
    total_inFlow = total_inFlow.add(transhipments_inFlow)
    total_outFlow = totalExport_outFlow.add(totalImport_outFlow)
    total_outFlow = total_outFlow.add(transhipments_outFlow)

    visualise_occupancy(yardStorageBlocks, total_inFlow, total_outFlow, totalNormal_inFlow, totalReefer_inFlow)


def visualise_occupancy(yardStorageBlocks, total_inFlow, total_outFlow, totalNormal_inFlow, totalReefer_inFlow):
    total_capacity = yardStorageBlocks['Capacity'].sum()
    reefer_capacity = calculate_reefer_capacity(yardStorageBlocks)
    normal_capacity = calculate_normal_capacity(yardStorageBlocks)

    # Subtract flow -> Calculate absolute flow
    total_inFlow, total_outFlow = sort(total_inFlow, total_outFlow)
    absolute_flow = total_inFlow.sub(total_outFlow)

    # cummulative = occupancy
    absolute_occupancy = absolute_flow.cumsum()

    if DAY_BASED:
        pass

    else:
        # Formateer index string
        pass