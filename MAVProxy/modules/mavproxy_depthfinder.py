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
        self.lat = 0
        self.lon = 0
        self.current_depth = 0.0
        self.current_temp = 0.0
        self.num_readings = 10
        self.ser = serial.Serial()
        self.ser.baudrate = 4800
        self.ser.port = '/dev/ttyS0'
        self.home_dir = os.path.expanduser('~')
        self.armed = False
        self.landed = True
        self.mission = False
        self.logFile =  ""
        self.time = 0
        self.initflag = False

        self.depthfinder_settings = mp_settings.MPSettings(
            [ ('verbose', bool, False),
                ('debug', bool, False),
                ('target_system', int, 1),
                ('write_on_gps', bool, False),
          ])
        self.add_command('depthfinder', self.cmd_depthfinder, "depthfinder module", ['status','set (LOGSETTING)', 'capture'])

    def usage(self):
        '''show help on command line options'''
        return "Usage: depthfinder <status|set|capture|write>"
    
    def create_logfile(self):
        try:
            epoch = int(self.time) / 1000000 #convert from microseconds to seconds
            timestr = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(epoch))
            self.logFile = self.home_dir + "/surveys/" + str(timestr) + ".csv"

            self.file = open(self.logFile, "w") #change to a if we want it to be able to be turned on and off again and write to same file
            self.file.write("Latitude,Longitude,Depth(m),Tempurature(C)\n")
            self.file.close()
            print("CREATED NEW SURVEY FILE AT: " + self.logFile)
        except Exception as e:
            print("Error creating file")
            print(e)

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
        elif args[0] == "write":
            self.write_status()
            print(f"wrote current data as file entry to {self.logFile}")
        else:
            print(self.usage())
    
    def status(self):
        '''returns information about module'''
        self.status_callcount += 1
        return f"status callouts: {self.status_callcount} \n lat={self.lat} lon={self.lon} \n depth={self.current_depth} temp={self.current_temp}" 

    def idle_task(self):
        '''
        called rapidly by mavproxy
        
        i don't think there's really a particular "idle state", pretty sure this is just called every time through the main loop... or something
        '''
        self.nmea_packet()
        if (self.armed == 0) and (self.landed == 1) and (self.mission == 0): # state for when vehicle is disarmed and landed
            self.initflag = False
            self.logFile = ""
            return
        elif (self.armed == 1) and (self.landed == 0) and (self.mission == 1): # state for when vehicle is in the air as part of a mission
            if self.initflag == False:
                self.create_logfile()
                self.initflag = True
            return
        elif (self.armed == 1) and (self.landed == 1) and (self.mission == 1): # state for when vehicle is landed as part of a mission
            if self.initflag == True: # only write if log file has been created
                self.write_status()
            return

    def write_status(self):
        try:
            self.file = open(self.logFile, "a")
            self.file.write(f"{self.lat * 0.0000001},{self.lon * 0.0000001},{self.current_depth * (-1.0)},{self.current_temp}\n")
            self.file.close()
        except Exception as e:
            print(e)
        
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
        return    

    def mavlink_packet(self, m):
        '''
        handle mavlink packets
        
        The m object is a mavlink message object. You can check its type via the get_type() method.
        To figure out the fields available in the message, see https://mavlink.io/en/messages/common.html.
        They should just be accessible as attributes of the m object, as you can see below. Python moment.
        '''

        if m.get_type() == 'GLOBAL_POSITION_INT': 
            if (self.depthfinder_settings.verbose):
                print(f"got GPS message from FC at: {m.get_srcSystem()} ")
            if self.settings.target_system == 0 or self.depthfinder_settings.target_system == m.get_srcSystem():
                if (self.depthfinder_settings.verbose):
                    print(f"msg pos: {m.lat} {m.lon}")
                try:
                    self.lat = m.lat
                    self.lon = m.lon
                    if self.depthfinder_settings.write_on_gps :
                        self.write_status()
                except Exception as e:
                    print(e)
                if (self.depthfinder_settings.verbose):
                    print(f"we are at: {self.lat} {self.lon}")
        elif m.get_type() == 'EXTENDED_SYS_STATE':
            if (self.depthfinder_settings.verbose):
                print(f"landing state is: {m.landed_state}")
            if m.landed_state == 1: # see: https://mavlink.io/en/messages/common.html#MAV_LANDED_STATE
                self.landed = True
            else:
                self.landed = False
        elif m.get_type() == 'HEARTBEAT':
            self.mission = bool(m.base_mode & 0b00001100)       # see: https://mavlink.io/en/messages/common.html#MAV_MODE_FLAG
            self.armed = bool(m.base_mode & 0b10000000)

            if (self.depthfinder_settings.verbose):
                print(f"mission active: {self.mission}")
                print(f"mission state is: {m.base_mode}")
        elif m.get_type() == 'SYSTEM_TIME':
            self.time = m.time_unix_usec
            if (self.depthfinder_settings.verbose):
                print(f"time is: {self.time}")

def init(mpstate):
    '''initialise module'''
    return depthfinder(mpstate)
