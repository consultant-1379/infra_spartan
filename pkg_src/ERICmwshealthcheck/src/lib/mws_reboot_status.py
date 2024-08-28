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
# Name      : mws_reboot_status.py
# Purpose   : The script wil perform mws health check automatically
# ********************************************************************

import os.path
import subprocess
import os
import signal
import sys
import time
import logging

a5 = subprocess.check_output("hostname").split()
b5 = 'mws_health_report-'+ str(a5[0])
if os.path.exists('/var/tmp/'):
    path5 = os.path.join('/var/tmp/', b5)
    if not os.path.exists(path5):
        os.mkdir(path5)
else:
    print("/var/tmp directory does not exist!")
    sys.exit(1)
"""
Global variables used within the script
"""
LOG_DIR5 = path5 + '/'
LOG_NAME5 = os.path.basename(__file__).replace('.py', '_') + time.strftime("%m_%d_%Y-%H_%M_%S") + '.log'
MSG1 = "Issue with the execution of command"

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
        self.logging_config5()
        self.colors5 = {'RED': '\033[91m', 'END': '\033[00m',
                       'GREEN': '\033[92m', 'YELLOW': '\033[93m'}

    def logging_config5(self):
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
        if not os.path.exists(LOG_DIR5):
            os.makedirs(LOG_DIR5)
        s_handler5 = logging.StreamHandler()
        f_handler5 = logging.FileHandler(LOG_DIR5 + LOG_NAME5)
        s_handler5.setLevel(logging.ERROR)
        f_handler5.setLevel(logging.WARNING)
        s_format5 = logging.Formatter('%(message)s')
        f_format5 = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        self.logging_config5reboot(s_format5, f_format5, s_handler5, f_handler5)

    def logging_config5reboot(self, s_format5, f_format5, s_handler5, f_handler5):
        """
        Continuation of the custom logger
        function
        Param:
              s_format5 -> StreamHandler object
              f_format5 -> FileHandler object
        Return -> None
        """
        s_handler5.setFormatter(s_format5)
        f_handler5.setFormatter(f_format5)
        self.logger.addHandler(s_handler5)
        self.logger.addHandler(f_handler5)

    def log_file_scrn5(self, msgs, log_dec=0):
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

    def print_logging_details5(self):
        """
        Print Logging Details with log file for exit,
        completion and start of the script
        Param: None
        Return: None
        """
        hash_prints = '########################################################################'
        self.log_file_scrn5(hash_prints)
        self.log_file_scrn5("Please find the script execution logs  ---> " + \
                           LOG_DIR5 + LOG_NAME5)
        self.log_file_scrn5(hash_prints)

    def exit_codes5(self, code, msgs):
        """
        Script Exit funtion
        Based on the code will print the message in different colors
        param:
               code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        """
        if code == 1:
            self.log_file_scrn5("[ERROR] " + ": " + msgs)
            self.print_logging_details5()
            sys.exit(code)
        elif code == 3:
            self.log_file_scrn5("[ERROR] " + ":" + "\n" + msgs)
            self.print_logging_details5()
        elif code == 2:
            self.log_file_scrn5("[WARN] " + ":" + msgs)
        else:
            self.log_file_scrn5("[INFO] " + ":" + "\n\n" + msgs)

mwshealth = MwsHealthCheck()

def reboot_status():
    """
    Function to check reboot status details.
    Return: None
    """
    try:
        mwshealth.log_file_scrn5("-" * 65)
        mwshealth.log_file_scrn5("*****Checking reboot status*****")
        mwshealth.log_file_scrn5("-" * 65)
        print("\n\n")
        rs = "last -x reboot".split(' ')
        msgs = subprocess.check_output(rs)
        mwshealth.exit_codes5(0, msgs)
    except Exception as err:
        mwshealth.log_file_scrn5("-" * 65)
        mwshealth.log_file_scrn5(err.output)
        mwshealth.log_file_scrn5("-" * 65)
        mwshealth.exit_codes5(3, MSG1)

def handler5(signum, frame):
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
    signal.signal(signal.SIGINT, handler5)
    mwshealth.log_file_scrn5("-" * 75)
    mwshealth.log_file_scrn5("*******Starting the execution of MWS Health Check Script******")
    mwshealth.log_file_scrn5("-" * 75)
    mwshealth.log_file_scrn5("\n")
    reboot_status()

if __name__ == "__main__":
    main()

