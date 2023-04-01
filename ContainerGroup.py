class ContainerGroup:
    def __init__(self, type, number_of_containers, arrival_time, service_time, arrival_point, departure_point):
        self.type = type
        self.number_of_containers = number_of_containers
        self.arrival_time = arrival_time
        self.service_time = service_time
        self.arrival_point = arrival_point
        self.departure_point = departure_point

    def __str__(self):
        return f"{self.type}: {self.number_of_containers}, {self.arrival_time}, {self.service_time}, {self.arrival_point}, {self.departure_point}"
