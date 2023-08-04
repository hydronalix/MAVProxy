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

Build & test procedure
----------------------
1. clone the repo. be on the right branch. 
2. if you have a shell terminal, run `python3 setup.py build install --user`
3. run mavproxy from `build/scripts-3.11/mavproxy.py`. 
    - when testing with FC hardware, be sure to specify the connection point with `--master` (see https://ardupilot.org/mavproxy/docs/getting_started/starting.html#master)
    - if you're using python2 or some cringe, the mavproxy file might be at a different location
    - you may need to uninstall mavproxy or other dependencies from other locations. be sure to read the error messages carefully!
4. if you see "detected vehicle" and a bunch of info regarding the FC, good job! otherwise, go back and figure out where in 1-3 you messed up.
5. load the depthfinder module via `module load depthfinder`
6. run `depthfinder status` or whatever is implemented to help debug.

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
