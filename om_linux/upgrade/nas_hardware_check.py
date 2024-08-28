#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
script for NAS_HARDWARE_CHECK
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
# Name      : nas_hardware_check.py
# Purpose   : The script wil perform VA validation for ENIQ upgrade
# Exit Values:
#  0  :: SUCCESS
#  141::FAILURE::Unsupported hardware type
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
LOG_KK = '/eniq/local_logs/precheck_logs/'
LOG_NAME = os.path.basename(__file__).replace('.py', '') + '.log'
"""
Class Started
"""
class precheckhardware(object):
    """
    This class will do precheck of NAS hardware type
    """
    def __init__(self):
        """
        Function to initialise the
        class object variables
        param: None
        return: None
        """
        if not os.path.exists(LOG_KK):
            print("Error:log_dir not present")
            sys.exit(0)
        self.logger = logging.getLogger()
        self.logging_configs()
        self.h2=""
        self.h4=""
        self.out2=""
    def check_hardware_type(self):
        """
        This function will check hardware type
        """
        try:
            t = ['dmidecode','-t','chassis','|','grep -w "Type"']
            t1 = subprocess.check_output(t)
            if 'Blade' in t1:
                self.log_file_hardware("Current deployment type is Blade", 1)
                return 0
            else:
                self.log_file_hardware("Current deployment type is simplex or multiplex Rack", 1)
                return 64
        except Exception:
            self.log_file_hardware("Command execution issue for NAS hardware check", 1)
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
        if not os.path.exists(LOG_KK):
            print("Error:log_dir not present")
            sys.exit(0)
        s_handlers3 = logging.StreamHandler()
        f_handlers4 = logging.FileHandler(LOG_KK + LOG_NAME)
        s_handlers3.setLevel(logging.ERROR)
        f_handlers4.setLevel(logging.WARNING)
        s_formats = logging.Formatter('%(message)s')
        f_formats = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_handlers3.setFormatter(s_formats)
        f_handlers4.setFormatter(f_formats)
        self.logger.addHandler(s_handlers3)
        self.logger.addHandler(f_handlers4)

    def log_file_hardware(self, msg1, log_dec=0):
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
        s = log_dec
        if s == 0:
            self.logger.error(msg1)
        else:
            self.logger.warning(msg1)

    def hardware_check(self):
        """
        This function will check the existing hardware type(Gen8,9,10 or Gen10+)
        """
        code3=self.check_hardware_type()
        if code3!=0:
            return code3
        try:
            self.log_file_hardware("Collecting details for NAS hardware type", 1)
            out1 = ["su", "-c", "ssh -o StrictHostKeyChecking=no -n support@nasconsole 'ls'", "storadm"]
            h = out1[2].split()
            h1 = h[4]
            self.h2 = h1.replace(" 'ls'", "")
            h3 = self.h2.replace("support@", "")
            try:
                if socket.gethostbyaddr(h3):
                    d="ssh -o StrictHostKeyChecking=no -n support@nasconsole 'dmidecode -t system'"
                    self.out2 = ["su", "-c",d, "storadm"]
                    self.h4 = self.out2[2].split()
                    out5=self.hardware_check_type()
                    return out5
            except socket.herror:
                self.log_file_hardware("Server not reachable", 1)
                return 146
        except Exception:
            self.log_file_hardware("Command execution issue for NAS hardware check", 1)
            return 148
    def hardware_check_type(self):
        """
        This function will check the existing hardware type(Gen8,9,10 or Gen10+)
        """
        if self.h2 in self.h4:
            try:
                hard = subprocess.check_output(self.out2)
            except Exception:
                self.log_file("Command execution issue for NAS media check", 1)
                return 148
            hard2 = hard[173:177]
            self.log_file_hardware("Existing Hardware: {}".format(hard2), 1)
            if "Gen8" in hard:
                self.log_file_hardware("Existing NAS hardware not supported.Please upgrade to supported hardware", 1)
                a = 141
            else:
                self.log_file_hardware("Existing NAS hardware is supported", 1)
                a = 0
            self.log_file_hardware("Successfully completed precheck for NAS hardware", 1)
            return a
        else:
            d1="Passwordless connection is not working. Please re-establish passwordless connection"
            self.log_file_hardware(d1, 1)
            return 146
def exit_gracefully_hardware(signum, frame):
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
    if os.path.exists(LOG_KK + LOG_NAME):
        os.remove(LOG_KK + LOG_NAME)
    signal.signal(signal.SIGINT, exit_gracefully_hardware)
    pre4 = precheckhardware()
    pre4.log_file_hardware("Starting precheck for NAS hardware", 1)
    l4= pre4.hardware_check()
    sys.exit(l4)
if __name__ == "__main__":
    main()

