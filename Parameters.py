# 120 results in proper runs
AMOUNT_SIMULATIONS = 10

SIMULATION_MONTHS = 12
SIMULATION_DAYS = SIMULATION_MONTHS * 30
SIMULATION_HOURS = SIMULATION_DAYS * 24

# LATEX formats table to copy paste in Latex-doc
LATEX = False
OVERVIEW = True

# Possible scenarios
CLOSEST = True  # This was the base scenario
LOWEST_OCCUPANCY = False
SPLIT_UP = False
MIXED_RULE = False

# Distance calculation reference
ARRIVAL_BASED = True
DEPARTURE_BASED = False


def only_one_true():
    counter = 0
    if CLOSEST:
        counter += 1
    if LOWEST_OCCUPANCY:
        counter += 1
    if SPLIT_UP:
        counter += 1
    if MIXED_RULE:
        counter += 1
    return counter == 1


def check_parameters():
    if not only_one_true():
        raise Exception("Only one simulation scenario can be true")

    if not (ARRIVAL_BASED or DEPARTURE_BASED):
        raise Exception("At least one distance calculation reference can be true (arrival or departure based)")

    print("Parameters: ")
    if CLOSEST:
        print("\tCLOSEST")
    if LOWEST_OCCUPANCY:
        print("\tLOWEST_OCCUPANCY")
    if SPLIT_UP:
        print("\tSPLIT_UP")
    if MIXED_RULE:
        print("\tMIXED_RULE")
    if ARRIVAL_BASED and DEPARTURE_BASED:
        print("\tARRIVAL_BASED and DEPARTURE_BASED combined")
    elif ARRIVAL_BASED:
        print("\tARRIVAL_BASED")
    elif DEPARTURE_BASED:
        print("\tDEPARTURE_BASED")
    print("Duration: " + str(SIMULATION_MONTHS) + " months = " + str(SIMULATION_DAYS) + " days = " + str(
        SIMULATION_HOURS) + " hours")
    print()