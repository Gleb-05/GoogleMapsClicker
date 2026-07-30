import tkinter as tk

from z_app_components.config_app import C_size, load_preferences_once
from z_app_components.keypress_publisher import KeypressPublisher
from tk_app_frames.switch_frame_controller import setup_switch_frame_controller, FrameAndVariables
from tk_app_frames.get_area_img import GetAreaImg
from tk_app_frames.edit_configs import EditConfigs


class MainApp(tk.Tk):
    '''Make single instance of the app to run in a tk loop'''
    # https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter
    
    MAX_HEIGHT = 555
    MAX_WIDTH = 555

    FRAMES = (GetAreaImg, EditConfigs)

    def __init__(self, *args, **kwargs):
        load_preferences_once()
        tk.Tk.__init__(self, *args, **kwargs)

        C_size.SCREEN_W = self.winfo_screenwidth()
        C_size.SCREEN_H = self.winfo_screenheight()
        self.minsize(300, 100)
        self.attributes("-topmost", True)
        self.resizable(False, True)

        self.keypress_publisher = KeypressPublisher()

        switch_controller_frame = tk.Frame(self, bg="darkgray")
        switch_controller_frame.pack(side="top", fill="both")

        self.switch_container = tk.Frame(self)
        self.switch_container.pack(side="top", fill="both", expand=True)

        frames = {}
        for F in self.FRAMES:
            page_name = F.__name__
            frame = F(master=self.switch_container, controller=self)
            frames[page_name] = FrameAndVariables(frame, {})

        setup_switch_frame_controller(frames, switch_controller_frame, self.update_root_geometry)


    def update_root_geometry(self, active_fav: FrameAndVariables, active_name: str = ""):
        '''
        Function provided as callback for `setup_switch_frame_controller`.
        
        After mainapp contents are updated, resize to fit active frame.
        If `active_frame` provides `custom_reqwidth` and `custom_reqheight` - use them (see example in BasicFrame).
        Otherwise, use `winfo_reqwidth` and `winfo_reqheight`.
        '''
        self.update_idletasks()
        active_frame = active_fav.frame

        if hasattr(active_frame, "custom_reqwidth") and hasattr(active_frame, "custom_reqheight"):
            # custom_reqheight will generally compensate for canvas or other elements
            # that don't take part in tk reqheight calculations.
            mainapp_height = self.winfo_reqheight() - active_frame.winfo_reqheight()
            height = min(mainapp_height + active_frame.custom_reqheight(), MainApp.MAX_HEIGHT)
            # the app is constructed by packing frames vertically. mainapp is defined by its contents.
            # for that reason, mainapp_width is expected to always be 0. Other values would be a bug.
            width = min(active_frame.custom_reqwidth(), MainApp.MAX_WIDTH)
        else:
            width = min(self.winfo_reqwidth(), MainApp.MAX_WIDTH)
            height = min(self.winfo_reqheight(), MainApp.MAX_HEIGHT)
        self.geometry(f"{width}x{height}")


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
