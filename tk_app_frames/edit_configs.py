import os
import json
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tk_app_frames.BasicFrame import BasicFrame
from tk_app_frames.SwitchFrameController import setup_switch_frame_controller, FrameAndVariables

from constants import ROOT_DIR
from utils import CustomError
import usr_get_area_img  # crutch to get all necessary configs
# from usr_get_area_img import C
from config_registry import _config_register, ConfigRegistryMixin, dump_config, load_config_from_dict, load_config
from config_to_tk_entries import get_tk_fields, build_field_editor, StringVarManager
from keypress_publisher import KeypressPublisher


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

        kb_publisher = KeypressPublisher()
        self.stringvar_manager = StringVarManager(self.root, kb_publisher)  # maybe move from EditConfigsFrame to somewhere higher in hierarchy? plus not necessary to use exactly root

        # Store (tk frame to render)-(tk variables to set and get values) pairs for each config
        self.configs = {
            key: config_frame_and_variables
            for key, config in _config_register.items()
            if (config_frame_and_variables:=self._frame_and_variables(config)) is not None
        }
        setup_switch_frame_controller(self.configs, self.body, lambda: (self.update_root_geometry(), kb_publisher.on_cancel()))

        # Add buttons to work with config files and the currently used config itself.
        self._last_used_path_to_config = "default_1366x768_config.json"
        tk.Button(self.footer, text="Save to file", command=self._save_to_file).pack(side="right")
        tk.Button(self.footer, text="Save changes", command=self._save_changes).pack(side="right", padx=5)
        tk.Button(self.footer, text="Load from file", command=self._load_from_file).pack(side="right")

        self.update_root_geometry()


    def _frame_and_variables(self, config: ConfigRegistryMixin) -> FrameAndVariables | None:
        tk_fields = get_tk_fields(config)
        if len(tk_fields) == 0:
            return None
        config_frame = tk.Frame(self.body)
        variables = {}
        for field in tk_fields:
            variables[field.name] = build_field_editor(field, config_frame, self.stringvar_manager) 
        return FrameAndVariables(config_frame, variables)


    def _save_changes(self, showbox = True):
        '''Update config registry by iterating over tk variables. Return True on success'''
        bad_key = ""
        bad_field = ""
        try:
            # config_dict = {
            #     key: 
            #     {fieldname: json.loads(tkvar.get()) for fieldname, tkvar in config.variables.items()} 
            #     for key, config in self.configs.items()
            # }
            config_dict = {}
            for key, config in self.configs.items():
                bad_key = key
                field_values = {}
                for fieldname, tkvar in config.variables.items():
                    bad_field = fieldname  # awkward loops to get to the field that caused the json error
                    field_values[fieldname] = json.loads(tkvar.get())
                config_dict[key] = field_values

            load_config_from_dict(config_dict)
            if showbox: 
                messagebox.showinfo(message="SAVE SUCCESSFUL")
            return True
        
        except (json.JSONDecodeError) as e:
            messagebox.showerror("VALUES INCOMPLETE OR MISSING", f"{bad_key}: {bad_field}\n{str(e)}")
            return False
        except (CustomError) as e:
            messagebox.showerror("BAD NEW VALUES", f"{bad_key}: {str(e.original_e)}")
            print(e)  # for developers
            return False


    def _get_config_name(self, title: str, save: bool):
        '''Returns filename of config, selected by user from a filedialog. Savedialog if `save=True`, else opendialog.'''
        dialog = filedialog.asksaveasfilename if save else filedialog.askopenfilename
        return dialog(
            title=title,
            defaultextension=".json",
            filetypes=[("json", ["*.json","*.JSON"])],
            initialdir=os.path.join(ROOT_DIR, "usr_configs"),
            initialfile=self._last_used_path_to_config
        )


    def _save_to_file(self):
        '''Update config registry and save to file of choice'''
        if self._save_changes(showbox=False) is False:  # new config values were rejected
            return
        
        path_to_config = self._get_config_name("Save config to json file", save=True)
        if len(path_to_config) == 0:  # selection was cancelled
            return
        
        try:
            dump_config(path_to_config)
            messagebox.showinfo(message="FILESAVE SUCCESSFUL")
            self._last_used_path_to_config = path_to_config

        except CustomError as e:
            messagebox.showerror("ERROR ON CONFIG DUMP", str(e.original_e))
            print(e)  # for developers
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON ERROR ON FILESAVE", str(e))
        except (ValueError, TypeError) as e:
            messagebox.showerror("UNUSUAL ERROR ON FILESAVE", str(e))


    def _load_from_file(self):
        '''From file of choice load new config values and pass them to tk variables'''
        path_to_config = self._get_config_name("Load config from json file", save=False)
        if len(path_to_config) == 0:  # selection was cancelled
            return

        try:
            load_config(path_to_config)
            self._reload_variables()
            self._last_used_path_to_config = path_to_config

        except CustomError as e:
            messagebox.showerror("ERROR ON CONFIG LOAD", str(e.original_e))
            print(e)  # for developers
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON ERROR ON FILELOAD", str(e))
        except (ValueError, TypeError) as e:
            messagebox.showerror("UNUSUAL ERROR ON FILELOAD", str(e))


    def _reload_variables(self):
        '''
        Iterate over tk variables across all the frames and set values from _config_register into them.
        Call AFTER _config_register is updated.
        '''
        for key, fav in self.configs.items():
            for field, tkvar in fav.variables.items():
                config = _config_register[key]
                tkvar.set(json.dumps(getattr(config, field)))
        messagebox.showinfo(message="LOAD SUCCESSFUL")



if __name__ == "__main__":
    tk_root = tk.Tk()
    app = EditConfigsFrame(tk_root)
    tk_root.mainloop()
