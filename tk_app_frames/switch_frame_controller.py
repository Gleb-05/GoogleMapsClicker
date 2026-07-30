import tkinter as tk
from tkinter import messagebox
from typing import NamedTuple, Any
from collections.abc import Callable

class FrameAndVariables(NamedTuple):
    '''
    Variables tightly coupled with a frame that contains them
    
    *If no logic depends on it, do `variables={}` if Frames are more important.*
    '''
    frame: tk.Frame
    variables: dict[str, tk.StringVar]  # maybe replace tk.StringVar with a (.get .set) Protocol for custom wrappers around tk widgets?


def setup_switch_frame_controller(
        frame_and_variables_dict: dict[str, FrameAndVariables], 
        master: tk.Misc, 
        callback_on_switched_frame: Callable[[str, FrameAndVariables], Any] | None = None, 
        on_switch: Callable[[], Any] | None = None
    ):
    """
    Having multiple tk frames to switch between (coupled with tk variables within them), set up a controller: 
    display one frame at a time and switch between them using an option menu.

    Args:
        frame_and_variables_dict:
            Shall have keys that are unique string codes (usually classnames) for each frame,
            and values that are FrameAndVariables constructed beforehand.

        master: 
            passed to option menu at creation for packing.

        on_switch: 
            optional callable, invoked after the frames are switched.
            Takes no arguments and returns Any.

        callback_on_switched_frame: 
            optional callable, invoked after the frames are switched.
            Can return Any, must accept keyword arguments `active_name` and `active_fav`.
            Will be invoked with the current key-value pair from `frame_and_variables_dict`, that is,
            a name (usually classname of currently displayed frame) and corresponding FrameAndVariables.
            This is an opportunity to have one orchestrator define `callback_on_switched_frame` 
            that expects certain behavior from the frames being displayed,
            and in turn have different behaviors where needed across frames inside `frame_and_variables_dict`
    """
    frame_names = list(frame_and_variables_dict.keys())
    current_frame_name = frame_names[0]  # keep track of which fav is displayed internally here

    # set up OptionMenu to switch between frames
    def switch_frame(name):
        nonlocal current_frame_name
        frame_and_variables_dict[current_frame_name].frame.pack_forget()
        fav = frame_and_variables_dict[name]
        fav.frame.pack(fill="both", expand=True)
        current_frame_name = name
        if callback_on_switched_frame is not None:
            callback_on_switched_frame(active_name=name, active_fav=fav)  # WHAT IS THE NAME OF THIS DEPENDENCY INJECTION
        if on_switch is not None:
            on_switch()
    option_menu_highlight = tk.Frame(master, background="white")
    option_menu_highlight.pack(fill="x", expand=True, pady=10)
    center_frame = tk.Frame(option_menu_highlight)
    center_frame.pack(anchor="center", pady=10)
    option_menu = tk.OptionMenu(
        center_frame,
        tk.StringVar(value=current_frame_name), 
        *frame_names, 
        command=switch_frame
    )
    option_menu.pack(side="left")
    tk.Button(
        center_frame,
        text=" ? ",
        command=lambda: messagebox.showinfo("Switch between frames", "Click on the dropdown menu and select one of the frames you'd like to see.")
    ).pack(side="left", padx=(5,0))

    frame_and_variables_dict[current_frame_name].frame.pack(fill="both", expand=True)
    if callback_on_switched_frame is not None:
        callback_on_switched_frame(active_name=current_frame_name, active_fav=frame_and_variables_dict[current_frame_name])
    if on_switch is not None:
        on_switch()
    