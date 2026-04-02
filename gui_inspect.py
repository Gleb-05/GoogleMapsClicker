import time
import pyautogui
import pyperclip

from constants import RMB_FIRST_OPTION_BELOW_RELATIVE_XY
from utils import py_paste
from wait_contexts import wait_for_screen_change, wait_for_screen_image

INSPECT_ELEMENTS_TAB_XY=548,100

def inspect_find(find_query):
    """
    Return `False` if `find_query` is absent in page's HTML. Return `True` for 1 or more occurences.
    `find_query` goes directly into inspect find, and as such can be an html selector"""
    # this region corresponds to prevbtn position unshifted by "x of x" that appears when find_query is present
    INSPECT_PREVBTN_REGION=(783-5, 698-3, 16+5, 10+10)  # FIX: browser dimension setup is wonky, think about error margins like here
    pyautogui.click(INSPECT_ELEMENTS_TAB_XY)
    pyautogui.hotkey('ctrl', 'f')
    # TODO each time.sleep can be changed to `wait_...`, but then highly specific regions need to be set
    time.sleep(0.3)
    pyautogui.hotkey('ctrl', 'a')
    py_paste(find_query)
    try:
        pyautogui.locateOnScreen("img/inspect_prevbtn.png", region=INSPECT_PREVBTN_REGION)
        return False
    except pyautogui.ImageNotFoundException:
        return True
    

def inspect_find_and_copy_first(find_query):
    """
    When using inspect find, `$0` args can be used to access what's found in the console.
    Use `$0.textContent` and click on `copy string content` in the context menu.
    `find_query` goes directly into inspect find, and as such can be an html selector.
    """
    # INSPECT_FINDBTN_XY = (760,525)
    INSPECT_CONSOLE_TAB_XY=606,100
    INSPECT_CONSOLE_OUTPUT_XY=490,230  # Context menu with X>490 may give "Clear console" as first option, leading to errors
    INSPECT_CLEAR_SUCCESS_REGION=(482-5, 202-2, 70+10, 20+5)  

    pyautogui.click(INSPECT_ELEMENTS_TAB_XY)
    for _ in range(20):
        find_success = inspect_find(find_query=find_query)
        if find_success:
            break
        time.sleep(1)
    if not find_success:
        return None
    
    pyautogui.click(INSPECT_CONSOLE_TAB_XY)
    time.sleep(0.1)
    # successful `clear()` command should give a purely white region here
    with wait_for_screen_image(INSPECT_CLEAR_SUCCESS_REGION, "img/inspect_clear_success.png"):
        py_paste("clear()")
        pyautogui.press('enter')
    py_paste("$0.textContent")
    inspect_console_output_region = *INSPECT_CONSOLE_OUTPUT_XY, 20, 20
    with wait_for_screen_change(inspect_console_output_region):
        pyautogui.press('enter')
    time.sleep(0.1)
    pyautogui.rightClick(INSPECT_CONSOLE_OUTPUT_XY, duration=0.1)
    pyautogui.moveRel(RMB_FIRST_OPTION_BELOW_RELATIVE_XY, duration=0.1)
    pyautogui.click(duration=0.1)
    time.sleep(0.1)
    return pyperclip.paste()
