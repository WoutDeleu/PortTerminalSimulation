import matplotlib.pyplot as plt
import numpy as np

from Data.DataParser import cleanData, WEEKDAYS, filterDayOfWeek, WEEKDAYS_NUMERIC, reorderCols

# TODO fixen histogrammen
HIST = False
DAY_BASED = True


def Visualisation_Import(localImport, localImportReefer, schedule):
    localImport = cleanData(localImport)
    localImportReefer = cleanData(localImportReefer)

    schedule = schedule.set_index('VESSEL')

    sumSchedule = schedule.merge(localImport, left_index=True, right_index=True)
    sumSchedule = sumSchedule.merge(localImportReefer, left_index=True, right_index=True)
    if DAY_BASED:
        sumSchedule['Arrival'] = sumSchedule.apply(lambda x: filterDayOfWeek(x.Arrival), axis=1)

    arrivalNormals = sumSchedule.groupby(['Arrival'])['Containers_x'].sum()
    arrivalReefer = sumSchedule.groupby(['Arrival'])['Containers_y'].sum()
    totalImport = arrivalNormals.add(arrivalReefer)

    if HIST:
        pass
    else:
        if DAY_BASED:
            indices = WEEKDAYS_NUMERIC.argsort()
            sorted_weekdays = np.array(WEEKDAYS)[indices]
            sorted_exportNormals = np.array(arrivalNormals)[indices]
            sorted_exportReefer = np.array(arrivalReefer)[indices]
            plt.plot(sorted_exportNormals, label='#Normal containers arriving')
            plt.plot(sorted_exportReefer, label='#Reefer containers arriving')
            plt.xticks(np.arange(len(sorted_weekdays)), sorted_weekdays)
            plt.title('Local Export')
            plt.legend()
            plt.show()
        else:
            plt.plot(arrivalNormals, label='#Normal containers arriving')
            plt.plot(arrivalReefer, label='#Reefer containers arriving')
            plt.title('Local import')
            plt.legend()
            plt.show()


def Visualisation_Export(localExport, localExportReefer, schedule):
    localExport = cleanData(localExport)
    localExportReefer = cleanData(localExportReefer)

    schedule = schedule.set_index('VESSEL')

    sumSchedule = schedule.merge(localExport, left_index=True, right_index=True)
    sumSchedule = sumSchedule.merge(localExportReefer, left_index=True, right_index=True)
    if DAY_BASED:
        sumSchedule['Arrival'] = sumSchedule.apply(lambda x: filterDayOfWeek(x.Arrival), axis=1)

    exportNormals = sumSchedule.groupby(['Arrival'])['Containers_x'].sum()
    exportReefer = sumSchedule.groupby(['Arrival'])['Containers_y'].sum()
    totalExport = exportNormals.add(exportReefer)

    if HIST:
        # fig, ax = plt.subplots()
        # width = 0.8
        #
        # ax.hist(WEEKDAYS_NUMERIC - width / 2, weights=exportNormals, label='#Normal containers leaving',
        #         bins=7, width=width, histtype='bar')
        # ax.hist(WEEKDAYS_NUMERIC + width / 2, weights=exportReefer, label='#Reefer containers leaving',
        #         bins=7, width=width, histtype='bar')
        #
        # ax.set_xticks(np.arange(7))
        # ax.set_xticklabels(WEEKDAYS, rotation=45)
        #
        # plt.plot(np.arange(7), totalExport, label='#Total export', color='red')
        # plt.title('Local Export')
        # plt.legend()
        # plt.show()
        pass
    else:
        indices = WEEKDAYS_NUMERIC.argsort()
        sorted_weekdays = np.array(WEEKDAYS)[indices]
        sorted_exportNormals = np.array(exportNormals)[indices]
        sorted_exportReefer = np.array(exportReefer)[indices]

        if DAY_BASED:
            plt.plot(sorted_exportNormals, label='#Normal containers arriving')
            plt.plot(sorted_exportReefer, label='#Reefer containers arriving')
            plt.xticks(np.arange(len(sorted_weekdays)), sorted_weekdays)

        else:
            plt.plot(exportNormals, label='#Normal containers arriving')
            plt.plot(exportReefer, label='#Reefer containers arriving')
        plt.title('Local Export')
        plt.legend()
        plt.show()


def Visualization_Transshipments(tranNormal, tranReefer, schedule):
    # Visualize the amount of containers transferring between ships per hour

    # Cleaning data
    tranNormal = cleanData(tranNormal)
    tranNormal = reorderCols(tranNormal)
    tranReefer = cleanData(tranReefer)
    tranReefer = reorderCols(tranReefer)

    schedule = schedule.set_index('VESSEL')  # Replaces the 0 index with the actual indexes

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
