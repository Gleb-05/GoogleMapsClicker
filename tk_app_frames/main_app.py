import tkinter as tk

from z_app_components.config_app import C_size, load_preferences_once
from z_app_components.keypress_publisher import KeypressPublisher
from tk_app_frames.switch_frame_controller import setup_switch_frame_controller, FrameAndVariables
from tk_app_frames.get_area_img import GetAreaImg
from tk_app_frames.edit_configs import EditConfigs


class MainApp(tk.Tk):

    # https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter

    def __init__(self, *args, **kwargs):
        load_preferences_once()
        tk.Tk.__init__(self, *args, **kwargs)

        C_size.SCREEN_W = self.winfo_screenwidth()
        C_size.SCREEN_H = self.winfo_screenheight()
        self.minsize(300, 100)
        self.attributes("-topmost", True)
        self.resizable(False, True)

        self.keypress_publisher = KeypressPublisher()

        switch_container = tk.Frame(self, bg="darkgray")
        switch_container.pack(side="top", fill="both")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        frames = {}
        for F in (GetAreaImg, EditConfigs):
            page_name = F.__name__
            frame = F(master=container, controller=self)
            frames[page_name] = FrameAndVariables(frame, {})

        setup_switch_frame_controller(frames, switch_container)


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
