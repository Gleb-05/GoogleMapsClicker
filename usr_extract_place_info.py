import time
import pyautogui
import pyperclip

from config import PLACE_NAME_HTML, PLACE_TYPE_HTML, SCREEN_H
from gui_search import SEARCH_Y
from utils import py_reload, py_locateCenter, CustomError
from wait_contexts import wait_for_screen_change, wait_for_animation_end
from gui_inspect import inspect_find_and_copy_first
from gui_scroll import py_scroll

PLACE_LINKBTN_REGION = (325, 380, 375-325, 580-380)
# TODO
"""
Notice how in two months time the `place_linkbtn.png` img stopped working.
Recapturing it was easy, since all the other constants already worked on my machine.
But for a new machine, the guesswork behind the constants is too large to also include img recapturing.
Working with page elements through the console seems more reliable.
This usr_ file shall be refactored accordingly.
"""


def extract_place_info():
    """
    When place webpage is opened, get:
    - place_name
    - place_type
    - place_pluscode
    - place_link (google maps shortened link to the place)
    """
    # order matters:
    # link doesnt scroll the page, pluscode does,
    # and both name and type use inspect window and work slower
    place_link = extract_place_link()
    place_pluscode = extract_place_pluscode()
    place_name = inspect_find_and_copy_first(PLACE_NAME_HTML)
    place_type = inspect_find_and_copy_first(PLACE_TYPE_HTML)

    return place_name, place_type, place_pluscode, place_link


def extract_place_link():
    PLACE_LINKLOAD_REGION = (20,460,310,20)
    PLACE_LINKTEXT_XY = (10+70//2, 450+17//2)  # hopefully link text is always at the same height
    # PLACE_LINK_REGION = (10, 450-3, 70, 17+6)  # clicking on 'place_link.png' coordinates failed
    # PLACE_LINK_CLOSE_XY = (405,245)  # using precise coordinates failed

    x, y, w, h = pyautogui.locateOnScreen("img/place_linkbtn.png", region=PLACE_LINKBTN_REGION)
    with wait_for_screen_change(PLACE_LINKBTN_REGION):
        pyautogui.click(x+w//2, y+h//2)
    with wait_for_animation_end(PLACE_LINKLOAD_REGION):  # link may not load immediately
        time.sleep(0.1)
    # link_x, link_y = pyautogui.locateCenterOnScreen("img/place_link.png", region=PLACE_LINK_REGION)
    pyautogui.click(PLACE_LINKTEXT_XY)  
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.3)
    place_link = pyperclip.paste()
    with wait_for_screen_change(PLACE_LINKBTN_REGION):
        pyautogui.click(PLACE_LINKBTN_REGION[0], SEARCH_Y)
    
    return place_link


def extract_place_pluscode():
    PLACE_PLUSCODE_REGION = (20, SEARCH_Y, 50-20, SCREEN_H-SEARCH_Y-10)

    pyautogui.moveTo(PLACE_LINKBTN_REGION[:2])  # for scroll to work, cursor should be in a good position
    pluscode_xy = None
    for _ in range(3):
        # sometimes cursor will land on pluscode row, making the background gray
        pluscode_xy = py_locateCenter("img/place_pluscode.png", region=PLACE_PLUSCODE_REGION) \
            or py_locateCenter("img/place_pluscode_gray.png", region=PLACE_PLUSCODE_REGION)
        if pluscode_xy is not None:
            break
        # sometimes pluscode row will be further down, requiring an additional scroll down
        py_scroll(300 - SCREEN_H)
    if pluscode_xy is None:
        raise pyautogui.ImageNotFoundException
    pyautogui.click(pluscode_xy)
    time.sleep(0.3)
    place_pluscode = pyperclip.paste()
    return place_pluscode


def extract_place_info_safe():
    """
    Wrap extract_place_info in some retry and errorcatch logic.
    On unexpected error raise `CustomError` with `place_link` attached to be handled by caller."""
    time.sleep(5)  # extract_place_info is called on the page immediately, but it may be not loaded yet
    try:
        try:
            place_info = extract_place_info()
        except (TimeoutError, pyautogui.ImageNotFoundException):
            # one more chance to work if something took too long
            py_reload()
            place_info = extract_place_info()
        return place_info
    except Exception as e:
        # remember address of this page as problematic
        pyautogui.hotkey('alt', 'd')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.3)
        raise CustomError(original_exception = e, place_link = pyperclip.paste()) from e
