import time
import pyautogui
from utils import select_addressbar, py_paste
from gui_sidepanel import collapse_sidepanel
from wait_contexts import wait_for_screen_change, wait_for_animation_end


def addressbar_center_at_dd(dd: str, satellite=False):
    """
    Pass `dd` string pair (example = '48.003034,1.984737') to display it on the map. Use default map, or satellite if `True` is passed.
    The visible area is automatically centerd on the `dd` coordinates provided.
    """
    SET_MAPVIEW_ADDRESS = "https://www.google.com/maps/@?api=1&basemap=satellite"
    DD_MAP_ADDRESS_TEMPLATE = "https://www.google.com/maps/place//@{},17z"
    DD_SAT_ADDRESS_TEMPLATE = "https://www.google.com/maps/place//@{},542m/data=!3m2!1e3!4b1"
    
    template = DD_SAT_ADDRESS_TEMPLATE if satellite else DD_MAP_ADDRESS_TEMPLATE
    dd = dd.replace(" ", "")
    
    if satellite is False:
        # crutch - force change of view by visiting an additional webpage
        select_addressbar()
        time.sleep(0.3)
        py_paste(SET_MAPVIEW_ADDRESS)
        time.sleep(0.3)
        with wait_for_screen_change(region=None):
            pyautogui.press('enter')
        with wait_for_animation_end(region=None, interval=1):
            time.sleep(0.3)

    select_addressbar()
    time.sleep(0.3)
    py_paste(template.format(dd))
    time.sleep(0.3)
    with wait_for_screen_change(region=None):
        pyautogui.press('enter')
    with wait_for_animation_end(region=None, interval=1):
        time.sleep(0.3)

    collapse_sidepanel()
