from dataclasses import dataclass, field
from config_registry import ConfigRegistryMixin
from config_to_tk_entries import ConfigTkMeta


@dataclass
class Config(ConfigRegistryMixin):
    """search.py config."""
    REGISTER_KEY = "gui_search"

    SEARCH_Y : int = field(
        default=112,
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            doc="Middle height of the google maps search bar.",
            xy_read=ConfigTkMeta.READ_Y
        )}
    )
    SEARCH_BACK_X : int = field(
        default=28,
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            doc="Horisontal position of the 'back' button on the left of the search bar. "
            "This button is available ONLY IF the webpage has small width.",
            xy_read=ConfigTkMeta.READ_X
        )}
    )
    SEARCH_BAR_X : int = field(
        default=122,
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            doc="Middle width of the google maps search bar.",
            xy_read=ConfigTkMeta.READ_X
        )}
    )

    # Subtract `from xy` - pixel coordinates of marker as it appears when the sidepanel is expanded
    # from `to_xy` - coordinates of marker in the center of the screen (goes there after same page is reloaded)
    DRAG_MARKER_TO_CENTER_DISPLACEMENT_XY : tuple[int,int] = (-240,-1)

C_search = Config()
C_search.register()
