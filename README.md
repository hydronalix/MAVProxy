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

Notes
-----
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
