import json
from typing import ClassVar
from dataclasses import dataclass, fields, asdict
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
    # foobar.py
    @dataclass
    class Config(ConfigRegistryMixin):
        REGISTER_KEY = "foobar"
        # ...
    C = Config()
    C.register()
    ```

    If needed, specify unusual types inside the config's `DACITE_CAST_TYPES` tuple to ensure dacite.from_dict works correctly.
    Whatever the type, it should be **JSON serializable**
    ```
    class Config(ConfigRegistryMixin):
        REGISTER_KEY = "foobar"
        DACITE_CAST_TYPES = (Enum,)  # remember that one-element tuples require a comma
        # ...

    ```
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

    def deregister(self):
        """Remove `self` instance from the config register"""
        deregister(config_key=self.REGISTER_KEY)


_config_register : dict[str, ConfigRegistryMixin] = {}
"""
DO NOT use this variable to access config values. 
Those should be accessed through a *singleton-like* config instance inside a relevant file.

This variable aggregates individual configs for two things:
- making dumps
- updating existing *singleton-like* configs from the loaded dumps.
"""


def register(config_key: str, config: ConfigRegistryMixin):
    if config_key in _config_register:
        raise ValueError("Registering a config aborted - register key already exists")
    _config_register[config_key] = config


def deregister(config_key: str):
    if config_key in _config_register:
        del _config_register[config_key]


def _get_from_registry(config_key: str):
    """debug function, avoid using outside of tests"""
    return _config_register.get(config_key, None)


def dump_config(path: str = "config.json"):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {k : asdict(c) for k,c in _config_register.items()}, 
                f, 
                # cls = ConfigEncoder
                indent=2, 
                ensure_ascii=False
            )
    except TypeError as e:
        raise CustomError(
            original_exception=e,
            attention="ConfigRegistryMixin descendant *must* use JSON-serializable fields",
            fix="Taking the simple nature of this app into account, please switch to JSON-serializable field types. " \
            "For example, IntEnum instead of bare Enum."
        ) from e
    # In an unlikely event that some config CANNOT exist without a field of unserializable type,
    # and this type turns out to be common or critical enough,
    # consider adding the type to the ConfigEncoder, which is to be passed as `cls` parameter to `json.dump`

# class ConfigEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, Enum):
#             return obj.value

#         if isinstance(obj, set):
#             return list(obj)

#         return super().default(obj)


def load_config(path: str = "config.json"):
    with open(path, "r", encoding="utf-8") as f:
        data : dict[str,dict] = json.load(f)
        load_config_from_dict(data)


def load_config_from_dict(config_dict: dict[str,dict]):
    for c_key, c_dict in config_dict.items():
        if c_key not in _config_register:
            continue  # unsupported config fields are skipped
        old_c = _config_register[c_key]
        old_c._update(c_dict)  # pylint: disable=protected-access ; intended usecase
