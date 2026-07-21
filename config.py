from dataclasses import dataclass, field
from config_registry import ConfigRegistryMixin
from config_tk_bridge import ConfigTkMeta

@dataclass
class Config(ConfigRegistryMixin):
    "Configurations that impact the whole app"
    REGISTER_KEY = "app"
    
    SCREEN_W : int = 1366 # TODO inherit winfo_screenwidth from tk app, don't leave constant!
    SCREEN_H : int = 768  # TODO same with winfo_screenheight

    LANG : str = field(
        default='eng',
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            doc="Choose language of google maps. Supported: ['eng']"
        )}
    )

C_app = Config()
C_app.register()
