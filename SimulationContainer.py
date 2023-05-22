import math
import time

from Position import Position


class SimulationContainer:
    def __init__(self, canvas, gui, begin, end, speed_scale, container_group, min_x, max_x, min_y, max_y, border_space):
        self.begin_point = begin
        self.end_point = end
        self.container_group = container_group

        self.border_space = border_space
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.speed_scale = speed_scale

        self.container_size = 10 * (container_group.number_of_containers/2500) + 10
        self.frame = 0
        self.canvas = canvas
        self.gui = gui

        x = self.transpose_x(self.begin_point.x_cord)
        y = self.transpose_y(self.begin_point.y_cord)
        self.current_position = Position(x, y)


    def create_component(self):
        x = self.transpose_x(self.begin_point.x_cord)
        y = self.transpose_y(self.begin_point.y_cord)
        fill = '#00FF00' if self.container_group.container_flow_type == 'export' else '#FFFF00' if self.container_group.container_flow_type == 'import' else '#ADD8E6'
        border = 'orange' if self.container_group.container_type == "reefer" else 'blue'
        return self.canvas.create_rectangle(x, y, x + self.container_size, y + self.container_size, fill=fill, outline=border)

    def calculate_step(self):
        target_x = self.transpose_x(self.end_point.x_cord)
        target_y = self.transpose_y(self.end_point.y_cord)
        x = self.transpose_x(self.begin_point.x_cord)
        y = self.transpose_y(self.begin_point.y_cord)

        distance_x = target_x - x
        distance_y = target_y - y

        max_distance = max(abs(distance_y), abs(distance_x))
        step = 1.5 + (1 - self.speed_scale/100) * 6
        frames = math.ceil(max_distance / step)

        step_x = distance_x / frames
        step_y = distance_y / frames
        #print(f"x={step_x}, y={step_y}")

        return step_x, step_y, frames

    def move(self, vessel):
        self.component = self.create_component()
        step_x, step_y, total_frames = self.calculate_step()
        move = True
        self.canvas.itemconfig(vessel, state='normal')
        while move:
            move = self.move_container(step_x, step_y, total_frames)
            time.sleep(0.01)
        self.canvas.itemconfig(vessel, state='hidden')
        self.gui.update()

    def move_container(self, step_x, step_y, total_frames):
        if self.frame >= total_frames:
            self.canvas.delete(self.component)
            return False

        self.frame += 1

        x = self.current_position.x_cord + step_x
        y = self.current_position.y_cord + step_y
        self.current_position = Position(x, y)

        self.canvas.coords(self.component, x, y, x + self.container_size, y + self.container_size)
        return True


    def transpose_x(self, x):
        return (x - self.min_x) / (self.max_x - self.min_x) * (self.canvas.winfo_width() - 2 * self.border_space) + self.border_space
    def transpose_y(self, y):
        return y / self.max_y * (self.canvas.winfo_height() - 2 * self.border_space) + self.border_space - self.min_y

