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
# Name      : mws_verify_hw.py
# Purpose   : The script wil perform mws health check automatically
# ********************************************************************

import os.path
import subprocess
import os
import glob
import signal
import sys
import time
import logging

a13 = subprocess.check_output("hostname").split()
b13 = 'mws_health_report-'+ str(a13[0])
if os.path.exists('/var/tmp/'):
    path13 = os.path.join('/var/tmp/', b13)
    if not os.path.exists(path13):
        os.mkdir(path13)
else:
    print("/var/tmp directory does not exist!")
    sys.exit(1)
"""
Global variables used within the script
"""
LOG_DIR13 = path13 + '/'
LOG_NAME13 = os.path.basename(__file__).replace('.py', '_') + time.strftime("%m_%d_%Y-%H_%M_%S") + '.log'
dir_name13 = LOG_DIR13 + LOG_NAME13
MSG13 = "Issue in fetching global shares details!"
DATA13 = '/var/tmp/mwshealth'
DATAS13 = '/var/tmp/mws_health'

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
        self.logging_config13()
        self.colors13 = {'RED': '\033[91m', 'END': '\033[00m',
                       'GREEN': '\033[92m', 'YELLOW': '\033[93m'}
        self.precheck13 = "Check_NFS_details"
        self.logs13 = LOG_DIR13 + LOG_NAME13
        self.REMARKS = ' '
    def logging_config13(self):
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
        if not os.path.exists(LOG_DIR13):
            os.makedirs(LOG_DIR13)
        s_handler13 = logging.StreamHandler()
        f_handler13 = logging.FileHandler(LOG_DIR13 + LOG_NAME13)
        s_handler13.setLevel(logging.ERROR)
        f_handler13.setLevel(logging.WARNING)
        s_format13 = logging.Formatter('%(message)s')
        f_format13 = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H-%M-%S')
        self.logging_config13n(s_format13, f_format13, s_handler13, f_handler13)

    def logging_config13n(self, s_format13, f_format13, s_handler13, f_handler13):
        """
        Continuation of the custom logger
        function
        Param:
              s_format13 -> StreamHandler object
              f_format13 -> FileHandler object
        Return -> None
        """
        s_handler13.setFormatter(s_format13)
        f_handler13.setFormatter(f_format13)
        self.logger.addHandler(s_handler13)
        self.logger.addHandler(f_handler13)

    def log_file_scrn13(self, msgs, log_dec=0):
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

    def print_logging_details13(self):
        """
        Print Logging Details with log file for exit,
        completion and start of the script
        Param: None
        Return: None
        """
        hash_prints = '########################################################################'
        self.exit_codes13(2, hash_prints)
        self.exit_codes13(4, "Please find the script execution logs  ---> " + \
                           LOG_DIR13 + LOG_NAME13 )
        self.exit_codes13(2, hash_prints)

    def exit_codes13(self, code, msgs):
        """
        Script Exit funtion
        Based on the code will print the message in different colors
        param:
               code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        """
        if code == 1:
            self.log_file_scrn13("[ERROR] " + ": " + msgs)
            self.print_logging_details13()
            sys.exit(code)
	elif code == 2:
            print(self.colors13['YELLOW'] + msgs + self.colors13['END'])
        elif code == 3:
	    self.log_file_scrn13("[ERROR] " + ":" + msgs)
        elif code == 4:
            print("[INFO] " + ":" + msgs)
        else:
            self.log_file_scrn13("[INFO] " + ":" + "\n\n" +  msgs)


    def summary13(self):
        """
        This function will save the
        information to summary file.
        """
        with open(dir_name13) as f:
            for phrase in f:
                if "WARNING" in phrase:
                    phrase = phrase.rstrip('\n').split(':')
                    headers = [self.precheck13, "", phrase[2], "",phrase[1], "", self.logs13, '\n']
                    with open(DATA13, 'a') as da:
                        da.writelines(headers)
	        elif "HEALTHY" in phrase:
                    phrase = phrase.rstrip('\n').split(':')
                    headers1 = [self.precheck13, "", phrase[2], "",phrase[1], "", self.logs13, '\n']
                    with open(DATAS13, 'a') as db:
                        db.writelines(headers1)

    def mws_nfs_detail(self):
        """
        This function will verify
        NFS details.
        Return: None
        """
        try:
            self.log_file_scrn13("-" * 65)
            self.log_file_scrn13("*****Verifying NFS Details*****")
            self.log_file_scrn13("-" * 65)
            print("\n")
            out1 = "df -h /JUMP".split(' ')
            msgs = subprocess.check_output(out1)
            self.exit_codes13(0, msgs)
            self.log_file_scrn13("-" * 65)
            self.log_file_scrn13("*****Export file status*****")
            self.log_file_scrn13("-" * 65)
            print("\n")
            out2 = "/usr/sbin/exportfs -v".split(' ')
            msgs1 = subprocess.check_output(out2)
            self.exit_codes13(0, msgs1)
            infile = r"/etc/exports"
            with open(infile) as f:
                val = f.read()
                if '*' not in val:
                    self.log_file_scrn13(":  No Global shares are present on /etc/exports  :  HEALTHY")
                else:
                    self.mws_nfs()
        except Exception as err:
            self.log_file_scrn13("-" * 65)
            self.log_file_scrn13(err)
            self.log_file_scrn13("-" * 65)
            self.exit_codes13(3, MSG13)

    def mws_nfs(self):
        """
        This function will verify
        NFS Warning details.
        Return: None
        """
        infile = r"/etc/exports"
        with open(infile) as f:
            for phrase in f:
                if "*" in phrase:
                    out3 = ((phrase).rstrip('\n'))
                    self.log_file_scrn13(":  Global shares are present on /etc/exports")
                    self.log_file_scrn13(out3)
	    self.log_file_scrn13(":  Global shares are present on /etc/exports  :  WARNING")

def handler13(signum, frame):
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
    signal.signal(signal.SIGINT, handler13)
    mwshealth.log_file_scrn13("-" * 75)
    mwshealth.log_file_scrn13("*******Starting the execution of MWS Health Check Script******")
    mwshealth.log_file_scrn13("-" * 75)
    mwshealth.log_file_scrn13("\n")
    mwshealth.mws_nfs_detail()
    mwshealth.summary13()

if __name__ == "__main__":
    main()

