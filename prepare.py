import threading
import time
import csv
import tkinter as tk
import pyautogui
import pyperclip
import keyboard

from constants import *
from wait_contexts import *
from utils import py_locateCenter
from tk_inspect import inspect_find, inspect_find_and_copy_first
from tk_scroll import py_scroll, total_scroll_down, scroll_to_next_card, SCROLLBAR_REGION

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
            "extract_place_info": self.extract_place_info,
            "process_search_results": self.process_search_results,
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
       

    def process_search_results_newtab(self):
        """
        Multiple places - TOO COMPUTATIONALLY EXPENSIVE with new tabs
        
        After using the search, it is possible that:
        - there is one place: the inspect find has PLACE_NAME_HTML.
          the card is already opened, the tab should be duplicated.
          processing should begin with count=1.
        - there are multiple places: the inspect find does NOT have a PLACE_NAME_HTML.
          each card from the search results should be opened in a new tab.
          processing should begin with count acquired during the iteration over search results.
        """

        place_count = 0

        if inspect_find(PLACE_NAME_HTML):
            print("to implement")
            place_count = 1
        else:
            total_scroll_down()
            last_card = False
            while True:
                place_count += 1
                pyautogui.rightClick()
                pyautogui.moveRel(RMB_FIRST_OPTION_BELOW_RELATIVE_XY if last_card else RMB_FIRST_OPTION_ABOVE_RELATIVE_XY)
                pyautogui.click()
                if last_card:
                    break
                time.sleep(0.1)
                last_card = scroll_to_next_card()

        # move to the newly opened tab to the right
        pyautogui.shortcut('ctrl', 'tab')  

        with open("output.csv", "a", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            for i in range(place_count):
                print(i)
                time.sleep(5)
                INSPECT_ELEMENTS_TAB_REGION = (841-5, 90-2, 12+10, 17+5)  
                # wait for inspect tab to be open
                with wait_for_screen_image(INSPECT_ELEMENTS_TAB_REGION, "img/inspect_elements_tab.png"):
                    pyautogui.shortcut('ctrl', 'shift', 'i')  # open inspect window
                try:
                    try:
                        place_info = self.extract_place_info()
                    except TimeoutError:
                        # one additional chance to work
                        pyautogui.hotkey('ctrl', 'f5')
                        time.sleep(5)
                        place_info = self.extract_place_info()
                    writer.writerow((i,) + place_info)
                except Exception:
                    # remember address of this page as problematic
                    pyautogui.hotkey('alt', 'd')
                    time.sleep(0.3)
                    pyautogui.hotkey('ctrl', 'c')
                    time.sleep(0.1)
                    writer.writerow((i, None, None, None, pyperclip.paste()))
                pyautogui.shortcut('ctrl', 'w')  # close current tab to be replaced with tab to the right

    def extract_place_info_safe(self):
        """Wrap extract_place_info in some retry and errorcatch logic"""
        time.sleep(5)
        try:
            try:
                place_info = self.extract_place_info()
            except (TimeoutError, pyautogui.ImageNotFoundException):
                # one more chance to work if something took too long
                pyautogui.hotkey('ctrl', 'f5')
                time.sleep(5)
                place_info = self.extract_place_info()
            return place_info
        except Exception as e:
            # remember address of this page as problematic
            pyautogui.hotkey('alt', 'd')
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(0.3)
            return((str(e).replace(',',';'),type(e), None, pyperclip.paste()))

    def write_to_csv(self, info_tuple, filepath="output.csv", mode="a"):
        with open(filepath, mode, newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(info_tuple)

    def process_search_results(self):
        """
        After using the search, it is possible that:
        - there is one place: the inspect find has PLACE_NAME_HTML.
          the card is already opened, the tab should be processed immediately.
        - there are multiple places: the inspect find does NOT have a PLACE_NAME_HTML.
          each card from the search results should be opened, processed, and then search list should be opened back.
        """
        if inspect_find(PLACE_NAME_HTML):
            self.write_to_csv(self.extract_place_info_safe())
        else:
            total_scroll_down()
            last_card = False
            while True:
                scrollbar_snapshot = pyautogui.screenshot(region=SCROLLBAR_REGION)
                pyautogui.click()
                self.write_to_csv(self.extract_place_info_safe())
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


    def extract_place_info(self):
        """
        When place page is opened, get:
        - place_name
        - place_type
        - place_pluscode
        - place_link (google maps shortened link to the place)
        """
        PLACE_LINKBTN_REGION = (325, 380, 375-325, 580-380)
        # PLACE_LINK_REGION = (10, 450-3, 70, 17+6)
        # PLACE_LINK_CLOSE_XY = (405,245) # unreliable for some reason
        PLACE_PLUSCODE_REGION = (20, SEARCH_Y, 50-20, self.H-SEARCH_Y-10)

        x, y, w, h = pyautogui.locateOnScreen("img/place_linkbtn.png", region=PLACE_LINKBTN_REGION)
        with wait_for_screen_change(PLACE_LINKBTN_REGION):
            pyautogui.click(x+w//2, y+h//2)
        with wait_for_animation_end((20,460,310,20)):  # link may not load immediately
            time.sleep(0.1)
        # link_x, link_y = pyautogui.locateCenterOnScreen("img/place_link.png", region=PLACE_LINK_REGION)
        pyautogui.click(10+70//2, 450+17//2)  # hopefully link text is always at the same height
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.3)
        place_link = pyperclip.paste()
        with wait_for_screen_change(PLACE_LINKBTN_REGION):
            pyautogui.click(PLACE_LINKBTN_REGION[0], SEARCH_Y)

        pyautogui.moveTo(PLACE_LINKBTN_REGION[:2])
        py_scroll(SEARCH_Y - y - h)  # scroll down until `linkbtn` and `search` are aligned
        time.sleep(0.1)
        pluscode_xy = None
        for _ in range(2):
            # sometimes cursor will land on pluscode row, making the background gray
            pluscode_xy = py_locateCenter("img/place_pluscode.png", region=PLACE_PLUSCODE_REGION) \
                or py_locateCenter("img/place_pluscode_gray.png", region=PLACE_PLUSCODE_REGION)
            if pluscode_xy is not None:
                break
            # sometimes pluscode row will be further down, requiring an additional scroll down
            py_scroll(300 - self.H)
        if pluscode_xy is None:
            raise pyautogui.ImageNotFoundException
        pyautogui.click(pluscode_xy)
        time.sleep(0.3)
        place_pluscode = pyperclip.paste()

        place_name = inspect_find_and_copy_first(PLACE_NAME_HTML)

        place_type = inspect_find_and_copy_first(PLACE_TYPE_HTML)

        self.label.config(text=f"{place_name}\n{place_type}\n{place_pluscode}\n{place_link}")
        return place_name, place_type, place_pluscode, place_link


if __name__ == "__main__":
    root = tk.Tk()
    app = DebugFrame(root)
    root.mainloop()
