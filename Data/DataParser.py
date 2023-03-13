import re
from datetime import datetime, timedelta

import pandas as pd

from Data.CONST import WEEKDAYS, WEEKDAYS_DIC, WEEKDAYS_DIC_REV, DAY_BASED


def parse_data(fileName):
    fileName = './Data/' + fileName
    data = pd.read_csv(fileName)
    columns = list(data.columns)[0]
    data = formatDataframe(columns, data)
    return data


def formatDataframe(columns, df):
    data = pd.DataFrame(columns=columns.split(';'))
    for index, row in df.iterrows():
        unit = pd.DataFrame([row[columns].split(';')])
        unit.columns = columns.split(';')
        data = pd.concat([data, unit])
    return data


def cleanData(dataframe):
    # Cleaning data
    dataframe = dataframe.rename(columns={'VESSELfrom_VESSELto': 'VESSEL'})  # Rename column for later merge
    dataframe = dataframe.set_index('VESSEL')  # Replaces the 0 index with the actual indexes
    dataframe = dataframe.replace('', 0)  # Replaces empty fields with 0
    dataframe = dataframe.astype(int)  # Changes the type of the parameters to 'int' instead of 'object'

    return dataframe


def filterDayOfWeek(arrival):
    for day in WEEKDAYS:
        if day in arrival:
            return day
    raise Exception("No matching day was found, fault in format arrival")


def reorderCols(dataframe):
    rows, cols = dataframe.shape

    vesselKeys = []
    for x in range(cols):
        vesselKeys.append('V' + str(x))

    dataframe = dataframe.reindex(columns=vesselKeys)  # Sort columns
    return dataframe.reindex(vesselKeys)


def shift_time(day_time, offset_hours):
    if DAY_BASED:
        day = day_time
        day_offset = int(offset_hours / 24)
    else:
        day, time = day_time.split(" ")
        hour, minutes = time.split(":")
        day_offset = 0
        new_hour = int(hour) + offset_hours
        while new_hour < 0 or 24 <= new_hour:
            if new_hour < 0:
                new_hour += 24
                day_offset -= 1
            else:
                new_hour -= 24
                day_offset += 1
        new_time = "{}:{}".format(new_hour, minutes)

    for d in WEEKDAYS:
        if d in day:
            new_day_id = WEEKDAYS_DIC[d] + day_offset
    if new_day_id < 0:
        new_time = "00:00"
        new_day_id = 0
    elif new_day_id >= 6:
        new_time = "23:59"
        new_day_id = 6
    day = WEEKDAYS_DIC_REV[new_day_id]
    if DAY_BASED:
        return day
    return "{} {}".format(day, new_time)


def format_import_export(local, localReefer, schedule):
    scheduled = schedule.merge(local, left_index=True, right_index=True)
    scheduled = scheduled.merge(localReefer, left_index=True, right_index=True)
    if DAY_BASED:
        scheduled['Arrival'] = scheduled.apply(lambda x: filterDayOfWeek(x.Arrival), axis=1)
    normals = scheduled.groupby(['Arrival'])['Containers_x'].sum()
    reefers = scheduled.groupby(['Arrival'])['Containers_y'].sum()
    return normals, reefers


def reformat_index(series):
    series.index = [parse_to_datetime(x) for x in series.index]
    return series.sort_index()

def parse_to_datetime(time_index):
    default_date = '13/03/2023'
    split_day_time = re.split(' ', time_index)
    week_day = split_day_time[0]
    time = split_day_time[1]
    day_delta = WEEKDAYS_DIC[week_day]
    time = datetime.strptime(default_date + ' ' + time, '%d/%m/%Y %H:%M')
    return time + timedelta(days=day_delta)

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

