import tkinter as tk
from typing import NamedTuple, Any
from collections.abc import Callable

class FrameAndVariables(NamedTuple):
    '''Variables tightly coupled with a frame that contains them'''
    frame: tk.Frame
    variables: dict[str, tk.StringVar]  # maybe replace tk.StringVar with a (.get .set) Protocol for custom wrappers around tk widgets?


def setup_switch_frame_controller(frame_and_variables_dict: dict[str, FrameAndVariables], master: tk.Misc, on_switch: Callable[[], Any] | None = None):
    """
    Having multiple tk frames to switch between (coupled with tk variables within them), set up a controller: 
    display one frame at a time and switch between them using an option menu.

    Args:
        frame_and_variables_dict: constructed beforehand, must have FrameAndVariables as values. 
        master: passed to option menu at creation.
        on_switch: optional Callable[[], Any] that is invoked after the frames are switched.
    """
    frame_names = list(frame_and_variables_dict.keys())
    current_frame_name = frame_names[0]

    # set up OptionMenu to switch between frames
    def switch_frame(name):
        nonlocal current_frame_name
        frame_and_variables_dict[current_frame_name].frame.pack_forget()
        frame_and_variables_dict[name].frame.pack(fill="both", expand=False)
        current_frame_name = name
        if on_switch is not None:
            on_switch()
    option_menu_highlight = tk.Frame(master, background="white")
    option_menu_highlight.pack(fill="x", expand=True, pady=10)
    option_menu = tk.OptionMenu(
        option_menu_highlight,
        tk.StringVar(value=current_frame_name), 
        *frame_names, 
        command=switch_frame
    )
    option_menu.pack(anchor="center", pady=10)

    frame_and_variables_dict[current_frame_name].frame.pack(fill="both")
    