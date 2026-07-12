from dataclasses import dataclass
from config_registry import ConfigRegistryMixin


@dataclass
class Config(ConfigRegistryMixin):
    "place.py config"

    REGISTER_KEY = "gui_place"

    PLACE_TYPE_HTML : str ="/html/body/div[1]/div[2]/div[9]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div/div[2]/div/div[1]/div[2]/div/div[2]/span/span/button"
    PLACE_NAME_HTML : str ="/html/body/div[1]/div[2]/div[9]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div/div[2]/div/div[1]/div[1]/h1/text()"


C_place = Config()
C_place.register()
