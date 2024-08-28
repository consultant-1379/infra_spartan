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
# Name      : mws_inode_usage.py
# Purpose   : The script wil perform mws health check automatically
# ********************************************************************

import os.path
import subprocess
import os
import signal
import sys
import time
import logging

a14 = subprocess.check_output("hostname").split()
b14 = 'mws_health_report-'+ str(a14[0])
if os.path.exists('/var/tmp/'):
    path14 = os.path.join('/var/tmp/', b14)
    if not os.path.exists(path14):
        os.mkdir(path14)
else:
    print("/var/tmp directory does not exist!")
    sys.exit(1)
"""
Global variables used within the script
"""
LOG_DIR14 = path14 + '/'
LOG_NAME14 = os.path.basename(__file__).replace('.py', '_') + time.strftime("%m_%d_%Y-%H_%M_%S") + '.log'
MSG14 = "Issue with the execution of command"

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
        self.logging_config14()
        self.colors14 = {'RED': '\033[91m', 'END': '\033[00m',
                       'GREEN': '\033[92m', 'YELLOW': '\033[93m'}

    def logging_config14(self):
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
        if not os.path.exists(LOG_DIR14):
            os.makedirs(LOG_DIR14)
        s_handler14 = logging.StreamHandler()
        f_handler14 = logging.FileHandler(LOG_DIR14 + LOG_NAME14)
        s_handler14.setLevel(logging.ERROR)
        f_handler14.setLevel(logging.WARNING)
        s_format14 = logging.Formatter('%(message)s')
        f_format14 = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        self.logging_config14i(s_format14, f_format14, s_handler14, f_handler14)

    def logging_config14i(self, s_format14, f_format14, s_handler14, f_handler14):
        """
        Continuation of the custom logger
        function
        Param:
              s_format14 -> StreamHandler object
              f_format14 -> FileHandler object
        Return -> None
        """
        s_handler14.setFormatter(s_format14)
        f_handler14.setFormatter(f_format14)
        self.logger.addHandler(s_handler14)
        self.logger.addHandler(f_handler14)

    def log_file_scrn14(self, msgs, log_dec=0):
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

    def print_logging_details14(self):
        """
        Print Logging Details with log file for exit,
        completion and start of the script
        Param: None
        Return: None
        """
        hash_prints = '########################################################################'
        self.log_file_scrn14(hash_prints)
        self.log_file_scrn14("Please find the script execution logs  ---> " + \
                           LOG_DIR14 + LOG_NAME14 )
        self.log_file_scrn14(hash_prints)

    def exit_codes14(self, code, msgs):
        """
        Script Exit funtion
        Based on the code will print the message in different colors
        param:
               code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        """
        if code == 1:
            self.log_file_scrn14("[ERROR] " + ": " + msgs)
            self.print_logging_details14()
            sys.exit(code)
        elif code == 3:
            self.log_file_scrn14("[ERROR] " + ":" + "\n" + msgs)
            self.print_logging_details14()
        elif code == 2:
            self.log_file_scrn14("[WARN] " + ":" + msgs)
        else:
            self.log_file_scrn14("[INFO] " + ":" + "\n\n" + msgs)

mwshealth = MwsHealthCheck()

def inode_usage():
    """
    Function to check inode usage details.
    Return: None
    """
    try:
        mwshealth.log_file_scrn14("-" * 65)
        mwshealth.log_file_scrn14("*****Checking inode usage*****")
        mwshealth.log_file_scrn14("-" * 65)
        print("\n")
        iu = "df -iPThl -x tmpfs -x iso9660 -x devtmpfs -x squashfs".split(' ')
        msgs = subprocess.check_output(iu)
        mwshealth.exit_codes14(0, msgs)
    except Exception as err:
        mwshealth.log_file_scrn14("-" * 65)
        mwshealth.log_file_scrn14(err.output)
        mwshealth.log_file_scrn14("-" * 65)
        mwshealth.exit_codes14(3, MSG14)

def handler14(signum, frame):
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
    signal.signal(signal.SIGINT, handler14)
    mwshealth.log_file_scrn14("-" * 75)
    mwshealth.log_file_scrn14("*******Starting the execution of MWS Health Check Script******")
    mwshealth.log_file_scrn14("-" * 75)
    mwshealth.log_file_scrn14("\n")
    inode_usage()

if __name__ == "__main__":
    main()

