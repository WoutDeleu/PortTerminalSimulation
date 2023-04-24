import tkinter
import tkinter as tk

def start_simulation():
    print("start sim")

def startGUI():
    gui = tk.Tk()
    width = 500
    height = 500
    gui.geometry(f"{width}x{height}")

    tk.Button(gui, text="Start", command=start_simulation).place(x=width - 65, y=height - 40)
    tk.Scale(gui,from_=0, to=200, orient=tk.HORIZONTAL).place(x=width/2 + 60, y=height - 55)
    w = tk.Canvas(gui, width=width, height=height - 200)
    w.create_rectangle(0, 0, 100, 100, fill="blue", outline='blue')
    w.pack()
    gui.mainloop()

startGUI()