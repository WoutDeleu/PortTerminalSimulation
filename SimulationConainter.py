class SimulationContainer:
    def __init__(self, begin, end, container_group):
        self.begin_point = begin
        self.end_point = end
        self.container_group = container_group
        self.frame = 0
        self.current_position = begin

    def add_component(self, component):
        self.component = component
    def move_container(self):
        pass