import math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import fitter
from fitter import Fitter, get_common_distributions
from collections import Counter
import seaborn as sns
import scipy.stats as st

from Data.CONST import SORTED_WEEKDAYS, DAY_BASED, HIST, WEEKDAYS_DIC
from Data.DataParser import cleanData, filterDayOfWeek, reorderCols, format_import_export, shift_time, sort, \
    sum_by_index, add_series, subtract_series, convert_number_to_minutes


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
    if HIST:
        visualise_normals_reefers_hist('Import', importNormals.copy(), importReefer.copy())
        visualise_normals_reefers_hist('Export', exportNormals.copy(), exportReefer.copy())

    visualise_service_time(tranNormal.copy(), tranReefer.copy(), schedule.copy())

    visualise_normals_reefers(importNormals, importReefer, 'Import')
    visualise_normals_reefers(exportNormals, exportReefer, 'Export')

    calculate_flow(yardStorageBlocks.copy(), importNormals.copy(), importReefer.copy(), exportNormals.copy(), exportReefer.copy(), tranNormal.copy(), tranReefer.copy(), schedule.copy())

    visualise_cg_size(localExport.copy(), localExportReefer.copy(), localImport.copy(), localImportReefer.copy(), tranNormal.copy(), tranReefer.copy())


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


def visualise_normals_reefers_hist(title, normals, reefer):
    normals = sort(normals)
    reefer = sort(reefer)
    fig, ax = plt.subplots(figsize=(18, 8))
    if DAY_BASED:
        ax.bar(SORTED_WEEKDAYS, normals, align='center', alpha=0.5, label="#Normal containers")
        ax.bar(SORTED_WEEKDAYS, reefer, align='center', alpha=0.5, label="#Reefer containers")
    else:
        x = [dt.strftime('%a')[0:2] + dt.strftime(' %Hh') for dt in normals.keys()]
        x2 = [dt.strftime('%a')[0:2] + dt.strftime(' %Hh') for dt in reefer.keys()]
        ax.bar(x, normals.values, align='center', alpha=0.5, label="#Normal containers")
        ax.bar(x2, reefer.values, align='center', alpha=0.5, label="#Normal containers")
    ax.set_xlabel('Days of the week')
    ax.set_ylabel('# of containers')
    ax.set_title(title)
    plt.show()

    # Distribution
    # normal_flow = normals.index
    # f = Fitter(normal_flow)
    # f.fit()
    # print(f.summary())
    # print(f.get_best(method='sumsquare_error'))


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
    flow = flow.rename(columns={'index': 'Arrival'})
    flow['Arrival'] = flow.apply(lambda x: shift_time(x.Arrival, offset_hours), axis=1)
    result = flow.set_index('Arrival')[list(flow.columns)[1]]
    if DAY_BASED:
        return sum_by_index(result)
    return result


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
    # visualise_flow('Import', totalImport_inFlow, totalImport_outFlow)
    # visualise_flow('Export', totalExport_inFlow, totalImport_outFlow)

    totalNormal_inFlow = add_series(exportNormals_inFlow, importNormals_inFlow)
    totalReefer_inFlow = add_series(importReefer_inFlow, exportReefer_inFlow)
    totalNormal_outFlow = add_series(exportNormals_outFlow, importNormals_outFlow)
    totalReefer_outFlow = add_series(exportReefer_outFlow, importReefer_outFlow)
    # Visualise
    # visualise_flow('Normal', totalImport_inFlow, totalImport_outFlow)
    # visualise_flow('Reefer', totalNormal_outFlow, totalReefer_outFlow)

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

    visualise_innerInterval(total_inFlow.copy(), type='in_flow')
    visualise_innerInterval(total_outFlow.copy(), type='out_flow')


def calculate_full_occupancy(yardStorageBlocks, total_inFlow, total_outFlow, totalNormal_inFlow, totalReefer_inFlow,
                             totalNormal_outFlow, totalReefer_outFlow):
    total_capacity = yardStorageBlocks['Capacity'].sum()
    reefer_capacity = calculate_capacity(yardStorageBlocks, 'REEFER')
    normal_capacity = calculate_capacity(yardStorageBlocks, 'FULL')

    visualise_occupancy('Total', total_capacity, total_inFlow, total_outFlow)
    # visualise_occupancy('Normal', normal_capacity, totalNormal_inFlow, totalNormal_outFlow)
    # visualise_occupancy('Reefer', reefer_capacity, totalReefer_inFlow, totalReefer_outFlow)


def visualise_occupancy(title, capacity, inflow, outflow):
    # Subtract flow -> Calculate absolute flow
    total_inFlow = sort(inflow).fillna(0)
    total_outFlow = sort(outflow).fillna(0)
    absolute_flow = subtract_series(total_inFlow, total_outFlow)

    # cummulative = occupancy
    absolute_occupancy = absolute_flow.cumsum()
    occupancy = (absolute_occupancy / capacity) * 100

    # Create a dataframe
    occupancy = occupancy.to_frame()
    occupancy['Date'] = occupancy.index
    occupancy['Date'] = pd.to_datetime(occupancy['Date']).astype(np.int64)
    occupancy['Date'] = (occupancy['Date']-1678492800000000000)/3600000000000
    occupancy = occupancy.rename(columns={0: 'Occurrences'})

    # Fill up missing hours
    occupancy = occupancy.set_index(occupancy['Date'])
    occupancy = occupancy.drop(['Date'], axis=1)
    occupancy = occupancy.reindex(np.arange(occupancy.index[-1]+1), fill_value=0)
    occupancy = occupancy.replace(0.00000).ffill()

    # Visualise
    plt.xlabel('Time (hours)')
    plt.ylabel('Occupancy %')
    plt.title("Occupancy of the yard")
    plt.bar(occupancy.index, occupancy['Occurrences'], width=1)
    plt.show()

    # Find distribution
    date = occupancy.index
    f = Fitter(date, distributions=get_common_distributions(), bins=200)  # distributions parameter weglaten om alle mogelijke te proberen
    f.fit()
    print(f.summary())
    print(f.get_best(method='sumsquare_error'))
    plt.show()

    # if DAY_BASED:
    #     plt.xticks(np.arange(len(SORTED_WEEKDAYS)), SORTED_WEEKDAYS)
    # plt.plot(occupancy, label='#occupancy')
    # plt.title('{} Occupancy'.format(title))
    # plt.ylabel('%')
    # plt.xlabel('Date')
    # plt.legend()
    # plt.show()
def visualise_innerInterval(total_Flow, type):
    resulting = pd.Series()
    previous_index = 0
    for index, value in total_Flow.items():
        if previous_index != 0:
            if math.isnan(value) != True:
                value = index - previous_index
                resulting = pd.concat([resulting, pd.Series(value)])
            previous_index = index
        else:
            previous_index = index
    timedelta = [td.total_seconds() / 3600 for td in resulting]
    timedelta = [round(td, 1) for td in timedelta]

    # Sorteer de waarden
    timedelta_hours_sorted = pd.Series(np.sort(timedelta))

    # Bereken de cumulatieve frequenties en normeer ze tot een CDF
    cdf = pd.Series(np.cumsum(np.ones_like(timedelta_hours_sorted)) )
    df = pd.concat({'Time': timedelta_hours_sorted, 'CDF': cdf}, axis=1)
    df
    if HIST:
        # Visualise
        if type == 'in_flow':
            sns.histplot(data=timedelta_hours_sorted).set(
                title='Arrival time interval')
        else :
            sns.histplot(data=timedelta_hours_sorted).set(
                title='Departure time interval')
        plt.show()

    else:
        # Maak een plot van de CDF
        fig, ax = plt.subplots()
        ax.plot(timedelta_hours_sorted, cdf)
        ax.set_xlabel('Minuten')
        ax.set_ylabel('Cumulatieve frequentie')
        ax.set_title('Cumulatieve distributiefunctie')

        plt.show()
        print()

    # Find distribution
    # inter_time = [Counter(timedelta_hours_sorted.stack())]
    # inter_time = sum(inter_time, Counter())
    #
    # inter_time = timedelta_hours_sorted["Service time (hours)"].values
    # f = Fitter(timedelta_hours_sorted)  # distributions parameter weglaten om alle mogelijke te proberen
    # f.fit()
    # print(f.summary())
    # # print(f.get_best(method='sumsquare_error'))
    # plt.show()


def visualise_cg_size(localExport, localExportReefer, localImport, localImportReefer, tranNormal, tranReefer):
    # Calculating occurrences of each cg_size for import and export
    cg_sizes_normal = [Counter(d['Containers']) for d in [localExport, localImport]]
    res_normal = sum(cg_sizes_normal, Counter())
    cg_sizes_reefer = [Counter(d['Containers']) for d in [localExportReefer, localImportReefer]]
    res_reefer = sum(cg_sizes_reefer, Counter())

    # Calculating occurrences of each cg_size for transshipment's
    cg_sizes_normal = [Counter(tranNormal.stack())]
    res_normal = res_normal + sum(cg_sizes_normal, Counter())
    del res_normal[0]  # cg's of size 0 are no cg's and can be thrown away
    cg_sizes_reefer = [Counter(tranReefer.stack())]
    res_reefer = res_reefer + sum(cg_sizes_reefer, Counter())
    del res_reefer[0]  # cg's of size 0 are no cg's and can be thrown away

    # Calculating total occurrences
    res = res_normal + res_reefer

    # Visualise
    # plt.xlim(0, 100)
    # plt.xlabel('Amount of containers')
    # plt.ylabel('Occurrences')
    # plt.title("Container group sizes - Reefer")
    # plt.bar(res_reefer.keys(), res_reefer.values(), label='Reefer')
    # plt.show()

    # plt.xlim(0, 100)
    # plt.xlabel('Amount of containers')
    # plt.ylabel('Occurrences')
    # plt.title("Container group sizes - Normal")
    # plt.bar(res_normal.keys(), res_normal.values(), label='Normal')
    # plt.show()

    plt.xlim(0, 100)
    plt.xlabel('Amount of containers')
    plt.ylabel('Occurrences')
    plt.title("Container group sizes - Total")
    plt.bar(res.keys(), res.values(), label='Total')
    plt.show()

    # Distribution
    res = np.array(list(res.items()))
    f = Fitter(res,xmax=100, distributions=['skewcauchy'],bins=100) # distributions parameter weglaten om alle mogelijke te proberen
    f.fit()
    print(f.summary())
    print(f.get_best(method='sumsquare_error'))
    print(f.fitted_param['skewcauchy'])
    plt.show()

def visualise_service_time(tranNormal, tranReefer, schedule):
    # Convert the schedule dataframe to minutes starting with MO 00:00 as 0
    schedule = schedule.replace(['Mo ', 'Tu ', 'We ', 'Th ', 'Fr ', 'Sa ', 'Su ', ':'],
                                ['0', '24', '48', '72', '96', '120', '144', ''], regex=True)
    schedule = schedule.astype(int)
    schedule['Arrival'] = schedule['Arrival'].apply(convert_number_to_minutes)
    schedule['Departure'] = schedule['Departure'].apply(convert_number_to_minutes)

    # Change the value for the departure time of the non-empty cg
    for x in tranNormal.columns:
        tranNormal[x] = np.where(tranNormal[x] != 0, schedule.loc[x]['Departure'], 0)

    # Subtract the arrival time from the departure time for every non-empty cg
    tranNormal = tranNormal.T
    for y in tranNormal.columns:
        tranNormal[y] = np.where(tranNormal[y] != 0, tranNormal[y] - schedule.loc[y]['Arrival'], 0)
        tranNormal[y] = np.where(tranNormal[y] < 0, tranNormal[y] * (-1) + 10080, tranNormal[y])
    tranNormal = tranNormal.T
    tranNormal = tranNormal/60

    # Calculate occurrences of every service time
    service_times_normal = [Counter(tranNormal.stack())]
    res_normal = sum(service_times_normal, Counter())
    del res_normal[0]  # cg's of size 0 are no cg's and can be thrown away
    res_normal = pd.DataFrame.from_dict(res_normal, orient='index').reset_index()
    res_normal = res_normal.rename(columns={'index': 'Service time (hours)', 0: 'Occurrences'})

    # Visualise
    plt.xlabel('Service time')
    plt.ylabel('Occurrences')
    plt.title("Service time of container groups")
    plt.bar(res_normal['Service time (hours)'], res_normal['Occurrences'], width=3)
    plt.show()

    # Find distribution
    # service_time = res_normal["Service time (hours)"].values
    # f = Fitter(service_time,
    #            distributions=get_common_distributions())  # distributions parameter weglaten om alle mogelijke te proberen
    # f.fit()
    # print(f.summary())
    # print(f.get_best(method='sumsquare_error'))
    # plt.show()



