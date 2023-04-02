import numpy as np
from matplotlib import pyplot as plt

from ContainerGroup import ContainerGroup
from Position import Position
from YardBlock import YardBlock
import scipy.stats as scipyst
import random
import seaborn as sns


class Simulation:
    def __int__(self, data):
        self.data = data
        yard_block_list = data['YARDSTORAGEBLOCKS'].astype({'Capacity': 'int'}).values.tolist()
        self.yard_blocks = []
        for x in yard_block_list:
            self.yard_blocks.append(YardBlock(x[0], x[1], x[2], x[3], 0, Position(x[4], x[5])))

    def simulate(self):
        period = 1
        period_in_hours = period * 24 * 30
        self.fifo(period_in_hours, self.data)

    def fifo(self, period_in_hours, data):
        time = 0  # Simulation clock
        container_groups = []  # List of all container groups in the yard block
        while time < period_in_hours:  # Stop the simulation after the given period
            # Todo: find better sampling distributions (current ones are representative but probably not the best)
            time += self.get_inter_arrival_time_sample()
            # new container group
            new_containergroup = self.generate_new_containergroup(time, data['BerthingPositions'])

            # Add to closest yarblock
            closest_block = self.get_closest_feasible_yardblock(new_containergroup)
            if closest_block is None:
                print(f'Rejected containergroup ({new_containergroup.__str__()})')
            else:
                self.add_container_to_block(new_containergroup, closest_block)
                container_groups.append(new_containergroup)  # container group served

            # check if the current container groups need to leave (fifo)
            for containter_group in container_groups:
                if time > containter_group.service_time:
                    self.remove_container_from_block(containter_group, containter_group.yard_block)
                    container_groups.remove(containter_group)
                else:
                    break

    def generate_new_containergroup(self, arrival_time, berthingPositions):
        container_type = self.get_container_type_sample()
        group_size = self.get_number_of_containers_sample()
        service_time = self.get_service_time_sample()
        arrival_point = self.get_arrival_or_departure_point_sample(berthingPositions)
        departure_point = self.get_arrival_or_departure_point_sample(berthingPositions)

        return ContainerGroup(container_type, group_size, arrival_time, service_time, arrival_point, departure_point)

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
            if self.check_type(container_group.container_type, block.container_type) and (block.capacity - block.occupation) > container_group.number_of_containers:
                possible_blocks.append(block)

        return possible_blocks

    def check_type(self, group_type, block_type):
        if group_type.lower() == block_type.lower():
            return True
        if group_type == 'normal' and block_type == 'FULL':
            return True
        else:
            return False
    def add_container_to_block(self, container_group: ContainerGroup, block: YardBlock):
        block.occupation += container_group.number_of_containers
        container_group.yard_block = block

    def remove_container_from_block(self, container_group: ContainerGroup, block: YardBlock):
        block.occupation -= container_group.number_of_containers
        container_group.yard_block = None

    def get_inter_arrival_time_sample(self):
        return round(scipyst.expon.rvs(scale=3, loc=0))

    def get_container_type_sample(self):
        return random.choices(["normal", "reefer"], weights=[69, 31], k=1)[0]

    def get_service_time_sample(self):
        return round(random.uniform(0, 166))

    def get_arrival_or_departure_point_sample(self, data):
        row = data.sample()
        return Position(row['X_coord'].values[0], row['Y_coord'].values[0])

    def get_number_of_containers_sample(self):
        return round(scipyst.expon.rvs(scale=5, loc=0.5))
