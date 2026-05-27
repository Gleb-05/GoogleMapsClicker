import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import matplotlib.pyplot as plt

from .test_usr_get_area_img import gather_coordinates, plot_path

root = tk.Tk()

plt_frame = tk.Frame(root)
plt_frame.grid(row=0, column=0, columnspan=2, pady=(10,10))

fig, ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=plt_frame)
canvas.get_tk_widget().pack()

toolbar = NavigationToolbar2Tk(canvas, plt_frame)
toolbar.update()

def callback(p):
    return (str.isdigit(p) or p == "") and len(p) <= 7
vcmd = root.register(callback)

r_width_frame = tk.Frame(root)
r_width_frame.grid(row=1, column=0, sticky="E")
r_width_label = tk.Label(r_width_frame, text="r_width:")
r_width_label.pack(side="left")
r_width_entry = tk.Entry(r_width_frame, width=10, validate='all', validatecommand=(vcmd, '%P'))
r_width_entry.pack(side="left")

r_height_frame = tk.Frame(root)
r_height_frame.grid(row=1, column=1, sticky="W")
r_height_label = tk.Label(r_height_frame, text="r_height:")
r_height_label.pack(side="left")
r_height_entry = tk.Entry(r_height_frame, width=10, validate='all', validatecommand=(vcmd, '%P'))
r_height_entry.pack(side="left")


def update_plot():
    r_width, r_height = int(r_width_entry.get()), int(r_height_entry.get())
    ax.clear()
    plot_path(f"{2*r_width+1}x{2*r_height+1} nodes path", gather_coordinates(r_width, r_height), ax)
    canvas.draw()

btn = tk.Button(root, text="Update", command=update_plot)
btn.grid(row=2, column=0, columnspan=2, pady=10)

ax.plot([0],[0])
canvas.draw()

root.mainloop()
