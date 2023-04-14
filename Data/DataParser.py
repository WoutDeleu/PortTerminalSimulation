import math
import re
from datetime import datetime, timedelta

import pandas as pd

from Data.CONST import WEEKDAYS, WEEKDAYS_DIC, WEEKDAYS_DIC_REV, DAY_BASED, CG


def parse_data(fileName):
    fileName = './Data/' + fileName
    data = pd.read_csv(fileName)
    columns = list(data.columns)[0]
    data = formatDataframe(columns, data)
    return data


def cleanData(dataframe):
    # Cleaning data
    dataframe = dataframe.rename(columns={'VESSELfrom_VESSELto': 'VESSEL'})  # Rename column for later merge
    dataframe = dataframe.set_index('VESSEL')  # Replaces the 0 index with the actual indexes
    dataframe = dataframe.replace('', 0)  # Replaces empty fields with 0
    dataframe = dataframe.astype(int)  # Changes the type of the parameters to 'int' instead of 'object'

    return dataframe


def formatDataframe(columns, df):
    data = pd.DataFrame(columns=columns.split(';'))
    for index, row in df.iterrows():
        unit = pd.DataFrame([row[columns].split(';')])
        unit.columns = columns.split(';')
        data = pd.concat([data, unit])
    return data


def filterDayOfWeek(arrival):
    for day in WEEKDAYS:
        if day in arrival:
            return day
    raise Exception("No matching day was found, fault in format arrival")


def sort_by_day(serie):
    sorted_serie = pd.Series(dtype='S')
    for i in range(0, 7):
        if WEEKDAYS[i] in serie.index:
            sorted_serie = pd.concat([sorted_serie, serie[pd.Series(WEEKDAYS[i])]], ignore_index=True)
        else:
            sorted_serie = pd.concat([sorted_serie, pd.Series(0)], ignore_index=True)
    return sorted_serie.set_axis(WEEKDAYS)


def sum_by_index(serie):
    result_dict = generate_dict(WEEKDAYS)
    for day, value in serie.items():
        result_dict[day] = result_dict[day] + value
    result_df = pd.DataFrame(list(result_dict.items()), columns=['Arrival', 'Total'])
    return result_df.set_index('Arrival')[list(result_df.columns)[1]]


def generate_dict(index_array):
    result_dict = {}
    for index in index_array:
        result_dict[index] = 0
    return result_dict


def array_to_string(arr):
    s = '['
    for e in arr:
        s += str(e)
        s += '; '
    s = s[:-2]
    s += ']'
    return s


def sort(serie):
    if DAY_BASED:
        return sort_by_day(serie)
    else:
        return reformat_index(serie)


def reorderCols(dataframe):
    rows, cols = dataframe.shape

    vesselKeys = []
    for x in range(cols):
        vesselKeys.append('V' + str(x))

    dataframe = dataframe.reindex(columns=vesselKeys)  # Sort columns
    return dataframe.reindex(vesselKeys)


def shift_time(day_time, offset_hours):
    if not DAY_BASED:
        return day_time + timedelta(hours=offset_hours)

    day = day_time
    day_offset = int(offset_hours / 24)
    for d in WEEKDAYS:
        if d in day:
            new_day_id = WEEKDAYS_DIC[d] + day_offset
    if new_day_id < 0:
        new_day_id = 0
    elif new_day_id >= 6:
        new_day_id = 6
    day = WEEKDAYS_DIC_REV[new_day_id]
    return day


def format_import_export(local, localReefer, schedule):
    scheduled = schedule.merge(local, left_index=True, right_index=True)
    scheduled = scheduled.merge(localReefer, left_index=True, right_index=True)
    if DAY_BASED:
        scheduled['Arrival'] = scheduled.apply(lambda x: filterDayOfWeek(x.Arrival), axis=1)
    if CG:
        scheduled['Containers_x'] = 1
        scheduled['Containers_y'] = 1
    normals = scheduled.groupby(['Arrival'])['Containers_x'].sum()
    reefers = scheduled.groupby(['Arrival'])['Containers_y'].sum()
    return normals, reefers


def reformat_index(series):
    series.index = [parse_to_datetime(x) for x in series.index]
    return series.sort_index()


def add_series(s1, s2):
    # Voeg de 2 series samen met een outer join om alle indexen te behouden
    combined = pd.concat([s1, s2], axis=1, join='outer')

    # Vul eventuele ontbrekende waarden in met 0
    combined = combined.fillna(0)

    # Tel beide series op en geef het resultaat terug
    return combined.iloc[:, 0] + combined.iloc[:, 1]


def subtract_series(s1, s2):
    # Combineer de 2 series met een outer join om alle indexen te behouden
    combined = pd.concat([s1, s2], axis=1, join='outer')

    # Vul eventuele ontbrekende waarden in met 0
    combined = combined.fillna(0)

    # Trek de tweede serie af van de eerste en geef het resultaat terug
    return combined.iloc[:, 0] - combined.iloc[:, 1]


def parse_to_datetime(time_index):
    if type(time_index) is pd._libs.tslibs.timestamps.Timestamp:
        return time_index

    default_date = '13/03/2023'
    split_day_time = re.split(' ', time_index)
    week_day = split_day_time[0]
    time = split_day_time[1]
    day_delta = WEEKDAYS_DIC[week_day]
    time = datetime.strptime(default_date + ' ' + time, '%d/%m/%Y %H:%M')
    return time + timedelta(days=day_delta)


def convert_number_to_minutes(number):
    day_hours = math.floor(number / 10000)
    hours = math.floor(number - day_hours * 10000) / 100
    minutes = (number - day_hours * 10000 - hours * 100)
    return int((day_hours + hours) * 60 + minutes)