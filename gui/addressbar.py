from dataclasses import dataclass
import time
import pyautogui
from config_registry import ConfigRegistryMixin
from utils import select_addressbar, py_paste
from gui.sidepanel import collapse_sidepanel
from wait_contexts import wait_for_screen_change, wait_for_animation_end

@dataclass
class Config(ConfigRegistryMixin):
    "addressbar.py config"
    REGISTER_KEY = "addressbar"
    SET_MAPVIEW_ADDRESS : str = "https://www.google.com/maps/@?api=1&basemap=satellite"
    DD_MAP_ADDRESS_TEMPLATE : str = "https://www.google.com/maps/place//@{},17z"
    DD_SAT_ADDRESS_TEMPLATE : str = "https://www.google.com/maps/place//@{},542m/data=!3m2!1e3!4b1"

C = Config()
C.register()


def open_url(url_address: str):
    """Paste provided `url_address` into the address bar, press enter and wait for the page to load."""
    select_addressbar(hide_suggestions=False)
    time.sleep(0.3)
    py_paste(url_address)
    time.sleep(0.3)
    with wait_for_screen_change(region=None):
        pyautogui.press('enter')
    with wait_for_animation_end(region=None, interval=1):
        time.sleep(0.3)


def addressbar_center_at_dd(dd: str, satellite=False):
    """
    Pass `yx dd` string pair (example = '48.003034,1.984737') to display it on the map. Use default map, or satellite if `True` is passed.
    The visible area is automatically centered on the `dd` coordinates provided.
    """
    template = C.DD_SAT_ADDRESS_TEMPLATE if satellite else C.DD_MAP_ADDRESS_TEMPLATE
    dd = dd.replace(" ", "")
    
    if satellite is False:
        open_url(C.SET_MAPVIEW_ADDRESS)  # crutch - force change to map view by visiting an additional webpage
    open_url(template.format(dd))
    collapse_sidepanel()
