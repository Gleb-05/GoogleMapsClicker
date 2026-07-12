import pyautogui

from wait_contexts import wait_for_animation_end
from gui.core_configs import C_sidepanel as C


def collapse_sidepanel():
    with wait_for_animation_end(C.SIDEPANEL_MINIMAL_CHANGE_REGION):
        pyautogui.click(C.SIDEPANEL_COLLAPSE_X, C.SIDEPANEL_Y)


def expand_sidepanel():
    with wait_for_animation_end(C.SIDEPANEL_MINIMAL_CHANGE_REGION):
        pyautogui.click(C.SIDEPANEL_EXPAND_X, C.SIDEPANEL_Y)
