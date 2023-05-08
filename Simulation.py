import random

import pandas as pd
import scipy.stats as scipyst

from ContainerGroup import ContainerGroup
from Parameters import SIMULATION_HOURS, ARRIVAL_BASED, DEPARTURE_BASED, FIFO_BASIC, LOWEST_OCCUPANCY
from Position import Position
from YardBlock import YardBlock


def simulate(stats, data):
    sim = Simulation(data)
    sim.run()
    stats_fifo = pd.concat(
        [stats,
         pd.DataFrame([{'Containers_Rejected': sim.rejected_containers, 'CG_Rejected': sim.rejected_groups,
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
    sample = scipyst.weibull_min.rvs(0.6, loc = 0.5/scale)*scale
    while sample>max:
        sample = scipyst.weibull_min.rvs(0.6, loc = 0.5/scale)*scale
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


def check_type(group_type, block_type):
    if group_type.lower() == block_type.lower():
        return True
    if group_type == 'normal' and block_type == 'FULL':
        return True
    if block_type == 'MIX':
        return True
    else:
        return False


def add_to_Q(event_list, time):
    if time not in event_list:
        event_list.append(time)
        event_list.sort()
    return event_list


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
            generate_container = self.generate_new_time(departure_list, arrival_list)
            # check if the current container groups need to leave (fifo)
            for container_group in container_groups:
                if self.time >= container_group.getFinishTime():
                    block = container_group.yard_block
                    self.remove_container_from_block(container_group, block)
                    container_groups.remove(container_group)

            if generate_container:
                # new container group
                new_containergroup = self.generate_new_containergroup()

                # Update statistics
                self.total_containers += new_containergroup.number_of_containers
                self.total_GC += 1

                # Add to closest yarblock
                closest_block = self.get_storage_block(new_containergroup)
                if closest_block is None:
                    # No space for the container group
                    self.rejected_groups += 1
                    self.rejected_containers += new_containergroup.number_of_containers
                    self.rejected_per_type[new_containergroup.container_type] += new_containergroup.number_of_containers
                else:
                    # Add the container group to the closest block
                    self.add_container_to_block(new_containergroup, closest_block)
                    container_groups.append(new_containergroup)  # container group served
                    add_to_Q(departure_list, new_containergroup.getFinishTime())
                arrival_list = add_to_Q(arrival_list, self.time + get_inter_arrival_time_sample())

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

        return ContainerGroup(container_flowtype, container_type, group_size, self.time, service_time, arrival_point,
                              departure_point)

    def get_storage_block(self, container_group):
        feasible_yardblocks = self.find_feasible_yarblocks(container_group)
        if len(feasible_yardblocks) == 0:
            return None
        if FIFO_BASIC:
            return self.get_closest_yb(container_group, feasible_yardblocks)
        if LOWEST_OCCUPANCY:
            return self.get_lowest_occupancy_yb(container_group, feasible_yardblocks)

    def get_lowest_occupancy_yb(self, container_group, feasible_yardblocks):
        possible_blocks = []
        smallest_yb = feasible_yardblocks[0]
        for block in feasible_yardblocks:
            if block.getRemainingCapacity() < smallest_yb.getRemainingCapacity():
                smallest_yb = block

        for block in feasible_yardblocks:
            if block.getRemainingCapacity() == smallest_yb.getRemainingCapacity():
                possible_blocks.append(block)

        return self.get_closest_yb(container_group, possible_blocks)

    def get_closest_yb(self, container_group: ContainerGroup, feasible_yardblocks):
        closest_block = feasible_yardblocks[0]
        for block in feasible_yardblocks:
            if ARRIVAL_BASED:
                distance = block.position.calculate_distance(container_group.arrival_point)
            if DEPARTURE_BASED:
                distance = block.position.calculate_distance(container_group.departure_point)
            if distance < closest_block.position.calculate_distance(container_group.arrival_point):
                closest_block = block

        return closest_block

    def find_feasible_yarblocks(self, container_group: ContainerGroup):
        possible_blocks = []
        for block in self.yard_blocks:
            if check_type(container_group.container_type, block.container_type) and block.hasSpace(
                    container_group.number_of_containers):
                possible_blocks.append(block)

        return possible_blocks

    def add_container_to_block(self, container_group: ContainerGroup, block: YardBlock):
        self.total_travel_distance_containers += block.position.calculate_distance(container_group.arrival_point)
        block.addContainers(container_group.number_of_containers)
        block.update_daily_occupancy(self.day_counter)
        container_group.yard_block = block

    def remove_container_from_block(self, container_group: ContainerGroup, block: YardBlock):
        self.total_travel_distance_containers += block.position.calculate_distance(container_group.departure_point)
        block.removeContainers(container_group.number_of_containers)
        block.update_daily_occupancy(self.day_counter)
        container_group.yard_block = None

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