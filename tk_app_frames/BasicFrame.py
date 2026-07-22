import tkinter as tk

class BasicFrame:
    '''Vertically resizable frame with header, scrollable body, and footer'''
    
    MAX_HEIGHT = 555
    MAX_WIDTH = 555

    def __init__(self, root: tk.Tk):
        self.root = root
        self.header = tk.Frame(root)
        self.header.pack(fill="x", expand=False, padx=10, pady=10)
        middle_frame, self.body = self._create_body()
        middle_frame.configure(borderwidth=4, relief=tk.GROOVE, padx=2, pady=2)
        middle_frame.pack(fill="both", expand=True, padx=10)
        self.footer = tk.Frame(root)
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

        middle_frame = tk.Frame(self.root, height=0)

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
        return middle_frame, body_frame
    

    def update_root_geometry(self):
        '''
        After BasicFrame contents are updated, 
        resize window to fit `body.winfo_reqwidth` 
        and combined height of header, body and footer.
        
        `root.resizable(False, True)` is called to make the width locked and the height resizable.
        '''
        self.root.update_idletasks()

        width = (
            self.body.winfo_reqwidth() + self._vsb.winfo_reqwidth() 
            + 10*2 + 6*2 + 2 # middle padx, middle borders, small margin
        )
        width = min(width, BasicFrame.MAX_WIDTH)

        height = (
            self.body.winfo_reqheight() + self.header.winfo_reqheight() + self.footer.winfo_reqheight() 
            + 10*4 + 6*2 + 0 # header and footer pady, middle borders, small margin
        )
        height = min(height, BasicFrame.MAX_HEIGHT)
        
        # print(f"{width} x {height}")

        self.root.geometry(f"{width}x{height}")
        self.root.resizable(False, True)
