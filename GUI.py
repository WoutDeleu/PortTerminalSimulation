import math
import tkinter
import tkinter as tk

from Data.DataParser import load_data
from Parameters import SIMULATION_HOURS
from Simulation import Simulation, add_to_Q, get_inter_arrival_time_sample

ROWS = 10
COLS = 16

YB_WIDTH = 40
YB_HEIGHT = 15

TOLERANCE = 10
# width = COLS * (YB_WIDTH + TOLERANCE)
# height = ROWS * (YB_HEIGHT + TOLERANCE)
width = 1000
height = 500
refresh_sec = 0.01


def init_simulation():
    data = load_data('./Data/')
    sim = Simulation(data)
    return sim


def draw_yb(sim, canvas):
    blocks = []
    # [(min_x, min_y), (max_x, max_y)]
    normalisation = normalise_positions(sim.yard_blocks)
    min_x = normalisation[0][0]
    max_x = normalisation[1][0]

    for i in range(len(sim.yard_blocks)):
        block = sim.yard_blocks[i]
        row = math.floor(i / COLS)
        col = i - row * 16

        start_pos_x = (block.position.x_cord - min_x) / (max_x / width) + TOLERANCE
        start_pos_y = (block.position.y_cord - normalisation[0][1]) / (normalisation[1][1] / height) + TOLERANCE

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
    smallest_x = float('inf')
    smallest_y = float('inf')
    largest_x = 0
    largest_y = 0

    for block in yard_blocks:
        smallest_x = min(smallest_x, block.position.x_cord)
        smallest_y = min(smallest_y, block.position.y_cord)
        largest_x = max(largest_x, block.position.x_cord)
        largest_y = max(largest_y, block.position.y_cord)

    return [(smallest_x, smallest_y), (largest_x, largest_y)]


def update_ybs(gui, canvas, gui_blocks, yard_blocks):
    for i in range(len(yard_blocks)):
        yb_ocupancy = yard_blocks[i].getOccupancy()
        fill = "#%02x%02x%02x" % (math.floor(255 * yb_ocupancy), math.floor(255 - 255 * yb_ocupancy), 0)
        canvas.itemconfig(gui_blocks[i], fill=fill)
    gui.update()


def init_gui():
    gui = tk.Tk()
    # gui.geometry(f"{width + 400}x{height + 500}")

    return gui


def run_simulation(sim, gui, canvas):
    # sets day_clock, day_counter and time to 0
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
    # canvas = tk.Canvas(gui, width=width + 400, height=height)
    canvas = tk.Canvas(gui, width=width, height=height)
    sim = init_simulation()
    run_simulation(sim, gui, canvas)
    gui.mainloop()  # Update tinker


startGUI()
