class YardBlock:
    def __init__(self, name, container_type, flow_type, capacity, position):
        self.name = name
        self.container_type = container_type
        self.flow_type = flow_type
        self.capacity = capacity
        self.amount_containers = 0
        self.position = position

    def __str__(self):
        return f"Name: {self.name} | Container_type: {self.container_type} | Flow_type: {self.flow_type} | " \
               f"Capacity: {self.capacity} | Occupancy: {self.getOccupancy()} | Position: {self.position}"

    def removeContainers(self, number_of_containers):
        self.amount_containers -= number_of_containers

    def addContainers(self, number_of_containers):
        self.amount_containers += number_of_containers

    def getOccupancy(self):
        if self.capacity == 0:
            return 1
        return self.amount_containers / self.capacity

    def hasSpace(self, number_of_containers):
        return number_of_containers + self.amount_containers <= self.capacity