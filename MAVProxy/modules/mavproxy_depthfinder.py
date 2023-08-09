#!/usr/bin/env python
'''

depthfinder Module
hydronalix, 2023
from the mavproxy_example.py, uh ... example

'''

import os
import os.path
import sys
from pymavlink import mavutil
import errno
import time

from MAVProxy.modules.lib import mp_module
from MAVProxy.modules.lib import mp_util
from MAVProxy.modules.lib import mp_settings


class depthfinder(mp_module.MPModule):
    def __init__(self, mpstate):
        """Initialise module"""
        super(depthfinder, self).__init__(mpstate, "depthfinder", "")
        self.status_callcount = 0
        self.boredom_interval = 10 # seconds
        self.last_bored = time.time()
        self.lat = 0.0
        self.lon = 0.0
        self.landed = False

        self.packets_mytarget = 0
        self.packets_othertarget = 0

        self.depthfinder_settings = mp_settings.MPSettings(
            [ ('verbose', bool, False),
          ])
        self.add_command('depthfinder', self.cmd_depthfinder, "depthfinder module", ['status','set (LOGSETTING)'])

    def usage(self):
        '''show help on command line options'''
        return "Usage: depthfinder <status|set>"

    def cmd_depthfinder(self, args):
        '''control behaviour of the module'''
        if len(args) == 0:
            print(self.usage())
        elif args[0] == "status":
            print(self.status())
        elif args[0] == "set":
            self.depthfinder_settings.command(args[1:])
        else:
            print(self.usage())

    def status(self):
        '''returns information about module'''
        self.status_callcount += 1
        self.last_bored = time.time() # status entertains us
        return("status called %(status_callcount)d times.  My target positions=%(my_lat)f, %(my_lon)f (from %(packets_mytarget)u packets);  Other target positions=%(packets_mytarget)u" %
               {"status_callcount": self.status_callcount,
                "packets_mytarget": self.packets_mytarget,
                "packets_othertarget": self.packets_othertarget,
                "my_lat": self.lat,
                "my_lon": self.lon,
               })

    def boredom_message(self):
        if self.depthfinder_settings.verbose:
            return ("I'm very bored")
        return ("I'm bored")

    def idle_task(self):
        '''
        called rapidly by mavproxy
        
        i don't think there's really a particular "idle state", pretty sure this is just called every time through the main loop... or something
        '''
        now = time.time()
        if now-self.last_bored > self.boredom_interval:
            self.last_bored = now
            message = self.boredom_message()
            self.say("%s: %s" % (self.name,message))
            # See if whatever we're connected to would like to play:
            self.master.mav.statustext_send(mavutil.mavlink.MAV_SEVERITY_NOTICE,
                                            message)

    def mavlink_packet(self, m):
        '''
        handle mavlink packets
        
        The m object is a mavlink message object. You can check its type via the get_type() method.
        To figure out the fields available in the message, see https://mavlink.io/en/messages/common.html.
        They should just be accessible as attributes of the m object, as you can see below. Python moment.

        Some todos for this function:
        [x] check for some status message that tells us if we've landed (on the surface of the water)
        [ ] record lat/lon to a file, but only if we've landed
        [ ] record depth to a file, but only if we've landed (this might need to go elsewhere)
        '''
        if m.get_type() == 'GLOBAL_POSITION_INT':
            if self.settings.target_system == 0 or self.settings.target_system == m.get_srcSystem():
                self.packets_mytarget += 1
                self.lat = m.lat
                self.lon = m.lon
            else:
                self.packets_othertarget += 1
        elif m.get_type() == 'EXTENDED_SYS_STATE':
            if m.landed_state == 4: # see: https://mavlink.io/en/messages/common.html#MAV_LANDED_STATE
                self.landed = True
            else:
                self.landed = False

def init(mpstate):
    '''initialise module'''
    return depthfinder(mpstate)
