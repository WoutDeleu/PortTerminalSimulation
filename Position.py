class Position:
    def __init__(self, x_cord, y_cord):
        self.x_cord = float(x_cord)
        self.y_cord = float(y_cord)

    def calculate_distance(self, other_position):
        return abs(self.x_cord - other_position.x_cord) + abs(self.y_cord - other_position.y_cord)

    def __str__(self):
        return f"X: {self.x_cord} | Y: {self.y_cord}"

