import tkinter as tk
import pyautogui
from PIL import ImageChops, Image
import pyperclip
import keyboard
import threading
import time
import math

SAFE_Y=250  # safely below browser ui edge
SCROLL_MULT=1.3  # using precise distance leads to underscroll, use arbitrary multiplier to fix

BROWSER_RIGHT_X=870
INSPECT_LEFT_X=457
INSPECT_TOP_Y=555

PLACE_TYPE_HTML="/html/body/div[1]/div[2]/div[9]/div[8]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[2]/span/span/button"
PLACE_NAME_HTML="/html/body/div[1]/div[2]/div[9]/div[8]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[1]/h1/text()"

SEARCH_Y = 112
# SEARCH_BACK_X = 28
SEARCH_BAR_X = 122
# SEARCH_BUTTON_X = 278
# PLACE_CARD_PAGETOP_XY = (12,255)
PLACE_CARD_XY = (12,550)

RMB_NEW_TAB_BELOW_RELATIVE_XY = (90, 30)  
RMB_NEW_TAB_ABOVE_RELATIVE_XY = (90,-230)  # rmb menu appears above mouse cursor when closer to page bottom
RMB_COPY_STR_CONTENT_BELOW_RELATIVE_XY = RMB_NEW_TAB_BELOW_RELATIVE_XY

def is_no_change(img1, img2):
    """
    Accept two img variables captured with pyautogui.screenshot(region=region).
    Return `True` if images have no differences.
    """
    diff = ImageChops.difference(img1, img2)
    return diff.getbbox() is None

def refocus_page():
    """
    By clicking on hide-show, bring back focus to the page itself.
    Useful to bring shortcuts into correct context.
    """
    pyautogui.click(420,425)
    time.sleep(0.5)
    pyautogui.click(12,425)
    time.sleep(0.5)

class PreparationFrame:
    def __init__(self, root):
        self.root = root
        self.root.title("Prepare")
        self.W, self.H = root.winfo_screenwidth(), root.winfo_screenheight()
        self.root.geometry("300x100+%d+%d" % (self.W-400, 100))
        self.root.attributes("-topmost", True)

        self.steps = {
            "side_browser": lambda: self.side_browser(),
            "set_browser_x": lambda: self.set_browser_x(pyautogui.position()[0]),
            "set_inspect_x": lambda: self.set_inspect_x(pyautogui.position()[0]),
            "set_inspect_y": lambda: self.set_inspect_y(pyautogui.position()[1]),
            "show_xy": self.show_xy,
            "inspect_find": lambda: self.inspect_find(PLACE_NAME_HTML),
            "total_scroll_down": self.total_scroll_down,
            "scroll_up_to_white": self.scroll_to_next_card,
            "extract_place_info": self.extract_place_info,
            "process_search_results": self.process_search_results
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
            self.steps[self.step_var.get()]()
        except Exception as e:
            self.label.config(text=str(e))

    def listen_hotkey(self):
        keyboard.add_hotkey("num lock", self.execute_selected_step)
        keyboard.add_hotkey("alt+f2", self.execute_selected_step)  # fallback option
        keyboard.wait()  # Keep the thread alive

    def show_xy(self):
        x, y = pyautogui.position()
        self.label.config(text=f"X: {x}, Y: {y}")

    def auto_advance(func):
        # @wraps(func)
        def wrapper(self: "PreparationFrame", *args, **kwargs):
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
    def set_inspect_y(self, y_from):
        pyautogui.dragRel(0, self.H - 1, duration=0.3)

    def inspect_find(self, find_string):
        """Return `False` if `find_string` is absent in page's HTML. Return True for 1 or more occurences."""
        x_margin=100
        # this region corresponds to prevbtn position unshifted by "x of x" that appears when find_string is present
        INSPECT_PREVBTN_REGION=(783-3, 698-3, 16+5, 10+5)
        pyautogui.moveTo(INSPECT_LEFT_X + x_margin, SAFE_Y)
        pyautogui.click()
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'a')
        pyperclip.copy(find_string)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)
        try:
            pyautogui.locateOnScreen("inspect_prevbtn.png", region=INSPECT_PREVBTN_REGION)
            return False
        except pyautogui.ImageNotFoundException:
            return True

    def scroll_to_next_card(self, scroll_up=True):
        """
        In a list of search results with place cards, scroll (up by default) to next card.
        Return True when the last card is reached, False otherwise.
        May yield second-to-last card twice, but will not miss the last card.
        """
        FIRST_PLACE_CARD_TOP_Y = 240
        LAST_PLACE_CARD_BOTTOM_Y = 635

        left_x, left_y = PLACE_CARD_XY
        changing_region = (left_x, left_y, 30, 10)  # unreliable - edge case: same blank card bottoms are compared
        
        # Move the mouse over the place card for it to change color to gray
        pyautogui.moveTo(left_x, left_y+1)
        pyautogui.moveTo(left_x, left_y, 0.1)
        # img_before_scroll = pyautogui.screenshot(region=changing_region)

        distance = self.distance_to_white(left_x, left_y, from_down=scroll_up)
        self.label.config(text=str(distance))
        if distance is None:
            return
        pyautogui.scroll(int(-distance*SCROLL_MULT))
        time.sleep(0.3)
        
        # when the last two cards are reached, the card can't move toward the cursor because the scroll is at its edge.
        # thus, the cursor should move toward the card.
        SCROLLBAR_TOP_PIXEL_XY=(405,142)
        SCROLLBAR_COLOR=(94,94,94)
        # TODO consider switching to checking the Y coordinate (for cards with smaller height)
        # if pyautogui.screenshot(region=changing_region)):
        if pyautogui.pixelMatchesColor(*SCROLLBAR_TOP_PIXEL_XY, SCROLLBAR_COLOR):
            distance = self.distance_to_white(left_x, left_y, from_down=scroll_up)
            distance = distance + math.copysign(10, distance)
            new_y = left_y + distance
            if new_y <= FIRST_PLACE_CARD_TOP_Y or new_y >= LAST_PLACE_CARD_BOTTOM_Y:
                raise ValueError("corrective scroll to next card - out of bounds")
            self.label.config(text="corrective "+str(distance))
            pyautogui.moveRel(0, distance)
            return True
        
        return False
    
    @auto_advance
    def total_scroll_down(self, stop_text_lang='eng'):
        """
        Scroll down untill all of the results are dynamically loaded.
        Stop when "... end of the list" string is found exactly once on the page.
        Choose relevant `stop_text` by selecting lang: [eng, ukr]
        """
        STOP_TEXT = {
            'eng': "You've reached the end of the list",
            'ukr': "Ви переглянули весь список",
        }
        stop_text = STOP_TEXT[stop_text_lang]

        # SEARCH_F3_X = 410
        F3FIND_CLOSE_X = 705
        F3FIND_COUNT_REGION = (570-2, 98-2, 21+5, 14+5)  # exact search_f3_count.png coordinates, adjusted for error

        refocus_page()

        img_before_f3find = pyautogui.screenshot(region=F3FIND_COUNT_REGION)
        pyautogui.moveTo(PLACE_CARD_XY)
        for i in range(4):
            pyautogui.hotkey('ctrl', 'f')
            if is_no_change(img_before_f3find, pyautogui.screenshot(region=F3FIND_COUNT_REGION)):
                time.sleep(1)
                if i==3:
                    raise BufferError("f3 find couldn't be opened")
            else:
                break
        
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.3)
        pyperclip.copy(stop_text)
        pyautogui.hotkey('ctrl','v')
        time.sleep(0.3)
        while True:
            # TODO maybe change to holding a click at the bottom of search result scrollbar
            pyautogui.scroll(-1000)
            time.sleep(0.4)
            pyautogui.press('f3')
            try:
                pyautogui.locateOnScreen('f3find_count.png', region=F3FIND_COUNT_REGION)
                pyautogui.click(x=F3FIND_CLOSE_X, y=SEARCH_Y)
                break
            except pyautogui.ImageNotFoundException:
                continue
            

    def process_search_results(self):
        """
        After using the search, it is possible that:
        - there is one place: the inspect find has PLACE_NAME_HTML.
          the card is already opened, the tab should be duplicated.
          processing should begin with count=1.
        - there are multiple places: the inspect find does NOT have a PLACE_NAME_HTML.
          each card from the search results should be opened in a new tab.
          processing should begin with count acquired during the iteration over search results.
        """

        if self.inspect_find(PLACE_NAME_HTML):
            print("to implement")
            return
        
        self.total_scroll_down()
        pyautogui.moveTo(PLACE_CARD_XY)
        last_card = False
        while True:
            pyautogui.rightClick()
            pyautogui.moveRel(RMB_NEW_TAB_BELOW_RELATIVE_XY if last_card else RMB_NEW_TAB_ABOVE_RELATIVE_XY)
            pyautogui.click()
            if last_card:
                break
            time.sleep(0.1)
            last_card = self.scroll_to_next_card()


    def inspect_find_and_copy_first(self, find_string):
        """"""
        # INSPECT_FINDBTN_XY = (760,525)
        INSPECT_ELEMENTS_TAB_XY=548,100
        INSPECT_CONSOLE_TAB_XY=606,100
        INSPECT_CONSOLE_OUTPUT_XY=540,230

        pyautogui.click(INSPECT_ELEMENTS_TAB_XY)
        find_success = self.inspect_find(find_string=find_string)
        if not find_success:
            return None
        
        pyautogui.click(INSPECT_CONSOLE_TAB_XY)
        time.sleep(0.1)
        pyautogui.write("clear()", 0.01)
        pyautogui.press('enter')
        time.sleep(0.1)
        pyautogui.write("$0.textContent", 0.01)
        pyautogui.press('enter')
        pyautogui.rightClick(INSPECT_CONSOLE_OUTPUT_XY)
        pyautogui.moveRel(RMB_COPY_STR_CONTENT_BELOW_RELATIVE_XY)
        pyautogui.click()
        time.sleep(0.1)
        return pyperclip.paste()


    def extract_place_info(self):
        """
        When place page is opened, get:
        - place_name
        - place_type
        - place_pluscode
        - place_link (google maps shortened link to the place)
        """
        PLACE_LINKBTN_REGION = (325, 380, 375-325, 580-380)
        PLACE_LINK_COPY_XY = (380,456)
        # PLACE_LINK_CLOSE_XY = (405,245) # unreliable for some reason
        PLACE_PLUSCODE_REGION = (20, SEARCH_Y, 50-20, self.H-SEARCH_Y-10)

        place_name = self.inspect_find_and_copy_first(PLACE_NAME_HTML)

        place_type = self.inspect_find_and_copy_first(PLACE_TYPE_HTML)

        x, y, w, h = pyautogui.locateOnScreen("place_linkbtn.png", region=PLACE_LINKBTN_REGION)
        pyautogui.click(x+w//2, y+h//2)
        time.sleep(0.1)
        pyautogui.click(PLACE_LINK_COPY_XY)
        time.sleep(0.1)
        place_link = pyperclip.paste()
        pyautogui.click(None, SEARCH_Y, duration=0.1)

        refocus_page()
        
        linkbtn_to_search_distance = SEARCH_Y - y - h
        pyautogui.scroll(int(linkbtn_to_search_distance * SCROLL_MULT))  # scroll up to line up `linkbtn` with `search`
        x, y, w, h = pyautogui.locateOnScreen("place_pluscode.png", region=PLACE_PLUSCODE_REGION)
        pyautogui.click(x+w//2, y+h//2)
        time.sleep(0.1)
        place_pluscode = pyperclip.paste()

        self.label.config(text=f"{place_name}\n{place_type}\n{place_pluscode}\n{place_link}")
        return place_name, place_type, place_pluscode, place_link

    @staticmethod
    def distance_to_white(left_x, left_y, from_down, threshold=250):
        """
        For a vertical area starting at `left_x, left_y`, return relative distance to the first pixel with all channels greater than `threshold`.
        `from_down` means that `left_x, left_y` is at the bottom of the area, which means the distance will be negative.
        If no suitable pixel is found, None is returned.
        """
        region_width = 20  # good for debug, 1 is enough otherwise
        region_height = 500  # eyeballed value
        region = (left_x, left_y - (region_height if from_down else 0), region_width, region_height)

        screenshot = pyautogui.screenshot(region=region)  # TODO can change to directly calling pixelMatchesColor
        img = list(screenshot.get_flattened_data())  # TODO might be optimized with numpy
        
        for y in range(1, region_height):
            pixel_row = region_height - y if from_down else y
            pixel = img[pixel_row*region_width]
            if pixel[0] > threshold and pixel[1] > threshold and pixel[2] > threshold:
                return -y-1 if from_down else y+1
            
        return None


if __name__ == "__main__":
    root = tk.Tk()
    app = PreparationFrame(root)
    root.mainloop()