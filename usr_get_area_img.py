from dataclasses import dataclass, field
import time
import math
from enum import IntEnum
import pyautogui
from PIL import Image
import numpy as np

from constants import REGION_1, REGION_2
from config import SCREEN_H, SCREEN_W
from utils import tab_switch, tab_new, tab_close, ConfigTkMeta
from gui_sidepanel import expand_sidepanel
from gui_search import center_on_search_result
from gui_map import drag_map, map_get_coords_at_cursor, map_toggle_sat_labels
from addressbar import addressbar_center_at_dd

@dataclass
class Config:
    """
    get_area_img.py config
    """

    # should be safely (10px) beside interactive ui elements
    # TODO consider a function to define AREA_REGION
    # using .getBoundingClientRect() to get coordinates of page elements mentioned below through console

    AREA_LEFTUP_XY : tuple[int,int] = field(
        default = (110, 145),
        metadata = {ConfigTkMeta.KEY: ConfigTkMeta(
            "AREA_LEFTUP_XY", 
            "Select leftup corner of area to be captured. From center, left until 'Layers' button, up until account icon."
        )}
    )
    AREA_RIGHTDOWN_XY : tuple[int,int] = field(
        default = (1314,724),
        metadata = {ConfigTkMeta.KEY: ConfigTkMeta(
            "AREA_RIGHTDOWN_XY",
            "Select rightdown corner of area to be captured. From center, right until '+ -' buttons, down until 'Google Maps' text."
        )}
    )

    @property
    def AREA_WIDTH(self) -> int:
        return self.AREA_RIGHTDOWN_XY[0] - self.AREA_LEFTUP_XY[0]
    @property
    def AREA_HEIGHT(self) -> int:
        return self.AREA_RIGHTDOWN_XY[1] - self.AREA_LEFTUP_XY[1]
    @property
    def AREA_REGION(self) ->  tuple[int,int,int,int]:
        """AREA WIDTH: from 'Layers' button to '+ -' buttons, AREA HEIGHT: from account icon to 'Google Maps' text."""
        return [*self.AREA_LEFTUP_XY, self.AREA_WIDTH, self.AREA_HEIGHT]

    # TODO this config is "decision", others are "measurement". Differentiate?
    AREA_EDGES : bool = field(  # Debug purposes, affects `construct_region()`
        default = False,
        metadata = {ConfigTkMeta.KEY: ConfigTkMeta(
            "AREA_EDGES",
            "Draw edges for individual areas combined within a region?"
        )}
    )

    # Depending on resolution and screen size, actual geographical coverage of the visible area will change
    # and decimal degree width and height will describe it.
    AREA_WIDTH_DD : float = 0.012115772764788004
    """Set with `estimate_area_width_and_height_dd_constants_once()`"""
    AREA_HEIGHT_DD : float = 0.0040135544595252485
    """Set """

    # TODO both AREA_WIDTH_DD and AREA_HEIGHT_DD are set with `estimate_area_width_and_height_dd_constants_once()`
    # and would need to be reset on any change to AREA_REGION. It's a gray area between constants and configurables.
    # It is not explicitly set by the user, but depends on user's actions.

    SCALE_WH : tuple[int,int] = field(
        default = (224, 16),
        metadata={ConfigTkMeta.KEY: ConfigTkMeta(
            "SCALE_WH",
            "Select region in right-down corner of the screen with a pixel-per-meter ruler"
        )}
    )
    @property
    def SCALE_REGION(self) -> tuple[int,int,int,int]:
        return (SCREEN_W-self.SCALE_WH[0], SCREEN_H-self.SCALE_WH[1], *self.SCALE_WH)

    # A 3x2 region (35 areas) was made in 85 seconds, which gives around 2.5 seconds for one area. Calculating ETA is now possible.
    AREA_TIME_SEC : float = 3.2  # TODO replace with dynamic time estimation??

C = Config()


def get_area_img(area_query: str, r_width: int = 1, r_height: int = 1):
    """
    Return an image that shows a rectangular region of the map. At the center of the region is a marker found by searching `area_query`.

    `area_query` is typically a pair of decimal lat-long coordinates, like *(48.643650, 1.921213)*.

    The screen visible around the marker is called an AREA.
    AREA_WIDTH and AREA_HEIGHT constants define an area unobstructed by the elements of google maps interface.

    `r_width` and `r_height` extend the area horizontally and vertically. They determine the final region to be captured.
    AREA_WIDTH and AREA_HEIGHT are assumed as units for `r_width` and `r_height`, respectively.
    """
    center_on_search_result(area_query)   
    final_img = construct_region(r_width, r_height)
    Image.fromarray(final_img.astype(dtype=np.uint8), mode="RGB").save("area_img.png")
    return final_img


def construct_region(r_width: int = 1, r_height: int = 1):
    """
    Construct a rectangular region by screenshotting visible areas in a hamilton path and combining the screenshots.
    The path covers everything from area at `(-r_width, -r_height)` to area at `(r_width, r_height)`, relative to a center area.

    `construct_region` should be called when 
    - the screen shows the center area of the rectangular region
    - the sidepanel is collapsed (will be expanded on function end)
    - the zoom level and the map type are selected
    """
    final_img = np.zeros(((1+2*r_height)*C.AREA_HEIGHT, (1+2*r_width)*C.AREA_WIDTH, 3), dtype=np.uint8)
    for x,y in iter_drag_displacements(r_width, r_height):
        area = np.asarray(pyautogui.screenshot(region=C.AREA_REGION), dtype=np.uint8)
        x0, y0 = x*C.AREA_WIDTH, y*C.AREA_HEIGHT
        x1, y1 = x0 + C.AREA_WIDTH, y0 + C.AREA_HEIGHT
        final_img[y0:y1, x0:x1] = area
        fir = final_img[y0:y1, x0:x1]  # final image region
        if C.AREA_EDGES:
            fir[0, :] = fir[-1, :] = fir[:, 0] = fir[:, -1] = (0, 0, 0)
    expand_sidepanel()
    return final_img


def yx_dd_str_to_float(yx_dd: str):
    """Return a tuple of floats from a string defining a comma-separated pair of decimal degree coordinates"""
    return (float(c) for c in yx_dd.split(","))


def get_dd_rect_img(leftup_yx_dd: str, rightdown_yx_dd: str, use_const_area_dims_dd = True, satellite=False):
    """
    Return an image that shows a rectangular region of the map.
    `leftup_yx_dd` and `rightdown_yx_dd` define the corners of the region.
    Both arguments should be a string defining a comma-separated pair of decimal degree coordinates.

    The image is constructed by combining entire areas, defined by AREA_WIDTH_DD and AREA_HEIGHT_DD
    For that reason, `leftup_dd` and `rightdown_dd` can be approximate.
    """
    # TODO i have no idea why, but google maps now often freezes,
    # switching the tab forward and back seems to break the freeze.
    tab_new()
    tab_switch(to_left=True)
    
    t_start = time.perf_counter()

    lu_y, lu_x = yx_dd_str_to_float(leftup_yx_dd)
    rd_y, rd_x = yx_dd_str_to_float(rightdown_yx_dd)
    w = rd_x - lu_x
    h = rd_y - lu_y

    cx = lu_x+w/2
    cy = lu_y+h/2
    addressbar_center_at_dd(f"{cy},{cx}", satellite=satellite)
    if satellite:
        map_toggle_sat_labels()

    if use_const_area_dims_dd:
        area_width_dd, area_height_dd = C.AREA_WIDTH_DD, C.AREA_HEIGHT_DD
    else:
        # takes more time, brings little accuracy
        area_width_dd, area_height_dd = get_area_dd_wh()

    r_width = estimate_r_dim(w, area_width_dd)
    r_height = estimate_r_dim(h, area_height_dd)
    print(f"{r_width}x{r_height} => ETA {(1+2*r_width)*(1+2*r_height)*C.AREA_TIME_SEC/60:.2f}m")
    
    # TODO tab juggling
    tab_switch()
    # on tab_switch the 'sidepanel' label shows up. simple click solves the issue
    tab_switch(to_left=True)
    pyautogui.click(duration=0.1)

    final_img = construct_region(r_width, r_height)

    Image.fromarray(final_img.astype(dtype=np.uint8), mode="RGB").save(
        f"region_{leftup_yx_dd}_{rightdown_yx_dd}_" +
        f"{'sat' if satellite else 'map'}_" +
        time.strftime(r'%d.%m.%Y_%H.%M.%S') +
        ".png")

    t_end = time.perf_counter()
    print(f"get_dd_rect_img: {r_width}x{r_height} region - {t_end-t_start:.6f} sec")

    # TODO tab juggling
    tab_switch()
    tab_close()

    return final_img


def get_area_scale():
    """Get an image of map's scale (pixel distance to real distance)"""
    return pyautogui.screenshot(region=C.SCALE_REGION)


def get_area_dd_wh():
    """
    Get width and height of an area at current resolution in decimal degrees
    
    Potentially use in `get_dd_rect_img`. See corresponding md file for width-height samples.
    """
    leftup_xy = C.AREA_REGION[0], C.AREA_REGION[1]
    rightdown_xy = leftup_xy[0] + C.AREA_WIDTH, leftup_xy[1] + C.AREA_HEIGHT
    
    pyautogui.moveTo(leftup_xy, duration=0.1)
    time.sleep(0.1)
    leftup_xy_dd = map_get_coords_at_cursor()
    pyautogui.moveTo(rightdown_xy, duration=0.1)
    time.sleep(0.1)
    rightdown_xy_dd = map_get_coords_at_cursor()
    
    area_width_dd = abs(rightdown_xy_dd[0] - leftup_xy_dd[0])
    area_height_dd = abs(rightdown_xy_dd[1] - leftup_xy_dd[1])
    # area_width_dd, area_height_dd = round(area_width_dd, 6), round(area_height_dd, 6)
    time.sleep(0.3)
    return area_width_dd, area_height_dd


def estimate_r_dim(region_dim_dd, area_dim_dd):
    """
    For either dim=width or dim=height, 
    estimate minimal `r_dim` such that `(1 + 2*r_dim) * area_dim_dd >= region_dim_dd`.

    Solution: `math.ceil((abs(region_dim_dd) - area_dim_dd) / (2*area_dim_dd))`.
    
    This is an inverse of the `estimate_area_dim_dd_bounds` function.
    """
    return math.ceil((abs(region_dim_dd) - area_dim_dd) / (2*area_dim_dd))


def estimate_area_dim_dd_bounds(region_dim_dd, r_dim):
    """
    For either dim=width or dim=height, 
    return tuple of (lower, upper) bounds 
    such that for `area_dim_dd` within those bounds 
    the `(1 + 2*r_dim) * area_dim_dd >= region_dim_dd` inequality holds true.

    Solution: `abs(region_dim_dd) / (<lower=3, upper=1> + 2 * (r_dim - 1))`.

    This is an inverse of the `estimate_r_dim` function.
    """
    lower_bound = abs(region_dim_dd) / (3 + 2 * (r_dim - 1))
    upper_bound = abs(region_dim_dd) / (1 + 2 * (r_dim - 1))
    return (lower_bound, upper_bound)


def estimate_area_width_and_height_dd_constants_once(area_width_dd = 0.0129175, area_height_dd = 0.0041041):
    """
    With initial `area_width_dd` and `area_height_dd` provided by `get_area_dd_wh()`, 
    use `REGION_1` and `REGION_2` values to estimate `AREA_WIDTH_DD` and `AREA_HEIGHT_DD` constants. 
    They shall satisfy the `(1 + 2*r_dim) * area_dim_dd >= region_dim_dd` inequality.

    Steps:
    - `estimate_r_dim()` is used to get the initial estimation of `r_dim`.
    - `estimate_area_dim_dd_bounds()` is used to estimate bounds for the constants.
    - Let `lower_1`, `upper_1`, `lower_2`, `upper_2` be chosen in a way that defines two nested intervals.
      A point that divides both intervals in equal proportion 
      will become the value of the relevant area_dim_dd constant.
    """
    (lu_y_1, lu_x_1), (rd_y_1, rd_x_1) = (yx_dd_str_to_float(yx_dd_str) for yx_dd_str in REGION_1)
    (lu_y_2, lu_x_2), (rd_y_2, rd_x_2) = (yx_dd_str_to_float(yx_dd_str) for yx_dd_str in REGION_2)
    w1 = rd_x_1 - lu_x_1
    h1 = rd_y_1 - lu_y_1
    w2 = rd_x_2 - lu_x_2
    h2 = rd_y_2 - lu_y_2

    r_width_1 = estimate_r_dim(w1, area_width_dd)
    r_height_1 = estimate_r_dim(h1, area_height_dd)
    r_width_2 = estimate_r_dim(w2, area_width_dd)
    r_height_2 = estimate_r_dim(h2, area_height_dd)

    area_w_bounds_1 = estimate_area_dim_dd_bounds(w1, r_width_1)
    area_w_bounds_2 = estimate_area_dim_dd_bounds(w2, r_width_2)
    area_h_bounds_1 = estimate_area_dim_dd_bounds(h1, r_height_1)
    area_h_bounds_2 = estimate_area_dim_dd_bounds(h2, r_height_2)

#     print(f"""{area_w_bounds_1=}
# {area_w_bounds_2=}
# {area_h_bounds_1=}
# {area_h_bounds_2=}"""
#     )

    def find_proportional_division(l1, u1, l2, u2):
        # arrange to have nested intervals: [l1 l2 u2 u1]
        l1, l2 = min(l1, l2), max(l1, l2)
        u1, u2 = max(u1, u2), min(u1, u2)
        assert l1 <= l2 <= u2 <= u1, "making nested intervals failed"
        # print(l1,l2,u2,u1)
        interval = u1 - l1
        d_upper = u1 - u2
        d_lower = l2 - l1
        return u1 - (interval * d_upper) / (d_upper + d_lower)
    
    area_width_dd_const = find_proportional_division(*area_w_bounds_1, *area_w_bounds_2)
    area_height_dd_const =  find_proportional_division(*area_h_bounds_1, *area_h_bounds_2)

    return area_width_dd_const, area_height_dd_const


class disp(IntEnum):
    """
    Define three main displacement options:
    - POS: in a positive direction
    - NEG: in a negative direction
    - ZER: zero displacement

    X increases from left to right, Y increases from top to bottom.
    """
    POS = 1
    NEG = -1
    ZER = 0


def drag_area(xd=disp.ZER, yd=disp.ZER, area_region = C.AREA_REGION):
    """
    For currently displayed area at (x,y), perform dragging to view area at (x+xd, y+yd).
    AREA_WIDTH and AREA_HEIGHT are assumed as units for `xd` (horizontal) and `yd` (vertical) displacements, respectively.
    
    If `xd == 1`, for example, then `drag_area` will show an area to the right of the current area.
    *It is already accounted for that for a positive displacement the drag should be negative.*
    """
    area_width = area_region[2]
    area_height = area_region[3]

    x_from = x_to = area_region[0]
    if xd==disp.POS:
        x_from += area_width
    elif xd==disp.NEG:
        x_to += area_width

    y_from = y_to = area_region[1]
    if yd==disp.POS:
        y_from += area_height
    elif yd==disp.NEG:
        y_to += area_height
    
    drag_map(x_from, y_from, x_to, y_to)


def core_dimensions(r_width: int, r_height: int):
    """
    Derive smallest possible "core dimensions" for which the difference is equal to `r_width - r_height`.
    For example
    - core_dimensions(7, 5) => (3,1)
    - core_dimensions(4, 9) => (1,6)
    - core_dimensions(1, 1) => (1,1)
    """
    diff = min(r_width, r_height)
    core_width, core_height = 1 + r_width - diff, 1 + r_height - diff
    return core_width, core_height


def iter_core_drag_displacements(r_width: int, r_height: int, do_drag_area: bool = False):
    """
    Starting from the reference area at (cx, cy), 
    generate a sequence of relative displacements `(rel_x, rel_y)` 
    to visit all surrounding areas EXACTLY once.
    Pass `do_drag_area = True` to do `drag_area(xd, yd)` immediately during the generation of the sequence.
    
    Surrounding areas should be within the smallest possible core rectangle for which the difference between sides is equal to  `r_width - r_height`.
    At least one of `r_height` or `r_width` should be equal to 1.

    Conclude (rel_x, rel_y) generation at (1, -core_height) to ensure continuous dragging by other methods.

    The core rectangle, if `r_width > r_height`:
        - `core_width = r_width - r_height + 1` and `core_height = 1`
        - Top-left corner: `(c_x - core_width, c_y - 1)`
        - Width:  `2 * core_width + 1`
        - Height: `3`
    
    For `r_height > r_width`, similar reasoning applies.

    AREA_WIDTH and AREA_HEIGHT are assumed as units for `xd` (horizontal) and `yd` (vertical) displacements, respectively.
    """
    # begin at reference area
    rel_x, rel_y = 0, 0
    assert r_width==1 or r_height==1, "iter_core_drag_displacements expects at least one of r_width or r_height to equal 1"
    assert r_width>=1 and r_height>=1, "iter_core_drag_displacements expects both argument to be equal or greater than 1"
    yield rel_x, rel_y

    def move(disp_x: disp, disp_y: disp, do_drag_area = do_drag_area):
        """
        Update and return rel_x and rel_y using disp_x and disp_y.
        """
        nonlocal rel_x, rel_y
        rel_x += disp_x
        rel_y += disp_y
        if do_drag_area:
            drag_area(disp_x, disp_y)
        return rel_x, rel_y

    # move up
    while rel_y > r_height * -1:
        yield move(disp.ZER, disp.NEG)

    # upper edge center, move left
    while rel_x > r_width * -1:
        yield move(disp.NEG, disp.ZER)

    # upper edge left corner, move down
    while rel_y < r_height:
        yield move(disp.ZER, disp.POS)

    # lower edge left corner, zigzag to center (right)
    while rel_x < -1:
        yield move(disp.POS, disp.NEG)
        yield move(disp.ZER, disp.POS)

    # lower edge center, move right
    while rel_x < r_width:
        yield move(disp.POS, disp.ZER)

    # lower edge right corner, zigzag to center (up)
    while rel_y > 1:
        yield move(disp.NEG, disp.NEG)
        yield move(disp.POS, disp.ZER)

    # right edge center, move up
    while rel_y > r_height * -1:
        yield move(disp.ZER, disp.NEG) 

    # upper edge right corner, zigzag to center (left)
    while rel_x > 1:
        yield move(disp.NEG, disp.POS)
        yield move(disp.ZER, disp.NEG)

    # stop at relative (1, -r_height)
    # move on to the next r_height (increase radius)


def iter_enclose_drag_displacement(r_width: int, r_height: int = 0, do_drag_area: bool = False):
    """Starting from an area at (cx+1, cy - (r_height - 1)), 
    generate a sequence of relative displacements `(rel_x, rel_y)` 
    to visit all areas that enclose a ***r_width-by-r_height* rectangle for which (cx, cy - r_height) is a center of the upper edge**.
    Pass `do_drag_area = True` to do `drag_area(xd, yd)` immediately during the generation of the sequence.
    
    `iter_enclose_drag_displacement` is used after the `iter_core_drag_displacement` or another `iter_enclose...`.
    This determines the (cx+1, cy - (r_height-1)) starting area and the (cx, cy) reference point for the displacements.

    Conclude (rel_x, rel_y) generation at (1, -r_height) to ensure continuous dragging by other methods.
    
    AREA_WIDTH and AREA_HEIGHT are assumed as units for `xd` (horizontal) and `yd` (vertical) displacements, respectively.
    """
    # begin at starting area
    rel_x, rel_y = 1, 1 - r_height

    def move(disp_x: disp, disp_y: disp, do_drag_area = do_drag_area):
        """
        Update and return rel_x and rel_y using disp_x and disp_y.
        """
        nonlocal rel_x, rel_y
        rel_x += disp_x
        rel_y += disp_y
        if do_drag_area:
            drag_area(disp_x, disp_y)
        return rel_x, rel_y

    # initial move to relative coordinates (0, -r_height)
    yield move(disp.NEG, disp.NEG)
    
    # upper edge center, move left
    while rel_x > r_width * -1:
        yield move(disp.NEG, disp.ZER)

    # upper edge left corner, move down
    while rel_y < r_height:
        yield move(disp.ZER, disp.POS)
    
    # lower edge left corner, move right
    while rel_x < r_width:
        yield move(disp.POS, disp.ZER)

    # lower edge right corner, move up
    while rel_y > r_height * -1:
        yield move(disp.ZER, disp.NEG)

    # upper edge right corner, move to center (left)
    while rel_x > 1:
        yield move(disp.NEG, disp.ZER)


def iter_drag_displacements(r_width: int, r_height: int, do_drag_area: bool = True):
    """Starting from the reference area at the Center, yield coordinates `(x, y)` for all surrounding areas 
    within a rectangle defined as follows:
    - Center: `c_x = r_width` and `c_y = r_height`
    - Top-left corner: `(c_x - r_width, c_y - r_height)`
    - Width:  `2 * r_width + 1`
    - Height: `2 * r_height + 1`

    The coordinates are positive indices starting from 0, meaning that they can be used to arrange the yielded areas in a correct order.

    Pass `do_drag_area = True` to do `drag_area(xd, yd)` immediately during the generation of coordinates.

    AREA_WIDTH and AREA_HEIGHT are assumed as units for `r_width` and `r_height`, respectively.
    """
    x, y = r_width, r_height
    if x == y == 0:
        yield 0, 0
        return

    core_width, core_height = core_dimensions(r_width, r_height)
    for core_rel_x, core_rel_y in iter_core_drag_displacements(core_width, core_height, do_drag_area):
        yield x + core_rel_x, y + core_rel_y

    # iter_core concludes at relative (0, -core_height - 1) where iter_enclose picks up
    y_offset = core_height + 1
    while y_offset <= r_height:
        enclose_width = r_width - (r_height - y_offset)
        for enclose_rel_x, enclose_rel_y in iter_enclose_drag_displacement(enclose_width, y_offset, do_drag_area):
            yield x + enclose_rel_x, y + enclose_rel_y
        y_offset += 1
