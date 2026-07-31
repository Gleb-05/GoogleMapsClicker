import inspect
import json
import tkinter as tk
from tkinter import messagebox
from typing import Any
from collections.abc import Callable

from z_app_components.keypress_publisher import KeypressPublisher, ButtonKeyboardManager, TargetFunctionError
from z_app_components.config_to_tk_entries import _add_jsonify_button

def build_function_editor(
        target_function: Callable[..., Any], 
        master: tk.Misc, 
        button_kb_manager: ButtonKeyboardManager,
        set_feedback: Callable[[Any], None] | None
    ) -> list[tk.StringVar]:
    '''
    Using `inspect.signature(target_function)` to fetch a docstring and generate entries for its arguments, 
    construct tk.Frame for a given function and pack it into `master`.
    Return a list of variables that correspond to `target_function` arguments to manage them from the main app.
    `button_kb_manager` is used for each function to support execution on keypress.
    '''
    
    field_frame = tk.Frame(master)
    field_frame.pack(fill=tk.X, expand=True, padx=10, pady=15)

    tk.Frame(field_frame, height=2, background="gray").pack(fill=tk.X, expand=True)

    f_signature = inspect.signature(target_function)

    kw_label_make = {"master": field_frame, "wraplength": 400, "justify":"left"}
    _heading = target_function.__name__.replace("_"," ").capitalize()
    tk.Label(text=f"{_heading}\n\n{inspect.getdoc(target_function)}\n", **kw_label_make).pack(anchor=tk.W)

    kwarg_stringvars : dict[str, tk.StringVar] = {}
    for argname, argvalue in f_signature.parameters.items():
        entry_frame = tk.Frame(field_frame)
        entry_frame.pack(fill="x", expand=True, pady=(0,5))

        variable = tk.StringVar(value=json.dumps(argvalue.default) if argvalue.default is not inspect.Parameter.empty else None)
        kwarg_stringvars[argname] = variable

        if argvalue.annotation is bool:
            option_list = [json.dumps(False),json.dumps(True)]
            menu = tk.OptionMenu(entry_frame, variable, *option_list)
            menu.pack(side=tk.LEFT, anchor=tk.W)
        else:
            entry = tk.Entry(entry_frame, textvariable=variable)
            entry.pack(side=tk.LEFT, anchor=tk.W)

        if argvalue.annotation is str:
            _add_jsonify_button(entry_frame, variable)

        tk.Label(
            text=f"{argname} ({argvalue.annotation.__name__})", **{**kw_label_make, "master": entry_frame}
            ).pack(side=tk.LEFT,anchor=tk.W)

    _add_execute_kb_button(field_frame, kwarg_stringvars, target_function, button_kb_manager, set_feedback)

    return list(kwarg_stringvars.values())


def _add_execute_kb_button(
        field_frame: tk.Misc, 
        kwarg_stringvars: dict[str, tk.StringVar], 
        target_function: Callable, 
        button_kb_manager: ButtonKeyboardManager,
        set_feedback: Callable
    ):
    '''
    Packs an 'execute' button into field_frame. The button:
    listens to the keyboard, binds to execute target_function with values from kwarg_stringvars, binds to set_feedback if returns anything.
    Also adds a 'howto' button nearby.
    '''
    btn_txt = "execute"
    btn = tk.Button(field_frame, text=btn_txt)
    btn.pack(side=tk.BOTTOM, anchor=tk.CENTER, padx=5)

    def _target_function():
        try:
            kwargs = {kw: json.loads(var.get()) for kw, var in kwarg_stringvars.items()}
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON ERROR ON FUNCTION CALL", str(e))
            raise TargetFunctionError from e
        return target_function(**kwargs)

    f_return_annotation = inspect.signature(target_function).return_annotation
    _set_feedback = None if f_return_annotation is inspect.Signature.empty else set_feedback

    button_command = button_kb_manager.build_command(btn, _target_function, _set_feedback, hide_app_on_proceed=True)
    btn.configure(command=button_command)

    tk.Button(
        field_frame,
        text=" ? ",
        command=lambda: messagebox.showinfo("HOWTO", KeypressPublisher.btn_doc(btn_txt) + '\n- If you wish to hault the operation, quickly move your cursor to one of the screen corners and wait for the `GUI automation haulted` message.')
        ).pack(side=tk.BOTTOM, anchor=tk.CENTER)
