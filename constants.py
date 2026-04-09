SCREEN_W = 1366 # TODO inherit winfo_screenwidth from tk app, don't leave constant!
SCREEN_H = 768  # TODO same with winfo_screenheight

SEARCH_Y = 112
SEARCH_BAR_X = 122
# rectangle somewhere in the middle of the google maps interface, useful for scroll checks
SEARCH_SCREEN_CHANGE_REGION = (30, 330, 50, 20)

SCROLLBAR_REGION=(405,142,1,586)

PLACE_TYPE_HTML="/html/body/div[1]/div[2]/div[9]/div[8]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[2]/span/span/button"
PLACE_NAME_HTML="/html/body/div[1]/div[2]/div[9]/div[8]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[1]/h1/text()"

RMB_FIRST_OPTION_BELOW_RELATIVE_XY = (90, 30)
RMB_FIRST_OPTION_ABOVE_RELATIVE_XY = (90,-230)  # rmb menu appears above mouse cursor when closer to page bottom
