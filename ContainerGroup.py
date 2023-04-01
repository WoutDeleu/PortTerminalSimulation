class ContainerGroup:
    def __init__(self, container_type, number_of_containers, arrival_time, service_time, arrival_point, departure_point):
        self.yard_block = None
        self.container_type = container_type
        self.number_of_containers = number_of_containers
        self.arrival_time = arrival_time
        self.service_time = service_time
        self.arrival_point = arrival_point
        self.departure_point = departure_point

    def add_yard_storage_block(self, yard_block):
        self.yard_block = yard_block

    def __str__(self):
        return f"{self.container_type}: {self.number_of_containers}, {self.arrival_time}, {self.service_time}, {self.arrival_point}, {self.departure_point}"
