#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
script for NAS_RHEL_CHECK
"""
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
# Name      : nas_rhel_check11_f.py
# Purpose   : The script wil perform VA validation for ENIQ upgrade
# Exit Values:
#  0   : SUCCESS
#  143::FAILURE::RHEL OS upgrade required
#  146::FAILURE::Server not reachable or invalid credentials
#  148::FAILURE::Command execution failed
#  64::NO RUN::Not applicable for SIMPLEX-RACK and MULTIPLEX-RACK Server
# ********************************************************************
"""
Modules used in the script
"""
import signal
import sys
import logging
import os
import socket
import subprocess
"""
Global variables used within the script
"""
FILE_PATH = "/eniq/local_logs/precheck_logs"
LOG_JJ = '/eniq/local_logs/precheck_logs/'
LOG_NAME = os.path.basename(__file__).replace('.py', '') + '.log'
rhel1="7.9"
"""
Class Started
"""
class precheckrhel(object):
    """
    This class will do precheck of NAS RHEL OS
    """
    def __init__(self):
        """
        Function to initialise the
        class object variables
        param: None
        return: None
        """
        if not os.path.exists(LOG_JJ):
            print("Error:log_dir not present")
            sys.exit(0)
        self.logger = logging.getLogger()
        self.logging_configs()
        self.c=""
        self.b2=""
        self.out=""
    def check_hardware_for_rhel(self):
        """
        This function will check hardware type
        """
        try:
            c1 = ['dmidecode','-t','chassis','|','grep -w "Type"']
            c2 = subprocess.check_output(c1)
            if 'Blade' in c2:
                self.log_file_rhel("Current deployment type is Blade", 1)
                return 0
            else:
                self.log_file_rhel("Current deployment type is simplex or multiplex Rack", 1)
                return 64
        except Exception:
            self.log_file_rhel("Command execution issue for NAS RHEL check",1)
            return 148
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
        if not os.path.exists(LOG_JJ):
            print("Error:log_dir not present")
            sys.exit(0)
        s_handlers3 = logging.StreamHandler()
        f_handlers4 = logging.FileHandler(LOG_JJ + LOG_NAME)
        s_handlers3.setLevel(logging.ERROR)
        f_handlers4.setLevel(logging.WARNING)
        s_formats = logging.Formatter('%(message)s')
        f_formats = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_handlers3.setFormatter(s_formats)
        f_handlers4.setFormatter(f_formats)
        self.logger.addHandler(s_handlers3)
        self.logger.addHandler(f_handlers4)

    def log_file_rhel(self, msg3, log_dec=0):
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
        u = log_dec
        if u == 0:
            self.logger.error(msg3)
        else:
            self.logger.warning(msg3)

    def rhel_version(self):
        """
        This function will check the existing hardware type(Gen8,9,10 or Gen10+)
        """
        code=self.check_hardware_for_rhel()
        if code!=0:
            return code
        try:
            self.log_file_rhel("Collecting details for NAS RHEL OS", 1)
            out3 = ["su", "-c", "ssh -o StrictHostKeyChecking=no -n support@nasconsole 'ls'", "storadm"]
            b=out3[2].split()
            b1=b[4]
            self.b2=b1.replace(" 'ls'","")
            b3 = self.b2.replace("support@", "")
            try:
                if socket.gethostbyaddr(b3):
                    g="ssh -o StrictHostKeyChecking=no -n support@nasconsole 'cat /etc/redhat-release'"
                    self.out = ["su", "-c",g, "storadm"]
                    self.c=self.out[2].split()
                    out9=self.nas_rhel_version()
                    return out9
            except socket.herror:
                self.log_file_rhel("Server not reachable", 1)
                return 146
        except Exception:
            self.log_file_rhel("Command execution issue for NAS RHEL check",1)
            return 148
    def nas_rhel_version(self):
        """
        This function will check the existing hardware type(Gen8,9,10 or Gen10+)
        """
        if self.b2 in self.c:
            try:
                rhel = subprocess.check_output(self.out).split(' ')
            except Exception:
                self.log_file_rhel("Command execution issue for NAS RHEL check", 1)
                return 148
            rel = ''
            for i in range(0, len(rhel)):
                if 'release' == rhel[i]:
                    rel = rel + rhel[i + 1]
            str1 = "Existing rhel_version is {}".format(rel)
            str2 = "Targeted rhel_version is {}".format(rhel1)
            if rhel1 in rhel:
                self.log_file_rhel(str1, 1)
                self.log_file_rhel(str2, 1)
                self.log_file_rhel("Existing RHEL Version is up to date", 1)
                d = 0
            else:
                self.log_file_rhel(str1, 1)
                self.log_file_rhel(str2, 1)
                self.log_file_rhel("Existing RHEL version needs to be upgraded to the target version", 1)
                d = 143
            self.log_file_rhel("Successfully completed precheck for NAS RHEL OS", 1)
            return d
        else:
            g1="Passwordless connection is not working. Please re-establish passwordless connection"
            self.log_file_rhel(g1, 1)
            return 146
def exit_gracefully_rhel(signum, frame):
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
    if os.path.exists(LOG_JJ + LOG_NAME):
        os.remove(LOG_JJ + LOG_NAME)
    signal.signal(signal.SIGINT, exit_gracefully_rhel)
    pre3 = precheckrhel()
    pre3.log_file_rhel("Starting precheck for NAS RHEL OS", 1)
    l3 = pre3.rhel_version()
    sys.exit(l3)
if __name__ == "__main__":
    main()

