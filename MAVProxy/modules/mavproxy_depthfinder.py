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
import serial

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
        self.current_depth = 0.0
        self.current_temp = 0.0
        self.depth_readings = []        #TODO: make this a circular buffer
        self.temp_readings = []  
        self.num_readings = 10
        self.ser = serial.Serial()
        self.ser.baudrate = 4800
        self.ser.port = '/dev/ttyS0'
        self.fileNum = 1
        self.home_dir = os.path.expanduser('~')
        self.logFile = self.home_dir + "/file" +str(self.fileNum)+".csv"
        

        while os.path.isfile(self.logFile):
            self.fileNum += 1
            self.logFile = self.home_dir + "/file" +str(self.fileNum)+".csv"

        self.file = open(self.logFile, "w") #change to a if we want it to be able to be turned on and off again and write to same file
        self.file.write("Latitude,Longitude,Depth(m),Tempurature(C)\n")
        self.file.close()

        self.depthfinder_settings = mp_settings.MPSettings(
            [ ('verbose', bool, False),
                ('debug', bool, False),
          ])
        self.add_command('depthfinder', self.cmd_depthfinder, "depthfinder module", ['status','set (LOGSETTING)', 'capture'])

    def usage(self):
        '''show help on command line options'''
        return "Usage: depthfinder <status|set|caputre>"

    def cmd_depthfinder(self, args):
        '''control behaviour of the module'''
        if len(args) == 0:
            print(self.usage())
        elif args[0] == "status":
            print(self.status())
        elif args[0] == "set":
            self.depthfinder_settings.command(args[1:])
        elif args[0] == "capture":
            self.nmea_packet()
            print(self.current_depth)
            print(self.lat)
            print(self.lon)  
        else:
            print(self.usage())
    
    def status(self):
        '''returns information about module'''
        self.status_callcount += 1
        self.last_bored = time.time() # status entertains us
        return("status called %(status_callcount)d times.  \n
                My target position=%(my_lat)f, %(my_lon)f \n
                Depth=%(my_depth)%f, Temp=%(my_temp)%f \n 
                " %
               {"status_callcount": self.status_callcount,
                "my_lat": self.lat,
                "my_lon": self.lon,
                "my_depth": self.current_depth,
                "my_temp": self.current_temp,
               })

    def idle_task(self):
        '''
        called rapidly by mavproxy
        
        i don't think there's really a particular "idle state", pretty sure this is just called every time through the main loop... or something
        '''
        if (self.landed == True) or (self.depthfinder_settings.debug == True):
            self.nmea_packet()
        else:
            return
        
    def nmea_packet(self):
        charBegin = '$'
        charCheck = '*'
        charEnd = '\\'

        try:
            if self.ser.isOpen() == False:
                self.ser.open()
        except serial.SerialException as e:
            print("Error opening serial port: " + str(e))
            return

        raw = self.ser.readline()

        #check if in correct format
        if raw[-2:] != b"\x0d\x0a":
            print("Read Error")
            return
        rawS = str(raw)
        result = rawS[rawS.find(charBegin)+1 : rawS.find(charCheck)]
        checkSum = rawS[rawS.find(charCheck)+1 : rawS.find(charEnd)]
        #confirm checksum
        if bool(checkSum) != bool(result):
            print("Checksum doesn't match")
            return
        else:    
            nmeaList = result.split(",")
            if 'SDDPT' in nmeaList:
                        self.current_depth = float(nmeaList[1])
                        if (self.depthfinder_settings.verbose) :
                            print("Depth: "+nmeaList[1])
            if 'YXMTW' in nmeaList:
                        self.current_temp = float(nmeaList[1])
                        if (self.depthfinder_settings.verbose) :
                            print("Temperature: "+nmeaList[1]+"C")

            #write to file everytime a NMEA line is read
            self.file = open(self.logFile, "a")
            self.file.write(self.lat+"\t"+self.lon+"\t"+self.current_depth+"\t\t"+self.current_temp+"\n")
            self.file.close()
        return    

    def mavlink_packet(self, m):
        '''
        handle mavlink packets
        
        The m object is a mavlink message object. You can check its type via the get_type() method.
        To figure out the fields available in the message, see https://mavlink.io/en/messages/common.html.
        They should just be accessible as attributes of the m object, as you can see below. Python moment.
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
