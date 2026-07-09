import threading
import traceback
import time
import tkinter as tk
import pyautogui
import keyboard

SAFE_Y=250  # safely below browser ui edge
BROWSER_RIGHT_X=870
INSPECT_LEFT_X=457


class PrepareFrame:
    """
    Move boundaries of certain GUI elements to predefined values.

    This introduces enough precision to use clicks with constant coordinates in extract_place_info
    instead of searching for images or html within the webpage.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Prepare")
        self.W, self.H = root.winfo_screenwidth(), root.winfo_screenheight()
        self.root.geometry("300x250+{}+{}".format(self.W-400, 100))
        self.root.attributes("-topmost", True)

        self.steps = {
            "side_browser": self.side_browser,
            "set_browser_x": self.set_browser_x,
            "set_inspect_x": self.set_inspect_x,
            "set_inspect_y": self.set_inspect_y,
            "show_xy": self.show_xy,
        }
        self.steps_names = list(self.steps.keys())
        self.step_var = tk.StringVar(value="show_xy")
        tk.OptionMenu(root, self.step_var, *self.steps_names).pack(pady=10)
        
        instruction = "Press NumLk (or alt+f2) after moving your cursor to a suitable position."
        tk.Label(root, text=instruction, wraplength=300).pack(expand=True)
        
        self.debug_text = tk.Text(root, width=300)
        self.debug_text.insert("1.0", "Debug text")
        self.debug_text.pack(expand=True)

        threading.Thread(target=self.listen_hotkey, daemon=True).start()

    def execute_selected_step(self):
        try:
            result = self.steps[self.step_var.get()]()
        except Exception as e:
            result = e
            traceback.print_exc()
        self.debug_text.delete("1.0", tk.END)
        self.debug_text.insert("1.0", str(result))

    def listen_hotkey(self):
        keyboard.add_hotkey("num lock", self.execute_selected_step)
        keyboard.add_hotkey("alt+f2", self.execute_selected_step)  # fallback option
        keyboard.wait()  # Keep the thread alive

    def show_xy(self):
        x, y = pyautogui.position()
        return f"X: {x}, Y: {y}"

    @staticmethod
    def auto_advance(func):
        # @wraps(func)
        def wrapper(self: "PrepareFrame", *args, **kwargs):
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
    def set_browser_x(self):
        pyautogui.dragTo(BROWSER_RIGHT_X, None, duration=0.3)

    @auto_advance
    def set_inspect_x(self):
        pyautogui.dragTo(INSPECT_LEFT_X, None, duration=0.3)

    @auto_advance
    def set_inspect_y(self):
        pyautogui.dragTo(None, self.H - 1, duration=0.3)


if __name__ == "__main__":
    root = tk.Tk()
    app = PrepareFrame(root)
    root.mainloop()
