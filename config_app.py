from dataclasses import dataclass, field
from config_registry import ConfigRegistryMixin
from config_to_tk_entries import ConfigTkMeta

@dataclass
class Config(ConfigRegistryMixin):
    "Configurations that impact the whole app"
    REGISTER_KEY = "app"
    
    SCREEN_W : int = 1366 # TODO inherit winfo_screenwidth from tk app, don't leave constant!
    SCREEN_H : int = 768  # TODO same with winfo_screenheight

    LANG : str = field(
        default='eng',
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            doc="Choose language used by google maps. Important for checking text on the page.",
            option_list=['eng']
        )}
    )

C_app = Config()
C_app.register()
