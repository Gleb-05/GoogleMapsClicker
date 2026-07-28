import time
import inspect
import json
import tkinter as tk
from tkinter import messagebox
from typing import Any
from collections.abc import Callable
import pyautogui

from constants import ATTENTION_HIGHLIGH
from keypress_publisher import KeypressPublisher

class ButtonManager():
    '''
    Having multiple buttons, choose one at a time to execute the target function 
    with arguments equal to values of linked tk variables (triggered by specific key presses)
    '''

    def __init__(self, master: tk.Misc, kb_publisher : KeypressPublisher, text: tk.Text):
        super().__init__()
        self.master = master
        self.kb_publisher = kb_publisher
        self.text = text
        self.long_operation_time_sec = 3

    def tk_after(self, f: Callable[[], Any]):
        def safe_f():
            try:
                self.master.winfo_toplevel().iconify()
                f()
            except pyautogui.FailSafeException:
                messagebox.showinfo(message="GUI automation haulted")
            except Exception:
                messagebox.showwarning("EMERGENCY", "unexpected error")
                raise
            finally:
                self.master.winfo_toplevel().deiconify()
        def inner():
            self.master.after(0, safe_f)
        return inner


    def configure(self, button: tk.Button, target_function: Callable[..., Any], kwarg_stringvars: dict[str, tk.StringVar]):
        bg = button["bg"]

        def button_command():
            button.configure(bg=ATTENTION_HIGHLIGH)

            @self.tk_after
            def cancel():
                button.configure(bg=bg)
            
            @self.tk_after
            def proceed():
                button.configure(bg=bg)
                try:
                    kwargs = {kw: json.loads(var.get()) for kw, var in kwarg_stringvars.items()}
                except json.JSONDecodeError as e:
                    messagebox.showerror("JSON ERROR ON FUNCTION CALL", str(e))
                    return
                _s = time.perf_counter()
                value = target_function(**kwargs)
                _e = time.perf_counter() - _s
                if _e > self.long_operation_time_sec:
                    messagebox.showinfo("Executing function", "Operation finished")  # UX for longer operations
                self.text.delete("1.0", tk.END)
                self.text.insert("1.0", str(value))
            
            self.kb_publisher.update_callbacks(proceed, cancel)

        button.configure(command=button_command)


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
    button_manager.configure(btn, target_function, kwarg_stringvars)
    btn.pack(side=tk.BOTTOM, anchor=tk.CENTER, padx=5)

    tk.Button(
        field_frame,
        text=" ? ",
        command=lambda: messagebox.showinfo("HOWTO", KeypressPublisher.btn_doc(btn_txt))
        ).pack(side=tk.BOTTOM, anchor=tk.CENTER)

    return list(kwarg_stringvars.values())
