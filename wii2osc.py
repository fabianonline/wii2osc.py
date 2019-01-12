#!/usr/bin/env python

import cwiid
import time, sys, traceback
import OSC

############ Configuration - optional ############
# You can define the bluetooth addresses of your wiimotes and give them aliases.
# This gives you some advantages:
# * The connection can be established a lot faster.
# * You can set an alias for each wiimote which will be set everytime you use it.
#
# If you don't do this, you can just start this tool with a third parameter: The
# number of Wiimotes you would like to use. In that case, that number of Wiimotes
# is expected to connect to and the Wiimotes will just be numbered sequentially.
# First Wiimote will send events to wiimote/1, second one to wiimote/2 and so on.
#
# If you want to use addresses with aliases, use the following syntax:
# addresses = {"00:1F:C5:50:E9:B7": "fabian", "00:1F:C5:50:AB:BA": "uli"}
# If you dont' want to use fixed addresses, use the following syntax:
# addresses = {}

addresses = {"00:1F:C5:50:E9:B7": "fabian", "00:19:1D:6D:9E:C6": "markus", "00:17:AB:3B:A5:78": "jan"}
############ End of configuration ############

if len(sys.argv)<3 or sys.argv[1]=="--help" or sys.argv[1]=="-h":
    print("Usage: {} <ip_of_osc_server> <port_of_osc_server> (<number_of_wiimotes_to_use>)".format(sys.argv[0]))
    sys.exit(1)

wm = None
wiimotes = []

server_ip = sys.argv[1]
server_port = int(sys.argv[2])
wiimote_count = int(sys.argv[3]) if len(sys.argv)>=4 else None

osc_client = OSC.OSCClient()
print("Sending OSC messages to {}:{}.".format(server_ip, server_port))
osc_client.connect((server_ip, server_port))

def log(str):
    print(str)
    


class MyWiimote:
    def __init__(self, wm, mac, alias):
        self.wm = wm
        self.mac = mac
        self.alias = alias
        self.address = "wiimote/{}".format(alias)
        self.wm.led = 1
        self.wm.rpt_mode = cwiid.RPT_BTN | cwiid.RPT_NUNCHUK
        #self.wm.enable(cwiid.FLAG_MESG_IFC)
        #self.wm.mesg_callback = self.callback
        #self.wm.request_status()
        self.last_buttons = None
        self.last_main = None
        self.last_nunchuk = None
        self.invert_main = False
        self.invert_nunchuk = False
        self.rumble_until = None
        self.last_pressed = {}
    
    #def callback(self, data, ts):
    #    print(data)
    #
    #def battery(self):
    #    return self.wm.state["battery"] * 100.0 / cwiid.BATTERY_MAX
    
    def check_rumble(self):
        if self.rumble_until is not None and self.rumble_until < time.time():
            self.wm.rumble = False
            self.rumble_until = None
    
    def check_invert(self, btn, btn_id, name):
        if btn & btn_id:
            self.log("Inverting {} buttons.".format(name))
            self.rumble(0.5)
            return True
        else:
            return False
    
    def rumble(self, length):
        self.wm.rumble = True
        self.rumble_until = time.time() + length
        
    def check_buttons(self):
        state = self.wm.state
        buttons = buttons_main = state['buttons']
        
        buttons_nunchuk = None
        
        if "nunchuk" in state:
            buttons_nunchuk = state['nunchuk']['buttons']
            stick = state['nunchuk']['stick']
            if stick[0] < 64: buttons_nunchuk = buttons_nunchuk | cwiid.BTN_LEFT << 20
            if stick[0] > 192:  buttons_nunchuk = buttons_nunchuk | cwiid.BTN_RIGHT << 20
            if stick[1] < 64: buttons_nunchuk = buttons_nunchuk | cwiid.BTN_DOWN << 20
            if stick[1] > 192:  buttons_nunchuk = buttons_nunchuk | cwiid.BTN_UP << 20
            buttons = buttons | (buttons_nunchuk << 20)
        
        if buttons == self.last_buttons:
            return
        
        self.invert_main ^= self.check_invert(buttons_main, cwiid.BTN_1, "main")
        self.invert_nunchuk ^= self.check_invert(buttons_main, cwiid.BTN_2, "nunchuk")
        
        self.check_button(buttons_main, cwiid.BTN_A | cwiid.BTN_B, self.invert_main, "main", True)
        self.check_button(buttons_main, cwiid.BTN_LEFT, False, "left", False)
        self.check_button(buttons_main, cwiid.BTN_RIGHT, False, "right", False)
        self.check_button(buttons_main, cwiid.BTN_UP, False, "up", False)
        self.check_button(buttons_main, cwiid.BTN_DOWN, False, "down", False)
        self.check_button(buttons_main, cwiid.BTN_MINUS, False, "minus", False)
        self.check_button(buttons_main, cwiid.BTN_PLUS, False, "plus", False)
        self.check_button(buttons_main, cwiid.BTN_HOME, False, "home", False)
        
        self.check_button(buttons_nunchuk, cwiid.NUNCHUK_BTN_C | cwiid.NUNCHUK_BTN_Z, self.invert_nunchuk, "nunchuk", True)
        self.check_button(buttons_nunchuk, cwiid.BTN_LEFT << 20, False, "nunchuk_left", False)
        self.check_button(buttons_nunchuk, cwiid.BTN_RIGHT << 20, False, "nunchuk_right", False)
        self.check_button(buttons_nunchuk, cwiid.BTN_UP << 20, False, "nunchuk_up", False)
        self.check_button(buttons_nunchuk, cwiid.BTN_DOWN << 20, False, "nunchuk_down", False)
        
        self.last_buttons = buttons
    
    def check_button(self, buttons, btnid, invert, name, long_pressable):
        if buttons is None:
            return
        pressed = (buttons & btnid != 0) ^ invert
        if long_pressable and (not btnid in self.last_pressed or pressed != self.last_pressed[btnid]):
            value = 1.0 if pressed else 0.0
            self.send_msg(name, value)
            self.last_pressed[btnid] = pressed
        elif not long_pressable:
            if pressed and (not btnid in self.last_pressed or pressed != self.last_pressed[btnid]):
                self.send_msg(name)
            self.last_pressed[btnid] = pressed
    
    def send_msg(self, key, value=None):
        addr = self.address + "/" + key
        self.log("Sending: {} {}".format(addr, value))
        
        msg = OSC.OSCMessage()
        msg.setAddress(addr)
        if value is not None: msg.append(value)
        osc_client.send(msg)
        
    def step(self):
        self.check_rumble()
        self.check_buttons()
    
    def log(self, message):
        if True:
            print("Wiimote \"{}\": {}".format(self.alias, message))

def connect(mac, alias):
    if mac is not None:
        print("Connecting to Wiimote \"{}\" with address {}...".format(alias, mac))
    else:
        print("Connecting to unspecified Wiimote #{}...".format(alias))
    wm = None
    while wm is None:
        try:
            if mac is not None:
                wm = cwiid.Wiimote(mac)
            else:
                wm = cwiid.Wiimote()
            print("Connected.")
            wiimotes.append(MyWiimote(wm, mac, alias))
        except RuntimeError:
            pass

if wiimote_count is not None:
    print("Trying to connect to {} wiimotes...".format(wiimote_count))
    for i in xrange(wiimote_count):
        connect(None, str(i+1))
elif len(addresses)>0:
    print("Trying to connect to the {} wiimotes defined in addresses...".format(len(addresses)))
    for mac, alias in addresses.items():
        connect(mac, alias)
else:
    print("No addresses set and no wiimote_count given on the command line. I don't know what to do. Quitting.")
    sys.exit(1)


############ Main loop #################
while True:
    for wiimote in wiimotes:
        try:
            wiimote.step()
        except:
            print("An unexpected error occurred. I will just ignore it, but it should definitely not happen. Please report it on github.")
            print("The error was:")
            traceback.print_exc()
            print()
    time.sleep(0.05)
