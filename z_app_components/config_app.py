import os
import json
from tkinter import filedialog
from tkinter import messagebox
from dataclasses import dataclass, field, asdict

from constants import USR_CONFIGS_DIR, PREFERENCES_PATH
from utils import is_inside, CustomError
from z_app_components.config_registry import LoadFromJsonMixin, ConfigRegistryMixin, load_config
from z_app_components.config_to_tk_entries import ConfigTkMeta, ConfigRecomputeMeta, ConfigRecomputeMixin

@dataclass
class Config(LoadFromJsonMixin, ConfigRecomputeMixin):
    "Configurations and states that impact the whole app"
    RECOMPUTE_FUNCTIONS = {}

    LANG : str = field(
        default='eng',
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            doc="Choose language used by google maps. Important for checking text on the page.",
            option_list=['eng']
        )}
    )

    DEFAULT_CONFIG : str = field(
        default="default_1366x768_config.json",
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            doc="Choose a config file to load on app startup",
        ), ConfigRecomputeMeta.KEY: ConfigRecomputeMeta(
            recompute_function_doc="Select from a filedialog",
            recompute_function_getter=ConfigRecomputeMixin.recompute_getter(
                RECOMPUTE_FUNCTIONS,
                "get_config_name"
            ),
            recompute_causes=[]
        )}
    )
    @property
    def CONFIG_PATH(self) -> str:
        '''USR_CONFIGS_DIR / DEFAULT_CONFIG'''
        return os.path.join(USR_CONFIGS_DIR, self.DEFAULT_CONFIG)

    # there are states to keep track of in order to choose which state-changing functions to execute
    # TODO move back to configs that are responsible for those states?
    DEVPANEL_OPEN = False
    '''Remember whether chrome devtools panel is open. Used for Inspect (ctrl shift i) and Console (ctrl shift j)'''
    SIDEPANEL_OPEN = None
    '''Remember if sidepanel is open (bool). "None" for now since no code yet addresses it'''
    TAB_HOPPING_SPAWNED = False
    '''Remember if get_area_img config spawned a tab for hopping. Check if True in `get_dd_rect_img`'''

C_app = Config()
'''Preferences'''

def load_preferences_once():
    '''Before the app starts, call it to make sure that user preferences are loaded correctly'''
    with open(PREFERENCES_PATH, encoding="utf-8") as f:
        try:
            data : dict = json.load(f)
            load_preferences_from_dict(data)
            load_config(C_app.CONFIG_PATH)  # important byproduct of preferences!
        except (json.JSONDecodeError, CustomError) as e:
            messagebox.showerror("ERROR ON LOADING PREFERENCES", f"default values for the preferences and configurations will be used\n\n{e}")

def load_preferences_from_dict(config_dict: dict[str,dict]):
    C_app._update(config_dict)  # pylint: disable=protected-access ; subset of intended usecase

def save_preferences():
    try:
        # maybe refactor to be derived from dump_config
        with open(PREFERENCES_PATH, "w", encoding="utf-8") as f:
            json.dump(asdict(C_app), f, indent=2, ensure_ascii=False
                # cls = ConfigEncoder
            )
    except TypeError as e:
        raise CustomError(
            original_exception=e,
            attention="LoadFromJsonMixin descendant *must* use JSON-serializable fields",
            fix="Taking the simple nature of this app into account, please switch to JSON-serializable field types. " \
            "For example, IntEnum instead of bare Enum."
        ) from e

def get_config_name():
    filename = filedialog.askopenfilename(
        title="Default config file",
        defaultextension=".json",
        filetypes=[("json", ["*.json","*.JSON"])],
        initialdir=USR_CONFIGS_DIR,
    )
    if is_inside(filename, USR_CONFIGS_DIR):
        return os.path.basename(filename)
    return C_app.DEFAULT_CONFIG

C_app.add_recompute(get_config_name)


@dataclass
class SizeConfig(ConfigRegistryMixin):
    '''Register winfo width and height to contextualize the rest of the config'''
    # maybe revisit this piece of code. can't get rid of it for now
    REGISTER_KEY = "size"
    SCREEN_W : int = 1366
    SCREEN_H : int = 768

C_size = SizeConfig()
C_size.register()
