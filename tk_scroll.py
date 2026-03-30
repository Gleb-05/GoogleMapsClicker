import math
import time
import pyautogui

from constants import SEARCH_SCREEN_CHANGE_REGION, SEARCH_Y, SCROLLBAR_REGION
from utils import is_no_change, py_paste, distance_to_white
from wait_contexts import wait_for_animation_end

PLACE_CARD_XY = (12,550)
# PLACE_CARD_PAGETOP_XY = (12,255)
SCROLL_MULT=1.3

def refocus_page():
    """
    By clicking on hide and on show, bring back focus to the page itself.
    Useful to bring shortcuts into correct context.
    """
    with wait_for_animation_end((0, 425-10, 20, 20)):
        pyautogui.click(420,425)
    with wait_for_animation_end((0, 425-10, 20, 20)):
        pyautogui.click(12,425)


def py_scroll(distance, region=SEARCH_SCREEN_CHANGE_REGION):
    """Pass `distance` to scroll and `region` to wait_for_animation_end"""
    # Using precise distance leads to underscroll, arbitrary multiplier is used as a fix
    with wait_for_animation_end(region):
        pyautogui.scroll(int(distance*SCROLL_MULT))


def scroll_to_next_card(scroll_up=True):
    """
    In a list of search results with place cards, scroll (up by default) to next card.
    Return True when the last card is reached, False otherwise.
    May stop at second to last card if more than two cards are visible at the top of the list.
    """
    FIRST_PLACE_CARD_TOP_Y = 240
    LAST_PLACE_CARD_BOTTOM_Y = 635

    left_x, left_y = PLACE_CARD_XY
    # changing_region was unreliable - edge case: same blank card bottoms are compared

    # Move the mouse over the place card for it to change color to gray
    pyautogui.moveTo(left_x, left_y+1)
    pyautogui.moveTo(left_x, left_y, 0.1)

    distance = distance_to_white(left_x, left_y, from_down=scroll_up)
    if distance is None:
        return
    py_scroll(-distance)

    # when the last two cards are reached, the card can't move toward the cursor because the scroll is at its edge.
    # thus, the cursor should move toward the card.
    SCROLLBAR_COLOR=(94,94,94)
    # TODO consider switching to checking the Y coordinate (for cards with smaller height)
    if pyautogui.pixelMatchesColor(*SCROLLBAR_REGION[:2], SCROLLBAR_COLOR):
        distance = distance_to_white(left_x, left_y, from_down=scroll_up)
        distance = distance + math.copysign(10, distance)
        new_y = left_y + distance
        if new_y <= FIRST_PLACE_CARD_TOP_Y or new_y >= LAST_PLACE_CARD_BOTTOM_Y:
            raise ValueError("corrective scroll to next card - out of bounds")
        pyautogui.moveRel(0, distance)
        return True
    
    return False


def total_scroll_down(stop_text_lang='eng'):
    """
    Scroll down untill all of the results are dynamically loaded.
    Stop when "... end of the list" string is found exactly once on the page.
    Choose relevant `stop_text` by selecting lang: [eng, ukr].

    When finished, cursor will rest at PLACE_CARD_XY.
    """
    STOP_TEXT = {
        'eng': "You've reached the end of the list",
        'ukr': "Ви переглянули весь список",
    }
    stop_text = STOP_TEXT[stop_text_lang]

    # F3FIND_X = 410
    F3FIND_CLOSE_X = 705
    F3FIND_COUNT_REGION = (570-2, 98-2, 21+5, 14+5)  # exact search_f3_count.png coordinates, adjusted for error

    refocus_page()
    pyautogui.moveTo(PLACE_CARD_XY)

    # NOTE: special case when wait_for_screen_change wouldnt work, because leading action is repeated in the same loop
    img_before_f3find = pyautogui.screenshot(region=F3FIND_COUNT_REGION)
    for i in range(4):
        pyautogui.hotkey('ctrl', 'f')
        if is_no_change(img_before_f3find, pyautogui.screenshot(region=F3FIND_COUNT_REGION)):
            time.sleep(1)
            if i==3:
                raise BufferError("f3 find couldn't be opened")
        else:
            break

    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.3)
    py_paste(stop_text)
    while True:
        # TODO maybe change to holding a click at the bottom of search result scrollbar
        pyautogui.scroll(-1000)
        time.sleep(0.4)
        pyautogui.press('f3')
        try:
            pyautogui.locateOnScreen('img/f3find_count.png', region=F3FIND_COUNT_REGION)
            pyautogui.click(x=F3FIND_CLOSE_X, y=SEARCH_Y)
            break
        except pyautogui.ImageNotFoundException:
            continue

    time.sleep(0.1)
    pyautogui.moveTo(PLACE_CARD_XY)
    