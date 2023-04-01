class YardBlock:
    def __init__(self, name, container_type, flow_type, capacity, occupation, position):
        self.name = name
        self.container_type = container_type
        self.flow_type = flow_type
        self.capacity = capacity
        self.occupation = occupation
        self.position = position

    def __str__(self):
        return f"Name: {self.name} | Container_type: {self.container_type} | Flow_type: {self.flow_type} | " \
               f"Capacity: {self.capacity} | Occupation: {self.occupation} | Position: {self.position}"

