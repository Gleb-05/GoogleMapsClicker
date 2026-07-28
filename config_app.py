from dataclasses import dataclass, field
from config_registry import ConfigRegistryMixin
from config_to_tk_entries import ConfigTkMeta

@dataclass
class Config(ConfigRegistryMixin):
    "Configurations that impact the whole app" 
    # TODO this one should be persisted - change saving and loading procedure.
    REGISTER_KEY = "app"

    LANG : str = field(
        default='eng',
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            doc="Choose language used by google maps. Important for checking text on the page.",
            option_list=['eng']
        )}
    )

@dataclass
class SizeConfig(ConfigRegistryMixin):
    '''Register winfo width and height to contextualize the rest of the config'''
    # maybe revisit this piece of code. can't get rid of it for now
    REGISTER_KEY = "size"
    SCREEN_W : int = 1366
    SCREEN_H : int = 768

C_size = SizeConfig()
C_size.register()

C_app = Config()
C_app.register()
