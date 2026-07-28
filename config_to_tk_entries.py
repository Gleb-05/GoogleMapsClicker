import time
import json
import keyboard
import pyautogui
from dataclasses import Field, field, dataclass, fields
import tkinter as tk
from tkinter import messagebox
from typing import ClassVar, Any
from collections.abc import Callable

from constants import ATTENTION_HIGHLIGH
from config_registry import ConfigRegistryMixin
from keypress_publisher import KeypressPublisher


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
    '''
    KEY: ClassVar[str] = "recompute"
    '''`metadata = { ConfigRecomputeMeta.KEY: ConfigRecomputeMeta(...) }` is the way to augment the dataclass field().'''
    recompute_function_doc: str
    recompute_function_getter: Callable[[], Callable]
    '''Returns `lambda: recompute_function`'''
    recompute_causes: list[str]


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
    class Config(ConfigRegistryMixin, ConfigRecomputeMixin):
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


class StringVarManager():
    '''
    Having multiple StringVars, choose one at a time to change its value using an arbitrary helper function (triggered by specific key presses).

    Attributes:
        :(not to be accessed directly)
        root: for thread safety, since keyboard is listening in a separate thread.
        long_operation_time_sec (default = 3) : if changing the value takes longer than that, 
            an info messagebox will show on operation finish.
    '''
    def __init__(self, master : tk.Misc,  kb_publisher : KeypressPublisher):
        super().__init__()
        self.master = master
        self.kb_publisher = kb_publisher
        self.long_operation_time_sec = 3

    def tk_after(self, f: Callable[[], Any]):
        def safe_f():
            try:
                f()
            except pyautogui.FailSafeException:
                messagebox.showinfo(message="GUI automation haulted")
            except Exception:
                messagebox.showwarning("EMERGENCY", "unexpected error")
                raise
        def inner():
            self.master.after(0, safe_f)
        return inner
    
    def configure(self, variable: tk.StringVar, new_value_getter: Callable[[], Any]):
        '''
        Generally, `new_value_getter` is `lambda: _get_new_value(*args, **kwargs)` 
        
        *Sometimes, it is `helper_function_getter()` (returns `helper_function` that returns `new_value` when executed)*
        
        - target: StringVar whose value is changed on proceeding with the operation..
        - new_value_getter: when executed (with no arguments), its return is to be put into the target StringVar.
        '''
        var_value = variable.get()  # TODO variable reverts to its first value on cancel

        def command():
            variable.set("AWAITS SHIFT / ESC")

            @self.tk_after
            def cancel():
                variable.set(var_value)
            
            @self.tk_after
            def proceed():
                variable.set(var_value)
                _s = time.perf_counter()
                value = new_value_getter()
                _e = time.perf_counter() - _s
                if _e > self.long_operation_time_sec:
                    messagebox.showinfo("Changing value", "Operation finished")  # UX for longer operations
                variable.set(json.dumps(value))

            self.kb_publisher.update_callbacks(proceed, cancel)

        return command


def get_tk_fields(config: ConfigRegistryMixin):
    """For a given config, return all fields with ConfigTkMeta.KEY in metadata"""
    return [f for f in fields(config) if ConfigTkMeta.KEY in f.metadata]


def build_field_editor(config_field: Field, master: tk.Misc, stringvar_manager: StringVarManager) -> tk.StringVar:
    '''
    Using a `config_field` and its ConfigTkMeta, construct tk.Frame for display and edit and pack it into `master`.
    Return `tk.StringVar` to manage its value from the main app.
    `stringvar_manager` is used for entries that can be changed using a helper function.

    Notice that everything revolves around `json.dumps` and `json.loads`, that is, strings.
    This approach allows to greatly simplify widget selection, effectively converging it to tk.StringVar.
    Which can be linked to an Entry or an OptionMenu.
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

    recompute_meta : ConfigRecomputeMeta | None = config_field.metadata.get(ConfigRecomputeMeta.KEY, None)
    if recompute_meta:
        conditions = (
            f"{config_field.name} shall be recomputed if one of the following config values was changed: {recompute_meta.recompute_causes}." +
            "\nProceed with recomputing once you are satisfied with all config values listed."
        )
        tk.Label(entry_frame, wraplength=400, justify="left", text=conditions, bg=ATTENTION_HIGHLIGH).pack(anchor=tk.NW)

        entry = tk.Entry(entry_frame, textvariable=variable, state="readonly")
        entry.pack(side=tk.LEFT, anchor=tk.S)
        btn_txt = "recompute"

        def _warn_and_request():
            # TODO maybe add support for functions with arguments. need a modal window to get them though. 
            messagebox.showwarning("BEFORE PROCEEDING", recompute_meta.recompute_function_doc)
            cmd = stringvar_manager.configure(variable, recompute_meta.recompute_function_getter())
            cmd()
        
        tk.Button(
            entry_frame,
            text = btn_txt,
            command = _warn_and_request
        ).pack(side=tk.LEFT, anchor=tk.W, padx=5)

        before_proceeding = "complete preparations that are displayed when the button is pressed"
        tk.Button(
            entry_frame,
            text=" ? ",
            command=lambda: messagebox.showinfo("HOWTO", KeypressPublisher.btn_doc(btn_txt, before_proceeding))
        ).pack(side=tk.LEFT, anchor=tk.W)

        return variable
    
    if (isbool:=config_field.type is bool) or meta.option_listing:
        option_list = [json.dumps(False),json.dumps(True)] if isbool else [json.dumps(o) for o in meta.option_list]
        menu = tk.OptionMenu(entry_frame, variable, *option_list)
        menu.pack(side=tk.LEFT, anchor=tk.S)

        return variable

    entry = tk.Entry(entry_frame, textvariable=variable)
    entry.pack(side=tk.LEFT, anchor=tk.S)

    if meta.xy_reading:
        btn_txt = "set from cursor coordinates"
        tk.Button(
            entry_frame, 
            text=btn_txt, 
            command=stringvar_manager.configure(variable, lambda: _get_xy_read(meta.xy_read))
            ).pack(side=tk.LEFT, anchor=tk.W, padx=5)
        before_proceeding = "move the cursor to where you want to read the coordinates"
        tk.Button(
            entry_frame,
            text=" ? ",
            command=lambda: messagebox.showinfo("HOWTO", KeypressPublisher.btn_doc(btn_txt, before_proceeding))
            ).pack(side=tk.LEFT, anchor=tk.W)

    return variable


def _get_xy_read(xy_read: int | slice):
    x,y = pyautogui.position()
    return [x,y][xy_read]
