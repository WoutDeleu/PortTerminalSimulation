import math
import tkinter
import tkinter as tk

def start_simulation():
    print("start sim")

def startGUI():
    gui = tk.Tk()
    width = 1000
    height = 1000
    gui.geometry(f"{width}x{height}")

    tk.Button(gui, text="Start", command=start_simulation).place(x=width - 65, y=height - 40)
    tk.Scale(gui,from_=0, to=200, orient=tk.HORIZONTAL).place(x=width/2 + 60, y=height - 55)
    w = tk.Canvas(gui, width=width, height=height - 200)
    # (X + 5) * n = Width
    # (Y + 5) * m = Width
    # n * m = total
    for j in range(math.floor((height - 200) / 55)):
        start_pos_y = j * (50 + 5)
        for i in range(math.floor(width / 55)):
            start_pos_x = i * (50 + 5)
            w.create_rectangle(start_pos_x, start_pos_y, start_pos_x + 50, start_pos_y + 50, fill="black", outline='black')
    w.pack()
    gui.mainloop()

startGUI()