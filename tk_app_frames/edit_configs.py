
import tkinter as tk
from tk_app_frames.BasicFrame import BasicFrame
from dataclasses import Field
from typing import NamedTuple
# from gui.core_configs import C_search
import usr_get_area_img  # crutch to get all necessary configs
from config_registry import get_tk_fields, _config_register, ConfigRegistryMixin, ConfigTkMeta


class FrameWithVariables(NamedTuple):
    '''Variables tightly coupled with a frame that contains them'''
    frame: tk.Frame
    variables: dict[str, tk.Variable]


def field_entry_w_variable(field: Field, master: tk.Misc) -> tk.Variable:
    field_frame = tk.Frame(master)
    field_frame.pack(fill=tk.X, expand=True, padx=10, pady=10)

    tk.Frame(field_frame, height=1, background="gray").pack(fill=tk.X, expand=True, pady=(0,5))
    
    variable = tk.StringVar(value=str(field.default))
    entry = tk.Entry(field_frame, textvariable=variable)
    entry.pack(anchor=tk.W)
    
    meta: ConfigTkMeta = field.metadata.get(ConfigTkMeta.KEY)
    kw_label_make = {"master": field_frame, "wraplength": 400, "justify":"left"}
    tk.Label(text=field.name, **kw_label_make).pack(anchor=tk.W)
    tk.Label(text=meta.doc,   **kw_label_make).pack(anchor=tk.W)
    return variable

class EditConfigsFrame(BasicFrame):
    '''See and change individual fields of configs'''
    def __init__(self, root: tk.Tk):
        super().__init__(root)
        self.root = root
        self.root.title("Prepare")
        self.W, self.H = root.winfo_screenwidth(), root.winfo_screenheight()
        self.root.minsize(300, 100)
        self.root.attributes("-topmost", True)

        instruction = "Press NumLk (or alt+f2) after moving your cursor \n to a suitable position."
        tk.Label(self.header, text=instruction, wraplength=300).pack(expand=True)

        self.configs = {
            key: config_frame_and_entries
            for key, config in _config_register.items()
            if (config_frame_and_entries:=self._frame_with_variables(config)) is not None
        }
        self.config_names = list(self.configs.keys())
        self.current_config_name = self.config_names[0]

        def switch_frame(name):
            self.configs[self.current_config_name].frame.pack_forget()
            self.configs[name].frame.pack(fill="both")
            self.current_config_name = name
            self.update_root_geometry()
        tk.OptionMenu(self.body, 
                tk.StringVar(value=self.current_config_name), 
                *self.config_names, 
                command=switch_frame
                ).pack(side="top", anchor="center", pady=10)

        self.configs[self.current_config_name].frame.pack(fill="both")
     
        tk.Button(self.footer, text="Save to file").pack(side="right")
        tk.Button(self.footer, text="Load from file").pack(side="right", padx=5)
        tk.Button(self.footer, text="Load default").pack(side="right")

        self.update_root_geometry()

    def _frame_with_variables(self, config: ConfigRegistryMixin) -> FrameWithVariables | None:
        tk_fields = get_tk_fields(config)
        if len(tk_fields) == 0:
            return None
        config_frame = tk.Frame(self.body)
        variables = {}
        for field in tk_fields:
            variables[field.name] = field_entry_w_variable(field, config_frame) 
        return FrameWithVariables(config_frame, variables)



if __name__ == "__main__":
    tk_root = tk.Tk()
    app = EditConfigsFrame(tk_root)
    tk_root.mainloop()
