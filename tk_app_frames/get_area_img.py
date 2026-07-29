import tkinter as tk
import pyautogui
from tk_app_frames.basic_frame import BasicFrame

from usr_get_area_img import get_dd_rect_img
from z_app_components.function_to_tk_entries import build_function_editor
from z_app_components.keypress_publisher import KeypressPublisher, ButtonKeyboardManager


# keep those functions close for expanding target_functions_list

# def throw_error():
#     "calibrate tkmanager-kbpub relationship"
#     raise ValueError("whatever")

# def long_func():
#     "test pyautogui corner error"
#     for _ in range(10):
#         pyautogui.moveTo(20,20, duration=1)

class GetAreaImg(BasicFrame):
    '''See and change individual fields of configs'''
    def __init__(self, master: tk.Misc, controller):
        super().__init__(master, controller)
        
        tk.Frame(self.body, width=controller.MAX_WIDTH-140).pack()  # crutch to standardize the width of different windows

        debug_text = tk.Text(self.header, width=300, height=10)
        debug_text.insert("1.0", "Debug text")
        # debug_text.pack(expand=True)
        def set_feedback(value):
            debug_text.delete("1.0", tk.END)
            debug_text.insert("1.0", str(value))
        set_feedback = None  # for now, debugging is unnecessary.
        #  TODO pass debug flag through the controller and expand target function list accordingly?

        keypress_publisher: KeypressPublisher = controller.keypress_publisher
        self.button_manager = ButtonKeyboardManager(self, keypress_publisher)

        target_functions_list = [get_dd_rect_img]

        for target_function in target_functions_list:
            build_function_editor(target_function, self.body, self.button_manager, set_feedback)


if __name__ == "__main__":
    root = tk.Tk()
    app = GetAreaImg(root, None)
    root.mainloop()
