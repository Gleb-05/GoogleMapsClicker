import threading
import time
import csv
import tkinter as tk
import pyautogui
import keyboard

from constants import PLACE_NAME_HTML, SEARCH_Y
from utils import py_paste
from wait_contexts import wait_for_screen_change, wait_for_screen_image
from gui_inspect import inspect_find
from gui_scroll import total_scroll_down, scroll_to_next_card, SCROLLBAR_REGION
from usr_extract_place_info import extract_place_info_safe

SAFE_Y=250  # safely below browser ui edge
# INSPECT_SCREEN_CHANGE_REGION = (460,) + SEARCH_SCREEN_CHANGE_REGION[1:]

BROWSER_RIGHT_X=870
INSPECT_LEFT_X=457



SEARCH_BACK_X = 28
SEARCH_BAR_X = 122
# SEARCH_BUTTON_X = 278


class DebugFrame:
    """
    Combine pieces of functionality necessary to navigate the google maps page
    to extract information about multiple places.

    Log Label at the window's bottom allows to debug most of the present functions.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Prepare")
        self.W, self.H = root.winfo_screenwidth(), root.winfo_screenheight()
        self.root.geometry("300x100+{}+{}".format(self.W-400, 100))
        self.root.attributes("-topmost", True)

        self.steps = {
            "side_browser": self.side_browser,
            "set_browser_x": lambda: self.set_browser_x(pyautogui.position()[0]),
            "set_inspect_x": lambda: self.set_inspect_x(pyautogui.position()[0]),
            "set_inspect_y": self.set_inspect_y,
            "show_xy": self.show_xy,
            "inspect_find": lambda: inspect_find(PLACE_NAME_HTML),
            "total_scroll_down": total_scroll_down,
            "scroll_to_next_card": scroll_to_next_card,
            "extract_place_info_safe": extract_place_info_safe,
            "process_search_queries": self.process_search_queries,
        }
        self.steps_names = list(self.steps.keys())
        self.step_var = tk.StringVar(value="show_xy")
        tk.OptionMenu(root, self.step_var, *self.steps_names).pack(pady=10)
        
        instruction = "Press NumLk (or alt+f2) after moving your cursor to a suitable position."
        tk.Label(root, text=instruction, wraplength=300).pack(expand=True)
        
        self.label = tk.Label(root, text="Log Label", wraplength=300)
        self.label.pack(expand=True)

        threading.Thread(target=self.listen_hotkey, daemon=True).start()

    def execute_selected_step(self):
        try:
            result = self.steps[self.step_var.get()]()
        except Exception as e:
            result = e
        self.label.config(text=str(result))

    def listen_hotkey(self):
        keyboard.add_hotkey("num lock", self.execute_selected_step)
        keyboard.add_hotkey("alt+f2", self.execute_selected_step)  # fallback option
        keyboard.wait()  # Keep the thread alive

    def show_xy(self):
        x, y = pyautogui.position()
        self.label.config(text=f"X: {x}, Y: {y}")

    @staticmethod
    def auto_advance(func):
        # @wraps(func)
        def wrapper(self: "DebugFrame", *args, **kwargs):
            result = func(self, *args, **kwargs)
            try:
                idx = self.steps_names.index(self.step_var.get())
                next_step = self.steps_names[idx + 1]
                self.step_var.set(next_step)
            except (ValueError, IndexError):
                pass
            return result
        return wrapper
    
    @auto_advance
    def side_browser(self, x_to=0, y_to=SAFE_Y):
        pyautogui.mouseDown()
        pyautogui.moveTo(x_to, y_to, duration=0.3)
        pyautogui.mouseUp()
        time.sleep(0.3)
        pyautogui.click()  # remove splitscreen suggestions

    @auto_advance
    def set_browser_x(self, x_from):
        pyautogui.dragRel(BROWSER_RIGHT_X - x_from, 0, duration=0.3)

    @auto_advance
    def set_inspect_x(self, x_from):
        pyautogui.dragRel(INSPECT_LEFT_X - x_from, 0, duration=0.3)

    @auto_advance
    def set_inspect_y(self):
        pyautogui.dragRel(0, self.H - 1, duration=0.3)


    def write_to_csv(self, info_tuple, filepath="output.csv", mode="a"):
        with open(filepath, mode, newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(info_tuple)


    def iter_search_results(self):
        """
        Yield search results.

        Possible search results:
        - there is one place: the inspect find has PLACE_NAME_HTML.
          the place webpage is already opened, yield immediately.
        - there are multiple places: the inspect find does NOT have a PLACE_NAME_HTML.
          each place card from the search results should be opened, yield, and then search page should be opened back.
        """
        if inspect_find(PLACE_NAME_HTML):
            yield
            # going back to search page is unnecessary, since search bar is still displayed
        else:
            total_scroll_down()
            last_card = False
            while True:
                scrollbar_snapshot = pyautogui.screenshot(region=SCROLLBAR_REGION)
                pyautogui.click()
                yield
                # press 'back' and wait for page to load before scrolling to next card
                # check if page is loaded using SCROLLBAR_REGION
                try:
                    with wait_for_screen_image(SCROLLBAR_REGION, scrollbar_snapshot, 5):
                        pyautogui.click(SEARCH_BACK_X, SEARCH_Y)
                except TimeoutError:
                    pass
                if last_card:
                    break
                last_card = scroll_to_next_card()

    def search_queries_naive(self):
        """Return hard-coded list of locations"""
        naive_list = ['puffy cookies']
        return [q + ' paris' for q in naive_list]

    def process_search_queries(self):
        """
        For each query from query generator:
        - enter query into search field
        - if "can't find" string is present on the page, skip query
        - if not, use chosen safe procesing on the query results
        """
        for search_query in self.search_queries_naive():
            pyautogui.click(SEARCH_BAR_X, SEARCH_Y)
            pyautogui.shortcut('ctrl', 'a')
            py_paste(search_query)
            pyautogui.press('enter')
            time.sleep(5)
            for _ in self.iter_search_results():
                self.write_to_csv(extract_place_info_safe())
        

if __name__ == "__main__":
    root = tk.Tk()
    app = DebugFrame(root)
    root.mainloop()
