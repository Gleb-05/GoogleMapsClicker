from dataclasses import dataclass, field
import pyautogui

from utils import ConfigTkMeta, ConfigUpdateMixin
from wait_contexts import wait_for_animation_end

@dataclass
class Config(ConfigUpdateMixin):
    """sidepanel.py config"""
    SIDEPANEL_Y : int = field(
        default=425,
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            "SIDEPANEL_Y", 
            "height at which the collapse-expand arrow for the sidepanel is")
    })
    SIDEPANEL_COLLAPSE_X : int = field(
        default=420,
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            "SIDEPANEL_COLLAPSE_X", 
            "horisontal position of the collapse-expand arrow when sidepanel is open")
    })
    SIDEPANEL_EXPAND_X : int = field(
        default=12,
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            "SIDEPANEL_EXPAND_X",
            "horisontal position of the collapse-expand arrow when sidepanel is closed")
    })

    @property
    def SIDEPANEL_CHANGE_REGION(self) -> tuple[int,int,int,int]:
        return (0, self.SIDEPANEL_Y-10, 2*self.SIDEPANEL_EXPAND_X, 20)

C = Config()

def collapse_sidepanel():
    with wait_for_animation_end(C.SIDEPANEL_CHANGE_REGION):
        pyautogui.click(C.SIDEPANEL_COLLAPSE_X, C.SIDEPANEL_Y)


def expand_sidepanel():
    with wait_for_animation_end(C.SIDEPANEL_CHANGE_REGION):
        pyautogui.click(C.SIDEPANEL_EXPAND_X, C.SIDEPANEL_Y)
