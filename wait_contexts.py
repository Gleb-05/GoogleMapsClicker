from contextlib import contextmanager
import time
import pyautogui
from PIL import Image

from utils import is_no_change


@contextmanager
def wait_for_screen_change(region, timeout=10, interval=0.3, timeout_msg="Screen did not change in time"):
    """
    Compare given region of screen at regular intervals until either:
    - region at the current moment is different from the previous moment
    - or the timeout was reached
    """
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
def wait_for_screen_image(region, image: str| Image.Image, timeout=10, interval=0.3, timeout_msg="The image did not appear in time"):
    """
    Compare given region of screen at regular intervals until either:
    - region at the current moment is same as the given image
    - or the timeout was reached
    """
    yield
    start = time.time()
    while True:
        try:
            pyautogui.locateOnScreen(image, region=region)
            time.sleep(0.3)
            break
        except pyautogui.ImageNotFoundException:
            pass

        if time.time() - start > timeout:
            raise TimeoutError(timeout_msg)
        time.sleep(interval)


@contextmanager
def wait_for_animation_end(region, timeout=10, interval=0.1, timeout_msg="Animation took too long"):
    """Wait until given region stops changing between intervaled comparisons. Example: when does scroll end"""
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
