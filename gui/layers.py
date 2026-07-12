from gui.inspect import inspect_use_console

LABELS_BUTTON_SELECTOR : str = "body > div:nth-child(5) > div.lbMcOd.y2iKwd.cSgCkb.qK6Xvf.znKqMd.Nkjr6c.K1N2o > div.UL7Qtf > div.seN1Zd.Hk4XGb > div > div > div > div.yYTQHb > ul > li:nth-child(2) > button"
SWITCHVIEW_BUTTON_SELECTOR : str = "body > div:nth-child(5) > div.lbMcOd > div.UL7Qtf > div.jsXHHe.i2s2Oe > div.t090lc.pEO5hf > div > div > button"
# TODO both values above feel like PLACE_TYPE_HTML and PLACE_NAME_HTML - move to separate file?

def map_toggle_sat_labels():
    """
    With satellite map selected, toggle displaying of roads and landmarks using the inspect console.
    """
    inspect_use_console(f"$('{LABELS_BUTTON_SELECTOR}').click()")


def map_switch_view():
    """Switch from map to sat view or from sat to map view using the inspect console"""
    inspect_use_console(f"$('{SWITCHVIEW_BUTTON_SELECTOR}').click()")
