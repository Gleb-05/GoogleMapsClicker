import time
import csv
import pyautogui
import pyperclip

from utils import py_reload, py_locateCenter, CustomError
from wait_contexts import wait_for_screen_change, wait_for_animation_end, wait_for_screen_image
from config import C_app
from gui.core_configs.scroll import SCROLLBAR_REGION
from gui.core_configs import C_place, C_search, C_sidepanel
from gui.scroll import total_scroll_down, scroll_to_next_card
from gui.search import use_search, search_back, single_search_result
from gui.inspect import inspect_find_and_copy_first
from gui.scroll import py_scroll

PLACE_LINKBTN_REGION = (325, 380, 375-325, 580-380)
# TODO
"""
Notice how in two months time the `place_linkbtn.png` img stopped working.
Recapturing it was easy, since all the other constants already worked on my machine.
But for a new machine, the guesswork behind the constants is too large to also include img recapturing.
Working with page elements through the console seems more reliable.
This usr_ file shall be refactored accordingly.
"""


def process_search_queries():
    """
    For each query from query generator:
    - enter query into search bar
    - if "can't find" string is present on the page, skip query
    - if not, use chosen safe procesing on the query results
    """
    for search_query in search_queries_naive():
        if not use_search(search_query):
            # TODO log that search_query gave zero search results
            continue
        for _ in iter_search_results():
            write_to_csv(extract_place_info_safe())


def search_queries_naive():
    """Return hard-coded list of locations"""
    naive_list = ['puffy cookies']
    return [q + ' paris' for q in naive_list]


def write_to_csv(info_tuple, filepath="output.csv", mode="a"):
    with open(filepath, mode, newline="", encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(info_tuple)


def iter_search_results():
    """
    Yield search results.

    Possible search results:
    - there is one place: the inspect find has PLACE_NAME_HTML.
        the place webpage is already opened, yield immediately.
    - there are multiple places: the inspect find does NOT have a PLACE_NAME_HTML.
        each place card from the search results should be opened, yield, and then search page should be opened back.
    
    A small width of the webpage is assumed (`search_back` only works if the place info replaces the search list visually)
    """
    if single_search_result():  # TODO this thing fails, most likely due to img/inspect_prevbtn.png obsolescence
        yield
        # going back to search page is unnecessary, since search bar is still displayed
    else:
        total_scroll_down()
        last_card = False
        while True:
            scrollbar_snapshot = pyautogui.screenshot(region=SCROLLBAR_REGION)
            pyautogui.click()
            yield
            # press 'back' and wait for page to load before scrolling to next card
            # check if page is loaded using SCROLLBAR_REGION
            try:
                with wait_for_screen_image(SCROLLBAR_REGION, scrollbar_snapshot, 5):
                    search_back()
            except TimeoutError:
                pass
            if last_card:
                break
            last_card = scroll_to_next_card()


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
    place_name = inspect_find_and_copy_first(C_place.PLACE_NAME_HTML)
    place_type = inspect_find_and_copy_first(C_place.PLACE_TYPE_HTML)

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
        pyautogui.click(PLACE_LINKBTN_REGION[0], C_search.SEARCH_Y)
    
    return place_link


def extract_place_pluscode():
    PLACE_PLUSCODE_REGION = (20, C_search.SEARCH_Y, 50-20, C_app.SCREEN_H-C_search.SEARCH_Y-10)

    pyautogui.moveTo(PLACE_LINKBTN_REGION[:2])  # for scroll to work, cursor should be in a good position
    pluscode_xy = None
    for _ in range(3):
        # sometimes cursor will land on pluscode row, making the background gray
        pluscode_xy = py_locateCenter("img/place_pluscode.png", region=PLACE_PLUSCODE_REGION) \
            or py_locateCenter("img/place_pluscode_gray.png", region=PLACE_PLUSCODE_REGION)
        if pluscode_xy is not None:
            break
        # sometimes pluscode row will be further down, requiring an additional scroll down
        py_scroll(300 - C_app.SCREEN_H, C_sidepanel.SIDEPANEL_CHANGE_REGION)
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
