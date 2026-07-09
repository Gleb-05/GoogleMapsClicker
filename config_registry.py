import json
from typing import ClassVar
from dataclasses import dataclass, field, fields, asdict
import dacite
from utils import CustomError



COMMON_DACITE_CAST_TYPES = [tuple]  
# json serializes tuples as lists, and tuples are common across configs
# this list can be expanded per future developer's discretion

@dataclass()
class ConfigRegistryMixin:
    """
    Cornerstone or a working config register.

    Use this class as base class for specific config dataclasses.
    Specify the REGISTER_KEY and call `register` after config instantiation.

    ```
    @dataclass
    class ConfigFoobar(ConfigUpdateMixin):
        REGISTER_KEY = "foobar"
        # ...
    C = ConfigFoobar()
    C.register()
    ```

    If needed, specify unusual types inside the config's `DACITE_CAST_TYPES` tuple to ensure dacite.from_dict works correctly.
    """

    REGISTER_KEY : ClassVar[str | None] = None

    DACITE_CAST_TYPES : ClassVar[tuple] = ()

    def _update(self, data : dict):
        """Update the config instance using the `data` from the config dump. Not to be called outside of that."""
        try:
            loaded = dacite.from_dict(
                type(self),
                data,
                config=dacite.Config(cast = list(self.DACITE_CAST_TYPES) + COMMON_DACITE_CAST_TYPES)
            )
        except dacite.exceptions.WrongTypeError as e:
            raise CustomError(
                original_exception=e,
                caution="Provided config may have invalid data!",
                fix="If data is valid, consider adding the should-be type to the DACITE_CAST_TYPES field "
                "of the config that the field belongs to; " \
                "or adding that type to COMMON_DACITE_CAST_TYPES if it is common among configs") from e

        for f in fields(self):
            setattr(self, f.name, getattr(loaded, f.name))

    def register(self):
        """Add `self` instance to the config register under the `self.REGISTER_KEY`"""
        if self.REGISTER_KEY is None:
            raise ValueError("ConfigRegistryMixin descendant should specify a REGISTER_KEY string")
        register(config_key=self.REGISTER_KEY, config=self)


_config_register : dict[str, ConfigRegistryMixin] = {}
"""
DO NOT use this variable to access config values. 
Those should be accessed through a *singleton-like* config instance inside a relevant file.

This variable aggregates individual configs for two things:
- making dumps
- updating existing configs from the loaded dumps.
"""
C = _config_register

def register(config_key: str, config: ConfigRegistryMixin):
    if config_key in _config_register:
        raise ValueError("Registering a config aborted - register key already exists")
    _config_register[config_key] = config


def dump_config(path: str = "config.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({k : asdict(c) for k,c in _config_register.items()}, f, indent=2, ensure_ascii=False)


def load_config(path: str = "config.json"):
    with open(path, "r", encoding="utf-8") as f:
        data : dict = json.load(f)
        for c_field, c_dict in data.items():
            if c_field not in _config_register:
                continue  # unsupported config fields are skipped
            old_c = _config_register[c_field]
            old_c._update(c_dict)  # pylint: disable=protected-access ; intended usecase


@dataclass(frozen=True)
class ConfigTkMeta:
    """A bridge between config code and user control.

    - label: str - the name of the config value
    - doc: str - guiding or explaining text alongside the config value
    - widget_dict: dict - all info needed to make a widget to change the config value.

    Additionaly, a KEY: ClassVar[str] = "tk" is specified for consistency.
    """
    KEY: ClassVar[str] = "tk"
    """`metadata = { ConfigTkMeta.KEY: ConfigTkMeta(...) }` is the way to augment the dataclass field()."""

    label: str
    doc: str
    widget_dict: dict = field(default_factory=dict)
