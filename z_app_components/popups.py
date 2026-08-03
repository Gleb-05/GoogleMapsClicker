import tkinter as tk

from constants import SUCCESS_HIGHLIGHT
from utils import timed_close

def _prepare_popup_frame(master: tk.Toplevel, bg: str):
    """Make a frame with a close button. The frame will disappear in 5 seconds"""
    popup = tk.Frame(master, background=bg)
    popup.place(x=0, y=70, width=master.winfo_width())  # 70 is from the main_app

    kw_flat_button = dict(borderwidth=0, relief="flat", highlightthickness=0)
    close_btn = tk.Button(popup, text="❌", bg=bg, **kw_flat_button)
    close_btn.pack(side="right", padx=8)

    close_btn.configure(command=timed_close(popup, 5))
    return popup


def popup_message(master: tk.Toplevel, message: str, bg: str = SUCCESS_HIGHLIGHT):
    """
    Show a `bg`-colored message at the top of `master` that will disappear in 5 seconds.
    Useful to signal the status of the last executed operation.
    """
    frame = _prepare_popup_frame(master, bg=bg)
    tk.Label(
        frame, 
        text=(" "*8)+message, 
        wraplength=frame.winfo_width() - 30, # 30 px for close button
        bg=bg
        ).pack(fill="x", side="left", pady=8)
