import time
import tkinter as tk
from threading import Thread
from tkinter import HORIZONTAL

from Data.DataParser import load_data
from Simulation import Simulation, add_to_Q, get_inter_arrival_time_sample
from SimulationContainer import SimulationContainer

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
pause_switch = False

lay = []


def startup_screen(gui):
    popup = tk.Toplevel()
    popup.attributes('-topmost', 'true')
    lay.append(popup)
    popup.grab_set()
    popup.title("Simulation Parameters")
    popup.geometry("300x250")
    popup.resizable(False, False)

    # Scenarios
    scenarios = {
        "Closest (Base Scenario)",
        "Lowest Occupancy",
        "Possible Split Up",
        "Mixed Rule - Block can only contain 1 type"
    }
    # datatype of menu text
    scenario = tk.StringVar()
    # initial menu text
    scenario.set("Closest (Base Scenario)")
    lbl_scenarios = tk.Label(popup, text="Scenarios: ")
    drop = tk.OptionMenu(popup, scenario, *scenarios)
    lbl_scenarios.pack()
    drop.pack()

    # Distance calculation reference
    bases = {
        "Arrival Based",
        "Departure Based",
        "Arrival and Departure Based"
    }
    # datatype of menu text
    dist_reference = tk.StringVar()
    # initial menu text
    dist_reference.set("Arrival Based")
    lbl_dist_reference = tk.Label(popup, text="Distance Calculation Reference: ")
    drop = tk.OptionMenu(popup, dist_reference, *bases)
    lbl_dist_reference.pack()
    drop.pack()

    # Input fields for months, days, and hours
    frame = tk.Frame(popup)
    frame.pack()

    lbl_months = tk.Label(frame, text="Months:")
    lbl_months.pack(side=tk.LEFT)

    months = tk.Entry(frame, width=5)
    months.insert(tk.END, "12")  # Default value is 12
    months.pack(side=tk.LEFT)

    lbl_days = tk.Label(frame, text="Days:")
    lbl_days.pack(side=tk.LEFT)

    days = tk.Entry(frame, width=5)
    days.insert(tk.END, "0")  # Default value is 0
    days.pack(side=tk.LEFT)

    lbl_hours = tk.Label(frame, text="Hours:")
    lbl_hours.pack(side=tk.LEFT)

    hours = tk.Entry(frame, width=5)
    hours.insert(tk.END, "0")  # Default value is 0
    hours.pack(side=tk.LEFT)

    btn_run = tk.Button(popup, text="Run Simulation",
                        command=lambda: init_simulation(gui, scenario.get(), dist_reference.get(), months.get(),
                                                        days.get(), hours.get()))
    btn_run.pack(side=tk.BOTTOM)


def init_simulation(gui, scenario, distance_reference, months, day, hours):
    data = load_data('./Data/')
    sim = Simulation(data, False, False, False, False, False, False)
    sim.setScenario(scenario)
    sim.setDistanceCalculationReference(distance_reference)
    sim.setSimulationHours(months, day, hours)
    sim.print_status()

    # Close popup window
    top = lay[0]
    top.destroy()
    top.update()

    canvas = init_canvas(gui)
    run_simulation(sim, gui, canvas, scenario, distance_reference, months, day, hours)
    return sim


def init_canvas(gui):
    canvas = tk.Canvas(gui, bg='darkgray', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)  # configure canvas to occupy the whole main window
    canvas.update()
    return canvas


def init_gui():
    gui = tk.Tk()
    gui.attributes('-fullscreen', True)  # make main window full-screen
    gui.title("Container yard simulation")

    return gui


def draw_yarblocks(sim, canvas):
    blocks = []
    fillers = []

    for block in sim.yard_blocks:
        start_pos_x = transpose_x(block.position.x_cord)
        # Not fully stretch to leave some room for parameters
        start_pos_y = transpose_y(block.position.y_cord)

        yb_width = block.capacity / 1000 * 30
        yb_height = block.capacity / 1000 * 110

        fill = '#00FF00' if block.flow_type == 'EXPORT' else '#FFFF00' if block.flow_type == 'IMPORT' else '#ADD8E6'
        border = 'orange' if block.container_type == "REEFER" else 'blue'
        block_rectangle = canvas.create_rectangle(start_pos_x,
                                                  start_pos_y,
                                                  start_pos_x + yb_width,
                                                  start_pos_y + yb_height,
                                                  fill=fill,
                                                  outline=border)
        blocks.append(block_rectangle)

        fill_rectangle = canvas.create_rectangle(start_pos_x,
                                                 start_pos_y,
                                                 start_pos_x + yb_width,
                                                 start_pos_y,
                                                 fill='#FF0000',
                                                 outline=border)
        fillers.append(fill_rectangle)

    return blocks, fillers


def draw_berthlocations(sim, canvas):
    vessels = []
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
    return vessels


def draw_truck_locations(sim, canvas):
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


def draw_text(canvas, label, pos_x, pos_y):
    var = tk.StringVar()
    var.set(label)
    window = tk.Label(canvas, textvariable=var, font=30)
    canvas.create_window(pos_x, pos_y, anchor=tk.SW, window=window)
    return var


def draw_labels(canvas):
    global timer_text
    timer_text = draw_text(canvas, "Time: 0", canvas_width - border_space - 200, canvas_height - border_space)

    global containers_rejected_text
    containers_rejected_text = draw_text(canvas, "Rejected containers: 0", border_space, canvas_height - 160)

    global cg_rejected_text
    cg_rejected_text = draw_text(canvas, "Rejected container groups: 0", border_space, canvas_height - 110)

    global normal_containers_rejected_text
    normal_containers_rejected_text = draw_text(canvas, "Rejected normal containers: 0", border_space, canvas_height - 60)

    global reefer_containers_rejected_text
    reefer_containers_rejected_text = draw_text(canvas, "Rejected reefer containers: 0", border_space, canvas_height - border_space)
    global total_travel_distance_text
    total_travel_distance_text = draw_text(canvas, "Total travel distance of container groups: 0", canvas_width / 2 - 200, canvas_height - 60)

    global average_travel_distance_text
    average_travel_distance_text = draw_text(canvas, "Average travel distance of container groups: 0", canvas_width / 2 - 200, canvas_height - border_space)


def draw(sim, canvas):
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
    blocks, fillers = draw_yarblocks(sim, canvas)

    # Water
    canvas.create_rectangle(0, 20, canvas_width, transpose_y(222), fill="#0000FF", outline='black')

    # draw birth locations
    vessels = draw_berthlocations(sim, canvas)
    draw_truck_locations(sim, canvas)

    # Animation button
    global animation_button
    animation_button = tk.Button(canvas, text="Toggle on", command=toggle_animation)
    canvas.create_window(canvas_width - border_space, transpose_y(222) + border_space, anchor=tk.NE,
                         window=animation_button)

    global pause_button
    pause_button = tk.Button(canvas, text="Pause", command=toggle_pause)
    canvas.create_window(canvas_width - border_space * 10, transpose_y(222) + border_space, anchor=tk.NE,
                         window=pause_button)


    global speed_controller
    speed_controller = tk.Scale(canvas, label="Animation speed", from_=100, to=0, orient=HORIZONTAL)
    canvas.create_window(canvas_width - 400, canvas_height - 70, anchor=tk.NW, window=speed_controller)
    speed_controller.set(50)
    # Parameter labels
    draw_labels(canvas)

    # Legend
    # Legend items
    legend_items = [
        {"color": "#00FF00", "label": "EXPORT"},
        {"color": "#ADD8E6", "label": "MIX"},
        {"color": "#FFFF00", "label": "IMPORT"},
        {"color": 'orange', "label": "REEFER"},
        {"color": 'blue', "label": "NORMAL"}
    ]

    # coordinates
    legend_x = canvas_width - 100
    legend_y = canvas_height - 150
    legend_item_height = 20
    legend_spacing = 10

    for item in legend_items:
        color = item["color"]
        label = item["label"]

        # Draw colored rectangle
        if color == 'orange' or color == 'blue':
            canvas.create_rectangle(legend_x, legend_y, legend_x + legend_item_height, legend_y + legend_item_height,
                                    fill="#A9A9A9", outline=color)
        else:
            canvas.create_rectangle(legend_x, legend_y, legend_x + legend_item_height, legend_y + legend_item_height,
                                    fill=color)

        # Draw label text
        canvas.create_text(legend_x + legend_item_height + legend_spacing, legend_y + legend_item_height // 2,
                           text=label, anchor=tk.W)

        # Adjust the y-coordinate for the next item
        legend_y += legend_item_height + legend_spacing

    canvas.pack()

    return blocks, vessels, fillers


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


def update_ybs(sim, gui, canvas, gui_blocks, yard_blocks, vessels, paths, gui_fillers):
    # Container animation
    if animation_switch:
        for p in paths:
            begin_position, end_position = p.begin_point, p.end_point

            x = transpose_x(begin_position.x_cord)
            y = transpose_y(begin_position.y_cord)
            target_x = transpose_x(end_position.x_cord)
            target_y = transpose_y(end_position.y_cord)

            vessel = None
            for v in vessels:
                coords = canvas.coords(v)
                if (coords[0] == x and coords[1] == y) or coords[0] == target_x and coords[1] == target_y:
                    vessel = v

            thread = Thread(target=p.move, args=(vessel,))
            thread.start()

    # Yard blocks animation
    for i in range(len(gui_blocks)):
        block = gui_blocks[i]
        x1, y1, x2, y2 = canvas.coords(block)
        yb_occupancy = yard_blocks[i].getOccupancy()
        canvas.coords(gui_fillers[i],
                      x1,
                      y1,
                      x2,
                      y1 + (yb_occupancy * (y2 - y1)))

    # Parameter animation
    timer_text.set("Time: " + str(round(sim.time)))
    containers_rejected_text.set("Rejected containers: " + str(sim.rejected_containers))
    cg_rejected_text.set("Rejected container groups: " + str(sim.rejected_groups))
    normal_containers_rejected_text.set("Rejected normal containers: " + str(sim.rejected_per_type['normal']))
    reefer_containers_rejected_text.set("Rejected reefer containers: " + str(sim.rejected_per_type['reefer']))
    total_travel_distance_text.set(
        "Total travel distance of container groups: " + str(round(sim.total_travel_distance_containers)))
    average_travel_distance_text.set("Average travel distance of container groups: " + str(
        round(sim.total_travel_distance_containers / sim.total_containers)))

    gui.update()


def toggle_animation():
    global animation_switch
    animation_switch = not animation_switch
    if animation_switch:
        animation_button.configure(text="Toggle On")
    else:
        animation_button.configure(text="Toggle Off")
def toggle_pause():
    global pause_switch
    pause_switch = not pause_switch
    if pause_switch:
        pause_button.configure(text="Play")
    else:
        pause_button.configure(text="Pause")


def run_simulation(sim, gui, canvas, scenario, distance_reference, months, day, hours):
    # sets day_clock, day_counter and time to 0
    sim.setup_timers()

    departure_list = []
    arrival_list = [0]

    blocks, vessels, fillers = draw(sim, canvas)
    container_groups = []
    last_update = time.time()
    while sim.time <= sim.SIMULATION_HOURS:
        gui.update()
        if ((time.time() - last_update) < (1 * (speed_controller.get() / 100))) | pause_switch:
            continue
        last_update = time.time()
        container_group_sim = []
        has_generated = sim.generate_new_time(departure_list, arrival_list)
        if sim.time == sim.SIMULATION_HOURS:
            break

        # Departure paths for animation
        for container_group in container_groups:
            if sim.time >= container_group.getFinishTime():
                block_dictionary = container_group.yard_blocks.copy()
                for block in block_dictionary:
                    container_group_sim.append(
                        SimulationContainer(canvas, gui, block.position, container_group.departure_point, speed_controller.get(),
                                            container_group, min_x, max_x, min_y, max_y, border_space))

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
                container_group_sim.append(
                    SimulationContainer(canvas, gui, new_cg.arrival_point, key.position, speed_controller.get(), new_cg, min_x, max_x, min_y,
                                        max_y, border_space))

        # update yb visualisation
        update_ybs(sim, gui, canvas, blocks, sim.yard_blocks, vessels, container_group_sim, fillers)


def startGUI():
    gui = init_gui()
    startup_screen(gui)
    gui.mainloop()  # Lets the window open after the simulation ends


def transpose_x(x):
    return (x - min_x) / (max_x - min_x) * (canvas_width - 2 * border_space) + border_space


def transpose_y(y):
    return y / max_y * (canvas_height - 2 * border_space) + border_space - min_y


if __name__ == '__main__':
    startGUI()