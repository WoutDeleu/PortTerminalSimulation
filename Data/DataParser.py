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
    days = {'Mo': 'Mon', 'Tu': 'Tue', 'We': 'Wed', 'Th': 'Thu', 'Fr': 'Fri', 'Sa': 'Sat', 'Su': 'Sun'}
    new_index = [days[x[:2]] + x[2:] for x in series.index]
    series.index = new_index
    return series