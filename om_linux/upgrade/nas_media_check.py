#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
script for NAS_MEDIA_CHECK
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
# Name      : nas_media_check1_f.py
# Purpose   : The script wil perform VA validation for ENIQ upgrade
# Exit Values:
#  0   : SUCCESS
#  142::FAILURE::NAS media upgrade required
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
LOG_MM = '/eniq/local_logs/precheck_logs/'
LOG_NAME = os.path.basename(__file__).replace('.py', '') + '.log'
nas1 = "7.4.2.400"
"""
Class Started
"""
class precheckmedia(object):
    """
    This class will do precheck of NAS media
    """
    def __init__(self):
        """
        Function to initialise the
        class object variables
        param: None
        return: None
        """
        if not os.path.exists(LOG_MM):
            print("Error:log_dir not present")
            sys.exit(0)
        self.logger = logging.getLogger()
        self.logging_configs()
        self.n2=""
        self.n4=""
        self.out4=""
    def check_hardware_media(self):
        """
        This function will check hardware type
        """
        try:
            k = ['dmidecode','-t','chassis','|','grep -w "Type"']
            k1 = subprocess.check_output(k)
            if 'Blade' in k1:
                self.log_file("Current deployment type is Blade", 1)
                return 0
            else:
                self.log_file("Current deployment type is simplex or multiplex Rack", 1)
                return 64
        except Exception:
            self.log_file("Command execution issue for NAS hardware check", 1)
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
        if not os.path.exists(LOG_MM):
            print("Error:log_dir not present")
            sys.exit(0)
        s_handlers3 = logging.StreamHandler()
        f_handlers4 = logging.FileHandler(LOG_MM + LOG_NAME)
        s_handlers3.setLevel(logging.ERROR)
        f_handlers4.setLevel(logging.WARNING)
        s_formats = logging.Formatter('%(message)s')
        f_formats = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_handlers3.setFormatter(s_formats)
        f_handlers4.setFormatter(f_formats)
        self.logger.addHandler(s_handlers3)
        self.logger.addHandler(f_handlers4)

    def log_file(self, msg2, log_dec=0):
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
        v = log_dec
        if v == 0:
            self.logger.error(msg2)
        else:
            self.logger.warning(msg2)

    def nas_media(self):
        """
        This function will check the existing hardware type(Gen8,9,10 or Gen10+)
        """
        code1=self.check_hardware_media()
        if code1!=0:
            return code1
        self.log_file("Collecting details for NAS media", 1)
        out8 = ["su", "-c", "ssh -o StrictHostKeyChecking=no -n support@nasconsole 'ls'", "storadm"]
        n5 = out8[2].split()
        n1 = n5[4]
        self.n2 = n1.replace(" 'ls'", "")
        n3 = self.n2.replace("support@", "")
        try:
            if socket.gethostbyaddr(n3):
                y= "ssh -o StrictHostKeyChecking=no -n support@nasconsole 'cat /opt/VRTSnas/conf/banner'"
                self.out4 = ["su", "-c",y, "storadm"]
                self.n4=self.out4[2].split()
                out7=self.nas_media_check()
                return out7
        except socket.herror:
            self.log_file("Server not reachable", 1)
            return 146
        except Exception:
            self.log_file("Command execution issue for NAS media check",1)
            return 148
    def nas_media_check(self):
        """
        This function will check the existing hardware type(Gen8,9,10 or Gen10+)
        """
        if self.n2 in self.n4:
            try:
                nas = subprocess.check_output(self.out4)
            except Exception:
                self.log_file("Command execution issue for NAS media check", 1)
                return 148
            n = nas[187:196]
            str1 = "Existing NAS media is {}".format(n)
            str2 = "Targetted NAS media is {}".format(nas1)
            if nas1 in nas:
                self.log_file(str1, 1)
                self.log_file(str2, 1)
                self.log_file("Existing NAS media is upgraded", 1)
                f = 0
            else:
                self.log_file(str1, 1)
                self.log_file(str2, 1)
                self.log_file("Existing NAS media needs to be upgraded to the target version", 1)
                f = 142
            self.log_file("Successfully completed precheck for NAS media", 1)
            return f
        else:
            y1="Passwordless connection is not working. Please re-establish passwordless connection"
            self.log_file(y1, 1)
            return 146
def exit_gracefully_media(signum, frame):
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
    if os.path.exists(LOG_MM + LOG_NAME):
        os.remove(LOG_MM + LOG_NAME)
    signal.signal(signal.SIGINT, exit_gracefully_media)
    pre5 = precheckmedia()
    pre5.log_file("Starting precheck for NAS media", 1)
    l6 = pre5.nas_media()
    sys.exit(l6)
if __name__ == "__main__":
    main()

