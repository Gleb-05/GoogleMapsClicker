
import tkinter as tk
from tk_app_frames.BasicFrame import BasicFrame
from dataclasses import Field
# from gui.core_configs import C_search
import usr_get_area_img  # crutch to get all necessary configs
from config_registry import get_tk_fields, _config_register, ConfigRegistryMixin, ConfigTkMeta


def make_config_frame(config: ConfigRegistryMixin, master: tk.Misc):
    tk_fields = get_tk_fields(config)
    config_frame = tk.Frame(master)
    for field in tk_fields:
        make_field_entry(field, config_frame).pack(fill=tk.X, expand=True, padx=10, pady=10)
    return config_frame

def make_field_entry(field: Field, master: tk.Misc):
    field_frame = tk.Frame(master)
    tk.Frame(field_frame, height=1, background="gray").pack(fill=tk.X, expand=True, pady=(0,5))
    meta: ConfigTkMeta = field.metadata.get(ConfigTkMeta.KEY)
    tk.Entry(field_frame).pack(anchor=tk.W)
    kw_label_make = {"master": field_frame, "wraplength": 400, "justify":"left"}
    tk.Label(text=field.name, **kw_label_make).pack(anchor=tk.W)
    tk.Label(text=meta.doc,   **kw_label_make).pack(anchor=tk.W)
    return field_frame

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

        # self.configs = {C_search.REGISTER_KEY: make_config_frame(C_search, self.body)}
        self.configs = {KEY: make_config_frame(config, self.body) for KEY, config in _config_register.items()}
        self.config_names = list(self.configs.keys())
        self.current_config_name = self.config_names[0]
        self.current_config_strvar = tk.StringVar(value=self.current_config_name)
        tk.OptionMenu(self.body, self.current_config_strvar, *self.config_names, command=self.show_frame).pack(side="top", anchor="center", pady=10)
        self.configs[self.current_config_name].pack(fill="both")

        # self.label = tk.Label(self.body, text="Log Label"*20, wraplength=500)
        # self.label.pack()
     
        self.update_root_geometry()

    def show_frame(self, name):
        self.configs[self.current_config_name].pack_forget()
        self.configs[name].pack(fill="both")
        self.current_config_name = name
        self.update_root_geometry()


if __name__ == "__main__":
    tk_root = tk.Tk()
    app = EditConfigsFrame(tk_root)
    tk_root.mainloop()
