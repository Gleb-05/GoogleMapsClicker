import time
import pyautogui
from utils import select_addressbar, py_paste
from wait_contexts import wait_for_screen_change, wait_for_animation_end

def addressbar_decimal_degrees(dd: str, satellite=False):
    """
    Pass `dd` string pair (example = '48.003034,1.984737'). Display map by default, satellite if `True` is passed.
    The viewable area is automatically centerd on the `dd` coordinates provided.
    """
    DD_MAP_ADDRESS_TEMPLATE = "https://www.google.com/maps/place//@{},17z"
    DD_SAT_ADDRESS_TEMPLATE = "https://www.google.com/maps/place//@{},542m/data=!3m2!1e3!4b1"
    
    template = DD_SAT_ADDRESS_TEMPLATE if satellite else DD_MAP_ADDRESS_TEMPLATE
    dd = dd.replace(" ", "")
    
    select_addressbar()
    time.sleep(0.3)
    py_paste(template.format(dd))
    time.sleep(0.3)
    with wait_for_screen_change(region=None):
        pyautogui.press('enter')
    with wait_for_animation_end(region=None, interval=1):
        time.sleep(0.3)
