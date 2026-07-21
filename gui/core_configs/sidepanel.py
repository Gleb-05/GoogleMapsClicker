from dataclasses import dataclass, field
from config_registry import ConfigRegistryMixin
from config_to_tk_entries import ConfigTkMeta


@dataclass
class Config(ConfigRegistryMixin):
    """sidepanel.py config"""
    REGISTER_KEY = "gui_sidepanel"
    SIDEPANEL_Y : int = field(
        default=425,
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            doc="height at which the collapse-expand arrow for the sidepanel is")
    })
    SIDEPANEL_COLLAPSE_X : int = field(
        default=420,
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            doc="horisontal position of the collapse-expand arrow when sidepanel is open")
    })
    SIDEPANEL_EXPAND_X : int = field(
        default=12,
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            doc="horisontal position of the collapse-expand arrow when sidepanel is closed")
    })

    @property
    def SIDEPANEL_MINIMAL_CHANGE_REGION(self) -> tuple[int,int,int,int]:
        return (0, self.SIDEPANEL_Y-10, 2*self.SIDEPANEL_EXPAND_X, 20)

    @property
    def SIDEPANEL_CHANGE_REGION(self) -> tuple[int,int,int,int]:
        "Rectangle in the middle of the google maps sidepanel, useful for scroll checks."
        return (self.SIDEPANEL_EXPAND_X, self.SIDEPANEL_Y - 10, self.SIDEPANEL_COLLAPSE_X, 20 )
    
C_sidepanel = Config()
C_sidepanel.register()
