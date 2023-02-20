import pandas as pd


def parse_data(fileName):
    fileName = 'Data/' + fileName
    data = pd.read_csv(fileName)
    columns = list(data.columns)[0]
    data = formatDataframe(columns, data)
    return data


def formatDataframe(columns, df):
    data = pd.DataFrame(columns=columns.split(';'))
    for index, row in df.iterrows():
        unit = pd.DataFrame([row[columns].split(';')])
        unit.columns = columns.split(';')
        data = pd.concat([data,unit])
    return data
