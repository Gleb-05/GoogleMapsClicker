import tkinter as tk

from keypress_publisher import KeypressPublisher
from tk_app_frames.switch_frame_controller import setup_switch_frame_controller, FrameAndVariables
from tk_app_frames.get_area_img import GetAreaImgFrame
from tk_app_frames.edit_configs import EditConfigsFrame


class MainApp(tk.Tk):

    # https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        W, H = self.winfo_screenwidth(), self.winfo_screenheight()
        self.minsize(300, 100)
        self.attributes("-topmost", True)

        self.keypress_publisher = KeypressPublisher()

        switch_container = tk.Frame(self, bg="darkgray")
        switch_container.pack(side="top", fill="both")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        frames = {}
        for F in (GetAreaImgFrame, EditConfigsFrame):
            page_name = F.__name__
            frame = F(master=container, controller=self)
            frames[page_name] = FrameAndVariables(frame, {})

        setup_switch_frame_controller(frames, switch_container)


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()