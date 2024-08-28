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
# Name      : mws_cpu_utilization.py
# Purpose   : The script wil perform mws health check automatically
# ********************************************************************

import os.path
import subprocess
import os
import signal
import sys
import time
import logging

a18 = subprocess.check_output("hostname").split()
b18 = 'mws_health_report-'+ str(a18[0])
if os.path.exists('/var/tmp/'):
    path18 = os.path.join('/var/tmp/', b18)
    if not os.path.exists(path18):
        os.mkdir(path18)
else:
    print("/var/tmp directory does not exist!")
    sys.exit(1)
"""
Global variables used within the script
"""
LOG_DIR18 = path18 + '/'
LOG_NAME18 = os.path.basename(__file__).replace('.py', '_') + time.strftime("%m_%d_%Y-%H_%M_%S") + '.log'
MSG18 = "Issue with the execution of command"

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
        self.logging_config18()
        self.colors18 = {'RED': '\033[91m', 'END': '\033[00m',
                       'GREEN': '\033[92m', 'YELLOW': '\033[93m'}

    def logging_config18(self):
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
        if not os.path.exists(LOG_DIR18):
            os.makedirs(LOG_DIR18)
        s_handler18 = logging.StreamHandler()
        f_handler18 = logging.FileHandler(LOG_DIR18 + LOG_NAME18)
        s_handler18.setLevel(logging.ERROR)
        f_handler18.setLevel(logging.WARNING)
        s_format18 = logging.Formatter('%(message)s')
        f_format18 = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        self.logging_config18c(s_format18, f_format18, s_handler18, f_handler18)

    def logging_config18c(self, s_format18, f_format18, s_handler18, f_handler18):
        """
        Continuation of the custom logger
        function
        Param:
              s_format18 -> StreamHandler object
              f_format18 -> FileHandler object
        Return -> None
        """
        s_handler18.setFormatter(s_format18)
        f_handler18.setFormatter(f_format18)
        self.logger.addHandler(s_handler18)
        self.logger.addHandler(f_handler18)

    def log_file_scrn18(self, msgs, log_dec=0):
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

    def print_logging_details18(self):
        """
        Print Logging Details with log file for exit,
        completion and start of the script
        Param: None
        Return: None
        """
        hash_prints = '########################################################################'
        self.log_file_scrn18(hash_prints)
        self.log_file_scrn18("Please find the script execution logs  ---> " + \
                           LOG_DIR18 + LOG_NAME18 )
        self.log_file_scrn18(hash_prints)

    def exit_codes18(self, code, msgs):
        """
        Script Exit funtion
        Based on the code will print the message in different colors
        param:
               code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        """
        if code == 1:
            self.log_file_scrn18("[ERROR] " + ": " + msgs)
            self.print_logging_details18()
            sys.exit(code)
        elif code == 3:
            self.log_file_scrn18("[ERROR] " + ":" + "\n" + msgs)
            self.print_logging_details18()
        elif code == 2:
            self.log_file_scrn18("[WARN] " + ":" + msgs)
        else:
            self.log_file_scrn18("[INFO] " + ":" + "\n\n" + msgs)

mwshealth = MwsHealthCheck()

def cpu_utilization():
    """
    Function to check top 5  CPU utilization details.
    Return: None
    """
    try:
        mwshealth.log_file_scrn18("-" * 65)
        mwshealth.log_file_scrn18("*****Checking CPU utilization*****")
        mwshealth.log_file_scrn18("-" * 65)
        print("\n")
        cu = "ps -eo pcpu,pid,ppid,user,stat,args --sort=-pcpu".split(' ')
        msgs = subprocess.check_output(cu).split('\n')
        for i in range (0,6):
            mwshealth.exit_codes18(0, msgs[i])
    except Exception as err:
        mwshealth.log_file_scrn18("-" * 65)
        mwshealth.exit_codes18(3, err.output)
        mwshealth.log_file_scrn18("-" * 65)
        mwshealth.log_file_scrn18("Issue in fetching the cpu utilization, Above are the actual errors")

def handler18(signum, frame):
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
    signal.signal(signal.SIGINT, handler18)
    mwshealth.log_file_scrn18("-" * 75)
    mwshealth.log_file_scrn18("*******Starting the execution of MWS Health Check Script******")
    mwshealth.log_file_scrn18("-" * 75)
    mwshealth.log_file_scrn18("\n")
    cpu_utilization()

if __name__ == "__main__":
    main()

