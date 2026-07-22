import json
import tkinter as tk
from tkinter import messagebox
from tk_app_frames.BasicFrame import BasicFrame
from typing import NamedTuple
from utils import CustomError
import usr_get_area_img  # crutch to get all necessary configs
# from usr_get_area_img import C
from config_registry import _config_register, ConfigRegistryMixin, dump_config, load_config_from_dict, load_config
from config_to_tk_entries import get_tk_fields, build_field_editor, XYReadManager

class FrameAndVariables(NamedTuple):
    '''Variables tightly coupled with a frame that contains them'''
    frame: tk.Frame
    variables: dict[str, tk.StringVar]


class EditConfigsFrame(BasicFrame):
    '''See and change individual fields of configs'''
    def __init__(self, root: tk.Tk):
        super().__init__(root)
        self.root = root
        self.root.title("Prepare")
        self.W, self.H = root.winfo_screenwidth(), root.winfo_screenheight()
        self.root.minsize(300, 100)
        self.root.attributes("-topmost", True)

        tk.Frame(self.body, width=BasicFrame.MAX_WIDTH-140).pack()  # crutch to standardize the width of different windows

        self.xy_read_manager = XYReadManager(self.root)
        self.configs = {
            key: config_frame_and_variables
            for key, config in _config_register.items()
            if (config_frame_and_variables:=self._frame_and_variables(config)) is not None
        }
        self.config_names = list(self.configs.keys())
        self.current_config_name = self.config_names[0]

        def switch_frame(name):
            self.configs[self.current_config_name].frame.pack_forget()
            self.configs[name].frame.pack(fill="both")
            self.current_config_name = name
            self.update_root_geometry()
        option_menu_highlight = tk.Frame(self.body, background="white")
        option_menu_highlight.pack(fill="x", expand=True, pady=10)
        tk.OptionMenu(option_menu_highlight, 
                tk.StringVar(value=self.current_config_name), 
                *self.config_names, 
                command=switch_frame
                ).pack(anchor="center", pady=10)

        self.configs[self.current_config_name].frame.pack(fill="both")
     
        # TODO Apply button for when the entries have changed but the config did not
        tk.Button(self.footer, text="Save to file", command=self._save_to_file).pack(side="right")
        tk.Button(self.footer, text="Load from file", command=self._load_from_file).pack(side="right", padx=5)
        tk.Button(self.footer, text="Load default", command=self._load_default).pack(side="right")

        self.update_root_geometry()

    def _frame_and_variables(self, config: ConfigRegistryMixin) -> FrameAndVariables | None:
        tk_fields = get_tk_fields(config)
        if len(tk_fields) == 0:
            return None
        config_frame = tk.Frame(self.body)
        variables = {}
        for field in tk_fields:
            variables[field.name] = build_field_editor(field, config_frame, self.xy_read_manager) 
        return FrameAndVariables(config_frame, variables)

    def _save_to_file(self):
        config_dict = {
            key: 
            {field: json.loads(tkvar.get()) for field, tkvar in config.variables.items()} 
            for key, config in self.configs.items()
        }
        try:
            load_config_from_dict(config_dict)
            # TODO unique file name
            dump_config("usr_configs/gui_config.json")
            messagebox.showinfo(message="SAVE SUCCESSFUL")
        except CustomError as e:
            messagebox.showerror("BAD NEW VALUES", str(e))

    def _load_default(self):
        load_config()
        self._reload_variables()

    def _load_from_file(self):
        # TODO file selection
        self._reload_variables()

    def _reload_variables(self):
        for key, config in _config_register.items():
            if key not in self.configs:
                continue
            for field, tkvar in self.configs[key].variables.items():
                tkvar.set(json.dumps(getattr(config, field)))
        messagebox.showinfo(message="LOAD SUCCESSFUL")

if __name__ == "__main__":
    tk_root = tk.Tk()
    app = EditConfigsFrame(tk_root)
    tk_root.mainloop()
