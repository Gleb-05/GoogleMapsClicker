"""
Expose one useful and stable function `get_dd_rect_img` to the user.
Part of the main app.
"""

import tkinter as tk
from tk_app_frames.basic_frame import BasicFrame

from usr_get_area_img import get_dd_rect_img_tk
from z_app_components.function_to_tk_entries import build_function_editor
from z_app_components.keypress_publisher import KeypressPublisher, ButtonKeyboardManager


class GetAreaImg(BasicFrame):
    '''Work with the google map to make images'''

    def __init__(self, master: tk.Misc, controller):
        super().__init__(master, controller)

        FUNCTIONS = [get_dd_rect_img_tk]
        
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

        for target_function in FUNCTIONS:
            build_function_editor(target_function, self.body, self.button_manager, set_feedback)


# keep those functions here to expand target_functions_list for testing

# def throw_error():
#     "calibrate tkmanager-kbpub relationship"
#     import time
#     time.sleep(1)
#     raise TimeoutError("whatever")

# def throw_timeout():
#     from wait_contexts import wait_for_screen_change
#     with wait_for_screen_change((10,10,10,10), 3):
#         pass

# def long_func():
#     "test pyautogui corner error"
#     import pyautogui
#     for _ in range(10):
#         pyautogui.moveTo(20,20, duration=1)
