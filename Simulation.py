import random

import pandas as pd
import scipy.stats as scipyst

from ContainerGroup import ContainerGroup
from Position import Position
from YardBlock import YardBlock


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


def generate_new_containergroup(arrival_time, berthingPositions):
    container_type = get_container_type_sample()
    group_size = get_number_of_containers_sample()
    service_time = get_service_time_sample()
    arrival_point = get_arrival_or_departure_point_sample(berthingPositions)
    departure_point = get_arrival_or_departure_point_sample(berthingPositions)

    return ContainerGroup(container_type, group_size, arrival_time, service_time, arrival_point, departure_point)


class Simulation:
    def __init__(self, data):
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

    def simulate_fifo(self):
        period_months = 12
        period_in_hours = period_months * 24 * 30
        self.fifo(period_in_hours, self.data)

    def fifo(self, period_in_hours, data):
        # Variables to get daily statistics
        day_clock = 0

        time = 0  # Simulation clock
        # List of all container groups in the yard block
        container_groups = []
        while time < period_in_hours:  # Stop the simulation after the given period
            # Todo: find better sampling distributions (current ones are representative but probably not the best)
            time += get_inter_arrival_time_sample()
            day_clock += get_inter_arrival_time_sample()
            # new container group
            new_containergroup = generate_new_containergroup(time, data['BerthingPositions'])
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
                if time > container_group.getFinishTime():
                    self.remove_container_from_block(container_group, container_group.yard_block)
                    container_groups.remove(container_group)
                else:
                    break

        if day_clock >= 24:
            day_clock -= 24
            self.average_daily_occupancy_per_YB = self.average_daily_occupancy_per_YB / day_clock
            self.average_daily_occupancy_total = self.average_daily_occupancy_total / day_clock

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
        container_group.yard_block = block

    def remove_container_from_block(self, container_group: ContainerGroup, block: YardBlock):
        self.total_travel_distance_containers += block.position.calculate_distance(container_group.departure_point)
        block.removeContainers(container_group.number_of_containers)
        container_group.yard_block = None

    def getAvgTravel_Containers(self):
        return self.total_travel_distance_containers / self.total_containers

    def getMaxOccupancy(self):
        max_occupation = 0
        for block in self.yard_blocks:
            if block.getOccupancy() > max_occupation:
                max_occupation = block.getOccupancy()
        return max_occupation

    def getAvgOccupancy_individual(self):
        # todo - methode hiervoor
        return 0

    def getDailyTotalOccupancy(self):
        # todo
        return 0