#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for MWS Health Check automation
"""
# ********************************************************************
# Ericsson Radio Systems AB                                     SCRIPT
# ********************************************************************
#
#
# (c) Ericsson Radio Systems AB 2019 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property
# of Ericsson Radio Systems AB, Sweden. The programs may be used
# and/or copied only with the written permission from Ericsson Radio
# Systems AB or in accordance with the terms and conditions stipulated
# in the agreement/contract under which the program(s) have been
# supplied.
#
# ********************************************************************
# Name      : mws_disk_usage.py
# Purpose   : The script wil perform mws health check automatically
# ********************************************************************

import os.path
import subprocess
import os
import signal
import sys
import time
import logging

a2 = subprocess.check_output("hostname").split()
b2 = 'mws_health_report-'+ str(a2[0])
if os.path.exists('/var/tmp/'):
    path2 = os.path.join('/var/tmp/', b2)
    if not os.path.exists(path2):
        os.mkdir(path2)
else:
    print("/var/tmp directory does not exist!")
    sys.exit(1)
"""
Global variables used within the script
"""
LOG_DIR2 = path2 + '/'
LOG_NAME2 = os.path.basename(__file__).replace('.py', '_') + time.strftime("%m_%d_%Y-%H_%M_%S") + '.log'
var2 = LOG_DIR2 + LOG_NAME2
MSG2 = "File mountsystem usage > 95%"
DATA2 = '/var/tmp/mwshealth'
DATA3 = '/var/tmp/mws_health'

class MwsHealthCheck(object):
    """
    Class to do MWS Health
    Check automation during
    MWS configure
    """
    def __init__(self):
        """
        Init for variable initialisation
        Also creates the logger object
        used for logging the various events
        of the script execution
        colors -> to print messages in different colors in the screen
        logger -> logging object used for logs
        Param: None
        Return: None
        """
        self.logger = logging.getLogger()
        self.logging_config2()
        self.colors2 = {'RED': '\033[91m', 'END': '\033[00m',
                       'GREEN': '\033[92m', 'YELLOW': '\033[93m'}
        self.precheck2 = "Check_Disk_Usage"
        self.logs2 = LOG_DIR2 + LOG_NAME2

    def logging_config2(self):
        """
        Creating a custom logger for logs
        It creates 2 different log handler
        StreamHandler which handles logs of
        ERROR level or above and FileHandler
        which handles logs of WARNING level or
        above
        Param: None
        Return: None
        """
        if not os.path.exists(LOG_DIR2):
            os.makedirs(LOG_DIR2)
        s_handler2 = logging.StreamHandler()
        f_handler2 = logging.FileHandler(LOG_DIR2 + LOG_NAME2)
        s_handler2.setLevel(logging.ERROR)
        f_handler2.setLevel(logging.WARNING)
        s_format2 = logging.Formatter('%(message)s')
        f_format2 = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        self.logging_config2disk(s_format2, f_format2, s_handler2, f_handler2)

    def logging_config2disk(self, s_format2, f_format2, s_handler2, f_handler2):
        """
        Continuation of the custom logger
        function
        Param:
              s_format -> StreamHandler object
              f_format -> FileHandler object
        Return -> None
        """
        s_handler2.setFormatter(s_format2)
        f_handler2.setFormatter(f_format2)
        self.logger.addHandler(s_handler2)
        self.logger.addHandler(f_handler2)

    def log_file_scrn2(self, msgs, log_dec=0):
        """
        Logging into file and screen
        based on the value of log_dec variable
        if value of log_dec is 0 it will print
        simultaneuously to screen and log file
        for log_dec value as 1 it will print to
        logfile directly
        Param:
              msgs -> the actual message
              log_dec -> integer
        Return: None
        """
        if log_dec == 0:
            self.logger.error(msgs)
        else:
            self.logger.warning(msgs)

    def print_logging_details2(self):
        """
        Print Logging Details with log file for exit,
        completion and start of the script
        Param: None
        Return: None
        """
        hash_prints = '########################################################################'
        self.exit_codes2(2, hash_prints)
        self.exit_codes2(4, "Please find the script execution logs  ---> " + \
                           LOG_DIR2 + LOG_NAME2 )
        self.exit_codes2(2, hash_prints)

    def exit_codes2(self, code, msgs):
        """
        Script Exit funtion
        Based on the code will print the message in different colors
        param:
               code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        """
        if code == 1:
            self.log_file_scrn2("[ERROR] " + ": " + msgs)
            self.print_logging_details2()
            sys.exit(code)
	elif code == 2:
            print(self.colors2['YELLOW'] + msgs + self.colors2['END'])
        elif code == 3:
            self.log_file_scrn2("[ERROR] " + ":" +  msgs)
        elif code == 4:
            print("[INFO] " + ":" + msgs)
        else:
            self.log_file_scrn2("[INFO] " + ":" + "\n\n" + msgs)

    def summary2(self):
        with open(var2) as f:
            for phrase in f:
                if "UNHEALTHY" in phrase:
                    phrase = phrase.rstrip('\n').split(':')
    		    p = phrase[0].split(" ",1)[0]
		    str1 = ' usage > 95%  '
		    pa = p + str1
		    headers = [self.precheck2, "", phrase[1], "", pa, "", self.logs2, '\n']
                    with open(DATA2, 'a') as da:
                        da.writelines(headers)
                elif "HEALTHY" in phrase:
                    phrase = phrase.rstrip('\n').split(':')
		    q = phrase[0].split(" ",1)[0]
		    str2 = '  '
		    pf = q + str2
		    headers1 = [self.precheck2, "", phrase[1], "", pf, "", self.logs2, '\n']
		    with open(DATA3, 'a') as db:
                        db.writelines(headers1)

    def disk_usage(self):
        """
        Function to check disk usage on server
        Return: None
        """
        try:
            self.log_file_scrn2("-" * 65)
            self.log_file_scrn2("*****Checking Disk Usage*****")
            self.log_file_scrn2("-" * 65)
            print("\n")
            f = open("tmp.txt", "w")
            out = "df -h".split(' ')
            msgs3 = subprocess.check_output(out)
            self.exit_codes2(0, msgs3)
            du = "df -PThl -x tmpfs -x iso9660 -x devtmpfs -x squashfs".split(' ')
            subprocess.call(du, stdout=f)
            msgs1 = subprocess.check_output("awk '+$6 >=95 {print}' tmp.txt", shell=True).rstrip('\n ')
	    msgs2 = msgs1.split('\n')
            value = 0
            for i in range(0, len(msgs2)):
                val = msgs2[i].split()
                if len(val) > 1:
                    if value == 0:
                        self.log_file_scrn2("Disk Usage is greater than 95% on below Mounted  Filesystem")
                        value = 1
                    out1 = (msgs2[i] + '  :  UNHEALTHY  ')
		    self.exit_codes2(0, out1)
        except Exception as err:
            self.log_file_scrn2("-" * 65)
            self.log_file_scrn2(err.output)
            self.log_file_scrn2("-" * 65)
            self.exit_codes2(3, MSG2)

    def disk_usage_healthy(self):
        """
        Function to check disk usage on server
        Return: None
        """
        try:
            print("\n")
            msgs1 = subprocess.check_output("awk '+$6 < 95 && +$6 >= 1 {print}' tmp.txt", shell=True).rstrip('\n ')
            msgs2 = msgs1.split('\n')
            value = 0
            for i in range(0, len(msgs2)):
                val = msgs2[i].split()
                if len(val) > 1:
                    if value == 0:
                        value = 1
                    out1 = (msgs2[i] + '  :  HEALTHY  ')
                    self.exit_codes2(0, out1)
        except Exception as err:
            self.log_file_scrn2("-" * 65)
            self.log_file_scrn2(err.output)
            self.log_file_scrn2("-" * 65)
            self.exit_codes2(3, MSG2)

def handler2(signum, frame):
    """
    restore the original signal handler
    in raw_input when CTRL+C is pressed will be handled by below
    """
    print("ctrl+c not allowed at this moment")

def main():
    """
    The main function to wrap all functions
    Param: None
    return: None
    """
    mwshealth = MwsHealthCheck()
    signal.signal(signal.SIGINT, handler2)
    mwshealth.log_file_scrn2("-" * 75)
    mwshealth.log_file_scrn2("*******Starting the execution of MWS Health Check Script******")
    mwshealth.log_file_scrn2("-" * 75)
    mwshealth.log_file_scrn2("\n")
    mwshealth.disk_usage()
    mwshealth.disk_usage_healthy()
    mwshealth.summary2()

if __name__ == "__main__":
    main()

