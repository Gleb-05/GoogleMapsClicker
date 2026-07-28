import tkinter as tk
import time
import pyautogui
from tk_app_frames.BasicFrame import BasicFrame

from usr_get_area_img import get_dd_rect_img
from function_to_tk_entries import build_function_editor
from keypress_publisher import KeypressPublisher, ButtonKeyboardManager


def throw_error():
    "calibrate tkmanager-kbpub relationship"
    raise ValueError("whatever")

def long_func():
    "test pyautogui corner error"
    for _ in range(10):
        pyautogui.moveTo(20,20, duration=1)

class GetAreaImgFrame(BasicFrame):
    '''See and change individual fields of configs'''
    def __init__(self, root: tk.Tk):
        super().__init__(root)
        self.root = root
        self.root.title("Work with Areas")
        self.W, self.H = root.winfo_screenwidth(), root.winfo_screenheight()
        self.root.minsize(300, 100)
        self.root.attributes("-topmost", True)

        tk.Frame(self.body, width=BasicFrame.MAX_WIDTH-140).pack()  # crutch to standardize the width of different windows

        debug_text = tk.Text(self.header, width=300, height=10)
        debug_text.insert("1.0", "Debug text")
        debug_text.pack(expand=True)
        def set_feedback(value):
            debug_text.delete("1.0", tk.END)
            debug_text.insert("1.0", str(value))

        kb_publisher = KeypressPublisher()
        self.button_manager = ButtonKeyboardManager(self.root, kb_publisher)

        for target_function in [get_dd_rect_img, throw_error, long_func]:
            build_function_editor(target_function, self.body, self.button_manager, set_feedback)

        self.update_root_geometry()


if __name__ == "__main__":
    root = tk.Tk()
    app = GetAreaImgFrame(root)
    root.mainloop()
