import random

import pandas as pd
import scipy.stats as scipyst

from ContainerGroup import ContainerGroup
from Parameters import SIMULATION_HOURS, ARRIVAL_BASED, DEPARTURE_BASED, CLOSEST, LOWEST_OCCUPANCY, SPLIT_UP, MIXED_RULE
from Position import Position
from YardBlock import YardBlock


def simulate(stats, data):
    sim = Simulation(data)
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
         ])
    return stats_fifo


def get_inter_arrival_time_sample():
    return round(scipyst.expon.rvs(scale=3, loc=0))


def get_number_of_containers_sample():
    scale = 52
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
    return random.choices(["import", "export"], weights=[25, 75], k=1)[0]
    # Transshipment's fall under export (say 50% of cargo groups are transshipment's)


def check_type(group, block):
    container_type_check = check_container_type(group.container_type, block.container_type)
    container_flow_check = check_flow_type(group, block)
    return container_type_check and container_flow_check


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


def get_closest_yb(container_group: ContainerGroup, feasible_yardblocks):
    closest_block = feasible_yardblocks[0]
    for block in feasible_yardblocks:
        if ARRIVAL_BASED and DEPARTURE_BASED:
            distance = block.position.calculate_distance(
                container_group.arrival_point) + block.position.calculate_distance(container_group.departure_point)
        elif ARRIVAL_BASED:
            distance = block.position.calculate_distance(container_group.arrival_point)

        elif DEPARTURE_BASED:
            distance = block.position.calculate_distance(container_group.departure_point)

        if distance < closest_block.position.calculate_distance(container_group.arrival_point):
            closest_block = block

    return [closest_block]


def get_lowest_occupancy_yb(container_group, feasible_yardblocks):
    possible_blocks = []
    smallest_yb = feasible_yardblocks[0]
    for block in feasible_yardblocks:
        if block.getRemainingCapacity() < smallest_yb.getRemainingCapacity():
            smallest_yb = block

    for block in feasible_yardblocks:
        if block.getRemainingCapacity() == smallest_yb.getRemainingCapacity():
            possible_blocks.append(block)

    return get_closest_yb(container_group, possible_blocks)


def check_flow_type(container, block):
    if block.flow_type.lower() == "mix" and MIXED_RULE:
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


class Simulation:
    def __init__(self, data):
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

    def run(self):
        # Variables to get daily statistics
        self.setup_timers()

        # 2 event lists, one for container arrivals and one for container departures
        departure_list = []
        arrival_list = [0]
        # List of all container groups in the yard blocks
        container_groups = []
        while self.time < SIMULATION_HOURS:  # Stop the simulation after the given period
            # Update the time based on the next event
            generated_container = self.generate_new_time(departure_list, arrival_list)

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
            export_type = random.choices(["export", "transshipment"], weights=[25, 50], k=1)[0]
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

        if SPLIT_UP:
            containers_to_store = container_group.number_of_containers
            ybs_to_store = []
            while containers_to_store > 0:
                yb = get_closest_yb(container_group, feasible_yardblocks)[0]
                containers_to_store -= yb.getRemainingCapacity()
                feasible_yardblocks.remove(yb)
                ybs_to_store.append(yb)
            return ybs_to_store

        if CLOSEST or MIXED_RULE:
            return get_closest_yb(container_group, feasible_yardblocks)

        if LOWEST_OCCUPANCY:
            return get_lowest_occupancy_yb(container_group, feasible_yardblocks)

    def find_feasible_ybs(self, container_group: ContainerGroup):
        possible_blocks = []

        for block in self.yard_blocks:
            if SPLIT_UP:
                if check_type(container_group, block) and block.hasSpace(1):
                    possible_blocks.append(block)
            else:
                if check_type(container_group, block) and block.hasSpace(
                        container_group.number_of_containers):
                    possible_blocks.append(block)

        return possible_blocks

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
        if MIXED_RULE and block.current_flow_type.lower() == "mix":
            block.current_flow_type = container_group.container_flow_type

        container_group.setYardBlock(block, nr_containers_to_store)
        block.update_daily_occupancy(self.day_counter)

    def remove_container_from_block(self, container_group: ContainerGroup, block: YardBlock):
        self.total_travel_distance_containers += block.position.calculate_distance(container_group.departure_point)
        block.removeContainers(container_group.getYardBlockContainers(block))
        block.update_daily_occupancy(self.day_counter)
        container_group.removeYardBlock(block)

        # Reset to mix if no containers are left in the block
        if MIXED_RULE:
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
