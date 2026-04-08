import time
from enum import IntEnum
import pyautogui

# x: from 'Layers' button to '+ -' buttons, y: from account icon to 'Google Maps' text.
AREA_WIDTH = 1314-100
AREA_HEIGHT = 724-140
AREA_REGION = (100, 140, AREA_WIDTH, AREA_HEIGHT)

def get_area_img():
    """With side pannel collapsed, make a screenshot of the map area."""
    return "image"


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


def drag_area(xd=disp.ZER, yd=disp.ZER):
    """
    For currently displayed area at (x,y), perform dragging to view area at (x+xd, y+yd).
    AREA_WIDTH and AREA_HEIGHT are assumed as units for `xd` (horizontal) and `yd` (vertical) displacements, respectively.
    
    If `xd == 1`, for example, then `drag_area` will show an area to the right of the current area.
    *It is already accounted for that for a positive displacement the drag should be negative.*
    """
    x_from = x_to = AREA_REGION[0]
    if xd==disp.POS:
        x_from += AREA_WIDTH
    elif xd==disp.NEG:
        x_to += AREA_WIDTH

    y_from = y_to = AREA_REGION[1]
    if yd==disp.POS:
        y_from += AREA_HEIGHT
    elif yd==disp.NEG:
        y_to += AREA_HEIGHT
    
    pyautogui.moveTo(x_from, y_from)
    pyautogui.dragTo(x_to, y_to, 1)
    time.sleep(0.1)


def core_dimensions(r_width: int, r_height: int):
    """
    Derive smallest possible "core dimensions" for which the difference is equal to `abs(r_width - r_height)`.
    For example
    - core_dimensions(7, 5) => (3,1)
    - core_dimensions(4, 9) => (1,6)
    - core_dimensions(1, 1) => (1,1)
    """
    diff = abs(r_width - r_height)
    core_width, core_height = diff + 1, 1
    if r_height > r_width:
        core_width, core_height = core_height, core_width
    return core_width, core_height


def iter_core_drag_displacements(r_width: int, r_height: int, do_drag_area: bool = False):
    """
    Starting from the reference area at (cx, cy), 
    generate a sequence of relative displacements `(rel_x, rel_y)` 
    to visit all surrounding areas EXACTLY once.
    Pass `do_drag_area = True` to do `drag_area(xd, yd)` immediately during the generation of the sequence.
    
    Surrounding areas should be within the smallest possible core rectangle for which the difference between sides is equal to  `abs(r_width - r_height)`.
    
    Conclude (rel_x, rel_y) generation at (0, -core_height - 1) to ensure continuous dragging by other methods.

    The core rectangle, if `r_width > r_height`:
        - `core_width = r_width - r_height + 1` and `core_height = 1`
        - Top-left corner: `(c_x - core_width, c_y - 1)`
        - Width:  `2 * core_width + 1`
        - Height: `3`
    
    For `r_height > r_width`, similar reasoning applies.

    At least one of `r_height` or `r_width` should be equal to 1.

    AREA_WIDTH and AREA_HEIGHT are assumed as units for `xd` (horizontal) and `yd` (vertical) displacements, respectively.
    """
    # begin at reference area
    rel_x, rel_y = 0, 0
    assert r_width==1 or r_height==1, "iter_core_drag_displacements expects at least one of r_width or r_height to equal 1"

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

    # final move to an area directly above the upper edge center
    yield move(disp.NEG, disp.NEG)


def iter_enclose_drag_displacement(r_width: int, r_height: int = 0, do_drag_area: bool = False):
    """Starting from an area at (cx, cy - r_height), 
    generate a sequence of relative displacements `(rel_x, rel_y)` 
    to visit all areas that enclose a *r_width-by-r_height* rectangle for which the starting area is a center of the upper edge.
    Pass `do_drag_area = True` to do `drag_area(xd, yd)` immediately during the generation of the sequence.
    
    `iter_enclose_drag_displacement` is assumed to be used after the `iter_core_drag_displacement`.
    This determined the (cx, cy - r_height) starting area and the (cx, cy) reference point for the displacements.

    Conclude (rel_x, rel_y) generation at (0, -r_height - 1) to ensure continuous dragging by other methods.
    
    AREA_WIDTH and AREA_HEIGHT are assumed as units for `xd` (horizontal) and `yd` (vertical) displacements, respectively.
    """
    # begin at starting area
    rel_x, rel_y = 0, -r_height

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

    # final move to an area directly above the upper edge center
    yield move(disp.NEG, disp.NEG)


def iter_drag_displacements(r_width: int, r_height: int, do_drag_area: bool = True):
    """Starting from the reference area at the Center, yield coordinates `(x, y)` for all surrounding areas 
    within a rectangle defined as follows:
    - Center: `c_x = r_width` and `c_y = r_height`
    - Top-left corner: `(c_x - r_width, c_y - r_height)`
    - Width:  `2 * r_width + 1`
    - Height: `2 * r_height + 1`

    Pass `do_drag_area = True` to do `drag_area(xd, yd)` immediately during the generation of coordinates.

    AREA_WIDTH and AREA_HEIGHT are assumed as units for `xd` (horizontal) and `yd` (vertical) displacements, respectively.
    """
    # those coordinates can be used to arrange yielded areas into one using array syntax
    x, y = r_width, r_height

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
