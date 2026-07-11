from dataclasses import dataclass
from config_registry import ConfigRegistryMixin

@dataclass
class Config(ConfigRegistryMixin):
    """
    place.py config. 
    Different from other configs.
    Created to store shared values, relevant to gui_scroll and gui_search.
    """ 
    # TODO consider making gui_shared.py decoupled from place logic, 
    # intended for all cases of resolving circular dependencies on constants
    REGISTER_KEY = "gui_place"

    PLACE_TYPE_HTML : str ="/html/body/div[1]/div[2]/div[9]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div/div[2]/div/div[1]/div[2]/div/div[2]/span/span/button"
    PLACE_NAME_HTML : str ="/html/body/div[1]/div[2]/div[9]/div[9]/div/div/div[1]/div[2]/div/div[1]/div/div/div/div[2]/div/div[1]/div[1]/h1/text()"

C = Config()
C.register()
C_place = C  # alias
