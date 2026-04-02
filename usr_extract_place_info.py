import time
import pyautogui
import pyperclip

from constants import SEARCH_Y, PLACE_NAME_HTML, PLACE_TYPE_HTML
from utils import py_locateCenter
from wait_contexts import wait_for_screen_change, wait_for_animation_end
from gui_inspect import inspect_find_and_copy_first
from gui_scroll import py_scroll


def extract_place_info():
    """
    When place webpage is opened, get:
    - place_name
    - place_type
    - place_pluscode
    - place_link (google maps shortened link to the place)
    """
    win_H = 760  # TODO inherit winfo_screenheight from tk app, don't leave constant!
    PLACE_LINKBTN_REGION = (325, 380, 375-325, 580-380)
    # PLACE_LINK_REGION = (10, 450-3, 70, 17+6)
    # PLACE_LINK_CLOSE_XY = (405,245) # using precise coordinates failed
    PLACE_PLUSCODE_REGION = (20, SEARCH_Y, 50-20, win_H-SEARCH_Y-10)
    # 
    place_linkload_region = (20,460,310,20)
    place_linktext_xy = (10+70//2, 450+17//2)

    x, y, w, h = pyautogui.locateOnScreen("img/place_linkbtn.png", region=PLACE_LINKBTN_REGION)
    with wait_for_screen_change(PLACE_LINKBTN_REGION):
        pyautogui.click(x+w//2, y+h//2)
    with wait_for_animation_end(place_linkload_region):  # link may not load immediately
        time.sleep(0.1)
    # link_x, link_y = pyautogui.locateCenterOnScreen("img/place_link.png", region=PLACE_LINK_REGION)
    pyautogui.click(place_linktext_xy)  # hopefully link text is always at the same height
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
        py_scroll(300 - win_H)
    if pluscode_xy is None:
        raise pyautogui.ImageNotFoundException
    pyautogui.click(pluscode_xy)
    time.sleep(0.3)
    place_pluscode = pyperclip.paste()

    place_name = inspect_find_and_copy_first(PLACE_NAME_HTML)

    place_type = inspect_find_and_copy_first(PLACE_TYPE_HTML)

    return place_name, place_type, place_pluscode, place_link


def extract_place_info_safe():
    """Wrap extract_place_info in some retry and errorcatch logic"""
    time.sleep(5)
    try:
        try:
            place_info = extract_place_info()
        except (TimeoutError, pyautogui.ImageNotFoundException):
            # one more chance to work if something took too long
            pyautogui.hotkey('ctrl', 'f5')
            time.sleep(5)
            place_info = extract_place_info()
        return place_info
    except Exception as e:
        # remember address of this page as problematic
        pyautogui.hotkey('alt', 'd')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.3)
        return((str(e).replace(',',';'),type(e), None, pyperclip.paste()))


# def process_search_results_newtab(self):
#     """

#     Multiple places - TOO COMPUTATIONALLY EXPENSIVE with new tabs
    
#     After using the search, it is possible that:
#     - there is one place: the inspect find has PLACE_NAME_HTML.
#         the place webpage is already opened, the tab should be duplicated.
#         processing should begin with count=1.
#     - there are multiple places: the inspect find does NOT have a PLACE_NAME_HTML.
#         each place card from the search results should be opened in a new tab.
#         processing should begin with count acquired during the iteration over search results.
#     """
#     place_count = 0

#     if inspect_find(PLACE_NAME_HTML):
#         print("to implement")
#         place_count = 1
#     else:
#         total_scroll_down()
#         last_card = False
#         while True:
#             place_count += 1
#             pyautogui.rightClick()
#             pyautogui.moveRel(RMB_FIRST_OPTION_BELOW_RELATIVE_XY if last_card else RMB_FIRST_OPTION_ABOVE_RELATIVE_XY)
#             pyautogui.click()
#             if last_card:
#                 break
#             time.sleep(0.1)
#             last_card = scroll_to_next_card()

#     # move to the newly opened tab to the right
#     pyautogui.shortcut('ctrl', 'tab')  

#     with open("output.csv", "a", newline="", encoding='utf-8') as f:
#         writer = csv.writer(f)
#         for i in range(place_count):
#             print(i)
#             time.sleep(5)
#             INSPECT_ELEMENTS_TAB_REGION = (841-5, 90-2, 12+10, 17+5)  
#             # wait for inspect tab to be open
#             with wait_for_screen_image(INSPECT_ELEMENTS_TAB_REGION, "img/inspect_elements_tab.png"):
#                 pyautogui.shortcut('ctrl', 'shift', 'i')  # open inspect window
#             try:
#                 try:
#                     place_info = self.extract_place_info()
#                 except TimeoutError:
#                     # one additional chance to work
#                     pyautogui.hotkey('ctrl', 'f5')
#                     time.sleep(5)
#                     place_info = self.extract_place_info()
#                 writer.writerow((i,) + place_info)
#             except Exception:
#                 # remember address of this page as problematic
#                 pyautogui.hotkey('alt', 'd')
#                 time.sleep(0.3)
#                 pyautogui.hotkey('ctrl', 'c')
#                 time.sleep(0.1)
#                 writer.writerow((i, None, None, None, pyperclip.paste()))
#             pyautogui.shortcut('ctrl', 'w')  # close current tab to be replaced with tab to the right