![GitHub Actions](https://github.com/ardupilot/MAVProxy/actions/workflows/windows_build.yml/badge.svg)

MAVProxy

This is a MAVLink ground station written in python. 

Please see https://ardupilot.org/mavproxy/index.html for more information

This ground station was developed as part of the CanberraUAV OBC team
entry

License
-------

MAVProxy is released under the GNU General Public License v3 or later


Maintainers
-----------

The best way to discuss MAVProxy with the maintainers is to join the
mavproxy channel on ArduPilot discord at https://ardupilot.org/discord

Lead Developers: Andrew Tridgell and Peter Barker

Windows Maintainer: Stephen Dade

MacOS Maintainer: Rhys Mainwaring


Hermes overview
---------------
This version aims to collect NMEA strings to also provide depth sensor information as a telemetry string, combining this and GPS info and stuff from the FC to create a depth map.

Operational notes
-----------------
For debugging purposes this drone will work differently than other things: the drone itself is setup on a static IP.

Network/IP setup
* The drone will automatically connect to both Hydro_Eng or tidepool depending on which one is active. If in the office, only use Hydro_Eng to avoid confusion, or put the router right next to the drone and hope it connects to tidepool (it probably will)
* On Hydro_Eng, the drone will be at 192.168.50.151
* On tidepool, the drone will be at 10.1.0.123
* To connect, your GS *device does not need at static ip*
* In QGC, navigate to `Q > Application Settings > Comm Links`
* Add a new connection (if you haven't yet) and name it like "hermes tidepool" or something
* Change `type` to "UDP"
* In the `Server Addresses` field, enter [drone IP for the particular network]:14550, click `Add Server`
* Save the connection and do this again for the other network (tidepool or Hydro_Eng)
* To connect to the drone, just select the connection & click `Connect` (provided you're on the same network as the drone)

SSH & Stuff
* Again, depending on the network, ssh to either 10.1.0.123 or 192.168.50.151, or use the hostname which should be h000x on both networks
* Creds are the same as usual
* mavproxy stuff is located in the `mavproxy` directory. To start in the field, run `./~/build/scripts-3.7/mavproxy.py --out=udpin:[pi ip]:14550` (whoever's on QGC can now just connect using the method described above while you're ssh'd in)
* to start the depthfinder, use `module load depthfinder`
* see below for more specific operational notes

If the static IP setup needs to be changed, see: https://raspberrypi.stackexchange.com/questions/89429/raspbian-stretch-multiple-wifi-networks-with-different-static-ip-routers-dns

Mavproxy module usage notes
---------------------------
- For a list of changeable parameters, call `depthfinder set`
- Writes to a new file whenever you load the module, which happens on start up. Still need to check if it will write to the file while in land state.
- NMEA does not get automatically called in the `idle_task` loop--use `depthfinder set debug true` to bypass the landed state thing and update on NMEA message receipt.
- If things seem like they're breaking, use `depthfinder set verbose 1`.  
- The default target system ID is 0. You may need to change this to receive GPS messages and update module lat/lon. Use `verbose` to see what sys ID you're receiving messages from.

Build & test procedure
----------------------
1. Clone the repo. be on the right branch.
2. Delete the previous build directory, `rm -r build`
3. Rf you have a shell terminal, run `python3 setup.py build install --user`
4. Run mavproxy from `build/scripts-3.11/mavproxy.py`. 
    - When testing with FC hardware, be sure to specify the connection point with `--master` (see https://ardupilot.org/mavproxy/docs/getting_started/starting.html#master)
    - If you're using python2 or some cringe, the mavproxy file might be at a different location: this is the case on raspberry pi, since the particular one I was using built to python 3.7 for some reason
    - You may need to uninstall mavproxy or other dependencies from other locations. be sure to read the error messages carefully!
5. If you see "detected vehicle" and a bunch of info regarding the FC, good job! otherwise, go back and figure out where in 1-3 you messed up.
6. Load the depthfinder module via `module load depthfinder`
7. Run `depthfinder status` or whatever is implemented to help debug.

Land & continue mission config
------------------------------
configuring the vehicle:
* set AUTO_OPTIONS "allow takeoff without raising throttle" bit TRUE. this may be helpful in general. also probably the "allow arming" bit as well. if it isn't already.
* set MIS_OPTIONS "continue after land" bit TRUE. this does not appear to be documented online, however QGC should have checkboxes.
* set DISARM_DELAY to 0, disabling the functionality. automatic disarming can mess with things.

mission planning:
* first portion is ez: takeoff, waypoint(s), land
* for the next item, use a "DO_AUX_FUNCTION" to disarm/ar or do other spicy behavior. this may be useful for the triggering the depth finder
* add a "Delay until" item and specify like 5-15 seconds maybe. *do not use the regular delay command or specify MAV_CMD_NAV_DELAY in "Show all values"*
* probably use another DO_AUX_FUNCTION to do whatever
* takeoff, waypoint, land, repeat

for more info see https://www.youtube.com/watch?v=BK3OsNJoF8A
  

Random notes
------------
* mavproxy modules extend `mp_module.MPModule`
* `mavproxy_serial` module handles the serial comm stuff
* `mavproxy_link` seems to do the admin work of holding udp/tcp links, but the actual socket activity is handled elsewhere
* for some reason, all classes hold within themselves a `mpstate` object, which is defined in `mavproxy.py`
* it looks like if a module needs a socket, it just imports it and there's no single socket handler:
    * `mavpxory_DGPS` attempts to receive in idle time. there's also this `gps_rtcm_data_send` method that's called in several places but doesn't appear to be defined anywhere.
    * the silvus radio module also just sorta defines it when needed to send a udp packet
* wtf is the `MPState` object lol this is also a property of literally every module
    * holds all the MPSettings  
    * 

Errors / unresolved bugs
------------------------

Friggn thing crashes after a while if I'm not doing anything, it seems.
```
Exception in thread log_writer:
Traceback (most recent call last):
  File "/opt/homebrew/Cellar/python@3.11/3.11.4_1/Frameworks/Python.framework/Versions/3.11/lib/python3.11/threading.py", line 1038, in _bootstrap_inner
    self.run()
  File "/opt/homebrew/Cellar/python@3.11/3.11.4_1/Frameworks/Python.framework/Versions/3.11/lib/python3.11/threading.py", line 975, in run
```
