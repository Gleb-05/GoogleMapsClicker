from dataclasses import dataclass, field
import time
import pyautogui
import pyperclip

from config_registry import ConfigTkMeta, ConfigRegistryMixin
from wait_contexts import wait_for_screen_change, wait_for_animation_end
from gui_inspect import inspect_use_console
from gui_contextmenu import contextmenu_click_option

@dataclass
class Config(ConfigRegistryMixin):
    "map.py config"
    REGISTER_KEY = "gui_map"
    
    CONTEXT_Y_CUTOFF : int = field(
        default=384,
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            "CONTEXT_Y_CUTOFF",
            "Y coordinate of the right click on the map at which the context menu that appears snaps to screen bottom"
        )}
    )
    CONTEXT_SNAPS_TO_SCREEN_BOTTOM : bool = True

    POPUP_CLOSE_XY : tuple[int,int] = field(
        default=(796,744),
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            "POPUP_CLOSE_XY",
            "Pixel coordinates of the close button of the message \"Copied to clipboard\" that pops up " \
            "after decimal degrees are selected from the context menu that appears on right click on the map"
        )}
    )

    LABELS_BUTTON_SELECTOR : str = "body > div:nth-child(5) > div.lbMcOd.y2iKwd.cSgCkb.qK6Xvf.znKqMd.Nkjr6c.K1N2o > div.UL7Qtf > div.seN1Zd.Hk4XGb > div > div > div > div.yYTQHb > ul > li:nth-child(2) > button"
    """related to `map_toggle_sat_labels()`"""

    SWITCHVIEW_BUTTON_SELECTOR : str = "body > div:nth-child(5) > div.lbMcOd > div.UL7Qtf > div.jsXHHe.i2s2Oe > div.t090lc.pEO5hf > div > div > button"
    """related to `map_switch_view()`"""

    # TODO both values above feel like PLACE_TYPE_HTML and PLACE_NAME_HTML - move to separate file?

C = Config()
C.register()


def drag_map(x_from, y_from, x_to, y_to, drag_duration=0.3):
    """Replicate dragging the map by providing two sets of coordinates: where the dragging begins and where it ends."""
    # google maps pics up dragging on 4th pixel with mousedown !!!
    pyautogui.moveTo(x_from - 3, y_from)
    pyautogui.mouseDown()
    time.sleep(0.1)
    pyautogui.moveTo(x_from, y_from, 0.1)
    with wait_for_animation_end(region=None):
        pyautogui.moveTo(x_to, y_to, drag_duration)
        # time.sleep to prevent inertia from moving areas further - already accounted for
    pyautogui.mouseUp()
    time.sleep(0.1)


def map_toggle_sat_labels():
    """
    With satellite map selected, toggle displaying of roads and landmarks using the inspect console.
    """
    inspect_use_console(f"$('{C.LABELS_BUTTON_SELECTOR}').click()")


def map_switch_view():
    """Switch from map to sat view or from sat to map view using the inspect console"""
    inspect_use_console(f"$('{C.SWITCHVIEW_BUTTON_SELECTOR}').click()")


def map_get_coords_at_cursor():
    """
    Get x(long)-y(lat) decimal degree coordinates of map point at current cursor position from leftclick context menu (lat-long).
    
    Might cause freezing of the visible area which can be ended by tab switching.
    """
    x, y = pyautogui.position()

    with wait_for_screen_change(region=(x,y,20,20)):
        pyautogui.rightClick()

    # when clicking on y below the cutoff, the context menu stays at the cutoff
    contextmenu_click_option(
        menu_snaps_to_screen_bottom=C.CONTEXT_SNAPS_TO_SCREEN_BOTTOM,
        y_cutoff=C.CONTEXT_Y_CUTOFF
    )

    pyautogui.click(C.POPUP_CLOSE_XY)
    time.sleep(0.01)

    y_dd, x_dd = pyperclip.paste().split(",")  # lat-long!
    return float(x_dd), float(y_dd)
