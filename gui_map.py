import time
import pyautogui
import pyperclip

from constants import RMB_FIRST_OPTION_BELOW_RELATIVE_XY
from wait_contexts import wait_for_screen_change, wait_for_animation_end
from gui_inspect import inspect_use_console


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
    labels_button_selector = "body > div:nth-child(5) > div.lbMcOd.y2iKwd.cSgCkb.qK6Xvf.znKqMd.Nkjr6c.K1N2o > div.UL7Qtf > div.seN1Zd.Hk4XGb > div > div > div > div.yYTQHb > ul > li:nth-child(2) > button"
    inspect_use_console(f"$('{labels_button_selector}').click()")


def map_get_coords_at_cursor():
    """Get pair of decimal degree coordinates of map point at current cursor position from leftclick context menu"""
    CONTEXT_Y_CUTOFF = 384  # when clicking on y below the cutoff, the context menu stays at the cutoff
    CONTEXT_CLOSE_XY = 796,744

    x, y = pyautogui.position()

    with wait_for_screen_change(region=(x,y,20,20)):
        pyautogui.rightClick()

    pyautogui.moveRel(RMB_FIRST_OPTION_BELOW_RELATIVE_XY)
    if y >= CONTEXT_Y_CUTOFF:
        rel_y = RMB_FIRST_OPTION_BELOW_RELATIVE_XY[1]
        pyautogui.moveTo(None, CONTEXT_Y_CUTOFF + rel_y)
    pyautogui.click()
    time.sleep(0.1)

    pyautogui.click(CONTEXT_CLOSE_XY)
    time.sleep(0.01)

    x_dd, y_dd = pyperclip.paste().split(",")
    return float(x_dd), float(y_dd)
