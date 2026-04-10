import unittest
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pyautogui
from PIL import Image

from usr_get_area_img import iter_core_drag_displacements, iter_drag_displacements, drag_area, disp, AREA_REGION


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

def plot_core_path(name, displacements):
    _, axs = plt.subplots()
    plot_path(name, displacements, axs)
    axs.figure.savefig(f'{name}.png', bbox_inches='tight')
    plt.close(axs.figure)

def plot_path(name, xy_list, ax: plt.Axes, lines_list: list = []):  # pylint: disable=dangerous-default-value
    x, y = zip(*xy_list)
    line, = ax.plot(x, y, marker="o", picker=5)
    ax.scatter(x[0], y[0], marker="x", color="red", s=20*2**5)
    ax.set_title(f"\"{name}\" displacements path")
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
            plot_core_path(k, displacements)

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
        Connects click events to bring a line to top temporarily.
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


class TestDragArea(unittest.TestCase):
    """test `drag_area` from usr_get_area_img"""

    @staticmethod
    def drag_shift():
        """Drag one point in a closed loop around the screen to see how drag imperfections accumulate.
        The loop from left-upper corner:
        - right-down, left-up, right, down, left, right-up, left-down, up

        After each step a screenshot of the left-upper corner is saved.
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
    
        # prepare an image of a table with loop_repeat rows and len(loop_steps) columns
        # account for black margins for cells with `+ 2` in the multiplier
        cell_side = area_side + 2
        test_img = np.zeros((loop_repeat*cell_side, len(loop_steps)*cell_side, 3))
    
        x, y, w, h = AREA_REGION
        x = x + r_area
        y = y + r_area
        w = w - area_side
        h = h - area_side
        shrinked_region = (x, y, w, h)

        x, y = x+w, y+h  # align x,y that duplicate loop displacements with the first displacement to track the same area
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



if __name__ == '__main__':
    unittest.main()
