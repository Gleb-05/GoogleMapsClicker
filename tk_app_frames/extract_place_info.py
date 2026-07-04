import threading
import traceback
import tkinter as tk
import keyboard

from config import PLACE_NAME_HTML

from gui_inspect import inspect_find
from gui_scroll import total_scroll_down, scroll_to_next_card
from usr_extract_place_info import process_search_queries, extract_place_info_safe


class DebugFrame:
    """
    Combine pieces of functionality necessary to navigate the google maps page
    to extract information about multiple places.

    Log Label at the window's bottom allows to debug most of the present functions.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Prepare")
        self.W, self.H = root.winfo_screenwidth(), root.winfo_screenheight()
        self.root.geometry("300x250+{}+{}".format(self.W-400, 100))
        self.root.attributes("-topmost", True)

        self.steps = {
            "process_search_queries": process_search_queries,
            "_extract_place_info_safe": extract_place_info_safe,
            "_inspect_find": lambda: inspect_find(PLACE_NAME_HTML),
            "_total_scroll_down": total_scroll_down,
            "_scroll_to_next_card": scroll_to_next_card,
        }
        self.steps_names = list(self.steps.keys())
        self.step_var = tk.StringVar(value="show_xy")
        tk.OptionMenu(root, self.step_var, *self.steps_names).pack(pady=10)


        
        instruction = "Press NumLk (or alt+f2) after moving your cursor to a suitable position."
        tk.Label(root, text=instruction, wraplength=300).pack(expand=True)
        
        self.debug_text = tk.Text(root, width=300)
        self.debug_text.insert("1.0", "Debug text")
        self.debug_text.pack(expand=True)

        threading.Thread(target=self.listen_hotkey, daemon=True).start()

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
        keyboard.add_hotkey("alt+f2", self.execute_selected_step)  # fallback option
        keyboard.wait()  # Keep the thread alive
