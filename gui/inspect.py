import time
import pyautogui
import pyperclip

from utils import py_paste
from z_app_components.config_app import C_app
from gui.contextmenu import contextmenu_click_option
from wait_contexts import wait_for_screen_change, wait_for_screen_image, wait_for_animation_end

INSPECT_ELEMENTS_TAB_XY=548,100

# TODO
"""
inspect_find and inspect_find_and_copy_first both work on a shrinked window and expect inspect window to be open.
inspect_use_console if built for a fullscreen window workflow and manages the inspect window on its own.

It's OK for now, because the workflows for shrinked and fullscreen window dont overlap.
But the need to standardize constants and make app-wide states rises.
"""

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

    Example: when on place webpage, pass `PLACE_NAME_HTML` or `PLACE_TYPE_HTML`
    as an argument to get name or type of the place.
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
    pyautogui.rightClick(INSPECT_CONSOLE_OUTPUT_XY)
    time.sleep(0.1)
    contextmenu_click_option()
    return pyperclip.paste()


def inspect_use_console(command: str):
    """
    Open console, execute `command`, close console.
    
    The otput of `command` should not matter. Usually `command` is a `$(selector).action()` string.
    The selector must be known to be present in page's HTML.

    Example: pass "$(body > div > div).click()" to trigger a button press.

    By utilizing the console, many gui-specific actions can be successfully omitted, 
    and with that many constant become unnecessary to create! Which raises compatibility with different resolution devices.
    """
    # get rid of all the constants let's gooo
    # _x = 504  # fullscreen_x_correction
    # INSPECT_CLEAR_SUCCESS_REGION = (_x+482-5, 202-2, 70+10, 20+5)  # waiting for console clear on entire screen
    # INSPECT_CONSOLE_OUTPUT_XY=_x+490,230  # waiting for output on entire screen
    
    # open console
    if not C_app.DEVPANEL_OPEN:
        # why interval=1? One console warning takes some sweet time to show up: The service worker navigation preload request was cancelled before 'preloadResponse' settled. If you intend to use 'preloadResponse', use waitUntil() or respondWith() to wait for the promise to settle.
        with wait_for_animation_end(region=None, interval=1):
            pyautogui.hotkey('ctrl','shift','j')  
            C_app.DEVPANEL_OPEN = not C_app.DEVPANEL_OPEN  # linked to ctrl+shift+j and ctrl+shift+i. move this relationship to util function?
            time.sleep(0.3)
    # wait until console is clear
    with wait_for_animation_end(region=None, interval=0.3):
        py_paste("clear()")
        time.sleep(0.3)  # wait before enter
        pyautogui.press('enter')
    # execute command
    py_paste(command)
    with wait_for_screen_change(region=None, interval=0.3):
        time.sleep(0.3)
        pyautogui.press('enter')
    time.sleep(0.1)
    # close console
    with wait_for_animation_end(region=None):
        pyautogui.hotkey('ctrl','shift','j')  
        C_app.DEVPANEL_OPEN = not C_app.DEVPANEL_OPEN
        time.sleep(0.3)
