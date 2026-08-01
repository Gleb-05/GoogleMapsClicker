# Config registry creation

The nature of the app requires the configs to be editable. This was achieved through the following:

1. MVP, rapid development - Constants in individual functions, in individual files. Changing constants inplace wouldn't propagate.
2. Increase discoverability - Constants atop each file, residual constants in rarely used functions
3. Prepare to make one config object - Constants are stored in config dataclass atop each file, its single instance used across files. Changing a constant through the config dataclass instance propagates!
4. Config registry - Define `ConfigRegistryMixin`, store all config instances in a single dictionary.
5. Dump/load the config - Define `LoadFromJsonMixin`, use `dacite` and `json.dump / json.load`

As a result, all configurable constants became discoverable, changeable, and load-dump available. See [`config_registry`](config_registry.py)

# Exposings configs to user

Config dataclasses couldn't be exposed to the user without some adjustments. Biggest problem - conversion between string values from tk entries and pure config values. Solution - leverage `json.loads` and `json.dumps`. 

Bad alternative - write `if type int: var = tk.IntVar, elif type bool: var = tk.BoolVar ...entry = tk.Entry(variable=var)` to create all entries and then write `if type int: return int(entry.get()) elif type bool: return bool(entry.get()) elif: ...` to read values from them into the config registry. <br>
Notice that the existing conversions defined by `json.dumps` and `json.loads` already covers this boring code. Also, using `json` is a great opportunity to standarsize how values are handled in both user interface AND config dumping/loading.

6. With `json`, it becomes possible to make everything work with strings. With strings, there is no need to choose tk widgets - just use tk.StringVar, which can be linked to an Entry or an OptionMenu. So, `json.loads` and `json.dumps` is a part of every entry's `get` and `set` exposed to the user.

Second biggets problem - the user cannot read the name of a config field and know what is meant by it or what value should they provide.

7. See `ConfigTkMeta` and `build_field_editor` in [`config_to_tk_entries`](config_to_tk_entries.py). `ConfigTkMeta` is attached to metadata of config fields, used to generate user-friengly tk interfaces.

Later, due to how jsonified string values look in the entries, with escape sequences and quotation marks and such, a [`json_string_var`](json_string_var.py) was introduces.

# IMPORTANT: Why config dataclasses have so many signatures

Working with dataclass configs offers considerable control over which values go where:

- `FIELD = value` - the field remains useful to the code, internal in a sence that it's neither exposed to the load/dump nor to the user.
- `@property` - the field is derived from other fields, it's neither exposed to load/dump nor to the user.
- `FIELD : type = value` - the field joins the load/dump, showing up in config files
- `FIELD : type = field(default=value, metadata={ConfigTkMeta..})` - the field obviously joins the load/dump, now carrying additional information about an entry in tk interface through which the user can see and change its value.

## SIDENOTE: Config fields that require recomputing

Sometimes there is a config field that has to be recomputed. It's in a gray area between properties and user interface - it is computed semi-automatically, but requires user decision.

Right now, it's AREA_WIDTH_AND_HEIGHT_DD in usr_get_area_img.py and DEFAULT_CONFIG in config_app.py. Just two cases, but they deserved to get `ConfigRecomputeMeta` (see [`config_to_tk_entries`](config_to_tk_entries.py)).

# Preferences are different from configs

Preferences are handled separately (saved to a separate file with a separate button), because in some sence they are meta-configs. For example, saving `default_config` into a config file would be pointless, since on app launch each config file would simply state that it is the `default_config`. See [`config_app.py`](config_app.py)

# Exposing functions to the user

With `config_to_tk_entries` in place, setting up `build_function_editor` was mostly copypasting. See [`function_to_tk_entries.py`](function_to_tk_entries.py). Entries to provide arguments to a given function are generated all the same.

# There is still work

Not all files in the [gui folder](../gui/) have a config object. Only those needed for `get_dd_rect_img` have, and they already expose what's necessary to the user with `ConfigTkMeta`.

Unfortunately, usr_extract_place_info requires great configuration effort (about 20 values and some screenshots) compared to `get_dd_rect_img` (9 values). Also, it relies on finding where to click using images. There is a way to reduce the configuration effort by interacting with the page through the console. But at that point, why not use Playwright or Selenium? For that reason, usr_extract_place_info, while a good showcase of gui automation, was abandoned together with configs that it requires. Sad.