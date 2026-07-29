import json
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tk_app_frames.basic_frame import BasicFrame
from tk_app_frames.switch_frame_controller import setup_switch_frame_controller, FrameAndVariables

from constants import USR_CONFIGS_DIR
from utils import CustomError
from config_app import save_preferences
from config_registry import ConfigRegistryMixin, dump_config, load_config_from_dict, load_config, _get_from_registry
from config_to_tk_entries import get_tk_fields, build_field_editor
from keypress_publisher import KeypressPublisher, ButtonKeyboardManager

# crutch - trim down the configs JUST to those in get_dd_rect_img
from config_app import C_app, load_preferences_from_dict
from usr_get_area_img import C as C_areaimg
from gui.core_configs import C_sidepanel
from gui.map import C as C_map
from gui.addressbar import C as C_addressbar


class EditConfigsFrame(BasicFrame):
    '''See and change individual fields of configs'''
    def __init__(self, master: tk.Misc, controller):
        super().__init__(master, controller)

        tk.Frame(self.body, width=BasicFrame.MAX_WIDTH-140).pack()  # crutch to standardize the width of different windows

        keypress_publisher: KeypressPublisher = controller.keypress_publisher
        self.button_kb_manager = ButtonKeyboardManager(self, keypress_publisher)

        # Store (tk frame to render)-(tk variables to set and get values) pairs for each config
        configs: list[ConfigRegistryMixin] = [C_addressbar, C_sidepanel, C_map, C_areaimg]
        self.configs = {
            C.REGISTER_KEY: config_frame_and_variables
            for C in configs
            if (config_frame_and_variables:=self._frame_and_variables(C)) is not None
        }
        # crutch - preferences shouldn't be a part of config processing
        preferences_fav = {"Preferences": self._frame_and_variables(C_app)}
        self.preferences = preferences_fav["Preferences"].variables
        setup_switch_frame_controller(
            {**preferences_fav, **self.configs}, # patch the dict to make configs and preferences share the switch...controller
            self.body, 
            lambda: (self.update_root_geometry(), keypress_publisher.on_cancel())
        )

        self._last_default_config_path = C_app.DEFAULT_CONFIG

        # Add buttons to work with config files and the currently used config itself.
        self._last_used_path_to_config = "default_1366x768_config.json"
        # TODO add confirm messagebox for things that dont require filedialog
        tk.Button(self.footer, text="Save to file", command=self._save_to_file).pack(side="right")
        tk.Button(self.footer, text="Save changes", command=self._save_changes).pack(side="right", padx=5)
        tk.Button(self.footer, text="Load from file", command=self._load_from_file).pack(side="right")
        tk.Button(self.footer, text="Save preferences", command=self._save_preferences).pack(side="left")

        self.update_root_geometry()


    def _frame_and_variables(self, config: ConfigRegistryMixin) -> FrameAndVariables | None:
        tk_fields = get_tk_fields(config)
        if len(tk_fields) == 0:
            return None
        field_values = [getattr(config, field.name) for field in tk_fields]
        config_frame = tk.Frame(self.body)
        variables : dict[str, tk.StringVar] = {}
        for tk_field, value in zip(tk_fields, field_values):
            variables[tk_field.name] = build_field_editor(tk_field, value, config_frame, self.button_kb_manager) 
        return FrameAndVariables(config_frame, variables)


    def _save_changes(self, show_messagebox = True):
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
            if show_messagebox: 
                messagebox.showinfo(message="SAVE SUCCESSFUL")
            return True
        
        except (json.JSONDecodeError) as e:
            messagebox.showerror("VALUES INCOMPLETE OR MISSING", f"{bad_key}: {bad_field}\n{str(e)}")
            return False
        except (CustomError) as e:
            messagebox.showerror("BAD NEW VALUES", f"{bad_key}: {str(e.original_e)}")
            print(e)  # for developers
            return False


    def _save_preferences(self):
        '''
        Update preferences by iterating over tk variables. 
        Updating DEFAULT_CONFIG updates the config variables in this window.
        '''
        try:
            preferences = {fieldname: json.loads(tkvar.get()) for fieldname, tkvar in self.preferences.items()}
            load_preferences_from_dict(preferences)
            save_preferences()

            if C_app.DEFAULT_CONFIG != self._last_default_config_path:
                self._last_default_config_path = C_app.DEFAULT_CONFIG
                load_config(C_app.CONFIG_PATH)
                self._reload_variables(show_messagebox=False)

            messagebox.showinfo(message="PREFERENCES SAVED")

        except (json.JSONDecodeError) as e:
            messagebox.showerror("VALUES INCOMPLETE OR MISSING", str(e))
        except (CustomError) as e:
            messagebox.showerror("BAD NEW VALUES", str(e.original_e))
            print(e)  # for developers    


    def _get_config_name(self, title: str, save: bool):
        '''Returns filename of config, selected by user from a filedialog. Savedialog if `save=True`, else opendialog.'''
        dialog = filedialog.asksaveasfilename if save else filedialog.askopenfilename
        return dialog(
            title=title,
            defaultextension=".json",
            filetypes=[("json", ["*.json","*.JSON"])],
            initialdir=USR_CONFIGS_DIR,
            initialfile=self._last_used_path_to_config
        )
 

    def _save_to_file(self):
        '''Update config registry and save to file of choice'''
        if self._save_changes(show_messagebox=False) is False:  # new config values were rejected
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


    def _reload_variables(self, show_messagebox=True):
        '''
        Iterate over tk variables across all the frames and set values from _config_register into them.
        Call AFTER _config_register is updated.
        '''
        for key, fav in self.configs.items():
            for field, tkvar in fav.variables.items():
                config = _get_from_registry(key)  # another exception to _get_from_registry use
                tkvar.set(json.dumps(getattr(config, field)))
        if show_messagebox:
            messagebox.showinfo(message="LOAD SUCCESSFUL")



if __name__ == "__main__":
    tk_root = tk.Tk()
    app = EditConfigsFrame(tk_root, None)
    tk_root.mainloop()
