import tkinter as tk
from tk_app_frames.BasicFrame import BasicFrame

from usr_get_area_img import get_dd_rect_img
from function_to_tk_entries import build_function_editor, ButtonManager



class GetAreaImgFrame(BasicFrame):
    '''See and change individual fields of configs'''
    def __init__(self, root: tk.Tk):
        super().__init__(root)
        self.root = root
        self.root.title("Work with Areas")
        self.W, self.H = root.winfo_screenwidth(), root.winfo_screenheight()
        self.root.minsize(300, 100)
        self.root.attributes("-topmost", True)

        tk.Frame(self.body, width=BasicFrame.MAX_WIDTH-140).pack()  # crutch to standardize the width of different windows

        debug_text = tk.Text(self.header, width=300, height=10)
        debug_text.insert("1.0", "Debug text")
        debug_text.pack(expand=True)
        self.button_manager = ButtonManager(debug_text)

        for target_function in [get_dd_rect_img]:
            build_function_editor(target_function, self.body, self.button_manager)

        self.update_root_geometry()


if __name__ == "__main__":
    root = tk.Tk()
    app = GetAreaImgFrame(root)
    root.mainloop()
