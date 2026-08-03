"""
Cornerstone of user-configs interfacing.
Part of the main app.
"""

import json
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tk_app_frames.basic_frame import BasicFrame
from tk_app_frames.switch_frame_controller import setup_switch_frame_controller, FrameAndVariables

from constants import USR_CONFIGS_DIR
from utils import CustomError
from z_app_components.popups import popup_message
from z_app_components.config_app import save_preferences
from z_app_components.config_registry import ConfigRegistryMixin, dump_config, load_config_from_dict, load_config, _get_from_registry
from z_app_components.config_to_tk_entries import get_tk_fields, build_field_editor
from z_app_components.keypress_publisher import KeypressPublisher, ButtonKeyboardManager

# trim down the configs JUST to those used by get_dd_rect_img (for now)
# mega crutch - pick out configs that are not needed for get_dd_rect_img by hand
# maybe standardize this? add a special screen to view configs relevant to a given function
from z_app_components.config_app import C_app, load_preferences_from_dict
from usr_get_area_img import C as C_areaimg, get_dd_rect_img_C_trim
from gui.core_configs import C_sidepanel
from gui.map import C as C_map
from gui.addressbar import C as C_addressbar


class EditConfigs(BasicFrame):
    '''See and change individual fields of configs'''
    def __init__(self, master: tk.Misc, controller):
        super().__init__(master, controller)

        tk.Frame(self.body, width=controller.MAX_WIDTH-140).pack()  # crutch to standardize the width of different windows

        keypress_publisher: KeypressPublisher = controller.keypress_publisher
        self.button_kb_manager = ButtonKeyboardManager(self, keypress_publisher)

        # Store (tk frame to render)-(tk variables to set and get values) pairs for each config
        configs: list[ConfigRegistryMixin] = [C_addressbar, C_sidepanel, C_map, C_areaimg]
        self.configs = {
            C.REGISTER_KEY: config_frame_and_variables
            for C in configs
            if (config_frame_and_variables:=self._frame_and_variables(C)) is not None
        }
        # preferences shouldn't be a part of config processing - handle separately
        _pref_key = "Preferences"
        preferences_fav = {_pref_key: self._frame_and_variables(C_app)}
        self.preferences = preferences_fav[_pref_key].variables
        setup_switch_frame_controller(
            frame_and_variables_dict={**preferences_fav, **self.configs}, # patch the dict to make configs and preferences share the switch...controller
            master=self.body, 
            # make sure that 
            # - window resizes on switching the inner frames (works because parent BasicFrame provides custom_req... picked up by update_root_geometry)
            # - if a button listens to the keyboard, it stops on config switch
            on_switch = lambda : (
                controller.update_root_geometry(active_fav=FrameAndVariables(self, {})), 
                keypress_publisher.on_cancel()
            )
        )

        # patch C_app frame with an exclusive button
        self._last_default_config_path = C_app.DEFAULT_CONFIG
        tk.Button(
            master=preferences_fav[_pref_key].frame, 
            text="Save preferences", 
            command=self.save_preferences
            ).pack(anchor="center", pady=(0,10))

        # Buttons to work with config files and the currently used config itself.

        self._last_used_path_to_config = "default_1366x768_config.json"

        tk.Button(self.footer, text=" ? ", command=lambda:
            messagebox.showinfo(
                title="Manage app configurations and your preferences.",
                message="The app uses one configuration object. You can change it using either files or the interface. Preferences use a separate object `C_app`.\n\n" \
                "Note that changes made with the interface apply only while the app runs. Namely:\n" \
                "- Save changes - save values from the interface to the object.\n" \
                "- Discard changes - use values from the object to replace those in the interface.\n\n" \
                "Operations with config files:\n" \
                "- Save to file - save values from the interface to the object AND a chosen file. Once you find good config values, save them in order not to loose them when the app closes.\n" \
                "- Load from file - use values from a chosen file to replace those in the interface AND the object. That's exactly where files with good config values help.\n\n" \
                "Preferences are persisted across app runs. See:\n" \
                "- Save preferences - a button exclusive to the 'Preferences' frame. " \
                "When clicked, saves values from the interface to both the `C_app` and the preferences file (not to be used directly).\n" \
                "- DEFAULT_CONFIG specifies the file from which configuration values are loaded at application startup." \
                "CAUTION: if changed, 'Load from file' is applied immediately, updating both the interface and the config object.")
            ).pack(side="right", padx=5)

        tk.Button(self.footer, text="Save to file", command=self.save_to_file).pack(side="right")
        tk.Button(self.footer, text="Save changes", command=self.save_changes_okcancel).pack(side="right", padx=5)
        tk.Button(self.footer, text="Discard changes", command=self.discard_changes_okcancel).pack(side="right")
        tk.Button(self.footer, text="Load from file", command=self.load_from_file).pack(side="left")
    

    def _frame_and_variables(self, config: ConfigRegistryMixin) -> FrameAndVariables | None:
        tk_fields = get_tk_fields(config)
        if len(tk_fields) == 0:
            return None
        # maybe standardize this? add a special screen to view configs relevant to a given function
        if config is C_areaimg:
            tk_fields = [field for field in tk_fields if field.name not in get_dd_rect_img_C_trim]
        
        field_values = [getattr(config, field.name) for field in tk_fields]
        config_frame = tk.Frame(self.body)
        variables : dict[str, tk.StringVar] = {}
        for tk_field, value in zip(tk_fields, field_values):
            variables[tk_field.name] = build_field_editor(tk_field, value, config_frame, self.button_kb_manager) 
        return FrameAndVariables(config_frame, variables)


    def save_changes_okcancel(self):
        proceed = messagebox.askokcancel(
            title="Proceed with save changes?", 
            message="New config values will overwrite values in use with no way to restore them")
        if not proceed:
            return
        if self._save_changes():
            popup_message(self.winfo_toplevel(), message="SAVE SUCCESSFUL")


    def _save_changes(self):
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
            return True
        
        except (json.JSONDecodeError) as e:
            messagebox.showerror("VALUES INCOMPLETE OR MISSING", f"{bad_key}: {bad_field}\n{str(e)}")
            return False
        except (CustomError) as e:
            messagebox.showerror("BAD NEW VALUES", f"{bad_key}: {str(e.original_e)}")
            print(e)  # for developers
            return False


    def save_preferences(self):
        '''
        Update preferences by iterating over tk variables. 
        Updating DEFAULT_CONFIG updates the config variables in this window.
        '''
        try:
            preferences = {fieldname: json.loads(tkvar.get()) for fieldname, tkvar in self.preferences.items()}

            if preferences['DEFAULT_CONFIG'] != self._last_default_config_path:
                proceed = messagebox.askokcancel(
                    title="Proceed with save preferences?", 
                    message="Config values in use will be replaced by values from DEFAULT_CONFIG.\n" \
                    "If the current config values work, make sure you save them to a file before saving preferences")
                if not proceed:
                    self.preferences['DEFAULT_CONFIG'].set(json.dumps(self._last_default_config_path))
                    return
                load_preferences_from_dict(preferences)
                save_preferences()
                self._last_default_config_path = C_app.DEFAULT_CONFIG
                load_config(C_app.CONFIG_PATH)
                self._reload_variables()
            else:
                proceed = messagebox.askokcancel(
                    title="Proceed with save preferences?", 
                    message="New preferences will overwrite the existing ones with no way to restore them")
                if not proceed:
                    return
                load_preferences_from_dict(preferences)
                save_preferences()
            
            popup_message(self.winfo_toplevel(), message="PREFERENCES SAVED")

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
 

    def save_to_file(self):
        '''Update config registry and save to file of choice'''
        if self._save_changes() is False:  # new config values were rejected
            return
        
        path_to_config = self._get_config_name("Save config to json file", save=True)
        if len(path_to_config) == 0:  # selection was cancelled
            return
        
        try:
            dump_config(path_to_config)
            
            popup_message(self.winfo_toplevel(), message="FILESAVE SUCCESSFUL")
            self._last_used_path_to_config = path_to_config

        except CustomError as e:
            messagebox.showerror("ERROR ON CONFIG DUMP", str(e.original_e))
            print(e)  # for developers
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON ERROR ON FILESAVE", str(e))
        except (ValueError, TypeError) as e:
            messagebox.showerror("UNUSUAL ERROR ON FILESAVE", str(e))


    def load_from_file(self):
        '''From file of choice load new config values and pass them to tk variables'''
        path_to_config = self._get_config_name("Load config from json file", save=False)
        if len(path_to_config) == 0:  # selection was cancelled
            return

        try:
            load_config(path_to_config)
            self._reload_variables()
            self._last_used_path_to_config = path_to_config

            popup_message(self.winfo_toplevel(), message="LOAD of config values from file SUCCESSFUL")

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
                config = _get_from_registry(key)  # another exception to _get_from_registry use
                tkvar.set(json.dumps(getattr(config, field)))


    def discard_changes_okcancel(self):
        proceed = messagebox.askokcancel(
            title="Proceed with discard changes?", 
            message="All config values will be restored to their previous values")
        if not proceed:
            return
        self._reload_variables()
        popup_message(self.winfo_toplevel(), message="Config values RESTORED")
