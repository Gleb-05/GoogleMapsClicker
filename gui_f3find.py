import time
import pyautogui

from constants import SEARCH_Y, SEARCH_BAR_X
from utils import is_no_change, py_paste

# TODO crutches like this arise from differences in the interface. Find better solution.
d = 1068-570 # difference between x of f3find_count_region in fullscreen and when set_browser_x is used
F3FIND_COUNT_REGION = (570-2, 98-2, 21+d+5, 14+5)  # exact search_f3_once.png coordinates, adjusted for error


def refocus_page():
    """
    Bring focus back to the page by clicking at the coordinates of a search bar.
    Useful to bring hotkeys (like ctrl+f) into correct context.
    """
    # this is the simplest lest demanding invariant part of google maps ui to use for refocusing
    pyautogui.click(SEARCH_BAR_X, SEARCH_Y)


def open_f3find(f3find_str: str):
    """
    Open the f3find bar using "ctrl+f" hotkey and paste `f3find_str` into it.
    Throw TimeoutError if "ctrl+f" hotkey doesnt work in the browser.
    """
    # F3FIND_X = 410
    refocus_page()
    close_f3find()
    time.sleep(0.1)
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


def f3find_once(close_after=True):
    """
    Use "f3" hotkey to update f3find that was set up with `open_f3find`.
    Return True if 1/1 match is found on the page, otherwise return False.
    Calling `f3find_once` will close the f3find bar by default. Pass `close_after=True` to override (for example in loops)
    """
    # TODO add a method for checking for 0/0 as a more robust option compared to 1/1?
    pyautogui.press('f3')
    match = True
    try:
        pyautogui.locateOnScreen('img/f3find_once.png', region=F3FIND_COUNT_REGION)
    except pyautogui.ImageNotFoundException:
        match = False

    if close_after:
        close_f3find()
    return match


def close_f3find():
    # F3FIND_CLOSE_X = 705
    # pyautogui.click(x=F3FIND_CLOSE_X, y=SEARCH_Y)
    pyautogui.press('esc')  # it seems that f3find is the first thing that consumes "esc". doesnt break context
