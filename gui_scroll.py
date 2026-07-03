import math
import time
import pyautogui

from config import SCROLLBAR_REGION
from utils import distance_to_white
from wait_contexts import wait_for_animation_end
from gui_f3find import open_f3find, f3find_once, close_f3find

PLACE_CARD_XY = (12,550)
# PLACE_CARD_PAGETOP_XY = (12,255)
SCROLL_MULT=1.3


def py_scroll(distance, region):
    """Pass `distance` to scroll and `region` to wait_for_animation_end"""
    # Using precise distance leads to underscroll, arbitrary multiplier is used as a fix
    with wait_for_animation_end(region):
        pyautogui.scroll(int(distance*SCROLL_MULT))


def scroll_to_next_card(scroll_up=True):
    """
    In a list of search results with place cards, scroll (up by default) to next card.
    Return True when the last card is reached, False otherwise.
    May stop at second to last card if more than two cards are displayed at the top of the list.
    """
    FIRST_PLACE_CARD_TOP_Y = 240
    LAST_PLACE_CARD_BOTTOM_Y = 635
     # rectangle somewhere in the middle of the google maps interface, useful for scroll checks
    SEARCH_SCREEN_CHANGE_REGION = (30, 330, 50, 20)  # TODO compute automatically from search bar Y, window Y and scroll X ?

    left_x, left_y = PLACE_CARD_XY
    # changing_region was unreliable - edge case: same blank card bottoms are compared

    # Move the mouse over the place card for it to change color to gray
    pyautogui.moveTo(left_x, left_y+1)
    pyautogui.moveTo(left_x, left_y, 0.1)

    distance = distance_to_white(left_x, left_y, from_down=scroll_up)
    if distance is None:
        return
    py_scroll(-distance, SEARCH_SCREEN_CHANGE_REGION)

    # when the last two cards are reached, the card can't move toward the cursor because the scroll is at its edge.
    # thus, the cursor should move toward the card.
    SCROLLBAR_COLOR=(94,94,94)
    # TODO consider switching to checking the cursor's Y coordinate (for cards with smaller height)
    if pyautogui.pixelMatchesColor(*SCROLLBAR_REGION[:2], SCROLLBAR_COLOR):
        distance = distance_to_white(left_x, left_y, from_down=scroll_up)
        distance = distance + math.copysign(10, distance)
        new_y = left_y + distance
        if new_y <= FIRST_PLACE_CARD_TOP_Y or new_y >= LAST_PLACE_CARD_BOTTOM_Y:
            raise ValueError("corrective scroll to next card - out of bounds")
        pyautogui.moveRel(0, distance)
        return True
    
    return False


def total_scroll_down(lang='eng'):
    """
    Scroll down untill all of the results are dynamically loaded.
    Stop when "... end of the list" text is found exactly once on the page.
    Choose relevant `stop_text` by selecting lang: [eng, ukr].

    When finished, cursor will rest at PLACE_CARD_XY.
    """
    LIST_END_STR = {
        'eng': "You've reached the end of the list",
        'ukr': "Ви переглянули весь список",
    }
    list_end_str = LIST_END_STR[lang]

    open_f3find(list_end_str)
    pyautogui.moveTo(PLACE_CARD_XY)

    while True:
        # TODO maybe change to holding a click at the bottom of search result scrollbar
        pyautogui.scroll(-1000)
        time.sleep(0.4)
        if f3find_once(close_after=False):
            close_f3find()
            break

    time.sleep(0.1)
    pyautogui.moveTo(PLACE_CARD_XY)
    