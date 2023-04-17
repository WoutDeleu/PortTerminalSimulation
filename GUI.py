from tkinter import *

def startGUI():
    root = Tk()

    label = Label(root, text="Hello World!")

    label.grid(row=0, column=0)
    root.mainloop()
