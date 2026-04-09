import pyautogui

from wait_contexts import wait_for_animation_end

SIDEPANEL_Y = 425
SIDEPANEL_COLLAPSE_X = 420
SIDEPANEL_EXPAND_X = 12
SIDEPANEL_CHANGE_REGION = (0, SIDEPANEL_Y-10, 2*SIDEPANEL_EXPAND_X, 20)


def collapse_sidepanel():
    with wait_for_animation_end(SIDEPANEL_CHANGE_REGION):
        pyautogui.click(SIDEPANEL_COLLAPSE_X, SIDEPANEL_Y)


def expand_sidepanel():
    with wait_for_animation_end(SIDEPANEL_CHANGE_REGION):
        pyautogui.click(SIDEPANEL_EXPAND_X, SIDEPANEL_Y)
