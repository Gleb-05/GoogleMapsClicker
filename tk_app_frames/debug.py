"""
To be launched separately with `python -m tk_app_frames.debug` 
during active development of new functionality.
"""

import traceback
import tkinter as tk
import pyautogui
import keyboard

from utils import show_image_modal
from gui.layers import map_toggle_sat_labels
from test.test_usr_get_area_img import TestDragArea

from gui.search import center_on_search_result
from utils import drag_map_idempotent
from usr_get_area_img import C, get_area_img, get_area_dd_wh, get_dd_rect_img, estimate_area_width_and_height_dd
from gui.map import map_get_coords_at_cursor
from gui.addressbar import addressbar_center_at_dd
from z_app_components.json_string_var import JsonStringVar


class DebugFrame:
    """
    Call functions directly during development to check that GUI still behaves correctly.

    Log Label at the window's bottom allows to debug most of the present functions.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Debug")
        self.W, self.H = root.winfo_screenwidth(), root.winfo_screenheight()
        self.root.geometry("300x250+{}+{}".format(self.W-400, 100))
        self.root.attributes("-topmost", True)

        self.steps = {
            "show_xy": self.show_xy,
            "drag_map_idempotent": drag_map_idempotent,
            "center_at_dd": lambda: addressbar_center_at_dd("48,2"),
            "show_image_modal": lambda: show_image_modal(self.root, "img/place_linkbtn.png"),
            "center_on_search_result": lambda: center_on_search_result("48,2"),
            "get_area_dd_wh": get_area_dd_wh,
            "estimate_area_width_and_height_dd": estimate_area_width_and_height_dd,
            "get_dd_dont_break_on_0": lambda: get_dd_rect_img("49.35202310068144, 2.6037845241133444", "49.34864736138488, 2.6150712597953283"),
            "get_dd_rect_img_small_map": lambda: get_dd_rect_img(*C.REGION_1, satellite=False),
            "get_dd_rect_img_small_sat": lambda: get_dd_rect_img(*C.REGION_1),
            "get_dd_rect_img_map": lambda: get_dd_rect_img(*C.REGION_2, satellite=False),
            "get_dd_rect_img_sat": lambda: get_dd_rect_img(*C.REGION_2),
            "get_area_img": lambda: get_area_img("48,2"),
            "test_drag_area": TestDragArea.drag_shift,
            "test_area_deforms": TestDragArea.area_deforms,
            "map_get_coords_at_cursor": map_get_coords_at_cursor,
            "map_toggle_sat_labels": map_toggle_sat_labels
        }
        self.steps_names = list(self.steps.keys())
        self.step_var = tk.StringVar(value="show_xy")
        tk.OptionMenu(root, self.step_var, *self.steps_names).pack(pady=10)
        
        instruction = "Press NumLk (or alt+f2) after moving your cursor to a suitable position."
        tk.Label(root, text=instruction, wraplength=300).pack(expand=True)

        var = JsonStringVar()
        entry = tk.Entry(root, textvariable=var)
        entry.pack()
        tk.Button(root, text="print entry", command=lambda: print(var.get())).pack()
        
        self.debug_text = tk.Text(root, width=300)
        self.debug_text.insert("1.0", "Debug text")
        self.debug_text.pack(expand=True)

        self.listen_hotkey()

    def execute_selected_step(self):
        try:
            result = self.steps[self.step_var.get()]()
        except Exception as e:
            result = e
            traceback.print_exc()
        self.debug_text.delete("1.0", tk.END)
        self.debug_text.insert("1.0", str(result))

    def listen_hotkey(self):
        keyboard.add_hotkey("num lock", self.execute_selected_step)
        keyboard.add_hotkey("shift", self.execute_selected_step)  # fallback option

    def show_xy(self):
        x, y = pyautogui.position()
        return f"X: {x}, Y: {y}"


if __name__ == "__main__":
    root = tk.Tk()
    app = DebugFrame(root)
    root.mainloop()
