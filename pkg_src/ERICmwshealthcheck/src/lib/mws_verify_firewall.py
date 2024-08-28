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
# Name      : mws_verify_firewall.py
# Purpose   : The script wil perform mws health check automatically
# ********************************************************************

import os.path
import subprocess
import os
import signal
import sys
import time
import logging

a15 = subprocess.check_output("hostname").split()
b15 = 'mws_health_report-'+ str(a15[0])
if os.path.exists('/var/tmp/'):
    path15 = os.path.join('/var/tmp/', b15)
    if not os.path.exists(path15):
        os.mkdir(path15)
else:
    print("/var/tmp directory does not exist!")
    sys.exit(1)
"""
Global variables used within the script
"""
LOG_DIR15 = path15 + '/'
LOG_NAME15 = os.path.basename(__file__).replace('.py', '_') + time.strftime("%m_%d_%Y-%H_%M_%S") + '.log'
MSG15 = "Issue with the execution of command"

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
        self.logging_config15()
        self.colors15 = {'RED': '\033[91m', 'END': '\033[00m',
                       'GREEN': '\033[92m', 'YELLOW': '\033[93m'}

    def logging_config15(self):
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
        if not os.path.exists(LOG_DIR15):
            os.makedirs(LOG_DIR15)
        s_handler15 = logging.StreamHandler()
        f_handler15 = logging.FileHandler(LOG_DIR15 + LOG_NAME15)
        s_handler15.setLevel(logging.ERROR)
        f_handler15.setLevel(logging.WARNING)
        s_format15 = logging.Formatter('%(message)s')
        f_format15 = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        self.logging_config15f(s_format15, f_format15, s_handler15, f_handler15)

    def logging_config15f(self, s_format15, f_format15, s_handler15, f_handler15):
        """
        Continuation of the custom logger
        function
        Param:
              s_format15 -> StreamHandler object
              f_format15 -> FileHandler object
        Return -> None
        """
        s_handler15.setFormatter(s_format15)
        f_handler15.setFormatter(f_format15)
        self.logger.addHandler(s_handler15)
        self.logger.addHandler(f_handler15)

    def log_file_scrn15(self, msgs, log_dec=0):
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

    def print_logging_details15(self):
        """
        Print Logging Details with log file for exit,
        completion and start of the script
        Param: None
        Return: None
        """
        hash_prints = '########################################################################'
        self.log_file_scrn15(hash_prints)
        self.log_file_scrn15("Please find the script execution logs  ---> " + \
                           LOG_DIR15 + LOG_NAME15 )
        self.log_file_scrn15(hash_prints)

    def exit_codes15(self, code, msgs):
        """
        Script Exit funtion
        Based on the code will print the message in different colors
        param:
               code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        """
        if code == 1:
            self.log_file_scrn15("[ERROR] " + ": " + msgs)
            self.print_logging_details15()
            sys.exit(code)
        elif code == 3:
            self.log_file_scrn15("[ERROR] " + ":" + "\n" + msgs)
            self.print_logging_details15()
        elif code == 2:
            self.log_file_scrn15("[WARN] " + ":" + msgs)
        else:
            self.log_file_scrn15("[INFO] " + ":" + "\n\n" + msgs)

mwshealth = MwsHealthCheck()

def verify_firewall():
    """
    Function to verify firewall status,
    open ports on firewalld
    and services enabled on firewalld
    Return: None
    """
    try:
        mwshealth.log_file_scrn15("-" * 65)
        mwshealth.log_file_scrn15("*****Verify Firewall*****")
        mwshealth.log_file_scrn15("-" * 65)
        print("\n")
        fi1 = "systemctl status firewalld".split(' ')
        msgs1 = subprocess.check_output(fi1)
        mwshealth.exit_codes15(0, msgs1)
        mwshealth.log_file_scrn15("-" * 65)
        mwshealth.log_file_scrn15("*****Ports open on firewalld*****")
        mwshealth.log_file_scrn15("-" * 65)
        fi2 = "firewall-cmd --list-ports".split(' ')
        msgs2 = subprocess.check_output(fi2)
        mwshealth.exit_codes15(0, msgs2)
        mwshealth.log_file_scrn15("-" * 65)
        mwshealth.log_file_scrn15("*****Services enabled on firewalld*****")
        mwshealth.log_file_scrn15("-" * 65)
        fi3 = "firewall-cmd --list-services".split(' ')
        msgs3 = subprocess.check_output(fi3)
        mwshealth.exit_codes15(0, msgs3)
    except Exception as err:
        mwshealth.log_file_scrn15("-" * 65)
        mwshealth.log_file_scrn15(err.output)
        mwshealth.log_file_scrn15("-" * 65)
        mwshealth.exit_codes15(3, "Firewalld service is UNHEALTHY")

def handler15(signum, frame):
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
    signal.signal(signal.SIGINT, handler15)
    mwshealth.log_file_scrn15("-" * 75)
    mwshealth.log_file_scrn15("*******Starting the execution of MWS Health Check Script******")
    mwshealth.log_file_scrn15("-" * 75)
    mwshealth.log_file_scrn15("\n")
    verify_firewall()

if __name__ == "__main__":
    main()

