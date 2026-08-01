import tkinter as tk
from tkinter import messagebox
import json


class JsonStringVar(tk.StringVar):
    """
    Expose pure strings to the user interface, while complying with how the app handles jsonification.
    An instance of this class is to be used as any tk.StringVar in the app's code that involves user interactions.

    Compared to types like int and float, only the strings expose unnecessary complexity to the user in form of escape sequences and surrounding quotation marks.
    Without `JsonStringVar`, you'd need a `jsonify` button that requires the user presses it each time they provide a new value.
    """

    def get(self):
        # adapt get() for json.loads that receives it
        pure_str = super().get() 
        return json.dumps(pure_str)

    def set(self, value: str):
        # adapt set() for received value=json.dumps
        pure_str = json.loads(value)
        super().set(pure_str)


def add_jsonify_button(entry_frame: tk.Frame, variable: tk.StringVar):
    '''
    JsonStringVar fallback for more complex types. 
    Adds a `jsonify` button to entries with string variables, to comply with how the app handles entries.
    '''
    tk.Button(
        entry_frame,
        text="jsonify",
        command=lambda var=variable: var.set(json.dumps(var.get())),  # counter lambda's closure on variable
        ).pack(side=tk.LEFT, anchor=tk.W, padx=5)
    tk.Button(
        entry_frame,
        text=" ? ",
        command=lambda: messagebox.showinfo(
            "Jsonify string values", 
            "For buttons saying 'jsonify':\n" \
            "- Provide a string value to the entry next to the button.\n" \
            "- Once satisfied with the value, click 'jsonify'\n" \
            "The button will change contents of the entry. Providing a jsonified version of the string immediately is possible but less practical.")
        ).pack(side=tk.LEFT, anchor=tk.W)