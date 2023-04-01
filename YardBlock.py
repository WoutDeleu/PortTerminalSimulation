class YardBlock:
    def __init__(self, name, container_type, flow_type, capacity, occupation, x_cord, y_cord):
        self.name = name
        self.container_type = container_type
        self.flow_type = flow_type
        self.capacity = capacity
        self.occupation = occupation
        self.x_cord = x_cord
        self.y_cord = y_cord

    def __str__(self):
        return f"{self.name}: {self.container_type}, {self.flow_type}, {self.capacity}, {self.occupation}, {self.x_cord}, {self.y_cord}"

