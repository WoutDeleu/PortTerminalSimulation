import random

import pandas as pd
import scipy.stats as scipyst

from ContainerGroup import ContainerGroup
from Position import Position
from YardBlock import YardBlock

SIMULATION_MONTHS = 12
SIMULATION_HOURS = SIMULATION_MONTHS * 24 * 30


def get_inter_arrival_time_sample():
    return round(scipyst.expon.rvs(scale=3, loc=0))


def get_number_of_containers_sample():
    return round(scipyst.expon.rvs(scale=5, loc=0.5))


def get_service_time_sample():
    return round(random.uniform(0, 166))


def get_container_type_sample():
    return random.choices(["normal", "reefer"], weights=[69, 31], k=1)[0]


def get_arrival_or_departure_point_sample(df):
    row = df.sample()
    return Position(row['X_coord'].values[0], row['Y_coord'].values[0])


def check_type(group_type, block_type):
    if group_type.lower() == block_type.lower():
        return True
    if group_type == 'normal' and block_type == 'FULL':
        return True
    if block_type == 'MIX':
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

    def fifo(self):
        # Variables to get daily statistics
        self.day_clock = 0
        self.day_counter = 0
        self.time = 0  # Simulation clock
        # List of all container groups in the yard block
        container_groups = []
        while self.time < SIMULATION_HOURS:  # Stop the simulation after the given period
            self.update_time()
            # new container group
            new_containergroup = self.generate_new_containergroup()
            # Update statistics
            self.total_containers += new_containergroup.number_of_containers
            self.total_GC += 1

            # Add to closest yarblock
            closest_block = self.get_closest_feasible_yardblock(new_containergroup)
            if closest_block is None:
                self.rejected_groups += 1
                self.rejected_contianers += new_containergroup.number_of_containers
                self.rejected_per_type[new_containergroup.container_type] += new_containergroup.number_of_containers
                print(f'Rejected containergroup ({str(new_containergroup)})')
            else:
                self.add_container_to_block(new_containergroup, closest_block)
                container_groups.append(new_containergroup)  # container group served

            # check if the current container groups need to leave (fifo)
            for container_group in container_groups:
                if self.time > container_group.getFinishTime():
                    block = container_group.yard_block
                    self.remove_container_from_block(container_group, block)
                    container_groups.remove(container_group)
                else:
                    break

    def generate_new_containergroup(self):
        container_type = get_container_type_sample()
        group_size = get_number_of_containers_sample()
        service_time = get_service_time_sample()
        arrival_point = get_arrival_or_departure_point_sample(self.data['BerthingPositions'])
        departure_point = get_arrival_or_departure_point_sample(self.data['BerthingPositions'])

        return ContainerGroup(container_type, group_size, self.time, service_time, arrival_point, departure_point)

    def get_closest_feasible_yardblock(self, container_group: ContainerGroup):
        feasible_yardblocks = self.find_feasible_yarblocks(container_group)
        if len(feasible_yardblocks) == 0:
            return None

        closest_block = feasible_yardblocks[0]
        for block in feasible_yardblocks:
            distance = block.position.calculate_distance(container_group.arrival_point)
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

    def update_time(self):
        # Todo: find better sampling distributions (current ones are representative but probably not the best)
        old_time = self.time
        self.time += get_inter_arrival_time_sample()
        self.day_clock += self.time - old_time

        if self.day_clock >= 24:
            self.day_clock -= 24
            self.day_counter += 1
            for b in self.yard_blocks:
                b.update_daily_occupancy(self.day_counter)