import csv
from contextlib import contextmanager
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
SEARCH_SCREEN_CHANGE_REGION = (30, 330, 50, 20)  # rectangle somewhere in the middle of the google maps interface, useful for scroll checks
# INSPECT_SCREEN_CHANGE_REGION = (460,) + SEARCH_SCREEN_CHANGE_REGION[1:]

BROWSER_RIGHT_X=870
INSPECT_LEFT_X=457
INSPECT_TOP_Y=555
INSPECT_ELEMENTS_TAB_XY=548,100

PLACE_TYPE_HTML="/html/body/div[1]/div[2]/div[9]/div[8]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[2]/span/span/button"
PLACE_NAME_HTML="/html/body/div[1]/div[2]/div[9]/div[8]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[1]/h1/text()"

SEARCH_Y = 112
SEARCH_BACK_X = 28
SEARCH_BAR_X = 122
# SEARCH_BUTTON_X = 278
# PLACE_CARD_PAGETOP_XY = (12,255)
PLACE_CARD_XY = (12,550)

RMB_NEW_TAB_BELOW_RELATIVE_XY = (90, 30)  
RMB_NEW_TAB_ABOVE_RELATIVE_XY = (90,-230)  # rmb menu appears above mouse cursor when closer to page bottom
RMB_COPY_STR_CONTENT_BELOW_RELATIVE_XY = RMB_NEW_TAB_BELOW_RELATIVE_XY


def is_no_change(img1, img2):
    """
    Accept two PIL.Image variables [captured with pyautogui.screenshot(region=region)].
    Return `True` if images have no differences.
    """
    diff = ImageChops.difference(img1, img2)
    return diff.getbbox() is None


@contextmanager
def wait_for_screen_change(region, timeout=10, interval=0.3, timeout_msg="Screen did not change in time"):
    before = pyautogui.screenshot(region=region)
    yield
    start = time.time()
    while True:
        current = pyautogui.screenshot(region=region)
        if not is_no_change(current, before):
            time.sleep(0.3)
            break

        if time.time() - start > timeout:
            raise TimeoutError(timeout_msg)
        time.sleep(interval)


@contextmanager
def wait_for_screen_image(region, image_path: str, timeout=10, interval=0.3, timeout_msg="The image did not appear in time"):
    yield
    start = time.time()
    while True:
        try:
            pyautogui.locateOnScreen(image_path, region=region)
            time.sleep(0.3)
            break
        except pyautogui.ImageNotFoundException:
            pass

        if time.time() - start > timeout:
            raise TimeoutError(timeout_msg)
        time.sleep(interval)


@contextmanager
def wait_for_animation_end(region, timeout=10, interval=0.1, timeout_msg="Animation took too long"):
    """Example: when does scroll end"""
    yield
    start = time.time()
    while True:
        before = pyautogui.screenshot(region=region)
        time.sleep(interval)
        current = pyautogui.screenshot(region=region)
        if is_no_change(current, before):
            time.sleep(0.3)
            break

        if time.time() - start > timeout:
            raise TimeoutError(timeout_msg)


def refocus_page():
    """
    By clicking on hide-show, bring back focus to the page itself.
    Useful to bring shortcuts into correct context.
    """
    with wait_for_animation_end((0, 425-10, 20, 20)):
        pyautogui.click(420,425)
    with wait_for_animation_end((0, 425-10, 20, 20)):
        pyautogui.click(12,425)


class PreparationFrame:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Prepare")
        self.W, self.H = root.winfo_screenwidth(), root.winfo_screenheight()
        self.root.geometry("300x100+%d+%d" % (self.W-400, 100))
        self.root.attributes("-topmost", True)

        self.steps = {
            "side_browser": self.side_browser,
            "set_browser_x": lambda: self.set_browser_x(pyautogui.position()[0]),
            "set_inspect_x": lambda: self.set_inspect_x(pyautogui.position()[0]),
            "set_inspect_y": lambda: self.set_inspect_y(),
            "show_xy": self.show_xy,
            "close_page": lambda: pyautogui.shortcut('ctrl', 'w'),
            "refocus_page": refocus_page,
            "inspect_find": lambda: self.inspect_find(PLACE_NAME_HTML),
            "total_scroll_down": self.total_scroll_down,
            "scroll_to_next_card": self.scroll_to_next_card,
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
    def set_inspect_y(self):
        pyautogui.dragRel(0, self.H - 1, duration=0.3)

    def inspect_find(self, find_query):
        """Return `False` if `find_query` is absent in page's HTML. Return True for 1 or more occurences. `find_query` can be an html selector"""
        x_margin=100
        # this region corresponds to prevbtn position unshifted by "x of x" that appears when find_query is present
        INSPECT_PREVBTN_REGION=(783-5, 698-3, 16+5, 10+10)  # FIX: browser dimension setup is wonky, think about error margins like here
        pyautogui.click(INSPECT_ELEMENTS_TAB_XY)
        pyautogui.hotkey('ctrl', 'f')
        # TODO each time.sleep can be changed to `wait_...`, but then highly specific regions need to be set
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'a')
        pyperclip.copy(find_query)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)
        try:
            pyautogui.locateOnScreen("inspect_prevbtn.png", region=INSPECT_PREVBTN_REGION)
            self.label.config(text="False")
            return False
        except pyautogui.ImageNotFoundException:
            self.label.config(text="True")
            return True

    def scroll_to_next_card(self, scroll_up=True):
        """
        In a list of search results with place cards, scroll (up by default) to next card.
        Return True when the last card is reached, False otherwise.
        May stop at second to last card if more than two cards are visible at the top of the list.
        """
        FIRST_PLACE_CARD_TOP_Y = 240
        LAST_PLACE_CARD_BOTTOM_Y = 635

        left_x, left_y = PLACE_CARD_XY
        # changing_region was unreliable - edge case: same blank card bottoms are compared
        
        # Move the mouse over the place card for it to change color to gray
        pyautogui.moveTo(left_x, left_y+1)
        pyautogui.moveTo(left_x, left_y, 0.1)
        # img_before_scroll = pyautogui.screenshot(region=changing_region)

        distance = self.distance_to_white(left_x, left_y, from_down=scroll_up)
        self.label.config(text=str(distance))
        if distance is None:
            return
        with wait_for_animation_end(SEARCH_SCREEN_CHANGE_REGION):
            pyautogui.scroll(int(-distance*SCROLL_MULT))
        
        
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

        # F3FIND_X = 410
        F3FIND_CLOSE_X = 705
        F3FIND_COUNT_REGION = (570-2, 98-2, 21+5, 14+5)  # exact search_f3_count.png coordinates, adjusted for error

        refocus_page()
        pyautogui.moveTo(PLACE_CARD_XY)

        # NOTE: special case when wait_for_screen_change wouldnt work, because leading action is repeated in the same loop
        img_before_f3find = pyautogui.screenshot(region=F3FIND_COUNT_REGION)
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

        if self.inspect_find(PLACE_NAME_HTML):
            print("to implement")
            place_count = 1
        else:
            self.total_scroll_down()
            pyautogui.moveTo(PLACE_CARD_XY)
            last_card = False
            while True:
                place_count += 1
                pyautogui.rightClick()
                pyautogui.moveRel(RMB_NEW_TAB_BELOW_RELATIVE_XY if last_card else RMB_NEW_TAB_ABOVE_RELATIVE_XY)
                pyautogui.click()
                if last_card:
                    break
                time.sleep(0.1)
                last_card = self.scroll_to_next_card()

        # move to the newly opened tab to the right
        pyautogui.shortcut('ctrl', 'tab')  

        with open("output.csv", "a", newline="") as f:
            writer = csv.writer(f)
            for i in range(place_count):
                print(i)
                time.sleep(5)
                INSPECT_ELEMENTS_TAB_REGION = (841-5, 90-2, 12+10, 17+5)  
                # wait for inspect tab to be open
                with wait_for_screen_image(INSPECT_ELEMENTS_TAB_REGION, "inspect_elements_tab.png"):
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
                except Exception as e:
                    # remember address of this page as problematic
                    pyautogui.hotkey('alt', 'd')
                    time.sleep(0.3)
                    pyautogui.hotkey('ctrl', 'c')
                    time.sleep(0.1)
                    writer.writerow((i, None, None, None, pyperclip.paste()))
                pyautogui.shortcut('ctrl', 'w')  # close current tab to be replaced with tab to the right

    def write_results_to_csv(self):
        time.sleep(5)
        with open("output.csv", "a", newline="", encoding='utf-8') as f:
            writer = csv.writer(f)
            try:
                try:
                    place_info = self.extract_place_info()
                except TimeoutError:
                    # one additional chance to work
                    pyautogui.hotkey('ctrl', 'f5')
                    time.sleep(5)
                    place_info = self.extract_place_info()
                writer.writerow(place_info)
            except Exception as e:
                # remember address of this page as problematic
                pyautogui.hotkey('alt', 'd')
                time.sleep(0.3)
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(0.1)
                writer.writerow((str(e).replace(',',';'),type(e), None, pyperclip.paste()))

    def process_search_results(self):
        """
        After using the search, it is possible that:
        - there is one place: the inspect find has PLACE_NAME_HTML.
          the card is already opened, the tab should be processed immediately.
        - there are multiple places: the inspect find does NOT have a PLACE_NAME_HTML.
          each card from the search results should be opened, processed, and then search list should be opened back.
        """
        if self.inspect_find(PLACE_NAME_HTML):
            self.write_results_to_csv()
        else:
            self.total_scroll_down()
            pyautogui.moveTo(PLACE_CARD_XY)
            last_card = False
            while True:
                pyautogui.click()
                self.write_results_to_csv()
                pyautogui.click(SEARCH_BACK_X, SEARCH_Y)
                time.sleep(5)
                if last_card:
                    break
                last_card = self.scroll_to_next_card()


    def inspect_find_and_copy_first(self, find_query):
        """
        When using inspect find, `$0` args can be used to access what's found in the console.
        Use `$0.textContent` and click on `copy string content`.
        `find_query` goes directly into inspect find, and as such can be an html selector.
        """
        # INSPECT_FINDBTN_XY = (760,525)
        INSPECT_CONSOLE_TAB_XY=606,100
        INSPECT_CONSOLE_OUTPUT_XY=490,230  # Context menu with X>490 may give "Clear console" as first option, leading to errors
        INSPECT_CLEAR_SUCCESS_REGION=(482-5, 202-2, 70+10, 20+5)  

        pyautogui.click(INSPECT_ELEMENTS_TAB_XY)
        for _ in range(4):
            find_success = self.inspect_find(find_query=find_query)
            if find_success:
                break
            time.sleep(5)
        if not find_success:
            return None
        
        pyautogui.click(INSPECT_CONSOLE_TAB_XY)
        time.sleep(0.1)
        # successful `clear()` command should give a purely white region here
        with wait_for_screen_image(INSPECT_CLEAR_SUCCESS_REGION, "inspect_clear_success.png"):
            pyautogui.write("clear()", 0.01)
            pyautogui.press('enter')
        pyautogui.write("$0.textContent", 0.01)
        inspect_console_output_region = *INSPECT_CONSOLE_OUTPUT_XY, 20, 20
        with wait_for_screen_change(inspect_console_output_region):
            pyautogui.press('enter')
        time.sleep(0.1)
        pyautogui.rightClick(INSPECT_CONSOLE_OUTPUT_XY, duration=0.1)
        pyautogui.moveRel(RMB_COPY_STR_CONTENT_BELOW_RELATIVE_XY, duration=0.1)
        pyautogui.click(duration=0.1)
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
        # PLACE_LINK_REGION = (10, 450-3, 70, 17+6)
        # PLACE_LINK_CLOSE_XY = (405,245) # unreliable for some reason
        PLACE_PLUSCODE_REGION = (20, SEARCH_Y, 50-20, self.H-SEARCH_Y-10)

        x, y, w, h = pyautogui.locateOnScreen("place_linkbtn.png", region=PLACE_LINKBTN_REGION)
        with wait_for_screen_change(PLACE_LINKBTN_REGION):
            pyautogui.click(x+w//2, y+h//2)
        time.sleep(0.1)
        # link_x, link_y = pyautogui.locateCenterOnScreen("place_link.png", region=PLACE_LINK_REGION)
        pyautogui.click(10+70//2, 450+17//2)  # hopefully link text is always at the same height
        time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.3)
        place_link = pyperclip.paste()
        with wait_for_screen_change(PLACE_LINKBTN_REGION):
            pyautogui.click(PLACE_LINKBTN_REGION[0], SEARCH_Y)

        # refocus_page()
        pyautogui.moveTo(PLACE_LINKBTN_REGION[:2])

        linkbtn_to_search_distance = SEARCH_Y - y - h
        with wait_for_animation_end(SEARCH_SCREEN_CHANGE_REGION):
            pyautogui.scroll(int(linkbtn_to_search_distance * SCROLL_MULT))  # scroll up until `linkbtn` and `search` are aligned
        time.sleep(0.1)
        try:
            pluscode_x, pluscode_y = pyautogui.locateCenterOnScreen("place_pluscode.png", region=PLACE_PLUSCODE_REGION)
        except pyautogui.ImageNotFoundException:
            # sometimes cursor will land on pluscode row
            pluscode_x, pluscode_y = pyautogui.locateCenterOnScreen("place_pluscode_gray.png", region=PLACE_PLUSCODE_REGION)
        pyautogui.click(pluscode_x, pluscode_y)
        time.sleep(0.3)
        place_pluscode = pyperclip.paste()

        place_name = self.inspect_find_and_copy_first(PLACE_NAME_HTML)

        place_type = self.inspect_find_and_copy_first(PLACE_TYPE_HTML)

        self.label.config(text=f"{place_name}\n{place_type}\n{place_pluscode}\n{place_link}")
        return place_name, place_type, place_pluscode, place_link


if __name__ == "__main__":
    root = tk.Tk()
    app = PreparationFrame(root)
    root.mainloop()