global strike_val               # current stock val
global event                    # for thread
global opendDlg                 # dlg is opned?
global current_login_userid     # for generate token file

global TDStreamingDbUserID      # user db pk
global TDStreamingClientID      # user client key
global TDStreamingClient        # stream path
global tradeCode                # actived trade Code buy/sell/cancel
global tradeXml                 # detail treade data
global tradeJson                # xml -> json

# global db_conn                  # sqlit connector
# global db_cursor                # sqlit cursor


global getprofit
global stoploss
global fridaymax

# global message                  # notification [ {text=string, color=string, opend=bool}, ... ]
messages = {}                   # notification [ {text=string, color=string, opend=bool}, ... ]
global msgduration
trade_msgs = []                 # trading state message
interact_msgs = []              # interactive notifications
acc_order_getted = []           # acc id that catched order
orders = {}                     # current triggered orders

color_red = '#9F0101'
color_red_arr = [0xAF, 0x11, 0x11]
color_blue = '#075F12'
color_blue_arr = [0x17, 0x6F, 0x22]
color_grey = '#6D6A6A'

color_info_back = '#078080'
color_err_back = '#AD0D03'
color_success_back = '#05761B'
color_warning_back = '#A3A707'