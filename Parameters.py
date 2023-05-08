AMOUNT_SIMULATIONS = 10

SIMULATION_MONTHS = 12
SIMULATION_DAYS = SIMULATION_MONTHS * 30
SIMULATION_HOURS = SIMULATION_DAYS * 24

# LATEX formats table to copy paste in Latex-doc
LATEX = False
OVERVIEW = True

# Possible scenarios
FIFO_BASIC = False
LOWEST_OCCUPANCY = True

# Distance calculation reference
ARRIVAL_BASED = True
DEPARTURE_BASED = False


def check_parameters():
    if not ((FIFO_BASIC ^ LOWEST_OCCUPANCY) and (FIFO_BASIC or LOWEST_OCCUPANCY)):
        raise Exception("Only one simulation scenario can be true")

    if not ((ARRIVAL_BASED ^ DEPARTURE_BASED) and (ARRIVAL_BASED or DEPARTURE_BASED)):
        raise Exception("Only one distance calculation reference can be true (arrival or departure based)")

    print("Parameters: ")
    if FIFO_BASIC:
        print("\tFIFO_BASIC")
    if LOWEST_OCCUPANCY:
        print("\tLOWEST_OCCUPANCY")
    if ARRIVAL_BASED:
        print("\tARRIVAL_BASED")
    if DEPARTURE_BASED:
        print("\tDEPARTURE_BASED")
    print("Duration: " + str(SIMULATION_MONTHS) + " months")
    print("Number of simulations: " + str(AMOUNT_SIMULATIONS))