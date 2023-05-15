import math
import tkinter
import tkinter as tk

from Data.DataParser import load_data
from Parameters import SIMULATION_HOURS
from Simulation import Simulation, add_to_Q, get_inter_arrival_time_sample

timer_text = None
containers_rejected_text = None
cg_rejected_text = None
normal_containers_rejected_text = None
reefer_containers_rejected_text = None
total_travel_distance_text = None
average_travel_distance_text = None

min_x = None
max_x = None
min_y = None
max_y = None
border_space = None
canvas_width = None
canvas_height = None

animation_switch = True


def init_simulation():
    data = load_data('./Data/')
    sim = Simulation(data)
    return sim


def draw(sim, canvas):
    blocks = []
    vessels = []

    normalisation = normalise_positions(sim.yard_blocks, sim.berthing_positions, sim.truck_parking_locations)
    global min_x
    min_x = normalisation[0][0]
    global max_x
    max_x = normalisation[1][0]
    global min_y
    min_y = normalisation[0][1]
    global max_y
    max_y = normalisation[1][1]

    global canvas_width
    canvas_width = canvas.winfo_width()
    global canvas_height
    canvas_height = canvas.winfo_height()
    global border_space
    border_space = 10

    # Figures

    for block in sim.yard_blocks:
        start_pos_x = transpose_x(block.position.x_cord)
        # Not fully stretch to leave some room for parameters
        start_pos_y = transpose_y(block.position.y_cord)

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

    # Water
    canvas.create_rectangle(0,
                            20,
                            canvas_width,
                            100,
                            fill="#0000FF",
                            outline='black')

    for berth_location in sim.berthing_positions:
        start_pos_x = transpose_x(berth_location.x_cord)
        # Not fully stretch to leave some room for parameters
        start_pos_y = transpose_y(berth_location.y_cord)

        rectangle = canvas.create_rectangle(start_pos_x,
                                            start_pos_y,
                                            start_pos_x + 50,
                                            start_pos_y + 10,
                                            fill="#808080",
                                            outline='black',
                                            state='hidden')
        vessels.append(rectangle)

    for truck_location in sim.truck_parking_locations:
        start_pos_x = transpose_x(truck_location.x_cord)
        # Not fully stretch to leave some room for parameters
        start_pos_y = transpose_y(truck_location.y_cord)

        canvas.create_rectangle(start_pos_x,
                                start_pos_y,
                                start_pos_x + 20,
                                start_pos_y + 10,
                                fill="#CD853F",
                                outline='black')
    # Animation button
    global animation_switch
    animation_button = tk.Button(canvas, text="Toggle animation", command=toggle_animation)
    canvas.create_window(canvas_width - border_space, 70, anchor=tk.NE, window=animation_button)

    # Parameter labels
    font = 30

    global timer_text
    timer_text = tk.StringVar()
    timer_text.set("Time: 0")
    timer_label = tk.Label(canvas, textvariable=timer_text, font=font)
    canvas.create_window(canvas_width - border_space, canvas_height - border_space, anchor=tk.SE, window=timer_label)

    global containers_rejected_text
    containers_rejected_text = tk.StringVar()
    containers_rejected_text.set("Rejected containers: 0")
    containers_rejected_label = tk.Label(canvas, textvariable=containers_rejected_text, font=font)
    canvas.create_window(border_space, canvas_height - 160, anchor=tk.SW, window=containers_rejected_label)

    global cg_rejected_text
    cg_rejected_text = tk.StringVar()
    cg_rejected_text.set("Rejected container groups: 0")
    cg_rejected_label = tk.Label(canvas, textvariable=cg_rejected_text, font=font)
    canvas.create_window(border_space, canvas_height - 110, anchor=tk.SW, window=cg_rejected_label)

    global normal_containers_rejected_text
    normal_containers_rejected_text = tk.StringVar()
    normal_containers_rejected_text.set("Rejected normal containers: 0")
    normal_containers_rejected_label = tk.Label(canvas, textvariable=normal_containers_rejected_text, font=font)
    canvas.create_window(border_space, canvas_height - 60, anchor=tk.SW, window=normal_containers_rejected_label)

    global reefer_containers_rejected_text
    reefer_containers_rejected_text = tk.StringVar()
    reefer_containers_rejected_text.set("Rejected reefer containers: 0")
    reefer_containers_rejected_label = tk.Label(canvas, textvariable=reefer_containers_rejected_text, font=font)
    canvas.create_window(border_space, canvas_height - border_space, anchor=tk.SW, window=reefer_containers_rejected_label)

    global total_travel_distance_text
    total_travel_distance_text = tk.StringVar()
    total_travel_distance_text.set("Total travel distance of container groups: 0")
    total_travel_distance_label = tk.Label(canvas, textvariable=total_travel_distance_text, font=font)
    canvas.create_window(canvas_width/2 -200, canvas_height - 60, anchor=tk.SW, window=total_travel_distance_label)

    global average_travel_distance_text
    average_travel_distance_text = tk.StringVar()
    average_travel_distance_text.set("Average travel distance of container groups: 0")
    average_travel_distance_label = tk.Label(canvas, textvariable=average_travel_distance_text, font=font)
    canvas.create_window(canvas_width/2 -200, canvas_height - border_space, anchor=tk.SW, window=average_travel_distance_label)

    canvas.pack()

    return blocks, vessels


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


def update_ybs(sim, gui, canvas, gui_blocks, yard_blocks, vessels, paths):
    for i in range(len(yard_blocks)):
        yb_ocupancy = yard_blocks[i].getOccupancy()
        fill = "#%02x%02x%02x" % (math.floor(255 * yb_ocupancy), math.floor(255 - 255 * yb_ocupancy), 0)
        canvas.itemconfig(gui_blocks[i], fill=fill)

    # Animation doesn't affect time
    frames = 10000

    # put in commentary for no animation
    # Todo: let paths go simultaneously (when multiple things happen at the same time)
    if animation_switch:
        for p in paths:
            begin_position, end_position = p

            x = transpose_x(begin_position.x_cord)
            y = transpose_y(begin_position.y_cord)
            target_x = transpose_x(end_position.x_cord)
            target_y = transpose_y(end_position.y_cord)
            # Create the rectangle on the canvas
            container = canvas.create_rectangle(x, y, x + 10, y + 10, fill='blue')

            # Calculate the distance between the current position and the target position
            distance_x = target_x - x
            distance_y = target_y - y

            # Calculate the increment for each frame
            step_x = distance_x / frames
            step_y = distance_y / frames

            vessel = None
            for v in vessels:
                coords = canvas.coords(v)
                if (coords[0] == x and coords[1] == y) or coords[0] == target_x and coords[1] == target_y:
                    vessel = v
                    canvas.itemconfig(v, state='normal')
                    gui.update()

            while abs(x - target_x) >= abs(step_x) and abs(y - target_y) >= abs(step_y):
                # Update the rectangle's position
                x += step_x
                y += step_y

                canvas.coords(container, x, y, x + 10, y + 10)
                gui.update()

            if vessel is not None:
                canvas.itemconfig(vessel, state='hidden')
                gui.update()

            canvas.delete(container)

    timer_text.set("Time: " + str(sim.time))
    containers_rejected_text.set("Rejected containers: " + str(sim.rejected_containers))
    cg_rejected_text.set("Rejected container groups: " + str(sim.rejected_groups))
    normal_containers_rejected_text.set("Rejected normal containers: " + str(sim.rejected_per_type['normal']))
    reefer_containers_rejected_text.set("Rejected reefer containers: " + str(sim.rejected_per_type['reefer']))
    total_travel_distance_text.set("Total travel distance of container groups: " + str(round(sim.total_travel_distance_containers)))
    average_travel_distance_text.set("Average travel distance of container groups: " + str(round(sim.total_travel_distance_containers/sim.total_containers)))

    gui.update()

def init_gui():
    gui = tk.Tk()
    gui.attributes('-fullscreen', True)  # make main window full-screen
    gui.title("Container yard simulation")
    # gui.geometry(f"{width + 400}x{height + 500}")

    return gui

def toggle_animation():
    global animation_switch
    animation_switch = not animation_switch

def run_simulation(sim, gui, canvas):
    # sets day_clock, day_counter and time to 0
    sim.setup_timers()

    departure_list = []
    arrival_list = [0]

    blocks, vessels = draw(sim, canvas)
    container_groups = []
    while sim.time <= SIMULATION_HOURS:
        paths = []

        has_generated = sim.generate_new_time(departure_list, arrival_list)

        # Departure paths for animation
        for container_group in container_groups:
            if sim.time >= container_group.getFinishTime():
                block_dictionary = container_group.yard_blocks.copy()
                for block in block_dictionary:
                    paths.append([block.position, container_group.departure_point])

        # check what container_groups get removed to show
        sim.remove_expired_container_groups(container_groups)

        if has_generated:
            # show the new cg arriving
            new_cg = sim.generate_new_containergroup()

            # show yb added
            sim.add_cg_to_closest_yb(new_cg, container_groups, departure_list)
            add_to_Q(arrival_list, sim.time + get_inter_arrival_time_sample())

            # Arrival path for animation
            for key in new_cg.yard_blocks.keys():
                paths.append([new_cg.arrival_point, key.position])

        # update yb visualisation
        update_ybs(sim, gui, canvas, blocks, sim.yard_blocks, vessels, paths)


def startGUI():
    gui = init_gui()
    canvas = tk.Canvas(gui, bg='darkgray', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)  # configure canvas to occupy the whole main window
    canvas.update()

    sim = init_simulation()
    run_simulation(sim, gui, canvas)
    gui.mainloop()  # Lets the window open after the simulation ends


def transpose_x(x):
    return (x - min_x) / (max_x - min_x) * (canvas_width - 2 * border_space) + border_space


def transpose_y(y):
    return y / max_y * (canvas_height - 2 * border_space) + border_space - min_y


startGUI()
