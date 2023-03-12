import numpy as np
import pandas as pd

WEEKDAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
WEEKDAYS_LIB = {"Mo": 0, "Tu": 1, "We": 2, "Th": 3, "Fr": 4, "Sa": 5, "Su": 6}
# Converteer de dagen van de week naar numerieke waarden
WEEKDAYS_NUMERIC = np.array([WEEKDAYS_LIB[d] for d in WEEKDAYS])
SORTED_WEEKDAYS = np.array(WEEKDAYS)[WEEKDAYS_NUMERIC.argsort()]


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


def format_import_export(local, localReefer, schedule, DAY_BASED=True):
    scheduled = schedule.merge(local, left_index=True, right_index=True)
    scheduled = scheduled.merge(localReefer, left_index=True, right_index=True)
    if DAY_BASED:
        scheduled['Arrival'] = scheduled.apply(lambda x: filterDayOfWeek(x.Arrival), axis=1)
    normals = scheduled.groupby(['Arrival'])['Containers_x'].sum()
    reefers = scheduled.groupby(['Arrival'])['Containers_y'].sum()
    return normals, reefers