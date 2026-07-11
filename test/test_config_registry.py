import os
import json
import unittest
from dataclasses import dataclass, field
from enum import IntEnum

from utils import CustomError
from config_registry import dump_config, load_config, _get_from_registry, ConfigRegistryMixin

@dataclass
class ConfigNokey(ConfigRegistryMixin):
    "config with no `REGISTER_KEY` specified that should throw an error"
    int_field : int = 42

@dataclass
class ConfigDumpLoad(ConfigRegistryMixin):
    "config with `int_field` to test loading and dumping capabilities of the config registry"
    REGISTER_KEY = "test"
    int_field : int = 42

class MyEnum(IntEnum):
    "enum used as a special type that requires type casting from its json representation"
    ONE = 1
    TWO = 2
    THREE = 3

@dataclass
class ConfigTypecasting(ConfigRegistryMixin):
    "config with `enum_field` of `EnumType` to test if special types are cast correctly during loading (requires specifying DACITE_CAST_TYPES)"
    REGISTER_KEY = "test"
    enum_field : MyEnum = MyEnum.TWO

@dataclass
class ConfigNoJsonSerialization(ConfigRegistryMixin):
    "config with `set_field` to show that right now dumping configs with non-json-serializable values is NOT possible."
    REGISTER_KEY = "test"
    set_field : set = field(default_factory=lambda:{1,2,3})

@dataclass
class ConfigNest(ConfigRegistryMixin):
    "config with `dc_field` to test the registry with nested dataclasses"
    REGISTER_KEY = "test"
    dc_field : ConfigDumpLoad = field(default_factory=ConfigDumpLoad)


class UtilMixin:
    """Things to share between testcases"""

    config_path = "test_config.json"

    def setUp(self):
        self._C : ConfigRegistryMixin | None = None

    def load_json(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            data : dict = json.load(f)
        return data
    
    def dump_json(self, data: dict):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def makeC(self, C_type: ConfigRegistryMixin):
        """Create C, add it to the registry, return it"""
        C = C_type()
        C.register()
        self._C = C
        return C

    def tearDown(self):
        """Remove C from the registry and None it. Also delete the test_config.json"""
        if self._C is not None:
            self._C.deregister()
            self._C = None
        if os.path.exists(self.config_path):
            os.remove(self.config_path)


class TestDumpAndLoad(UtilMixin, unittest.TestCase):
    """
    Establish how the config registry should work with:
    - managing specific configs
    - loading and dumping
    """

    def test_nokey(self):
        with self.assertRaisesRegex(ValueError, r'.*REGISTER_KEY.*', 
                                    msg="No REGISTER_KEY in the config should raise a ValueError"):
            self.makeC(ConfigNokey)

    def test_samekey(self):
        with self.assertRaisesRegex(ValueError, r'.*register key already exists.*', 
                                    msg="Same REGISTER_KEY values in different configs should raise a ValueError"):
            self.makeC(ConfigDumpLoad)
            self.makeC(ConfigDumpLoad)

    def test_dump(self):
        C : ConfigDumpLoad = self.makeC(ConfigDumpLoad)
        dump_config(self.config_path)
        data = self.load_json()
        self.assertEqual(data[C.REGISTER_KEY]["int_field"], C.int_field, 
                         "After dump, json should be non-empty and mirror current config values")
        C.int_field = -1 * C.int_field
        dump_config(self.config_path)
        data = self.load_json()
        self.assertEqual(data[C.REGISTER_KEY]["int_field"], C.int_field, 
                         "On dump, changes from specific configs should cascade into the json")
    
    def test_load(self):
        C : ConfigDumpLoad = self.makeC(ConfigDumpLoad)
        dump_config(self.config_path)
        data = self.load_json()
        data[C.REGISTER_KEY]["int_field"] = -1 * C.int_field
        self.dump_json(data)
        load_config(self.config_path)
        C_after_load : ConfigDumpLoad = _get_from_registry(C.REGISTER_KEY)
        self.assertIs(C_after_load, C, 
                      "On load, specific configs should be updated inplace " \
                      "rather than replaced within the registry")
        self.assertEqual(C_after_load.int_field, data[C.REGISTER_KEY]["int_field"], 
                         "After load, specific configs should mirror the json")


class TestEdgecases(UtilMixin, unittest.TestCase):
    """Test config registry on special types and nested configs"""

    def test_no_json_serialization(self):
        _ : ConfigNoJsonSerialization = self.makeC(ConfigNoJsonSerialization)
        with self.assertRaisesRegex(CustomError, r'.*use JSON-serializable fields.*', 
                                    msg="Dumping a config with non-serializable fields should raise an error"):
            dump_config(self.config_path)

    def test_typecasting(self):
        C : ConfigTypecasting = self.makeC(ConfigTypecasting)
        dump_config(self.config_path)
        with self.assertRaisesRegex(CustomError, r'.*DACITE_CAST_TYPES.*', 
                                    msg="If some specific config uses a custom type, " \
                                    "it should specify it in its DACITE_CAST_TYPES tuple field."):
            load_config(self.config_path)
        C.DACITE_CAST_TYPES = (MyEnum,)
        load_config(self.config_path)
        C_after_load : ConfigTypecasting = _get_from_registry(C.REGISTER_KEY)
        assert C_after_load is C
        self.assertIsInstance(C_after_load.enum_field, MyEnum, 
                              "After load, data for fields with custom types should be correctly typecasted")

    def test_nest(self):
        C : ConfigNest = self.makeC(ConfigNest)
        before_load_dc_field = C.dc_field
        dump_config(self.config_path)
        load_config(self.config_path)
        C_after_load : ConfigNest = _get_from_registry(C.REGISTER_KEY)
        assert C_after_load is C
        self.assertIsNot(C_after_load.dc_field, before_load_dc_field, 
                         "Loading nested configs should work without error, "
                         "and only the outer configs should be updated in place")
        