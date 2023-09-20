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
* On Hydro_Eng, the drone will be at **192.168.50.151**
* On tidepool, the drone will be at **10.1.0.123**
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

You can also just make changes to the following files:
* `/etc/wpa_supplicant/wpa_supplicant.conf`
* `/etc/dhcpcd.conf`

The content of the files should be evidently repeatable to add other networks or change IP addresses.

Mavproxy module usage notes
---------------------------
- For a list of changeable parameters, call `depthfinder set`
- Creates a new file whenever you load the module, which happens on start up.
- If things seem like they're breaking, use `depthfinder set verbose 1`.  
- The default target system ID is 1. You may need to change this to receive GPS messages and update module lat/lon. Use `verbose` to see what sys ID you're receiving messages from.

The logic for writing entries to the file is this:
```python
        self.nmea_packet()
        if (self.landed == True and self.mission_active == True) or (self.depthfinder_settings.debug == True): 
            if self.initflag == False:
                self.create_logfile()
                self.initflag = True
            self.write_status()
        else:
            if self.initflag == True:
                self.initflag = False
                self.logFile = ""
            return
```

If you're in a bind and the logic for only recording data in the landed state isn't working, you can do `depthfinder set debug 1` to just always get NMEA data and write file entries. You can either add that to `~/.mavinit.scr` and refresh the `systemd` task, or stop the `systemd` task and run mavproxy manually.

Build & test procedure
----------------------
1. Clone the repo. be on the right branch.
2. Delete the previous build directory, `rm -r build`
3. If you have a shell terminal, run `python3 setup.py build install --user` to make the new mavproxy script at `/build/scripts-3.7/mavproxy.py`. *This is what you will run to do hermes stuff*

From here, there are some divergent steps:
* If you want to make changes to the the systemd task that runs automatically on boot:
    1. `sudo systemctl stop mavproxserv.service`
    2. run `systemctl status`: if it returns "degraded" or something in red, run `sudo systemctl reset-failed`
    3. check the startup script at `~/.mavinit.scr` and make any desired changes
    4. edit the file at `/etc/systemd/system/mavproxserv.service`
    5. `sudo systemctl start mavproxserv.service`
    6. optionally restart the raspberry pi
* If you want to just run mavproxy manually with the interactive shell:
    1. `sudo systemctl stop mavproxserv.service`
    2. run `systemctl status`: if it returns "degraded" or something in red, run `sudo systemctl reset-failed`
    3. check the startup script at `~/.mavinit.scr` and make any desired changes
    4. do `python3 /build/scripts-3.7/mavproxy --out=udpin:[PI IP]:14550`. you will have to manually set the PI IP youself since the cool systemd scripts won't execute
    5. do mavproxy stuff! reference the docs for that :)


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

cool video: https://www.youtube.com/watch?v=BK3OsNJoF8A
  

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
* `MISSION_CURRENT` does not contain extened mavlink2 data. that's not really an error with the code here (i think) but rather something that's just confusing to watch out for.


Milestones
----------
18 September 2023: yay first successful flight & data collection!