import random

import pandas as pd
import scipy.stats as scipyst

from ContainerGroup import ContainerGroup
from Position import Position
from YardBlock import YardBlock


def simulate(stats, data, SIMULATION_HOURS, ARRIVAL_BASED, DEPARTURE_BASED, MIXED_RULE, CLOSEST, LOWEST_OCCUPANCY,
             SPLIT_UP):
    sim = Simulation(data, ARRIVAL_BASED, DEPARTURE_BASED, MIXED_RULE, CLOSEST, LOWEST_OCCUPANCY,
                     SPLIT_UP)
    sim.setSimulationHours(0, 0, SIMULATION_HOURS)
    sim.check_parameters()
    sim.run()
    stats_fifo = pd.concat(
        [stats, pd.DataFrame([{'Containers_Rejected': sim.rejected_containers, 'CG_Rejected': sim.rejected_groups,
                               'Normal_Rejected': sim.rejected_per_type["normal"],
                               'Reefer_Rejected': sim.rejected_per_type["reefer"],
                               'Total_Travel_Distance': sim.total_travel_distance_containers,
                               'AVG_Travel_Distance_Containers': sim.getAvgTravel_Containers(),
                               'Max_Occupancy': sim.getMaxOccupancy(),
                               'AVG_Daily_Individual_Occupancy': sim.getAvgOccupancy_individual(),
                               'AVG_daily_total_Occupancy': sim.getDailyTotalOccupancy()}])

         ]
    )
    if SPLIT_UP:
        return stats_fifo, sim.total_split_ups
    return stats_fifo


def get_inter_arrival_time_sample():
    return scipyst.expon.rvs(scale=0.09155, loc=0)


def get_number_of_containers_sample():
    scale = 21
    max = 2500
    sample = scipyst.weibull_min.rvs(0.6, loc=0.5 / scale) * scale
    while sample > max:
        sample = scipyst.weibull_min.rvs(0.6, loc=0.5 / scale) * scale
    return round(sample)


def get_service_time_sample():
    return round(random.uniform(0, 166))


def get_container_type_sample():
    return random.choices(["normal", "reefer"], weights=[69, 31], k=1)[0]


def get_arrival_or_departure_point_sample(df):
    row = df.sample()
    return Position(row['X_coord'].values[0], row['Y_coord'].values[0])


def get_container_flow_type():
    return random.choices(["import", "export"], weights=[19, 81], k=1)[0]


def check_container_type(group_type, block_type):
    if group_type.lower() == block_type.lower():
        return True
    if group_type == 'normal' and block_type == 'FULL':
        return True
    else:
        return False


def add_to_Q(event_list, time):
    if time not in event_list:
        event_list.append(time)
        event_list.sort()
    return event_list


class Simulation:

    def __init__(self, data, ARRIVAL_BASED, DEPARTURE_BASED, MIXED_RULE, CLOSEST, LOWEST_OCCUPANCY,
                 SPLIT_UP):
        # Simulation variables - time
        self.time = 0
        self.day_counter = 0
        self.day_clock = 0

        self.data = data

        self.total_containers = 0
        self.total_GC = 0

        self.rejected_containers = 0
        self.rejected_groups = 0
        self.rejected_per_type = {'reefer': 0, 'normal': 0}

        self.total_travel_distance_containers = 0
        self.served_containers = 0

        self.average_daily_occupancy_per_YB = pd.Series(dtype=float)
        self.average_daily_occupancy_total = pd.Series(dtype=float)

        yard_block_list = data['YARDSTORAGEBLOCKS'].astype({'Capacity': 'int'}).values.tolist()
        self.yard_blocks = []
        for x in yard_block_list:
            self.yard_blocks.append(YardBlock(x[0], x[1], x[2], x[3], Position(x[4], x[5])))

        berthing_position_list = data['BerthingPositions'].values.tolist()
        self.berthing_positions = []
        for x in berthing_position_list:
            self.berthing_positions.append(Position(x[1], x[2]))

        truck_parking_locations_list = data['TruckParkingLocations'].values.tolist()
        self.truck_parking_locations = []
        for x in truck_parking_locations_list:
            self.truck_parking_locations.append(Position(x[1], x[2]))

        self.SIMULATION_HOURS = 0

        self.ARRIVAL_BASED = ARRIVAL_BASED
        self.DEPARTURE_BASED = DEPARTURE_BASED

        self.MIXED_RULE = MIXED_RULE
        self.CLOSEST = CLOSEST
        self.LOWEST_OCCUPANCY = LOWEST_OCCUPANCY
        self.SPLIT_UP = SPLIT_UP
        if SPLIT_UP:
            self.total_split_ups = 0

    def run(self):
        # Variables to get daily statistics
        self.setup_timers()

        # 2 event lists, one for container arrivals and one for container departures
        departure_list = []
        arrival_list = [0]
        # List of all container groups in the yard blocks
        container_groups = []
        while self.time < self.SIMULATION_HOURS:  # Stop the simulation after the given period
            # Update the time based on the next event
            generated_container = self.generate_new_time(departure_list, arrival_list)

            if self.time == self.SIMULATION_HOURS:
                break
            # check if the current container groups need to leave (fifo)
            self.remove_expired_container_groups(container_groups)

            if generated_container:
                # new container group
                new_containergroup = self.generate_new_containergroup()

                # Add to closest yarblock
                self.add_cg_to_closest_yb(new_containergroup, container_groups, departure_list)
                add_to_Q(arrival_list, self.time + get_inter_arrival_time_sample())

    def generate_new_containergroup(self):
        container_flowtype = get_container_flow_type()
        container_type = get_container_type_sample()
        group_size = get_number_of_containers_sample()

        if container_flowtype == "import":
            arrival_point = get_arrival_or_departure_point_sample(self.data['BerthingPositions'])
            departure_point = get_arrival_or_departure_point_sample(self.data['TruckParkingLocations'])
            service_time = 48
        else:
            export_type = random.choices(["export", "transshipment"], weights=[31, 69], k=1)[0]
            if export_type == "export":
                arrival_point = get_arrival_or_departure_point_sample(self.data['TruckParkingLocations'])
                departure_point = get_arrival_or_departure_point_sample(self.data['BerthingPositions'])
                service_time = 48
            else:
                arrival_point = get_arrival_or_departure_point_sample(self.data['BerthingPositions'])
                departure_point = get_arrival_or_departure_point_sample(self.data['BerthingPositions'])
                service_time = get_service_time_sample()

        # Update statistics
        self.total_containers += group_size
        self.total_GC += 1
        return ContainerGroup(container_flowtype, container_type, group_size, self.time, service_time, arrival_point,
                              departure_point)

    def remove_expired_container_groups(self, container_groups):
        for container_group in container_groups:
            if self.time >= container_group.getFinishTime():
                block_dictionary = container_group.yard_blocks.copy()
                for block in block_dictionary:
                    self.remove_container_from_block(container_group, block)
                container_groups.remove(container_group)

    def add_cg_to_closest_yb(self, new_containergroup, container_groups, departure_list):
        closest_blocks = self.get_storage_blocks(new_containergroup)
        if closest_blocks is None:
            # No space for the container group
            self.rejected_groups += 1
            self.rejected_containers += new_containergroup.number_of_containers
            self.rejected_per_type[new_containergroup.container_type] += new_containergroup.number_of_containers
        else:
            if len(closest_blocks) > 1:
                self.total_split_ups += len(closest_blocks) - 1
            new_containergroup.temp_nr_of_containers_remaining = new_containergroup.number_of_containers
            for closest_block in closest_blocks:
                # Add the container group to the closest block
                self.add_container_to_block(new_containergroup, closest_block)
            container_groups.append(new_containergroup)  # container group served
            add_to_Q(departure_list, new_containergroup.getFinishTime())

    def get_storage_blocks(self, container_group):
        feasible_yardblocks = self.find_feasible_ybs(container_group)
        if len(feasible_yardblocks) == 0:
            return None

        if self.SPLIT_UP:
            containers_to_store = container_group.number_of_containers
            ybs_to_store = []
            while containers_to_store > 0:
                yb = self.get_closest_yb(container_group, feasible_yardblocks)[0]
                containers_to_store -= yb.getRemainingCapacity()
                feasible_yardblocks.remove(yb)
                ybs_to_store.append(yb)
                if len(feasible_yardblocks) == 0 and containers_to_store > 0:
                    return None
            return ybs_to_store

        if self.CLOSEST or self.MIXED_RULE:
            return self.get_closest_yb(container_group, feasible_yardblocks)

        if self.LOWEST_OCCUPANCY:
            return self.get_lowest_occupancy_yb(container_group, feasible_yardblocks)

    def get_closest_yb(self, container_group: ContainerGroup, feasible_yardblocks):
        closest_block = feasible_yardblocks[0]
        for block in feasible_yardblocks:
            if self.ARRIVAL_BASED and self.DEPARTURE_BASED:
                distance = block.position.calculate_distance(
                    container_group.arrival_point) + block.position.calculate_distance(container_group.departure_point)
            elif self.ARRIVAL_BASED:
                distance = block.position.calculate_distance(container_group.arrival_point)

            elif self.DEPARTURE_BASED:
                distance = block.position.calculate_distance(container_group.departure_point)

            if distance < closest_block.position.calculate_distance(container_group.arrival_point):
                closest_block = block

        return [closest_block]

    def get_lowest_occupancy_yb(self, container_group, feasible_yardblocks):
        possible_blocks = []
        smallest_yb = feasible_yardblocks[0]
        for block in feasible_yardblocks:
            if block.getRemainingCapacity() > smallest_yb.getRemainingCapacity():
                smallest_yb = block

        for block in feasible_yardblocks:
            if block.getRemainingCapacity() == smallest_yb.getRemainingCapacity():
                possible_blocks.append(block)

        return self.get_closest_yb(container_group, possible_blocks)

    def check_flow_type(self, container, block):
        if block.flow_type.lower() == "mix" and self.MIXED_RULE:
            if block.current_flow_type.lower() == "mix":
                return True
            elif container.container_flow_type.lower() == block.current_flow_type.lower():
                return True
            else:
                return False
        if block.flow_type.lower() == "mix":
            return True
        if container.container_flow_type.lower() == block.flow_type.lower():
            return True
        else:
            return False

    def find_feasible_ybs(self, container_group: ContainerGroup):
        possible_blocks = []

        for block in self.yard_blocks:
            if self.SPLIT_UP:
                if self.check_type(container_group, block) and block.hasSpace(1):
                    possible_blocks.append(block)
            else:
                if self.check_type(container_group, block) and block.hasSpace(
                        container_group.number_of_containers):
                    possible_blocks.append(block)

        return possible_blocks

    def check_type(self, group, block):
        container_type_check = check_container_type(group.container_type, block.container_type)
        container_flow_check = self.check_flow_type(group, block)
        return container_type_check and container_flow_check

    def add_container_to_block(self, container_group: ContainerGroup, block: YardBlock):
        self.total_travel_distance_containers += block.position.calculate_distance(container_group.arrival_point)
        # Store as many containers as possible in block
        if block.getRemainingCapacity() < container_group.temp_nr_of_containers_remaining:
            nr_containers_to_store = block.getRemainingCapacity()
            container_group.temp_nr_of_containers_remaining -= block.getRemainingCapacity()

        # Store all containers in a block
        else:
            nr_containers_to_store = container_group.temp_nr_of_containers_remaining
            container_group.temp_nr_of_containers_remaining = 0

        block.addContainers(nr_containers_to_store)

        # Update the flow type of the block with an empty block
        if self.MIXED_RULE and block.current_flow_type.lower() == "mix":
            block.current_flow_type = container_group.container_flow_type

        container_group.setYardBlock(block, nr_containers_to_store)
        block.update_daily_occupancy(self.day_counter)

    def remove_container_from_block(self, container_group: ContainerGroup, block: YardBlock):
        self.total_travel_distance_containers += block.position.calculate_distance(container_group.departure_point)
        block.removeContainers(container_group.getYardBlockContainers(block))
        block.update_daily_occupancy(self.day_counter)
        container_group.removeYardBlock(block)

        # Reset to mix if no containers are left in the block
        if self.MIXED_RULE:
            if block.flow_type.lower() == "mix" and block.amount_containers == 0:
                block.current_flow_type = "mix"

    def getAvgTravel_Containers(self):
        return self.total_travel_distance_containers / self.total_containers

    def getMaxOccupancy(self):
        max_occupation = []
        for block in self.yard_blocks:
            max_occupation.append(block.get_max_occupation())
        return max_occupation

    def getAvgOccupancy_individual(self):
        avg_occupancy_individual = []
        for block in self.yard_blocks:
            avg_occupancy_individual.append(block.get_avg_occupation())
        return avg_occupancy_individual

    def getDailyTotalOccupancy(self):
        avg_occupancy_individual = self.getAvgOccupancy_individual()
        return sum(avg_occupancy_individual) / len(avg_occupancy_individual)

    def update_time(self, new_time):
        if new_time >= self.SIMULATION_HOURS:
            new_time = self.SIMULATION_HOURS
        self.time = new_time
        old_time = self.time
        self.day_clock += self.time - old_time

        if self.day_clock >= 24:
            self.day_clock -= 24
            self.day_counter += 1
            for b in self.yard_blocks:
                b.update_daily_occupancy(self.day_counter)

    def generate_new_time(self, departure_list, arrival_list):
        # Returns True if a new container needs to be generated
        if not departure_list:
            self.update_time(arrival_list.pop(0))
            return True
        elif departure_list[0] < arrival_list[0]:
            self.update_time(departure_list.pop(0))
            return False
        elif departure_list[0] == arrival_list[0]:
            self.update_time(arrival_list.pop(0))
            departure_list.pop(0)
            return True
        else:
            self.update_time(arrival_list.pop(0))
            return True

    def setup_timers(self):
        self.day_clock = 0
        self.day_counter = 0
        # Simulation clock
        self.time = 0

    def setScenario(self, choice_str):
        if choice_str == "Closest (Base Scenario)":
            self.CLOSEST = True
            self.LOWEST_OCCUPANCY = False
            self.SPLIT_UP = False
            self.MIXED_RULE = False
        if choice_str == "Lowest Occupancy":
            self.CLOSEST = False
            self.LOWEST_OCCUPANCY = True
            self.SPLIT_UP = False
            self.MIXED_RULE = False
        if choice_str == "Possible Split Up":
            self.CLOSEST = False
            self.LOWEST_OCCUPANCY = False
            self.SPLIT_UP = True
            self.MIXED_RULE = False
        if choice_str == "Mixed Rule - Block can only contain 1 type":
            self.CLOSEST = False
            self.LOWEST_OCCUPANCY = False
            self.SPLIT_UP = False
            self.MIXED_RULE = True

    def setDistanceCalculationReference(self, choice_str):
        if choice_str == "Arrival Based":
            self.ARRIVAL_BASED = True
            self.DEPARTURE_BASED = False
        if choice_str == "Departure Based":
            self.ARRIVAL_BASED = False
            self.DEPARTURE_BASED = True
        if choice_str == "Arrival and Departure Based":
            self.ARRIVAL_BASED = True
            self.DEPARTURE_BASED = True

    def setSimulationHours(self, months, day, hours):
        self.SIMULATION_HOURS = int(months) * 30 * 24 + int(day) * 24 + int(hours)
        # print("Simulation hours: ", self.SIMULATION_HOURS)

    def only_one_scenario_true(self):
        counter = 0
        if self.CLOSEST:
            counter += 1
        if self.LOWEST_OCCUPANCY:
            counter += 1
        if self.SPLIT_UP:
            counter += 1
        if self.MIXED_RULE:
            counter += 1
        if counter == 0:
            raise Exception("No simulation scenario is true \n One simulation scenario must be true")
        if counter > 1:
            raise Exception("More than one simulation scenario is true \n Only one simulation scenario can be true")

    def print_status(self):
        self.check_parameters()
        print("Parameters: ")
        if self.CLOSEST:
            print("\tCLOSEST")
        if self.LOWEST_OCCUPANCY:
            print("\tLOWEST_OCCUPANCY")
        if self.SPLIT_UP:
            print("\tSPLIT_UP")
        if self.MIXED_RULE:
            print("\tMIXED_RULE")
        if self.ARRIVAL_BASED and self.DEPARTURE_BASED:
            print("\tARRIVAL_BASED and DEPARTURE_BASED combined")
        elif self.ARRIVAL_BASED:
            print("\tARRIVAL_BASED")
        elif self.DEPARTURE_BASED:
            print("\tDEPARTURE_BASED")

        print("Duration: " + str(self.SIMULATION_HOURS / (30 * 24)) + " months = " + str(
            self.SIMULATION_HOURS / 24) + " days = " + str(
            self.SIMULATION_HOURS) + " hours")
        print()

    def check_parameters(self):
        self.only_one_scenario_true()
        if not (self.ARRIVAL_BASED or self.DEPARTURE_BASED):
            raise Exception("At least one distance calculation reference can be true (arrival or departure based)")