"""
Work with the "Layers" google maps button through chrome developers console.

References:
- https://www.youtube.com/watch?v=fNedC1qBnZ8
- https://developer.chrome.com/docs/devtools/console/utilities/
"""

from dataclasses import dataclass

from gui.inspect import inspect_use_console
from z_app_components.config_registry import ConfigRegistryMixin


@dataclass
class Config(ConfigRegistryMixin):
    '''layers.py config'''
    REGISTER_KEY = "layers"
    LABELS_BUTTON_SELECTOR : str = "body > div:nth-child(5) > div.lbMcOd.y2iKwd.cSgCkb.qK6Xvf.znKqMd.Nkjr6c.K1N2o > div.UL7Qtf > div.seN1Zd.Hk4XGb > div > div > div > div.yYTQHb > ul > li:nth-child(2) > button"
    SWITCHVIEW_BUTTON_SELECTOR : str = "body > div:nth-child(5) > div.lbMcOd > div.UL7Qtf > div.jsXHHe.i2s2Oe > div.t090lc.pEO5hf > div > div > button"
    # TODO both values above feel like PLACE_TYPE_HTML and PLACE_NAME_HTML - move to separate file?

C = Config()
C.register()

def map_toggle_sat_labels():
    """
    With satellite map selected, toggle displaying of roads and landmarks using the inspect console.

    *Notice that labels in satellite view never stay off. New search - on. New tab - on. 
    Without a way to escape turned on labels, current solution is `map_toggle_sat_labels` 
    that invokes a .click() event on the 'labels' button through java script. 
    One alternative is to manually define the 
    "know where sidepanel is - click layers - scroll down - click labels button", 
    but that is too much variability between devices.*
    """
    inspect_use_console(f"$('{C.LABELS_BUTTON_SELECTOR}').click()")


def map_switch_view():
    """Switch from map to sat view or from sat to map view using the inspect console"""
    inspect_use_console(f"$('{C.SWITCHVIEW_BUTTON_SELECTOR}').click()")
