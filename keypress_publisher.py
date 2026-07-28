import keyboard
from typing import Any
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
