import json
from dataclasses import Field, dataclass, field, fields
import tkinter as tk
from typing import ClassVar

from config_registry import ConfigRegistryMixin


@dataclass(frozen=True)
class ConfigTkMeta:
    """A bridge between config code and user control.

    - doc: str - guiding or explaining text alongside the config value
    - xy_read: if (0,0), this config value shall not be set by a user via reading cursor coordinates.
                 otherwise, specify which coordinate shall be stored - x (1,0), y (0,1), or both (1,1)

    Additionaly, a KEY: ClassVar[str] = "tk" is specified for consistency.

    - xy_reading is a property to quickly filter config values that do not requre xy reading - not to be set in code.
    """
    KEY: ClassVar[str] = "tk"
    """`metadata = { ConfigTkMeta.KEY: ConfigTkMeta(...) }` is the way to augment the dataclass field()."""

    doc: str
    xy_read: tuple[int, int] = (0,0)
    @property
    def xy_reading(self):
        return self.xy_read == (0,0)


def get_tk_fields(config: ConfigRegistryMixin):
    """For a given config, return all fields with ConfigTkMeta.KEY in metadata"""
    return [f for f in fields(config) if ConfigTkMeta.KEY in f.metadata]


def field_entry_w_variable(config_field: Field, master: tk.Misc) -> tk.Variable:
    '''
    Using a `config_field` and its ConfigTkMeta, construct tk.Frame for display and edit and pack it into `master`.
    Return `tk.Variable` to track its value in the main app.
    '''
    field_frame = tk.Frame(master)
    field_frame.pack(fill=tk.X, expand=True, padx=10, pady=10)

    tk.Frame(field_frame, height=1, background="gray").pack(fill=tk.X, expand=True)

    meta: ConfigTkMeta = config_field.metadata.get(ConfigTkMeta.KEY)
    kw_label_make = {"master": field_frame, "wraplength": 400, "justify":"left"}
    tk.Label(text=f"{config_field.name}\n{meta.doc}",   **kw_label_make).pack(anchor=tk.W)

    variable = tk.StringVar(value=json.dumps(config_field.default))
    entry = tk.Entry(field_frame, textvariable=variable)
    entry.pack(anchor=tk.W)

    return variable