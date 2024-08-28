#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for MWS Hardware check
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
# Name      : mws_hardware_check.py
# Purpose   : The script wil perform mws hardware type supported or not
# Exit Values:
#  0::SUCCESS
#141::FAILURE::Unsupported hardware type
#145::FAILURE::MWS media upgrade required
#146::FAILURE::Server not reachable or invalid credentials
#147::FAILURE::Required parameters not available
#148::FAILURE::Command execution failed
# ********************************************************************

"""
Modules used in the script
"""
import subprocess
import os
import signal
import sys
import logging
from os import path
import time
import re
import base64
import getpass
import paramiko

"""
Global variables used within the script
"""
LOG_DIREC = '/eniq/local_logs/precheck_logs/'
LOG_NAME = os.path.basename(__file__).replace('.py', '')+'.log'
STATUS = '/ericsson/config/mws_status'
MSG1 = "Upgrade_params.ini file not present on server"
MSG2 = "MWS details not available on Upgrade_params.ini"
NMI="/eniq/installation/config/upgrade_params.ini"
MSG="MWS server is not reachable or invalid credentials"
PASS_PHRASE_PATH="/eniq/sw/conf/strong_passphrase"

class autoprecheck(object):
    """
    Class to do MWS upgrade automation
    """
    def __init__(self):
        """
        Function to initialise the
        class object variables
        param: None
        return: None
        """
        self.logger = logging.getLogger()
        self.logging_configs()
        self.mws_ip=''
        self.uname=''
        self.password=''

    def logging_configs(self):
        """
        Creates the custom logger for logs
        It create 2 different log handler
        StreamHandler which generally handles logs of
        ERROR level and FileHandler
        which handles logs of WARNING level or
        create a custom logger for logs.
        ERROR --> to display error
        WARNING --> To display warning
        return -->none
        args -->none
        LOG_DIRE --> Log dir path
        """
        if not os.path.exists(LOG_DIREC):
            os.makedirs(LOG_DIREC)
        s_handle1 = logging.StreamHandler()
        f_handle1 = logging.FileHandler(LOG_DIREC+LOG_NAME)
        s_handle1.setLevel(logging.ERROR)
        f_handle1.setLevel(logging.WARNING)
        s_formats = logging.Formatter('%(message)s')
        f_formats = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_handle1.setFormatter(s_formats)
        f_handle1.setFormatter(f_formats)
        self.logger.addHandler(s_handle1)
        self.logger.addHandler(f_handle1)

    def log_file_scrn(self, mesg, log_decs=0):
        """
        Logging into file and screen based
        on the value of log_dec variable
        if value of log_dec is 0 it will
        print simultaneously to screen and log file
        for log_dec value as 1 it will
        print to logfile directly
        Param:
              msg -> the actual message
              log_dec -> integer
        Return: None
        msg --> to display message
        return -->none
        args -->none
        """
        a= log_decs
        if a == 0:
            self.logger.error(mesg)
        else:
            self.logger.warning(mesg)

    def hardware_check(self):
        """
        This function will check the existing hardware type(Gen8,9,10 or Gen10+)
        """
        error_code = 0
        try:
            code = self.temp_file_check()
            if code != 0:
                return code
            self.log_file_scrn("Collecting MWS hardware type", 1)
            cmd = "dmidecode -t system | grep -w 'Product Name' | cut -d ':' -f2 | cut -d ' ' -f4,5"
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.mws_ip, 22, self.uname, self.password, look_for_keys=False)
            stdin, stdout, stderr = ssh.exec_command(cmd)
            val = stderr.read().strip()
            if val:
                self.log_file_scrn("Command execution issue for hardware type check", 1)
                error_code = 148
            outlines = stdout.read()
            data = outlines.strip("\n")
            self.log_file_scrn("Existing Hardware: {}".format(data), 1)
            if "Gen8" in outlines:
                self.log_file_scrn("Existing hardware not supported. Please upgrade to supported hardware", 1)
                error_code = 141
            else:
                self.log_file_scrn("Existing MWS hardware is supported", 1)
                error_code = 0
        except Exception as err:
            print(err)
            self.log_file_scrn(MSG, 1)
            error_code = 146
        return error_code

    def temp_file_check(self):
        """
        This function will check for user inputs
        """
        error_code = 0
        if os.path.exists(NMI):
            code2 = self.mws_inputs()
            if code2 != 0:
                error_code = code2
            elif (self.password == "") or (self.uname == "") or (self.mws_ip == ""):
                self.log_file_scrn(MSG2, 1)
                error_code = 147
        else:
            self.log_file_scrn(MSG1, 1)
            error_code = 147
        if error_code == 0:
            try:
                subprocess.check_output(["ping", self.mws_ip, "-c", "1"])
            except Exception:
                self.log_file_scrn(MSG, 1)
                error_code = 146
        if error_code == 0:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.mws_ip, username=self.uname, password=self.password)
                client.close()
            except Exception:
                self.log_file_scrn(MSG, 1)
                error_code = 146
        return error_code

    def mws_inputs(self):
        """
        This function will collect the inputs from the ENIQ input file
        """
        try:
            with open(NMI,"r") as f:
                out=f.readlines()
                for i in range(0,len(out)):
                   if "mws_ip" in out[i]:
                       data = out[i]
                       data1 = data.split("=")
                       self.mws_ip= str(data1[1]).strip()
                   if "mws_uname" in out[i]:
                       data = out[i]
                       data2 = data.split("=")
                       self.uname = str(data2[1]).strip()
                   if "mws_pwd" in out[i]:
                       data=out[i]
                       data3=data.split("=",1)
                       self.pwd=str(data3[1]).strip("\n")
                       pssword=self.decryption()
                       self.password=pssword.strip("\n")
            return 0
        except Exception:
            self.log_file_scrn(MSG1, 1)
            return 147
    def decryption(self):
        """
        This decryption function decrypts
        the encrypted password.
        """
        if os.path.exists(PASS_PHRASE_PATH):
            file1 = open(PASS_PHRASE_PATH, "r")
            pass_phrase = file1.read().strip()
            dec = "echo \"{}\" | openssl enc -aes-256-ctr -md sha512 -a -d -salt -pass pass:{}".format(
                self.pwd, pass_phrase)
            pssword = os.popen(dec).read().strip()
            file1.close()
            return pssword
        else:
            print(PASS_PHRASE_PATH + "Path doesn't exist. Aborting Script")
            sys.exit(1)

def exit_gracefully(signum, frame):
    """
    restore the original signal handler
    in raw_input when CTRL+C is pressed,
    and our signal handler is not reentrant
    Param: None
    return: None
    """
    print("ctr+c not allowed at this moment")

def main():
    """
    The main function to wrap all functions
    Param: None
    return: None
    """
    signal.signal(signal.SIGINT, exit_gracefully)
    if os.path.exists(LOG_DIREC + LOG_NAME):
        os.remove(LOG_DIREC + LOG_NAME)
    pre=autoprecheck()
    pre.log_file_scrn("Starting MWS hardware pre check",1)
    code=pre.hardware_check()
    sys.exit(code)

if __name__ == "__main__":
    main()

