#!/usr/bin/env python

import cwiid
import time, sys
import OSC

if len(sys.argv)!=4 or sys.argv[1]=="--help" or sys.argv[1]=="-h":
    print("Usage: {} <ip_of_osc_server> <port_of_osc_server> <number_of_wiimotes_to_use>".format(sys.argv[0]))
    sys.exit

wm = None
wiimotes = []

server_ip = sys.argv[1]
server_port = int(sys.argv[2])
wiimotes_count = int(sys.argv[3])

osc_client = OSC.OSCClient()
print("Sending OSC messages to {}:{}.".format(server_ip, server_port))
osc_client.connect((server_ip, server_port))

def log(str):
    print(str)
    
def send_msg(address, value):
    msg = OSC.OSCMessage()
    msg.setAddress(address)
    log("Sending: {} {}".format(address, value))
    msg.append(value)
    osc_client.send(msg)

class MyWiimote:
    def __init__(self, wm):
        self.wm = wm

print("Trying to connect to {} Wiimotes...".format(wiimotes_count))
while len(wiimotes) < wiimotes_count:
    print("Connecting to Wiimote #{}...".format(len(wiimotes)+1))
    while not wm:
        try:
            wm = cwiid.Wiimote()
            print("Connected.")
            wm.led = len(wiimotes)+1
            wm.rpt_mode = cwiid.RPT_BTN | cwiid.RPT_NUNCHUK
            wiimotes.append({"wiimote": wm, "last_buttons": None, "last_main": None, "last_nunchuk": None, "invert_main": False, "invert_nunchuk": False, "rumble_until": None})
        except RuntimeError:
            pass
    wm = None
            
while True:
    for id, data in enumerate(wiimotes, start=1):
        wm = data["wiimote"]
        state = wm.state
        btn = state['buttons']
        
        if data["rumble_until"] is not None and data["rumble_until"] < time.time():
            wm.rumble = False
            data["rumble_until"] = None
        
        btn_nc = state['nunchuk']['buttons'] if "nunchuk" in state else None
        btn_nc_number = 0 if btn_nc is None else btn_nc
        
        buttons = btn | btn_nc_number
        
        if buttons == data['last_buttons']:
            continue
        #log(data)
        
        data['last_buttons'] = buttons
        
        address = "wiimote/{}".format(id)
        
        #log(state)
        #log("Looking at Wiimote #{}".format(id))
        
        if (btn & cwiid.BTN_1):
            data["invert_main"] = not data["invert_main"]
            print("Main buttons of Wiimote #{} are now inverted: {}".format(id, data["invert_main"]))
            data["rumble_until"] = time.time() + 0.5
            wm.rumble = True
        if (btn & cwiid.BTN_2 and btn_nc is not None):
            data["invert_nunchuk"] = not data["invert_nunchuk"]
            print("Nunchuk buttons of Wiimote #{} are now inverted: {}".format(id, data["invert_nunchuk"]))
            data["rumble_until"] = time.time() + 0.5
            wm.rumble = True
        
        main_btn_pressed = (btn & (cwiid.BTN_A | cwiid.BTN_B) != 0) ^ data["invert_main"]
        if main_btn_pressed != data["last_main"]:
            value = 1.0 if main_btn_pressed else 0.0
            send_msg(address + "/main", value)
            data["last_main"] = main_btn_pressed
        
        if btn_nc is not None:
            nc_btn_pressed = (btn_nc & (cwiid.NUNCHUK_BTN_C | cwiid.NUNCHUK_BTN_Z) != 0) ^ data["invert_nunchuk"]
            if nc_btn_pressed != data["last_nunchuk"]:
                value = 1.0 if nc_btn_pressed else 0.0
                send_msg(address + "/nunchuk", value)
                data["last_nunchuk"] = nc_btn_pressed
    time.sleep(0.05)

