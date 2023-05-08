import math
import tkinter
import tkinter as tk

from Data.DataParser import load_data
from Parameters import SIMULATION_HOURS
from Simulation import Simulation, add_to_Q, get_inter_arrival_time_sample

ROWS = 10
COLS = 16

YB_WIDTH = 80
YB_HEIGHT = 40

TOLERANCE = 20
width = COLS * (YB_WIDTH + TOLERANCE) + 200
height = ROWS * (YB_HEIGHT + TOLERANCE) + 500
refresh_sec = 0.01


def init_simulation():
    data = load_data('./Data/')
    sim = Simulation(data)
    return sim


def draw_yb(sim, canvas):
    blocks = []
    normalisation = normalise_positions(sim.yard_blocks)
    for i in range(len(sim.yard_blocks)):
        row = math.floor(i / COLS)
        col = i - row * 16
        start_pos_y = row * (YB_HEIGHT + TOLERANCE) + TOLERANCE
        start_pos_x = col * (YB_WIDTH + TOLERANCE) + (200 / 2)

        yb_ocupancy = sim.yard_blocks[i].getOccupancy()
        fill = "#%02x%02x%02x" % (math.floor(255 * yb_ocupancy), math.floor(255 - 255 * yb_ocupancy), 0)
        border = 'orange' if sim.yard_blocks[i].container_type == "REEFER" else 'blue'
        rectangle = canvas.create_rectangle(start_pos_x,
                                            start_pos_y,
                                            start_pos_x + YB_WIDTH,
                                            start_pos_y + YB_HEIGHT,
                                            fill=fill,
                                            outline=border)
        blocks.append(rectangle)

    canvas.pack()

    return blocks


def normalise_positions(yard_blocks):
    smallest_x = 0
    smallest_y = 0

    largest_x = 0
    largest_y = 0

    for block in yard_blocks:
        if block.position.x_cord < smallest_x:
            smallest_x = block.position.x_cord
        elif block.position.x_cord  > largest_x:
            largest_x = block.position.x_cord

        if block.position.y_cord < smallest_y:
            smallest_y = block.position.y_cord
        elif block.position.y_cord > largest_y:
            largest_y = block.position.y_cord

    return [(smallest_x, smallest_y), (largest_x, largest_y)]


def update_ybs(gui, canvas, gui_blocks, yard_blocks):
    for i in range(len(yard_blocks)):
        yb_ocupancy = yard_blocks[i].getOccupancy()
        fill = "#%02x%02x%02x" % (math.floor(255 * yb_ocupancy), math.floor(255 - 255 * yb_ocupancy), 0)
        canvas.itemconfig(gui_blocks[i], fill=fill)
    gui.update()


def init_gui():
    gui = tk.Tk()
    gui.geometry(f"{width}x{height}")

    return gui


def run_simulation(sim, gui, canvas):
    sim.setup_timers()
    departure_list = []
    arrival_list = [0]

    blocks = draw_yb(sim, canvas)
    container_groups = []
    while sim.time < SIMULATION_HOURS:
        has_generated = sim.generate_new_time(departure_list, arrival_list)

        # check what containergroups get removed to show
        sim.remove_expired_container_groups(container_groups)

        if has_generated:
            # show the new cg ariving
            new_cg = sim.generate_new_containergroup()

            # show yb added
            sim.add_cg_to_closest_yb(new_cg, container_groups, departure_list)
            add_to_Q(arrival_list, sim.time + get_inter_arrival_time_sample())
            # update yb visualisation
            update_ybs(gui, canvas, blocks, sim.yard_blocks)


def startGUI():
    gui = init_gui()
    canvas = tk.Canvas(gui, width=width, height=height)
    sim = init_simulation()
    run_simulation(sim, gui, canvas)
    gui.mainloop()


startGUI()
