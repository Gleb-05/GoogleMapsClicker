import json
import keyboard
import pyautogui
from dataclasses import Field, dataclass, fields
import tkinter as tk
from tkinter import messagebox
from typing import ClassVar

from config_registry import ConfigRegistryMixin


@dataclass(frozen=True)
class ConfigTkMeta:
    """A bridge between config code and user control.

    - doc: str - guiding or explaining text alongside the config value
    - xy_read: if unset, this config value shall not be changed by a user via reading cursor coordinates.
      Otherwise, specify which coordinate shall be stored - ConfigTkMeta.READ_X, ConfigTkMeta.READ_Y, ConfigTkMeta.READ_XY

    Additionaly, a KEY: ClassVar[str] = "tk" is specified for consistency.

    - xy_reading is a property to quickly filter config values that do not requre xy reading - not to be set in code.
    """
    KEY: ClassVar[str] = "tk"
    """`metadata = { ConfigTkMeta.KEY: ConfigTkMeta(...) }` is the way to augment the dataclass field()."""
    READ_X: ClassVar[int] = 0
    READ_Y: ClassVar[int] = 1
    READ_XY: ClassVar[slice] = slice(2)

    doc: str
    xy_read: int | slice = -1
    @property
    def xy_reading(self):
        return self.xy_read != -1


class XYReadManager:
    '''Manage keyboard listening to keys. Prompted by one of many entries that read xy cursor coordinates.'''
    def __init__(self, root : tk.Tk):
        self.root = root
        self.target : tk.StringVar | None = None
        self.target_value: str | None = None
        self.xy_read : int | slice | None = None

        keyboard.hook(self._on_key)  # runs in a thread of its own it seems

    def request(self, variable: tk.StringVar, xy_read: int | slice):
        '''Call this from a button next to the entry to begin reading'''
        if self.target is not None:
            # new button was pressed immediately after, restore value of previously pressed button
            self.target.set(self.target_value)
        self.target = variable
        self.target_value = variable.get()
        variable.set("AWAITS NUM LK / ESC")
        self.xy_read = xy_read

    def _on_key(self, event: keyboard.KeyboardEvent):
        '''
        if target tk variable was not set using `request` - nothing.
        else if esc - cancel xy read.
        else if num lk or Rshift - pass x, y, or both coordinates to the target tk variable.
        '''
        if self.target is None:
            return

        if event.name == "esc":
            self.target.set(self.target_value)
            self.target = None
            self.target_value = None
            self.xy_read = None
            return
        
        if event.name == "num lock" or event.name == "right shift":
            x, y = pyautogui.position()
            _target = self.target
            _xy_read = self.xy_read
            self.target = None
            self.target_value = None
            self.xy_read = None
            value = [x,y][_xy_read]
            self.root.after(0, lambda: _target.set(json.dumps(value)))


def get_tk_fields(config: ConfigRegistryMixin):
    """For a given config, return all fields with ConfigTkMeta.KEY in metadata"""
    return [f for f in fields(config) if ConfigTkMeta.KEY in f.metadata]


def field_entry_w_variable(config_field: Field, master: tk.Misc, xy_read_manager: XYReadManager) -> tk.StringVar:
    '''
    Using a `config_field` and its ConfigTkMeta, construct tk.Frame for display and edit and pack it into `master`.
    Return `tk.StringVar` to track its value in the main app.
    `xy_read_manager` is used for entries that can be changed by reading cursor coordinates.
    '''
    field_frame = tk.Frame(master)
    field_frame.pack(fill=tk.X, expand=True, padx=10, pady=15)

    tk.Frame(field_frame, height=2, background="gray").pack(fill=tk.X, expand=True)

    meta: ConfigTkMeta = config_field.metadata.get(ConfigTkMeta.KEY)
    kw_label_make = {"master": field_frame, "wraplength": 400, "justify":"left"}
    tk.Label(text=f"{config_field.name}\n{meta.doc}",   **kw_label_make).pack(anchor=tk.W)

    entry_frame = tk.Frame(field_frame)
    entry_frame.pack(fill="x", expand=True)
    variable = tk.StringVar(value=json.dumps(config_field.default))
    entry = tk.Entry(entry_frame, textvariable=variable)
    entry.pack(side=tk.LEFT, anchor=tk.S)

    if meta.xy_reading:
        tk.Button(
            entry_frame, 
            text="set from cursor coordinates", 
            command=lambda:xy_read_manager.request(variable, meta.xy_read)
            ).pack(side=tk.LEFT, anchor=tk.W, padx=5)
        instruction = "For entries with buttons saying 'set from cursor coordinates',\n- press the button to begin the operation,\n- press NumLk (or right shift) after moving your cursor to a suitable position\n- or press ecs to cancel the operation."
        tk.Button(
            entry_frame,
            text=" ? ",
            command=lambda: messagebox.showinfo("HOWTO", instruction)
            ).pack(side=tk.LEFT, anchor=tk.W)

    return variable
