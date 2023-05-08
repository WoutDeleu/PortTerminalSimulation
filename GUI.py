import math
import tkinter
import tkinter as tk

def start_simulation():
    print("start sim")

def startGUI():
    gui = tk.Tk()
    rows = 10
    cols = 16

    yb_width = 80
    yb_height = 40
    tolerance = 20
    yb = 159

    width = cols * (yb_width + tolerance) + 200
    height = rows * (yb_height + tolerance) + 500
    gui.geometry(f"{width}x{height}")

    w = tk.Canvas(gui, width=width, height=height)

    for i in range(yb):
        row = math.floor(i / cols)
        col = i - row * 16
        start_pos_y = row * (yb_height + tolerance) + tolerance
        start_pos_x = col * (yb_width + tolerance) + (200/2)
        w.create_rectangle(start_pos_x, start_pos_y, start_pos_x + yb_width, start_pos_y + yb_height, fill="white", outline='orange')

    w.pack()
    gui.mainloop()

startGUI()