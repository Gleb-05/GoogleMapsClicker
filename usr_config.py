import json
from dataclasses import dataclass, fields, asdict

from utils import ConfigUpdateMixin
# from gui_sidepanel import Config as Config_sidepanel, C as C_sidepanel
# from gui_search import Config as Config_search, C as C_search
# from gui_map import Config as Config_map, C as C_map
# from addressbar import Config as Config_addressbar, C as C_addressbar
from usr_get_area_img import Config as Config_areaimg, C as C_areaimg

@dataclass()
class Config:
    "Aggregating Config to dump and load other configs"
    # sidepanel : Config_sidepanel
    # search: Config_search
    # gui_map: Config_map
    # addressbar: Config_addressbar
    areaimg: Config_areaimg

C = Config(
    #C_sidepanel, C_search, C_map, C_addressbar, 
    C_areaimg)
C_fields = (f.name for f in fields(C))


def dump_config():
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(asdict(C), f, indent=2, ensure_ascii=False)


def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        data : dict = json.load(f)
        for c_field, c_dict in data.items():
            if c_field not in C_fields:
                continue  # unsupported config fields are skipped
            old_c : ConfigUpdateMixin = getattr(C, c_field)
            old_c.update(c_dict)
