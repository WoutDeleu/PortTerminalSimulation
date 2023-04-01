from YardBlock import YardBlock


def simulate(data):
    # Simulation period (months)
    period = 1

    # converting the yard storage blocks dataframe into a list of objects
    yardBlockList = data['YARDSTORAGEBLOCKS'].astype({'Capacity': 'int'}).values.tolist()
    yardBlocks = []
    for x in yardBlockList:
        yardBlocks.append(YardBlock(x[0], x[1], x[2], x[3], 0, x[4], x[5]))




