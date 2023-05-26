class YardBlock:
    def __init__(self, name, container_type, flow_type, capacity, position):
        self.name = name
        self.container_type = container_type
        self.flow_type = flow_type
        self.current_flow_type = flow_type
        self.capacity = capacity
        self.amount_containers = 0
        self.position = position
        self.max_daily_occupancy = [0]

    def __str__(self):
        return f"Name: {self.name} | Container_type: {self.container_type} | Flow_type: {self.flow_type} | " \
               f"Capacity: {self.capacity} | Occupancy: {self.getOccupancy()} | Position: {self.position}"

    def removeContainers(self, number_of_containers):
        self.amount_containers -= number_of_containers

    def addContainers(self, number_of_containers):
        self.amount_containers += number_of_containers
        assert self.amount_containers <= self.capacity, "YB is overfull!!!"

    def getOccupancy(self):
        if self.capacity == 0:
            return 1
        return self.amount_containers / self.capacity

    def getRemainingCapacity(self):
        return self.capacity - self.amount_containers

    def update_daily_occupancy(self, day_counter):
        # Check if there is already an entry for the current day
        if day_counter < len(self.max_daily_occupancy):
            # If there is an entry for the current day, check if the current occupancy is higher than the current entry
            if self.getOccupancy() > self.max_daily_occupancy[day_counter]:
                # If it is greater, update the value
                self.max_daily_occupancy[day_counter] = self.getOccupancy()
        else:
            # If there is no entry for that day, the occupancy needs to be updated
            self.max_daily_occupancy.append(self.getOccupancy())

    def hasSpace(self, number_of_containers):
        return number_of_containers + self.amount_containers <= self.capacity

    def get_max_occupation(self):
        return max(self.max_daily_occupancy)

    def get_avg_occupation(self):
        return sum(self.max_daily_occupancy) / len(self.max_daily_occupancy)