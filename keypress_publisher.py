import keyboard
from typing import Any, TypeVar
from collections.abc import Callable


class KeypressPublisher():
    '''
    Listen for "cancelling" and "proceeding" key presses with `keyboard.hook` to execute 
    `proceed` and `cancel` callbacks. Those shall be set via the `update_callbacks` method.

    "cancelling": "esc" <br>
    "proceeding": "shift", "right shift", "left shift", "num lock"

    For example, reading cursor coordinates requires something beyond button press or mouse click.
    '''

    @classmethod
    def btn_doc(cls, btn_txt, before_proceeding="complete preparations that the operation requires"):
        _doc = "For buttons saying '{}'," \
        "\n- press the button to initiate the operation and choose between proceeding and cancelling," \
        "\n- to proceed, press Shift (or NumLk)" \
        "\n- before proceeding, {}" \
        "\n- to cancel, press Esc."
        return _doc.format(btn_txt, before_proceeding)
    
    cancel_keys = ["esc"]
    proceed_keys = ["shift", "right shift", "left shift", "num lock"]

    def __init__(self):
        self.proceed : Callable[[], Any] | None = None
        self.cancel  : Callable[[], Any] | None = None

        for key in self.cancel_keys:
            keyboard.on_press_key(key, self._on_cancel)
        for key in self.proceed_keys:
            keyboard.on_press_key(key, self._on_proceed)

    def update_callbacks(self, proceed : Callable[[], Any], cancel : Callable[[], Any]):
        '''
        Provide two callbacks for KeypressPublisher to execute when either cancelling or proceeding keys are pressed.
        After execution, the hooks will be cleared, so the callbacks work only once.
        '''
        if self.cancel is not None:
            self.cancel()
        self.proceed = proceed
        self.cancel = cancel

    def _clear(self):
        '''Clear the hooks after any key press (the callbacks shall work only once)'''
        self.proceed = None
        self.cancel = None

    def _on_proceed(self, _ : keyboard.KeyboardEvent):
        '''Execute current `proceed` callback and clear the hooks.'''
        if self.proceed is None:
            return
        self.proceed()
        self._clear()

    def _on_cancel(self, _ : keyboard.KeyboardEvent):
        "hook-compliant signature for `on_cancel`"
        self.on_cancel()

    def on_cancel(self):
        '''
        Execute current `cancel` callback and clear the hooks. 
        Useful when the callbacks should be forgotten at major UI changes.
        '''
        if self.cancel is None:
            return
        self.cancel()
        self._clear()


import tkinter as tk
from tkinter import messagebox
import time
import pyautogui

from constants import ATTENTION_HIGHLIGHT


class TargetFunctionError(Exception):
    '''Raise it at the end of handling exceptions in more complex target functions.'''


class ButtonKeyboardManager():
    '''
    Using an instance of this class, build a command out of button's target_function 
    that will support a centralized "cancel-proceed" keypress workflow (only one command can work at a time).
    See KeypressPublisher for a list of "cancelling" and "proceeding" keys.
   
    Attributes:
        master: for thread-safe `master.after(0, proceed_callback)`, since keyboard hooks works in a separate thread.
        kb_publisher: an app-wide single instance of KeyboardPublisher.
            Used for `self.kb_publisher.update_callbacks(proceed, cancel)` in the button command.
        long_operation_time_sec (default = 3) : if target_function takes longer than that, 
            an info messagebox will show when it's finished.
    
    Used like this:
    ```python
    root = tk.Tk()
    kb_publisher = KeyboardPublisher()
    button_kb_manager = ButtonKeyboardManager(root, kb_publisher)

    entry = tk.Entry(root)
    entry.pack()

    label = tk.Label(root, text="")
    label.pack()

    def target_function():
        input_value = entry.get()
        output_value = f"entry says '{input_value}'"
        
    def set_feedback(value: str)
        label.config(text=value)

    button = tk.Button(root, text="do stuff")
    button.pack()
    button.configure(command=button_kb_manager.build_command(
        button, target_function, set_feedback)
    )

    root.mainloop()
    ```
    '''

    long_operation_time_sec = 3
    T = TypeVar("ValueType")

    def __init__(self, master: tk.Misc, kb_publisher : KeypressPublisher):
        super().__init__()
        self.master = master
        self.kb_publisher = kb_publisher


    def tk_after(self, operation: Callable[[], Any]):
        '''Decorator to make callbacks from `cancel` and `proceed` button commands'''
        toplevel = self.master.winfo_toplevel()
        def safe_f():
            err = None
            msgbox_kwargs = {}
            try:
                operation()
            except pyautogui.FailSafeException as e:
                err = e
                msgbox_kwargs = dict(message="GUI automation haulted")
            except TimeoutError as e:
                err = e
                msgbox_kwargs = dict(message=f"{e}\n\nMost likely, the browser didn't receive focus or froze for too long")
            except Exception as e:
                err = e
                msgbox_kwargs = dict(title="EMERGENCY", message=f"unexpected error\n\n{e}")
                raise
            finally:
                if err is not None:
                    # messagebox has to be before toplevel.after, otherwise one of them doesnt appear
                    messagebox.showwarning(**msgbox_kwargs)
                toplevel.after(10, toplevel.deiconify)  # in case of `hide_app_on_proceed is True`
        def inner():
            self.master.after(0, safe_f)
        return inner


    def build_command(
            self, 
            button: tk.Button, 
            target_function: Callable[[], T], 
            set_feedback: Callable[[T],None] | None,
            hide_app_on_proceed: bool = False
        ):
        '''
        Returns a button_command. Can be combined with messagebox if the target_function requires warning or info.
        Use: `button.configure(command=button_kb_manager.build_command(button, target_function, set_feedback)`

        Returned command additionally supports a pyatogui failsafe. 
        Quickly bring your cursor to one of the screen corners to hault target functions for GUI automation.
        
        Args:
            button: would have `command=target_function` if not for the keypress workflow. 
                Will be highlighted to signify that the choice between "cancel" and "proceed" is active.
            
            target_function: Most often returns a `value`, but can also return None. Takes no arguments.
                If target_function includes exceptions, add `raise TargetFunctionException` at the end of them.
                They will be caught during proceed callback to safely terminate it.  
                *Generally, `target_function` is `lambda: _get_new_value(*args, **kwargs)`.
                Sometimes, it is `helper_function_getter()` (returns `helper_function` that returns `new_value` when executed)*  

            set_feedback (optional): If provided, shall put `value` from the `target_function` somewhere in the interface.
                Shall take responsibility for converting the `value` into its suitable representation.
                Examples: `text.insert("1.0", str(value))` or `variable.set(json.dumps(value))`.

            hide_app_on_proceed (default=False): some target functions will require that the app is minimized (hidden)
                and doesn't obstruct the screen. Those shall pass `True` to the `hide_app_on_proceed`.
                The app will reappear once the target_function is done.
        '''

        bg = button["bg"]
        toplevel = self.master.winfo_toplevel()

        def button_command():
            button.configure(bg=ATTENTION_HIGHLIGHT)

            @self.tk_after
            def cancel():
                button.configure(bg=bg)
            
            @self.tk_after
            def proceed():
                if hide_app_on_proceed:
                    toplevel.withdraw()
                    toplevel.iconify()  # steals focus without the withdraw
                    toplevel.update()
                
                button.configure(bg=bg)
                _s = time.perf_counter()
                try:
                    value = target_function()
                except TargetFunctionError:
                    return
                _e = time.perf_counter() - _s
                if _e > ButtonKeyboardManager.long_operation_time_sec:
                    messagebox.showinfo("Executing function", "Operation finished")  # UX for longer operations
                if set_feedback is not None:
                    set_feedback(value)
            
            self.kb_publisher.update_callbacks(proceed, cancel)

        return button_command
