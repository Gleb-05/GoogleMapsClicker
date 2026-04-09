import time
import pyautogui

from constants import SEARCH_Y, SEARCH_BAR_X, PLACE_NAME_HTML
from utils import py_paste, py_reload
from gui_inspect import inspect_find
from gui_sidepanel import collapse_sidepanel
from gui_f3find import open_f3find, f3find_once


def use_search(search_query: str):
    """
    Enter `search_query` into the search bar and wait for the results to load.
    Returned `True` indicates that the search was successfull.
    5sec wait is included.
    """
    # SEARCH_BUTTON_X = 278
    pyautogui.click(SEARCH_BAR_X, SEARCH_Y)
    pyautogui.hotkey('ctrl', 'a')
    py_paste(search_query)
    pyautogui.press('enter')
    time.sleep(5)
    return not zero_search_results()


def search_back():
    """
    Click on the "back" button on the left of the search bar.
    This button is available ONLY IF the webpage has small width.
    """
    SEARCH_BACK_X = 28
    pyautogui.click(SEARCH_BACK_X, SEARCH_Y)


def single_search_result():
    """Return `True` if one single place was found with google maps search, return `False` on multiple or no places"""
    # Only the webpage with one single search result has `place name` in its HTML
    return inspect_find(PLACE_NAME_HTML)


def zero_search_results(lang='eng'):
    """Return `True` if page has "can't find ..." string. Choose `lang`: [eng]"""
    NO_SEARCH_STR = {'eng': "Google Maps can't find"}
    no_search_str = NO_SEARCH_STR[lang]
    open_f3find(no_search_str)
    return f3find_once()


def center_on_search_result(search_query: str):
    """
    Align the center of the viewable area with the place marker by performing the following sequence:
    Enter query - Reload page - Hide side pannel
    """
    use_search(search_query)
    py_reload()
    collapse_sidepanel()
