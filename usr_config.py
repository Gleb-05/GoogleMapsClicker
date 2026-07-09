import json
from dataclasses import dataclass, asdict
from typing import get_type_hints
import dacite

from gui_sidepanel import Config as Config_sidepanel, C as C_sidepanel
from gui_search import Config as Config_search, C as C_search
from gui_map import Config as Config_map, C as C_map
from addressbar import Config as Config_addressbar, C as C_addressbar
from usr_get_area_img import Config as Config_areaigm, C as C_areaimg

@dataclass()
class Config:
    "Aggregating Config to dump and load other configs"
    sidepanel : Config_sidepanel
    search: Config_search
    gui_map: Config_map
    addressbar: Config_addressbar
    areaimg: Config_areaigm

C = Config(C_sidepanel, C_search, C_map, C_addressbar, C_areaimg)
C_field_type_dict = get_type_hints(C)


def dump_config():
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(asdict(C), f, indent=2, ensure_ascii=False)


def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        data : dict = json.load(f)
        for c_field, c_dict in data.items():
            if c_field not in C_field_type_dict:
                continue  # unsupported config fields are skipped
            new_c = dacite.from_dict(
                data_class = C_field_type_dict[c_field], 
                data=c_dict, 
                config=dacite.Config(cast=[tuple])
            )
            # TODO fix this brittle temporary way of updating app configs "in place by reference"
            old_c = getattr(C, c_field)
            old_c.__dict__.update(new_c.__dict__)
