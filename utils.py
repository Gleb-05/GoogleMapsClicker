import time
import functools
import pyautogui
import pyperclip
from PIL import ImageChops


class CustomError(Exception):
    """
    Re-raise this Error after catching broad exceptions, but with custom vars attached.
    Generally useful for safe wrappers of methods that process page content.
    """

    def __init__(self, *, original_exception, **context):
        """Pass the original exception and key-value arguments to attach meaningful data to the Exception"""
        self.original_e = original_exception
        self.context = context
        super().__init__(self._build_message())

    def _build_message(self):
        ctx = ", ".join(f"{k}={v}" for k, v in self.context.items())
        return f"{type(self.original_e).__name__}: {self.original_e} ({ctx})"


def is_no_change(img1, img2):
    """
    Accept two PIL.Image variables [captured with pyautogui.screenshot(region=region)].
    Return `True` if images have no differences.
    """
    diff = ImageChops.difference(img1, img2)
    return diff.getbbox() is None


def py_paste(text):
    """Util to paste text instead of typing (typing may fail if current locale is different from target language)"""
    pyperclip.copy(text)
    time.sleep(0.01)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.3)


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


def exception_to_none_decorator(func, exception_tuple):
    """
    Wrap any function to return None on errors from `exception_tuple`.
    For consistency it is highly recommended to do `if val = None: raise OriginalException` after wrapped function is used.
    
    Example: wrap `pyautogui.locateCenterOnScreen` and avoid try-catch nesting when doing search on multiple images.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exception_tuple:
            return None
    return wrapper


py_locateCenter = exception_to_none_decorator(pyautogui.locateCenterOnScreen, (pyautogui.ImageNotFoundException,))
"""
Works like `pyautogui.locateCenterOnScreen`, but returns None on `pyautogui.ImageNotFoundException`.
For consistency, if the return value is still None after multiple calls, raise the `...Exception`
"""
