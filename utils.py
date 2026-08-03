import time
import math
import traceback
import functools
import pyautogui
import pyperclip
from PIL import ImageChops, Image, ImageTk
import tkinter as tk
import numpy as np
from pathlib import Path
from constants import ATTENTION_HIGHLIGHT


# region error handling

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

def print_err_trace(err: BaseException, message: str = "Expected error"):
    '''
    Prints `OK: {message}` and calls `traceback.print_exception`.
    Useful on expected errors that are handled and do not raise.
    '''
    print('OK: ' + message)
    for trace in traceback.format_exception(type(err), err, err.__traceback__):
        for line in trace.split('\n')[:-1]:
            print('  --' + line)

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

# endregion

# region image processing

def strict_no_change(img1, img2):
    """
    Accept two PIL.Image variables [captured with pyautogui.screenshot(region=region)].
    Return `True` if images have no differences.
    """
    diff = ImageChops.difference(img1, img2)
    return diff.getbbox() is None


def is_no_change(img1, img2, threshold = 0.05, save_diff_img = False):
    """
    Accept two PIL.Image variables [captured with pyautogui.screenshot(region=region)].
    Return `True` if mean of absolute pixel differences between images is lover than threshold.

    Pass save_diff_img to save an array of absolute pixel differences in its own image.

    Example use:
    ```
    while True:
        before = pyautogui.screenshot(region=region)
        # something is done
        current = pyautogui.screenshot(region=region)
        if is_no_change(current, before):
            time.sleep(0.3)
            break
    ```
    """
    arr1 = np.array(img1).astype(np.int16)
    arr2 = np.array(img2).astype(np.int16)
    diff = np.abs(arr1 - arr2).astype(np.uint8)
    mean_diff = np.mean(np.abs(diff))
    if save_diff_img:
        Image.fromarray(diff).save(f"compare_{mean_diff}.png")

    return mean_diff < threshold


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


def pad_bottom(main_arr: np.ndarray, pad_arr: np.ndarray):
    """
    Return `np.concatenate((main_arr, pad_arr), axis=0)`.
    `pad_arr` is either horizontally repeated or cut off to fill the width of the bottom of `main_arr`.
    """
    if main_arr.ndim != 3 or pad_arr.ndim != 3:
        raise ValueError("Both arrays must be 3D (height-width-color)")

    target_width = main_arr.shape[1]
    pad_width = pad_arr.shape[1]
    if pad_width == 0:
        raise ValueError("pad_arr must have non-zero width")

    reps = (target_width + pad_width - 1) // pad_width  # 
    adjusted_pad = np.tile(pad_arr, (1, reps, 1))[:, :target_width]

    return np.concatenate((main_arr, adjusted_pad), axis=0)


def slice_large_image(path: str):
    '''
    Create vertical slices under 100Mb for an image at `path` 
    and save them into a new directory at `path`s stem.
    
    Note:
        GitHub has a 100Mb filelimit and is the primary reason this function exists.
        In retrospect, storing large files in releases is better - it doesnt make the git history heavy.
        The number of slices is estimated from the original file size.
    '''
    MAX_SIZE = 80 * 1024 * 1024  # 20Mb margin in case png compressions plays out worse than on the whole image
    image_path = Path(path)
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    if not image_path.is_file():
        raise ValueError(f"{image_path} is not a file")

    _MAX_IMAGE_PIXELS = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = 500_000_000
    image = Image.open(image_path)
    Image.MAX_IMAGE_PIXELS = _MAX_IMAGE_PIXELS

    output_dir = image_path.parent / (image_path.stem + '_slices')
    output_dir.mkdir(exist_ok=True)

    width, height = image.size

    file_size = image_path.stat().st_size + 1024  # margin for exact multiples of MAX_SIZE
    num_slices = max(1, math.ceil(file_size / MAX_SIZE))

    slice_width = math.ceil(width / num_slices)

    for i in range(num_slices):
        left = i * slice_width
        right = min(width, (i + 1) * slice_width)

        cropped = image.crop((left, 0, right, height))
        cropped.save(output_dir / f"{i}.png")

    image.close()


def unslice_large_image(path: str):
    '''
    `path` should be a folder with vertical image slices from `slice_large_image`.
    Concatenate them left-to-right and save the result as a sibling PNG named after the `path`.
    '''
    slice_dir = Path(path)

    if not slice_dir.exists():
        raise FileNotFoundError(slice_dir)
    if not slice_dir.is_dir():
        raise ValueError(f"{slice_dir} is not a directory")

    slices = sorted(
        slice_dir.glob("*.png"),
        key=lambda p: int(p.stem)
    )
    if not slices:
        raise ValueError(f"No PNG slices found in {slice_dir}")

    images = [Image.open(p) for p in slices]

    try:
        height = max(img.height for img in images)
        total_width = sum(img.width for img in images)

        result = Image.new(
            mode=images[0].mode,
            size=(total_width, height)
        )

        x = 0
        for img in images:
            result.paste(img, (x, 0))
            x += img.width

        output_path = slice_dir.parent / f"{slice_dir.name}.png"
        result.save(output_path)

    finally:
        for img in images:
            img.close()

# endregion

# region hotkey-based functions

def select_addressbar(hide_suggestions=True):
    """
    Move focus to the address bar of the browser, highlighting the entire webpage address. 
    By default suggestions that drop down are hidden immediately. Pass `False` to override.
    """
    pyautogui.hotkey('alt', 'd')
    if hide_suggestions:
        time.sleep(0.01)
        pyautogui.press('esc') # addressbar suggestions obstruct the page without it
    time.sleep(0.3)


def refocus_page():
    """
    Bring focus back to the page by focusing on the address bar.
    Useful to bring hotkeys (like ctrl+f) into correct context.
    """
    select_addressbar()
    time.sleep(0.01)
    pyautogui.press('esc')  # address bar suggestions obstruct the page otherwise
    time.sleep(0.1)


def tab_new():
    """Open new tab using a shortcut"""
    pyautogui.hotkey('ctrl', 't')
    time.sleep(0.1)


def tab_switch(to_left=False):
    """Switch to the nearest tab, the one to the right of the current one by default."""
    if to_left:
        pyautogui.hotkey('ctrl', 'shift', 'tab')
    else:
        pyautogui.hotkey('ctrl', 'tab')
    time.sleep(0.3)


def tab_close():
    """Close current tab. If it's the rightmost tab, a tab to the left will open. Otherwise, a tab to the right will open."""
    pyautogui.hotkey('ctrl', 'w')  # 
    time.sleep(0.1)


def py_reload(sleep_s: int = 5):
    """Reload page via ctlr+f5 hotkey and wait for `sleep_s` seconds"""
    pyautogui.hotkey('ctrl', 'f5')
    time.sleep(sleep_s)


def py_paste(text):
    """Paste text instead of typing (typing may fail if current locale is different from target language)"""
    pyperclip.copy(text)
    time.sleep(0.01)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.3)

# endregion

# region misc

def is_inside(path: str, directory: str) -> bool:
    '''Check if path is within the directory'''
    try:
        Path(path).resolve().relative_to(Path(directory).resolve())
        return True
    except ValueError:
        return False


def timed_close(widget: tk.Misc, close_after: int):
    """
    Returns a `close` function, schedules `widget.destroy` in `close_after` seconds.

    `close` is usually bound to a 'close' button or a 'WM_DELETE_WINDOW' protocol.
    """
    def timeout_close():
        if widget.winfo_exists():
            widget.destroy()
    timer_id = widget.after(close_after * 1000, timeout_close)

    def close():
        widget.after_cancel(timer_id)
        widget.destroy()
    return close


def show_image_modal(master: tk.Toplevel, image_path: str, title: str = "Image", caption: str = ""):
    '''
    Spawns a modal window with a single image. Closes it in 30 seconds.
    While modal is active, master cannot be interacted with.

    Args:
        master: makes windows overlay correctly, used in `modal = tk.Toplevel(master)` and `modal.transient(master)`
        image_path: which image to show
        title: title of the modal window
        caption: optional caption put before the image
    '''
    # maybe move to popups and achieve "modality" by placing canvas with a semi-transparent gray png over the master?
    modal = tk.Toplevel(master, background=ATTENTION_HIGHLIGHT)
    modal.resizable(False, False)
    modal.title(title)
    modal.transient(master)
    modal.grab_set()  # Make modal
    modal.focus_set() # Black window title

    # spawn the modal over the parent, not topleft screen corner. 
    # crutch - rel values taken from main_app
    x_rel = 3
    y_rel = 70
    modal.geometry(f"+{master.winfo_rootx() + x_rel}+{master.winfo_rooty() + y_rel}")

    _caption = tk.Label(modal, text=caption, justify="left", background=ATTENTION_HIGHLIGHT)
    _caption.pack(fill="x")

    label = tk.Label(modal)
    max_w, max_h = 400, 300
    try:
        image = Image.open(image_path)
        scale = min(max_w / image.width, max_h / image.height)
        new_size = (int(image.width * scale), int(image.height * scale))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        _caption.configure(wraplength=image.width)

        photo = ImageTk.PhotoImage(image)
        label.configure(image=photo)
        label.image = photo  # a reference to prevent photo from being garbage collected on function end
    except Exception as e:
        label.configure(text=f"Couldn't load {image_path}")
        print_err_trace(e)

    label.pack(padx=10, pady=10)
    
    modal.protocol("WM_DELETE_WINDOW", timed_close(modal, 30))
    modal.wait_window()


def drag_map_idempotent():
    '''
    Goes to center of the screen and performs dragging that ends exactly where it started.
    Brings focus back to google maps without triggering anything (much safer than clicking).
    '''
    w, h = pyautogui.size()
    pyautogui.moveTo(w // 2, h // 2)
    pyautogui.mouseDown()
    pyautogui.moveRel(4, 0)
    time.sleep(0.1)
    pyautogui.moveRel(1, 0)
    pyautogui.moveRel(-1, 0)
    pyautogui.mouseUp()
    time.sleep(0.3)

# endregion