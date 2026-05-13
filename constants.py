SCREEN_W = 1366 # TODO inherit winfo_screenwidth from tk app, don't leave constant!
SCREEN_H = 768  # TODO same with winfo_screenheight

SEARCH_Y = 112
SEARCH_BAR_X = 122
# rectangle somewhere in the middle of the google maps interface, useful for scroll checks
SEARCH_SCREEN_CHANGE_REGION = (30, 330, 50, 20)

SCROLLBAR_REGION=(405,142,1,586)

PLACE_TYPE_HTML="/html/body/div[1]/div[2]/div[9]/div[8]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[2]/span/span/button"
PLACE_NAME_HTML="/html/body/div[1]/div[2]/div[9]/div[8]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[1]/h1/text()"

RMB_FIRST_OPTION_BELOW_RELATIVE_XY = (60, 25)
"""
It's important to know that when the cursor is too close to screen bottom, two behaviors are possible:
- Context menu snaps to the screen bottom.
  Its first option maintains constant distance from the screen bottom - `y_cutoff`. <br>
  Opening the context menu with a `(x,y)` click where `y > y_cutoff`
  is guaranteed to make the first option clickable at `y_cutoff + 10`
- After falling below a certain `y_cutoff`, context menu reorients itself and appears above the cursor.
  Its first option maintains constant distance from the cursor - `context_height`. <br>
  Opening the context menu with a `(x,y)` click where `y > y_cutoff`
  is guaranteed to make the first option clickable at `y - context_height + 10`.

Be mindful of those cases when writing code.
"""
