from dataclasses import dataclass, field
import pyautogui

from config_registry import ConfigTkMeta, ConfigRegistryMixin
from wait_contexts import wait_for_animation_end

@dataclass
class Config(ConfigRegistryMixin):
    """sidepanel.py config"""
    REGISTER_KEY = "gui_sidepanel"
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
    def SIDEPANEL_MINIMAL_CHANGE_REGION(self) -> tuple[int,int,int,int]:
        return (0, self.SIDEPANEL_Y-10, 2*self.SIDEPANEL_EXPAND_X, 20)

    @property
    def SIDEPANEL_CHANGE_REGION(self) -> tuple[int,int,int,int]:
        """
        Rectangle somewhere in the middle of the google maps interface, useful for scroll checks.

        Notice how this value unexpectedly shows up in usr_extract_place_info. This constant takes on 
        more responsibilities than its name suggests, and cannot simply be put in a config file.

        I am not sure how to handle this behavior yet. But, in some way, usr_extract_place_info and py_scroll would
        share a CONTEXT. There is a search panel, and it doesn't move, so the scrollbar doesn't move also. Making
        the SEARCH_SCREEN_CHANGE_REGION a context that multiple parts of the program can address, 
        as opposed to passing directly as an argument.

        Also also, the need to share such elusive states would disappear 
        after transitioning to page manipulation through console.
        """
        return (self.SIDEPANEL_EXPAND_X, self.SIDEPANEL_Y - 10, self.SIDEPANEL_COLLAPSE_X, 20 )

C = Config()
C.register()
C_sidepanel = C  # alias

def collapse_sidepanel():
    with wait_for_animation_end(C.SIDEPANEL_MINIMAL_CHANGE_REGION):
        pyautogui.click(C.SIDEPANEL_COLLAPSE_X, C.SIDEPANEL_Y)


def expand_sidepanel():
    with wait_for_animation_end(C.SIDEPANEL_MINIMAL_CHANGE_REGION):
        pyautogui.click(C.SIDEPANEL_EXPAND_X, C.SIDEPANEL_Y)
