# wii2osc.py

Send OSC messages depending on events on a wiimote.

## Dependencies

* `libcwiid1` with python bindings
* `pyOSC`

## Installation

This describes the installation on a fresh installation of raspbian on a
Raspberry 3. Although this app is not fixed to be run on this platform, you
will have to figure out how to install it elsewhere by yourself.

* `sudo apt-get update`
* `sudo apt-get install python-cwiid python-pip git`
* `git clone https://github.com/fabianonline/wii2python.py.git`
* `cd wii2osc.py`
* `pip install -r requirements.txt`

## Usage

There are two ways of running python2wii: With fixed bluetooth addresses and
aliases or dynamically. The first method requires a bit more work to
configure, but has the nice advantage of being able to use a fixed alias per
Wiimote.

In every case you'll need the IP address and port of an OSC server. Many
professional software will have this included; check the docs to learn if /
how to enable it and which port is being used.

### Dynamically

Just run the tool with three parameters:
* The IP address of the OSC server,
* the port the OSC server is listening on and
* the number of Wiimotes you want to use.

So, for example if your OSC server is listening on port 8000 on IP address
10.10.2.33 and you want to use 2 Wiimotes, you'd run:

`python wii2osc.py 10.10.2.33 8000 2`

The tool will then connect to any two Wiimotes, giving the first one the
alias "1" and the other one the alias "2".

### Fixed addresses and aliases

You'll need the bluetooth addresses of each of your Wiimotes. Run `hcitool
scan` and press buttons 1+2 on your Wiimote. It should appear in the scan
results. Note it's address.

Edit wii2osc.py. At the top there will be a block containing a bit of
information followed by a line saying `addresses = {}`. There you can add
the bluetooth address and an alias.

Let's say the scan showed your Wiimote's address as being 00:1F:C5:50:AB:BA.
You want to give this Wiimote the alias "fabian". Then modify the line to
say:

`addresses = {"00:1F:C5:50:AB:BA": "fabian"}`

You can add multiple addresses and aliases:

`addresses = {"00:1F:C5:50:AB:BA": "fabian", "00:1F:C5:54:7C:D0": "uli"}`

Then run the tool with two parameters:
* The IP address of the OSC server and
* the port the OSC server is listening on.

So, for example if your OSC server is listening on port 8000 on IP address
10.10.2.33, you'd run:

`python wii2osc.py 10.10.2.33 8000`

The tool will then connect to the Wiimotes defined in the script.

Note that even after modifying the file you can still use the dynamic method
above by proving a third parameter. In that case, your given bluetooth
addresses and aliases will be completely ignored.

## OSC data

The data sent via OSC to your OSC server will be:

* To `wiimote/<alias>/main` whether buttons A or B on the Wiimote are
  pressed.
* To `wiimote/<alias>/nunchuk` whether buttons C or Z on a Nunchuk connected
to the Wiimote are pressed.

The data sent will be a float. By default, 1.0 is sent when a button is
pressed and 0.0 is sent when the button is released.
By pressing 1 or 2 on the Wiimote you can invert this values for the Wiimote
or the Nunchuk, respectively. So, after pressing 2 on the Wiimote, a 1.0
will be sent when no button is pressed on the Nunchuk and 0.0 is sent when a
button is pressed. By pressing 2 again, you would revert to the default
mapping.