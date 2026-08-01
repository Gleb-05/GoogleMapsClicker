import tkinter as tk

class BasicFrame(tk.Frame):
    '''Vertically resizable frame with header, scrollable body, and footer'''

    def __init__(self, master: tk.Misc, controller):
        tk.Frame.__init__(self, master)
        self.controller = controller
        
        self.header = tk.Frame(self)
        self.header.pack(fill="x", expand=False, padx=10, pady=10)
        middle_frame, self.body = self._create_body()
        middle_frame.configure(borderwidth=4, relief=tk.GROOVE, padx=2, pady=2)
        middle_frame.pack(fill="both", expand=True, padx=10)
        self.footer = tk.Frame(self)
        self.footer.pack(fill="x", expand=False, padx=10, pady=10)


    def _create_body(self) -> tuple[tk.Frame, tk.Frame]:
        '''
        Return 
        `middle_frame` - convenience container for scrollbar and such, 
        and `body_frame` - the actual body that has to be filled with content
        '''
        # https://stackoverflow.com/questions/3085696/adding-a-scrollbar-to-a-group-of-widgets-in-tkinter/3092341
        
        def onFrameConfigure(canvas: tk.Canvas):
            '''Reset the scroll region to encompass the inner frame'''
            canvas.configure(scrollregion=canvas.bbox("all"))

        middle_frame = tk.Frame(self, height=0)

        canvas = tk.Canvas(middle_frame, height=0, borderwidth=0, background="lightgray", highlightthickness=0)
        body_frame = tk.Frame(canvas, height=0)
        vsb = tk.Scrollbar(middle_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        # frame.pack(fill="both", expand=True)
        canvas.create_window((0,0),window=body_frame, anchor="nw")

        self._vsb = vsb  # crutch needed for update_root_geometry

        body_frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))

        # https://stackoverflow.com/questions/17355902/tkinter-binding-mousewheel-to-scrollbar
        def on_mousewheel(event: tk.Event):
            units = 0
            if event.num == 5 or event.delta == -120:
                units = 1  # 1 scrolls down
            if event.num == 4 or event.delta == 120:
                units = -1 # -1 scrolls up
            canvas.yview_scroll(units, "units")

        body_frame.bind('<Enter>', lambda event, canvas=canvas: 
                        canvas.bind_all("<MouseWheel>", on_mousewheel))
        body_frame.bind('<Leave>', lambda event, canvas=canvas: 
                        canvas.unbind_all("<MouseWheel>"))

        return middle_frame, body_frame

    def custom_reqwidth(self):
        width = (
            self.body.winfo_reqwidth() + self._vsb.winfo_reqwidth() 
            + 10*2 + 6*2 + 2 # middle padx, middle borders, small margin
        )
        return width

    def custom_reqheight(self):
        height = (
            self.body.winfo_reqheight() + self.header.winfo_reqheight() + self.footer.winfo_reqheight() 
            + 10*4 + 6*2 + 2 # header and footer pady, middle borders, small margin
        )
        return height
