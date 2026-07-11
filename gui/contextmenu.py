import time
import pyautogui


FIRST_OPTION_RELATIVE_XY = (60, 25)


def contextmenu_click_option(
        rel_y = FIRST_OPTION_RELATIVE_XY[1], 
        menu_snaps_to_screen_bottom = False, 
        y_cutoff: int = None, 
        context_height = 0
    ):
    """
    Click any option of the context menu that appears after right click. First option is targeted by default.

    `rel_y` is a relative vertical distance to the targeted option from the top of the context menu.
    Change it to click options further than the first one.

    It is assumed the context menu appears below the cursor.
    Context menus with large height behave differently closer to the screen bottom.
    
    Choose which arguments to provide based on two possible behaviors:

    - Context menu snaps to the screen bottom.
    Its first option maintains constant distance from the screen bottom - `y_cutoff`. <br>
    Opening the context menu with a `(x,y)` click where `y > y_cutoff`
    is guaranteed to make the first option clickable at `y_cutoff + rel_y` <br>
    Provide `menu_snaps_to_screen_bottom = True` and `y_cutoff`
    
    - After falling below a certain `y_cutoff`, context menu reorients itself and appears above the cursor.
    Its first option maintains constant distance from the cursor - `context_height`. <br>
    Opening the context menu with a `(x,y)` click where `y > y_cutoff`
    is guaranteed to make the first option clickable at `y - context_height + rel_y`. <br>
    Provide `y_cutoff` and `context_height`
    """
    pyautogui.moveRel(FIRST_OPTION_RELATIVE_XY[0], rel_y)
    
    _, y = pyautogui.position()
    if menu_snaps_to_screen_bottom:
        target_option_y = y_cutoff + rel_y
    else:
        target_option_y = y - context_height + rel_y

    if y_cutoff is not None and y >= y_cutoff:
        pyautogui.moveTo(None, target_option_y)
    
    pyautogui.click()
    time.sleep(0.1)
