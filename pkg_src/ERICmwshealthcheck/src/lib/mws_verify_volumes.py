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
# Name      : mws_verify_volumes.py
# Purpose   : The script wil perform mws health check automatically
# ********************************************************************

import os.path
import subprocess
import os
import signal
import sys
import time
import logging

a3 = subprocess.check_output("hostname").split()
b3 = 'mws_health_report-'+ str(a3[0])
if os.path.exists('/var/tmp/'):
    path3 = os.path.join('/var/tmp/', b3)
    if not os.path.exists(path3):
        os.mkdir(path3)
else:
    print("/var/tmp directory does not exist!")
    sys.exit(1)
"""
Global variables used within the script
"""
LOG_DIR3 = path3 + '/'
LOG_NAME3 = os.path.basename(__file__).replace('.py', '_') + time.strftime("%m_%d_%Y-%H_%M_%S") + '.log'
MSG3= "Issue with the execution of command"

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
        self.logging_config3()
        self.colors3 = {'RED': '\033[91m', 'END': '\033[00m',
                       'GREEN': '\033[92m', 'YELLOW': '\033[93m'}

    def logging_config3(self):
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
        if not os.path.exists(LOG_DIR3):
            os.makedirs(LOG_DIR3)
        s_handler3 = logging.StreamHandler()
        f_handler3 = logging.FileHandler(LOG_DIR3 + LOG_NAME3)
        s_handler3.setLevel(logging.ERROR)
        f_handler3.setLevel(logging.WARNING)
        s_format3 = logging.Formatter('%(message)s')
        f_format3 = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        self.logging_config3volume(s_format3, f_format3, s_handler3, f_handler3)

    def logging_config3volume(self, s_format3, f_format3, s_handler3, f_handler3):
        """
        Continuation of the custom logger
        function
        Param:
              s_format -> StreamHandler object
              f_format -> FileHandler object
        Return -> None
        """
        s_handler3.setFormatter(s_format3)
        f_handler3.setFormatter(f_format3)
        self.logger.addHandler(s_handler3)
        self.logger.addHandler(f_handler3)

    def log_file_scrn3(self, msgs, log_dec=0):
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

    def print_logging_details3(self):
        """
        Print Logging Details with log file for exit,
        completion and start of the script
        Param: None
        Return: None
        """
        hash_prints = '########################################################################'
        self.log_file_scrn3(hash_prints)
        self.log_file_scrn3("Please find the script execution logs  ---> " + \
                           LOG_DIR3 + LOG_NAME3 )
        self.log_file_scrn3(hash_prints)

    def exit_codes3(self, code, msgs):
        """
        Script Exit funtion
        Based on the code will print the message in different colors
        param:
               code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        """
        if code == 1:
            self.log_file_scrn3("[ERROR] " + ": " + msgs)
            self.print_logging_details3()
            sys.exit(code)
        elif code == 3:
            self.log_file_scrn3("[ERROR] " + ":" + "\n" + msgs)
            self.print_logging_details3()
        elif code == 2:
            self.log_file_scrn3("[WARN] " + ":" + msgs)
        else:
            self.log_file_scrn3("[INFO] " + ":" + "\n\n" + msgs)

mwshealth = MwsHealthCheck()

def verify_volumes():
    """
    This function will verify Volumes.
    Return: None
    """
    try:
        mwshealth.log_file_scrn3("-" * 65)
        mwshealth.log_file_scrn3("*****Verifying Volumes*****")
        mwshealth.log_file_scrn3("-" * 65)
        print("\n")
        vv1 = "/usr/sbin/dmsetup info".split(' ')
        msgs = subprocess.check_output(vv1)
        mwshealth.exit_codes3(0, msgs)
        print("\n\n")
        mwshealth.log_file_scrn3("-" * 65)
        mwshealth.log_file_scrn3("*****Physical Volume*****")
        mwshealth.log_file_scrn3("-" * 65)
        vv2 = "/usr/sbin/pvs"
        msgs = subprocess.check_output(vv2)
        mwshealth.exit_codes3(0, msgs)
        print("\n\n")
        mwshealth.log_file_scrn3("-" * 65)
        mwshealth.log_file_scrn3("*****Volume Groups*****")
        mwshealth.log_file_scrn3("-" * 65)
        vv3 = "/usr/sbin/vgs"
        msgs = subprocess.check_output(vv3)
        mwshealth.exit_codes3(0, msgs)
        print("\n\n")
        mwshealth.log_file_scrn3("-" * 65)
        mwshealth.log_file_scrn3("*****Logical Volume*****")
        mwshealth.log_file_scrn3("-" * 65)
        vv4 = "/usr/sbin/lvs"
        msgs = subprocess.check_output(vv4)
        mwshealth.exit_codes3(0, msgs)
    except Exception as err:
        mwshealth.log_file_scrn3("-" * 65)
        mwshealth.log_file_scrn3(err.output)
        mwshealth.log_file_scrn3("-" * 65)
        mwshealth.exit_codes3(3, MSG3)

def handler3(signum, frame):
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
    signal.signal(signal.SIGINT, handler3)
    mwshealth.log_file_scrn3("-" * 75)
    mwshealth.log_file_scrn3("*******Starting the execution of MWS Health Check Script******")
    mwshealth.log_file_scrn3("-" * 75)
    mwshealth.log_file_scrn3("\n")
    verify_volumes()

if __name__ == "__main__":
    main()

