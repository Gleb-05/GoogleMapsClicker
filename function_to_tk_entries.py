import time
import inspect
import json
import tkinter as tk
from tkinter import messagebox
from typing import Any
from collections.abc import Callable

from constants import ATTENTION_HIGHLIGH
from utils import KeyboardControlManager

class ButtonManager(KeyboardControlManager):
    '''
    Having multiple buttons, choose one at a time to execute the target function 
    with arguments equal to values of linked tk variables (triggered by specific key presses)
    '''

    def __init__(self, text: tk.Text):
        super().__init__()
        self.text = text
        self.button: tk.Button | None = None
        self.button_background: str | None = None
        self.target_function: Callable[..., Any] | None = None
        self.kwarg_stringvars: dict[str, tk.StringVar] | None = None
        self.long_operation_time_sec = 3

    def _nullify(self):
        self.button = None
        self.button_background = None
        self.kwarg_stringvars = None
        self.target_function = None

    def request(self, button: tk.Button, target_function: Callable[..., Any], kwarg_stringvars: dict[str, tk.StringVar]):
        if self.button is not None:
            # new button was pressed immediately after, restore value of previously pressed button
            self.button.configure(bg=self.button_background)
        self.button = button
        self.button_background = button['bg']
        self.button.configure(bg=ATTENTION_HIGHLIGH)
        self.target_function = target_function
        self.kwarg_stringvars = kwarg_stringvars

    def _on_key(self, event):
        '''
        if target function was not set using `request` - nothing.
        else if Esc - cancel the operation.
        else if Shift or NumLk - proceed with target_function(**kwargs).
        '''
        if self.target_function is None:
            return

        if self.cancelling(event):
            self.button.configure(bg=self.button_background)  # undo `button.configure` in `request`
            self._nullify()
            return
        
        if self.proceeding(event):
            kwargs = {kw: json.loads(var.get()) for kw, var in self.kwarg_stringvars.items()}
            _s = time.perf_counter()
            value = self.target_function(**kwargs)
            _e = time.perf_counter() - _s
            if _e > self.long_operation_time_sec:
                messagebox.showinfo("Executing function", "Operation finished")  # UX for longer operations
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", str(value))
            
            _button = self.button
            _bg = self.button_background
            self.text.after(0, lambda: _button.configure(bg=_bg))  # thread-save
            self._nullify()


def build_function_editor(target_function: Callable[..., Any], master: tk.Misc, button_manager: ButtonManager):
    field_frame = tk.Frame(master)
    field_frame.pack(fill=tk.X, expand=True, padx=10, pady=15)

    tk.Frame(field_frame, height=2, background="gray").pack(fill=tk.X, expand=True)

    f_signature = inspect.signature(target_function)

    kw_label_make = {"master": field_frame, "wraplength": 400, "justify":"left"}
    tk.Label(text=f"{target_function.__name__}\n\n{inspect.getdoc(target_function)}\n", **kw_label_make).pack(anchor=tk.W)

    kwarg_stringvars : dict[str, tk.StringVar] = {}
    for argname, argvalue in f_signature.parameters.items():
        entry_frame = tk.Frame(field_frame)
        entry_frame.pack(fill="x", expand=True)

        variable = tk.StringVar(value=json.dumps(argvalue.default) if argvalue.default is not inspect.Parameter.empty else None)
        kwarg_stringvars[argname] = variable

        if argvalue.annotation is bool:
            option_list = [json.dumps(False),json.dumps(True)]
            menu = tk.OptionMenu(entry_frame, variable, *option_list)
            menu.pack(side=tk.LEFT, anchor=tk.S)
        else:
            entry = tk.Entry(entry_frame, textvariable=variable)
            entry.pack(side=tk.LEFT, anchor=tk.S)

        tk.Label(
            text=f"{argname} ({argvalue.annotation.__name__})", **{**kw_label_make, "master": entry_frame}
            ).pack(side=tk.LEFT,anchor=tk.W)

    btn_txt = "execute"
    btn = tk.Button(field_frame, text=btn_txt)
    btn.configure(command = lambda: button_manager.request(
        btn, target_function, kwarg_stringvars)
    )
    btn.pack(side=tk.BOTTOM, anchor=tk.CENTER, padx=5)

    tk.Button(
        field_frame,
        text=" ? ",
        command=lambda: messagebox.showinfo("HOWTO", button_manager.doc(btn_txt))
        ).pack(side=tk.BOTTOM, anchor=tk.CENTER)

    return list(kwarg_stringvars.values())
