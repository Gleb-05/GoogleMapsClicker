import unittest
import time
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pyautogui
from PIL import Image

from usr_get_area_img import (
    iter_core_drag_displacements, 
    iter_drag_displacements, 
    drag_area, 
    addressbar_center_at_dd,
    map_get_coords_at_cursor,
    disp, 
    AREA_REGION
)


def gather_displacements(r_width: int, r_height: int):
    displacements = []
    for xy_displ in iter_core_drag_displacements(r_width, r_height):
        displacements.append(xy_displ)
    return displacements

def gather_coordinates(r_width: int, r_height: int):
    coords = []
    for xy in iter_drag_displacements(r_width, r_height, do_drag_area=False):
        coords.append(xy)
    return coords

def plot_core_path(name: str, displacements):
    _, axs = plt.subplots()
    plot_path(name, displacements, axs)
    fname = name.replace(" ", "_")
    axs.figure.savefig(f'{fname}.png', bbox_inches='tight')
    plt.close(axs.figure)

def plot_path(name, xy_list, ax: plt.Axes, lines_list: list = []):  # pylint: disable=dangerous-default-value
    x, y = zip(*xy_list)
    line, = ax.plot(x, y, marker="o", picker=5)
    ax.scatter(x[0], y[0], marker="x", color="red", s=20*2**3)
    ax.set_title(name)
    ax.invert_yaxis()
    ax.set_aspect('equal', adjustable='box')
    lines_list.append(line)


# values were taken from `test_unyielding_eyeballing` once and examined visually
expected_core_displacements: dict[str, list[tuple[int]]] = {
    # square
    "1,1": [(0,0), (0,-1), (-1,-1), (-1,0), (-1,1), (0,1), (1,1), (1,0), (1,-1)],
    # wide
    "2,1": [(0,0), (0, -1), (-1, -1), (-2, -1), (-2, 0), (-2, 1), (-1, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (2, 0), (2, -1), (1, 0), (1, -1)],
    "3,1": [(0,0), (0, -1), (-1, -1), (-2, -1), (-3, -1), (-3, 0), (-3, 1), (-2, 0), (-2, 1), (-1, 0), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1), (3, 0), (3, -1), (2, 0), (2, -1), (1, 0), (1, -1)],
    # tall
    "1,2": [(0,0), (0, -1), (0, -2), (-1, -2), (-1, -1), (-1, 0), (-1, 1), (-1, 2), (0, 2), (1, 2), (0, 1), (1, 1), (1, 0), (1, -1), (1, -2)],
    "1,3": [(0,0), (0, -1), (0, -2), (0, -3), (-1, -3), (-1, -2), (-1, -1), (-1, 0), (-1, 1), (-1, 2), (-1, 3), (0, 3), (1, 3), (0, 2), (1, 2), (0, 1), (1, 1), (1, 0), (1, -1), (1, -2), (1, -3)],
}


class TestCoreDisplacements(unittest.TestCase):
    """Test iter_core_drag_displacements from usr_get_area_img"""

    @unittest.skip("skip after using once to populate `expected_core_displacements` with confidence")
    def test_unyielding_eyeballing(self):
        for k in expected_core_displacements:
            print(k)
            w, h = k.split(",")
            w, h = int(w), int(h)
            displacements = gather_displacements(w, h)
            print(displacements)
            plot_core_path(f"{w},{h} displacement path", displacements)

    def test_assert_atleastone(self):
        for i in [2,3]:
            with self.subTest(i=i):
                with self.assertRaises(AssertionError):
                    next(iter_core_drag_displacements(i,i))

    def test_assert_nonneg(self):
        with self.assertRaises(AssertionError):
            next(iter_core_drag_displacements(-1,1))
    
    def test_square(self):
        displacements = gather_displacements(1,1)
        self.assertEqual(displacements, expected_core_displacements["1,1"])

    def test_wide_rectangle(self):
        for w in [2,3]:
            with self.subTest(w=w):
                displacements = gather_displacements(w,1)
                self.assertEqual(displacements, expected_core_displacements[f"{w},1"])

    def test_tall_rectangle(self):
        for h in [2,3]:
            with self.subTest(h=h):
                displacements = gather_displacements(1,h)
                self.assertEqual(displacements, expected_core_displacements[f"1,{h}"])


class TestDragDisplacements(unittest.TestCase):
    """Test iter_drag_displacements from usr_get_area_img"""

    def connect_pick_interactivity(self, fig: plt.Figure, lines: plt.Line2D):
        """
        Connects click events to bring one line of the graph to top temporarily.
        
        I have no idea how this works.
        """
        lines_z = [l.get_zorder() for l in lines]
        def on_pick(event: matplotlib.backend_bases.PickEvent):
            picked = event.artist
            # Reset all lines
            for l in lines:
                l.set_linewidth(1)
                l.set_alpha(0.5)
            # Highlight picked line
            picked.set_linewidth(3)
            picked.set_alpha(1.0)
            line_max_i = np.argmax(lines_z)
            line_max_z = lines_z[line_max_i]
            lines[line_max_i].set_zorder(picked.get_zorder())
            picked.set_zorder(line_max_z)

            fig.canvas.draw()
        fig.canvas.mpl_connect('pick_event', on_pick)

    @unittest.skip("skip after visual validation")
    def test_different_sizes(self):
        test_margins = [3,2,1,0]
        fig, axs = plt.subplots(1, len(expected_core_displacements), sharey=True)
        axs[0].invert_yaxis()
        lines_list = []
        for i, k in enumerate(expected_core_displacements):
            w, h = k.split(",")
            w, h = int(w), int(h)
            for j in test_margins:
                displacements = gather_coordinates(w+j, h+j)
                plot_path(f"{w+j},{h+j}", displacements, axs[i], lines_list)
        self.connect_pick_interactivity(fig, lines_list)
        plt.suptitle("Click on a line to view it")
        plt.show()   

    @unittest.skip("skip after plotting")
    def test_unyielding_eyeballing(self):
        margin = 2
        for k in expected_core_displacements:
            w, h = k.split(",")
            w, h = int(w)+margin, int(h)+margin
            displacements = gather_coordinates(w, h)
            plot_core_path(f"{2*w+1}x{2*h+1} nodes path", displacements)


class TestDragArea(unittest.TestCase):
    """test `drag_area` from usr_get_area_img"""

    @staticmethod
    def drag_shift():
        """Drag the visible area in a closed loop around the screen to see how drag imperfections accumulate.
        
        The loop happens in a 2x2 grid of visible areas.
        The loop starts in the left-upper area of this grid and goes through the following displacements:
        `[ right-down, left-up, right, down, left, right-up, left-down, up ]`

        All visible areas share one corner at the center of the grid, which is the only place shared across all steps of the loop.
        After each step a screenshot of the center of the grid is saved.
        All screenshots are saved into an image with margins between them, where one row corresponds to one complete loop.

        Before testing, search for "laduree" in google maps and hide sidebar.
        """
        # right = x positive, down = y positive
        loop_steps = [
            (disp.POS, disp.POS),
            (disp.NEG, disp.NEG),
            (disp.POS, disp.ZER),
            (disp.ZER, disp.POS),
            (disp.NEG, disp.ZER),
            (disp.POS, disp.NEG),
            (disp.NEG, disp.POS),
            (disp.ZER, disp.NEG)
        ]
        loop_repeat = 3
        r_area = 10
        area_side = 2 * r_area
    
        # prepare an image of a table with `loop_repeat` rows and `len(loop_steps)` columns
        # account for a black border around cells with `+2` margin
        cell_side = area_side + 2
        test_img = np.zeros((loop_repeat*cell_side, len(loop_steps)*cell_side, 3))
    
        # x, y of the AREA_REGION are at the left-upper corner
        x, y, w, h = AREA_REGION
        x = x + r_area
        y = y + r_area
        w = w - area_side
        h = h - area_side
        shrinked_region = (x, y, w, h)

        # Select a corner of the starting area which is the center of the 2x2 grid.
        # In this case, the left-up area of the grid is the starting area, 
        #   so its right-down corner is the center of the grid.
        x, y = x+w, y+h

        for j in range(loop_repeat):
            for i, step in enumerate(loop_steps):
                xd, yd = step
                drag_area(xd, yd, shrinked_region)
                x -= xd * w
                y -= yd * h
                area = np.asarray(pyautogui.screenshot(region=(x-r_area, y-r_area, area_side, area_side)))
                x0, y0 = i*cell_side, j*cell_side
                x1, y1 = x0 + area_side, y0 + area_side
                test_img[y0:y1, x0:x1] = area

        Image.fromarray(test_img.astype(dtype=np.uint8), mode="RGB").save("test_drag_area.png")


    @staticmethod
    def get_area_stats():
        """
        Research area deformities from map projection
        """
        x, y, w, h = AREA_REGION

        pyautogui.moveTo(x, y, duration=0.1)
        leftup_xy_dd = map_get_coords_at_cursor()
        pyautogui.moveTo(x+w, y, duration=0.1)
        rightup_xy_dd = map_get_coords_at_cursor()
        pyautogui.moveTo(x+w, y+h, duration=0.1)
        rightdown_xy_dd = map_get_coords_at_cursor()
        pyautogui.moveTo(x, y+h, duration=0.1)
        leftdown_xy_dd = map_get_coords_at_cursor()
        
        dx_left = abs(leftdown_xy_dd[0] - leftup_xy_dd[0])
        dx_right = abs(rightdown_xy_dd[0] - rightup_xy_dd[0])
        area_upwidth_dd = abs(rightup_xy_dd[0] - leftup_xy_dd[0])
        area_downwidth_dd = abs(rightdown_xy_dd[0] - leftdown_xy_dd[0])
        dwidth = area_upwidth_dd - area_downwidth_dd
        width_ratio = area_upwidth_dd / area_downwidth_dd if area_downwidth_dd != 0 else 0

        dy_up = abs(rightup_xy_dd[1] - leftup_xy_dd[1])
        dy_down = abs(rightdown_xy_dd[1] - leftdown_xy_dd[1])
        area_leftheight_dd = abs(leftdown_xy_dd[1] - leftup_xy_dd[1])
        area_rightheigth_dd = abs(rightdown_xy_dd[1] - rightup_xy_dd[1])
        dheight = area_leftheight_dd -  area_rightheigth_dd
        height_ratio = area_leftheight_dd / area_rightheigth_dd if area_rightheigth_dd != 0 else 0

        return(f"""==={leftup_xy_dd}===
    {dx_left=}\t{dx_right=}
    {area_upwidth_dd=}
    {area_downwidth_dd=}
    {dwidth=}\t{width_ratio=}
    {dy_up=}\t{dy_down=}
    {area_leftheight_dd=}
    {area_rightheigth_dd=}
    {dheight=}\t{height_ratio=}
    """)


    @staticmethod
    def area_deforms():
        """Drag from top of France downward and record area deformities caused by map projection into one file"""
        TOP = "51.019308981766414,2.1669934760145924"
        addressbar_center_at_dd(TOP)
        with open("map_projection_deforms.txt", mode="wt", encoding="utf-8") as f:
            for _ in range(50):
                stats = TestDragArea.get_area_stats()
                print(stats)
                f.write(stats)
                time.sleep(1)
                for _ in range(5):
                    drag_area(yd = disp.POS)
    

if __name__ == '__main__':
    unittest.main()
