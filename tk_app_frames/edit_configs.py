
import tkinter as tk
from dataclasses import Field
from gui.core_configs import C_search
from config_registry import get_tk_fields, _config_register, ConfigRegistryMixin, ConfigTkMeta


def make_config_frame(config: ConfigRegistryMixin, root: tk.Tk):
    tk_fields = get_tk_fields(config)
    config_frame = tk.Frame(root)
    for field in tk_fields:
        make_field_entry(field, config_frame).pack(fill=tk.X, expand=True)
    return config_frame

def make_field_entry(field: Field, master: tk.Misc):
    field_frame = tk.Frame(master)
    meta: ConfigTkMeta = field.metadata.get(ConfigTkMeta.KEY)
    tk.Entry(field_frame).pack(anchor=tk.W)
    tk.Label(field_frame, text=field.name, wraplength=400).pack(anchor=tk.W)
    tk.Label(field_frame, text=meta.doc, wraplength=400).pack(anchor=tk.W)
    return field_frame

class EditConfigsFrame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Prepare")
        self.W, self.H = root.winfo_screenwidth(), root.winfo_screenheight()
        self.root.minsize(300, 100)
        self.root.attributes("-topmost", True)

        self.configs = {C_search.REGISTER_KEY: make_config_frame(C_search, root)}
        self.config_names = list(self.configs.keys())
        self.current_config_name = C_search.REGISTER_KEY
        self.current_config_strvar = tk.StringVar(value=self.current_config_name)
        tk.OptionMenu(root, self.current_config_strvar, *self.config_names, command=self.show_frame).pack(pady=10)
        self.configs[self.current_config_name].pack(fill="both")
        
        # instruction = "Press NumLk (or alt+f2) after moving your cursor to a suitable position."
        # tk.Label(root, text=instruction, wraplength=300).pack(expand=True)

        self.label = tk.Label(root, text="Log Label", wraplength=300)
        self.label.pack()

    def show_frame(self, name):
        self.configs[self.current_config_name].pack_forget()
        self.configs[name].pack(fill="both")
        self.current_config_name = name
        self.root.update_idletasks()


if __name__ == "__main__":
    root = tk.Tk()
    app = EditConfigsFrame(root)
    root.mainloop()
