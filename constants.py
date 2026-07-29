import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
USR_CONFIGS_DIR = os.path.join(ROOT_DIR, "usr_configs")
_PREFERENCES_PATH = os.path.join(USR_CONFIGS_DIR, "_preferences.json")  # TODO transition to Path use
NO_SEARCH_STR : dict[str,str] = {'eng': "Google Maps can't find"}

ATTENTION_HIGHLIGHT : str = "#FEC8C8"
