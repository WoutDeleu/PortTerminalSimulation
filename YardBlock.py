class YardBlock:
    def __init__(self, name, container_type, flow_type, capacity, occupation, position):
        self.name = name
        self.container_type = container_type
        self.flow_type = flow_type
        self.capacity = capacity
        self.occupation = occupation
        self.position = position

    def __str__(self):
        return f"{self.name}: {self.container_type}, {self.flow_type}, {self.capacity}, {self.occupation}, {self.position}"

