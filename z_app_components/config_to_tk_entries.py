import os
import json
import pyautogui
from dataclasses import Field, field, dataclass, fields
import tkinter as tk
from tkinter import messagebox
from typing import ClassVar, Any
from collections.abc import Callable

from constants import ATTENTION_HIGHLIGHT, IMG_DIR
from utils import show_image_modal
from z_app_components.config_registry import LoadFromJsonMixin
from z_app_components.json_string_var import JsonStringVar
from z_app_components.keypress_publisher import KeypressPublisher, ButtonKeyboardManager


@dataclass(frozen=True)
class ConfigTkMeta:
    """A bridge between config code and user control.

    - doc: str - guiding or explaining text alongside the config value
    - xy_read: if unset, this config value shall not be changed by a user via reading cursor coordinates.
      Otherwise, specify which coordinate shall be stored - ConfigTkMeta.READ_X, ConfigTkMeta.READ_Y, ConfigTkMeta.READ_XY
    - option_list: if set, this config value can be changed by a user via Option Menu.
    
    Additionaly, a KEY: ClassVar[str] = "tk" is specified for consistency.

    Useful readonly (not to be changed) properties to filter configs by:
    - xy_reading - True for config values that requre xy reading.
    - option_listing - True for config values that have non-empty option_list.
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
    
    option_list: list[int|str|float] = field(default_factory=list)
    @property
    def option_listing(self):
        return len(self.option_list) > 0


@dataclass(frozen=True)
class ConfigRecomputeMeta():
    '''
    Cover a very narrow case when one config field depends on another. 
    Requires that config class inherits from ConfigRecomputeMixin.

    - recompute_function_doc - guiding or explaining text alongside the recompute function
    - .recompute_function_getter() - see `ConfigRecomputeMixin.recompute_getter`
    - .recompute_causes - list of names of fields the current one depends on

    Additionaly, a KEY: ClassVar[str] = "recompute" is specified for consistency.

    Useful readonly (not to be changed) properties to filter configs by:
    - keyboard_indepentent - if `recompute_causes` are empty, the config will be considered
      as such that doesn't require additional keyboard control. 
      `recompute_function_getter` will be assigned to button command immediately
    '''
    KEY: ClassVar[str] = "recompute"
    '''`metadata = { ConfigRecomputeMeta.KEY: ConfigRecomputeMeta(...) }` is the way to augment the dataclass field().'''
    recompute_function_doc: str
    recompute_function_getter: Callable[[], Callable]
    '''Returns `lambda: recompute_function`'''
    recompute_causes: list[str]

    @property
    def keyboard_independent(self):
        return len(self.recompute_causes) == 0


@dataclass
class ConfigRecomputeMixin():
    '''
    In rare cases, some fields within the config depend on other fields, 
    and there is a function that user shall invoke in order to recompute them.
    
    Most likely, the recompute function cannot be addressed until the config is instantiated.
    See code below:
    - add `ConfigRecomputeMeta` in relevant field's metadata
    - provide a `Callable[[], Callable]` value to the `recompute_function_getter` to delay getting the recompute function until it's defined.
      `get_recompute` helper is available as ConfigRecomputeMixin class method.
    - call `add_recompute(r_func)` on instantiated config class after the func is defined in code.

    ```
    @dataclass
    class Config(LoadFromJsonMixin, ConfigRecomputeMixin):
        RECOMPUTE_FUNCTIONS = {}
        c1 : int = field(...)
        c2 : float = field(
            default=42.0,
            metadata={ConfigRecomputeMeta.KEY: ConfigRecomputeMeta(
                recompute_function_doc="doc",
                recompute_function_getter=ConfigRecomputeMixin.get_recompute(RECOMPUTE_FUNCTIONS, "r_func"),
                recompute_causes=["c1"]
            )}
        )
        c3 : int = field(...)
        ...

    C = Config()
    C.register()

    def r_func() -> float:
        # relies on C.c1 and returns recomputed value of c2
        return C.c1 * 42.0

    C.add_recompute(r_func)
    ```
    '''
    RECOMPUTE_FUNCTIONS : ClassVar[dict[str,Callable] | None] = None

    def add_recompute(self, r_func: Callable):
        '''
        Do `C.add_recompute(r_func)` to do `self.RECOMPUTE_FUNCTIONS[r_func.__name__] = r_func`.
        
        Here `C` is the config instance that owns the field to be recomputed,
        and `r_func` is the function that recomputes the config field.
        '''
        self.RECOMPUTE_FUNCTIONS[r_func.__name__] = r_func

    @classmethod  # abysmal crutch, but it's much better than reworking everything for a very narrow case
    def recompute_getter(cls, r_dict : dict[str,Callable], r_func_name : str) -> Callable[[], Callable]:
        '''
        Return lambda that returns RECOMPUTE_FUNCTIONS[r_func_name].

        Do `recompute_function=ConfigRecomputeMixin.get_recompute(RECOMPUTE_FUNCTIONS, r_func_name)` 
        inside config field's metadata, where `r_func_name` is the name of the function that recomputes the config field.
        '''
        return lambda : r_dict[r_func_name]


def get_tk_fields(config: LoadFromJsonMixin):
    """For a given config, return all fields with ConfigTkMeta.KEY in metadata"""
    return [f for f in fields(config) if ConfigTkMeta.KEY in f.metadata]


def build_field_editor(
        config_field: Field, 
        config_field_value: Any,
        master: tk.Misc, 
        button_kb_manager: ButtonKeyboardManager
    ) -> tk.StringVar:
    '''
    Using a `config_field` and its ConfigTkMeta, construct tk.Frame for display and edit and pack it into `master`.
    Return `tk.StringVar` to manage its value from the main app.
    `button_kb_manager` is used for entries that can be changed using a helper function.

    Notice that everything revolves around `json.dumps` and `json.loads`, that is, strings.
    This approach allows to greatly simplify widget selection, effectively converging it to tk.StringVar.
    Which can be linked to an Entry or an OptionMenu.
    '''
    # A frame to hold everything
    field_frame = tk.Frame(master)
    field_frame.pack(fill=tk.X, expand=True, padx=10, pady=15)

    # Gray separator
    tk.Frame(field_frame, height=2, background="gray").pack(fill=tk.X, expand=True)  

    meta: ConfigTkMeta = config_field.metadata.get(ConfigTkMeta.KEY)

    # Title, description
    _add_description_labels_with_tricky_overlay(field_frame, meta.doc, config_field.name, master)

    # A frame to hold everything related to an entry, horizontally
    entry_frame = tk.Frame(field_frame)
    entry_frame.pack(fill="x", expand=True)

    variable = tk.StringVar(value=json.dumps(config_field_value))

    def _set_feedback(value):
        variable.set(json.dumps(value))

    # Choose entry:

    # - recomputing
    recompute_meta : ConfigRecomputeMeta | None = config_field.metadata.get(ConfigRecomputeMeta.KEY, None)
    if recompute_meta:
        _add_recompute_entry(recompute_meta, config_field, entry_frame, variable, button_kb_manager, _set_feedback)
        return variable

    # - option selection
    if (isbool:=config_field.type is bool) or meta.option_listing:
        option_list = [json.dumps(False),json.dumps(True)] if isbool else [json.dumps(o) for o in meta.option_list]
        menu = tk.OptionMenu(entry_frame, variable, *option_list)
        menu.pack(side=tk.LEFT, anchor=tk.S)
        return variable

    # - string variable
    if config_field.type is str:
        variable = JsonStringVar()
        entry = tk.Entry(entry_frame, textvariable=variable)
        entry.pack(side=tk.LEFT, anchor=tk.S)
        return variable

    # - regular entry
    entry = tk.Entry(entry_frame, textvariable=variable)
    entry.pack(side=tk.LEFT, anchor=tk.S)

    # Augment regular entry:

    # - xy_read button
    if meta.xy_reading:
        btn_txt = "set from cursor coordinates"
        btn = tk.Button(entry_frame, text=btn_txt)
        btn.pack(side=tk.LEFT, anchor=tk.W, padx=5)
        btn.configure(command=button_kb_manager.build_command(btn, lambda: _get_xy_read(meta.xy_read), _set_feedback))
        before_proceeding = "move the cursor to where you want to read the coordinates"
        tk.Button(
            entry_frame,
            text=" ? ",
            command=lambda: messagebox.showinfo("Keyboard control after button press", KeypressPublisher.btn_doc(btn_txt, before_proceeding))
            ).pack(side=tk.LEFT, anchor=tk.W)
        return variable

    return variable


def _get_xy_read(xy_read: int | slice):
    x,y = pyautogui.position()
    return [x,y][xy_read]


def _add_description_labels_with_tricky_overlay(field_frame: tk.Misc, metadoc: str, config_field_name: str, master):
    '''
    To field_frame, pack a frame with two labels:
    - description: holds `meta.doc`. Intentionally starts with a newline, leaving enough space for a one-line title.
    - title: holds `config_field.name`. Binded leftclick to dispaly a hint image.

    Both labels are placed (not packed) to enable overlay.
    '''
    title_frame = tk.Frame(field_frame)
    title_frame.pack(anchor=tk.W)
    kw_label_make = {"wraplength": 400, "justify":"left"}

    description_label = tk.Label(title_frame, text=f"\n{metadoc}", **kw_label_make)
    description_label.place(x=0,y=0)

    name_label = tk.Label(title_frame, text=config_field_name, **kw_label_make)
    name_label.place(x=0,y=0)

    config_hint_img_path = os.path.join(IMG_DIR, "config_hints", f"{config_field_name}.png")

    def enigma_on_bind(e: tk.Event):
        '''
        No idea why, but doing `.bind(<Button-1>...` inside the `if os.path.isfile(...)` doesnt work. 
        And yet `enigma_on_bind` works...
        '''
        path = config_hint_img_path
        if os.path.isfile(path):
            caption = "Image shows where to look. Orange lines mark the target."
            show_image_modal(master.winfo_toplevel(), config_hint_img_path, config_field_name, caption)

    if os.path.isfile(config_hint_img_path):
        name_label.configure(cursor="hand2", text=f"{config_field_name} 🔍")
    
    name_label.bind("<Button-1>", enigma_on_bind)

    # Things below work, and yet the same things inside `if os.path...` dont???
    # name_label.bind("<Enter>", lambda e: print("entered name"))
    # name_label.bind("<Button-1>", lambda e: print("name clicked"))

    title_frame.configure(width=description_label.winfo_reqwidth(), height=description_label.winfo_reqheight())


def _add_recompute_entry(
        recompute_meta: ConfigRecomputeMeta, 
        config_field: Field, 
        entry_frame: tk.Frame, 
        variable: tk.StringVar, 
        button_kb_manager: ButtonKeyboardManager, 
        _set_feedback: Callable
    ):
    '''
    Builds non-editable entry for a field with recompute_meta and binds a button to keyboard listening. 
    Separated into its own function without much consideration.
    '''

    if len(recompute_meta.recompute_causes) > 0:
        conditions = (
            f"{config_field.name} shall be recomputed if one of the following config values was changed: {recompute_meta.recompute_causes}." +
            "\nProceed with recomputing once you are satisfied with all config values listed."
        )
        tk.Label(entry_frame, wraplength=400, justify="left", text=conditions, bg=ATTENTION_HIGHLIGHT).pack(anchor=tk.NW)

    entry = tk.Entry(entry_frame, textvariable=variable, state="readonly")
    entry.pack(side=tk.LEFT, anchor=tk.S)

    btn_txt = "recompute"
    btn = tk.Button(entry_frame, text = btn_txt)
    btn.pack(side=tk.LEFT, anchor=tk.W, padx=5)

    if recompute_meta.keyboard_independent:
        btn.configure(text="change")
        recompute_f = recompute_meta.recompute_function_getter()
        btn.configure(command=lambda: _set_feedback(recompute_f()))
        return #variable

    def _button_command():
        # TODO maybe add support for functions with arguments. need a modal window to get them though. 
        messagebox.showwarning("BEFORE PROCEEDING", recompute_meta.recompute_function_doc)
        cmd = button_kb_manager.build_command(btn, recompute_meta.recompute_function_getter(), _set_feedback)
        cmd()

    btn.configure(command=_button_command)    

    before_proceeding = "complete preparations that are displayed when the button is pressed"
    tk.Button(
        entry_frame,
        text=" ? ",
        command=lambda: messagebox.showinfo("Keyboard control after button press", KeypressPublisher.btn_doc(btn_txt, before_proceeding))
    ).pack(side=tk.LEFT, anchor=tk.W)
