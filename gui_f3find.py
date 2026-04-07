import time
import pyautogui

from constants import SEARCH_Y, SIDEPANEL_Y, SIDEPANEL_COLLAPSE_X, SIDEPANEL_EXPAND_X
from utils import is_no_change, py_paste
from wait_contexts import wait_for_animation_end


 # F3FIND_X = 410
F3FIND_CLOSE_X = 705
F3FIND_COUNT_REGION = (570-2, 98-2, 21+5, 14+5)  # exact search_f3_once.png coordinates, adjusted for error


def refocus_page():
    """
    Bring focus back to the page itself by collapsing and expanding the side panel.
    Useful to bring hotkeys (like ctrl+f) into correct context.
    """
    SIDEPANEL_CHANGE_REGION = (0, SIDEPANEL_Y-10, 2*SIDEPANEL_EXPAND_X, 20)
    with wait_for_animation_end(SIDEPANEL_CHANGE_REGION):
        pyautogui.click(SIDEPANEL_COLLAPSE_X, SIDEPANEL_Y)
    with wait_for_animation_end(SIDEPANEL_CHANGE_REGION):
        pyautogui.click(SIDEPANEL_EXPAND_X, SIDEPANEL_Y)


def open_f3find(f3find_str: str):
    """
    Open the f3find bar using "ctrl+f" hotkey and paste `f3find_str` into it.
    Throw TimeoutError if "ctrl+f" hotkey doesnt work in the browser.
    """
    refocus_page()
    img_before_f3find = pyautogui.screenshot(region=F3FIND_COUNT_REGION)
    for i in range(4):
        # NOTE: special case when wait_for_screen_change wouldnt work, because leading action is repeated in the same loop
        pyautogui.hotkey('ctrl', 'f')
        if is_no_change(img_before_f3find, pyautogui.screenshot(region=F3FIND_COUNT_REGION)):
            time.sleep(1)
            if i==3:
                raise TimeoutError("f3 find couldn't be opened")
        else:
            break

    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.3)
    py_paste(f3find_str)


def f3find_once():
    """
    Use "f3" hotkey to update f3find that was set up with `open_f3find`.
    Return True if 1/1 match is found on the page, otherwise return False.
    When True is returned, the f3find bar is closed.
    """
    # TODO add a method for checking for 0/0 as a more robust option compared to 1/1?
    pyautogui.press('f3')
    try:
        pyautogui.locateOnScreen('img/f3find_once.png', region=F3FIND_COUNT_REGION)
        pyautogui.click(x=F3FIND_CLOSE_X, y=SEARCH_Y)
        return True
    except pyautogui.ImageNotFoundException:
        return False
