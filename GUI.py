import math
import tkinter
import tkinter as tk

from Data.DataParser import load_data
from Parameters import SIMULATION_HOURS
from Simulation import Simulation, add_to_Q, get_inter_arrival_time_sample

refresh_sec = 0.01

def init_simulation():
    data = load_data('./Data/')
    sim = Simulation(data)
    return sim


def draw(sim, canvas):
    blocks = []
    # [(min_x, min_y), (max_x, max_y)]
    normalisation = normalise_positions(sim.yard_blocks, sim.berthing_positions, sim.truck_parking_locations)
    min_x = normalisation[0][0]
    max_x = normalisation[1][0]
    min_y = normalisation[0][1]
    max_y = normalisation[1][1]

    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()
    border_space = 10

    for block in sim.yard_blocks:
        start_pos_x = (block.position.x_cord - min_x) / (max_x - min_x) * (canvas_width - 2 * border_space) + border_space
        # Not fully stretch to leave some room for parameters
        start_pos_y = block.position.y_cord / max_y * (canvas_height - 2 * border_space) + border_space - min_y

        yb_width = block.capacity / 1000 * 30
        yb_height = block.capacity / 1000 * 110
        yb_ocupancy = block.getOccupancy()
        fill = "#%02x%02x%02x" % (math.floor(255 * yb_ocupancy), math.floor(255 - 255 * yb_ocupancy), 0)
        border = 'orange' if block.container_type == "REEFER" else 'blue'
        rectangle = canvas.create_rectangle(start_pos_x,
                                            start_pos_y,
                                            start_pos_x + yb_width,
                                            start_pos_y + yb_height,
                                            fill=fill,
                                            outline=border)
        blocks.append(rectangle)

    # Todo: enkel laten zien wanneer vessel aanwezig is
    for berth_location in sim.berthing_positions:
        start_pos_x = (berth_location.x_cord - min_x) / (max_x - min_x) * (canvas_width - 2 * border_space) + border_space
        # Not fully stretch to leave some room for parameters
        start_pos_y = berth_location.y_cord / max_y * (canvas_height - 2 * border_space) + border_space - min_y

        canvas.create_rectangle(start_pos_x,
                                start_pos_y,
                                start_pos_x + 50,
                                start_pos_y + 10,
                                fill="#0000FF",
                                outline='black')

    for truck_location in sim.truck_parking_locations:
        start_pos_x = (truck_location.x_cord - min_x) / (max_x - min_x) * (canvas_width - 2 * border_space) + border_space
        # Not fully stretch to leave some room for parameters
        start_pos_y = truck_location.y_cord / max_y * (canvas_height - 2 * border_space) + border_space - min_y

        canvas.create_rectangle(start_pos_x,
                                start_pos_y,
                                start_pos_x + 20,
                                start_pos_y + 10,
                                fill="#8B4513",
                                outline='black')

    canvas.pack()

    return blocks


def normalise_positions(yard_blocks, berthing_locations, truck_parking_locations):
    smallest_x = float('inf')
    smallest_y = float('inf')
    largest_x = 0
    largest_y = 0

    for block in yard_blocks:
        smallest_x = min(smallest_x, block.position.x_cord)
        smallest_y = min(smallest_y, block.position.y_cord)
        largest_x = max(largest_x, block.position.x_cord)
        largest_y = max(largest_y, block.position.y_cord)

    for berthing_location in berthing_locations:
        smallest_x = min(smallest_x, berthing_location.x_cord)
        smallest_y = min(smallest_y, berthing_location.y_cord)
        largest_x = max(largest_x, berthing_location.x_cord)
        largest_y = max(largest_y, berthing_location.y_cord)

    for truck_parking_location in truck_parking_locations:
        smallest_x = min(smallest_x, truck_parking_location.x_cord)
        smallest_y = min(smallest_y, truck_parking_location.y_cord)
        largest_x = max(largest_x, truck_parking_location.x_cord)
        largest_y = max(largest_y, truck_parking_location.y_cord)

    return [(smallest_x, smallest_y), (largest_x, largest_y)]


def update_ybs(gui, canvas, gui_blocks, yard_blocks):
    for i in range(len(yard_blocks)):
        yb_ocupancy = yard_blocks[i].getOccupancy()
        fill = "#%02x%02x%02x" % (math.floor(255 * yb_ocupancy), math.floor(255 - 255 * yb_ocupancy), 0)
        canvas.itemconfig(gui_blocks[i], fill=fill)
    gui.update()


def init_gui():
    gui = tk.Tk()
    gui.attributes('-fullscreen', True) # make main window full-screen
    # gui.geometry(f"{width + 400}x{height + 500}")

    return gui


def run_simulation(sim, gui, canvas):
    # sets day_clock, day_counter and time to 0
    sim.setup_timers()

    departure_list = []
    arrival_list = [0]

    blocks = draw(sim, canvas)
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
    canvas = tk.Canvas(gui, bg='white', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True) # configure canvas to occupy the whole main window
    canvas.update()
    # canvas = tk.Canvas(gui, width=width + 400, height=height)

    sim = init_simulation()
    run_simulation(sim, gui, canvas)
    gui.mainloop()  # Update tinker


startGUI()
