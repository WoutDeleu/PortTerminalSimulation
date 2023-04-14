class ContainerGroup:
    def __init__(self, container_flowtype, container_type, number_of_containers, arrival_time, service_time, arrival_point,
                 departure_point):
        self.yard_block = None
        self.container_flowtype = container_flowtype
        self.container_type = container_type
        self.number_of_containers = number_of_containers
        self.arrival_time = arrival_time
        self.service_time = service_time
        self.arrival_point = arrival_point
        self.departure_point = departure_point

    def set_yard_storage_block(self, yard_block):
        self.yard_block = yard_block

    def __str__(self):
        return f"Flowtype: {self.container_flowtype} | Type: {self.container_type} | Number_of_containers: "\
               f"{self.number_of_containers} | Arrival_time: {self.arrival_time} | Service_time: {self.service_time} |"\
               f" Arrival_point: {self.arrival_point} | Departure_point: {self.departure_point}"

    def getFinishTime(self):
        return self.arrival_time + self.service_time