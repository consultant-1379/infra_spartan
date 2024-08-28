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
# Name      : mws_services.py
# Purpose   : The script wil perform mws health check automatically
# ********************************************************************

import os.path
import subprocess
import os
import signal
import sys
import time
import logging

a1 = subprocess.check_output("hostname").split()
b1 = 'mws_health_report-' + str(a1[0])
if os.path.exists('/var/tmp/'):
    path1 = os.path.join('/var/tmp/', b1)
    if not os.path.exists(path1):
        os.mkdir(path1)
else:
    print("/var/tmp directory does not exist!")
    sys.exit(1)
"""
Global variables used within the script
"""
LOG_DIR1 = path1 + '/'
LOG_NAME1 = os.path.basename(__file__).replace('.py', '_') + time.strftime("%m_%d_%Y-%H_%M_%S") + '.log'
var1 = LOG_DIR1 + LOG_NAME1
MSG1 = "Service is not running. Please take necessary actions!"
MSG2 = "Service is running fine."
MSG3 = "Service is not running. No action required!"
DATA1 = '/var/tmp/mwshealth'
DATA2 = '/var/tmp/mws_health'

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
        self.logging_config()
        self.colors1 = {'RED': '\033[91m', 'END': '\033[00m',
                        'GREEN': '\033[92m', 'YELLOW': '\033[93m'}
        self.precheck1 = "Verify_MWS_Services"
        self.logs1 = LOG_DIR1 + LOG_NAME1
        self.c = ""

    def logging_config(self):
        """
        Creating a custom logger for logs
        It creates 2 different log handler
        StreamHandler which handles Ilogs of
        ERROR level or above and FileHandler
        which handles logs of WARNING level or
        above
        Param: None
        Return: None
        """
        if not os.path.exists(LOG_DIR1):
            os.makedirs(LOG_DIR1)
        s_handler1 = logging.StreamHandler()
        f_handler1 = logging.FileHandler(LOG_DIR1 + LOG_NAME1)
        s_handler1.setLevel(logging.ERROR)
        f_handler1.setLevel(logging.WARNING)
        s_format1 = logging.Formatter('%(message)s')
        f_format1 = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H-%M-%S')
        self.logging_config1(s_format1, f_format1, s_handler1, f_handler1)

    def logging_config1(self, s_format1, f_format1, s_handler1, f_handler1):
        """
        Continuation of the custom logger
        function
        Param:
              s_format -> StreamHandler object
              f_format -> FileHandler object
        Return -> None
        """
        s_handler1.setFormatter(s_format1)
        f_handler1.setFormatter(f_format1)
        self.logger.addHandler(s_handler1)
        self.logger.addHandler(f_handler1)

    def log_file_scrn1(self, msgs, log_dec=0):
        """
        Logging into file and screen
        based on the value of log_dec
        variable if value of
        log_dec is 0 it will print
        simultaneuously to screen
        and log file for log_dec value
        as 1 it will print to logfile
        directly.
        Param:
              msgs -> the actual message
              log_dec -> integer
        Return: None
        """
        if log_dec == 0:
            self.logger.error(msgs)
        else:
            self.logger.warning(msgs)

    def print_logging_details(self):
        """
        Print Logging Details with
        log file for exit, completion
        and start of the script
        Param: None
        Return: None
        """
        hash_prints = '########################################################################'
        self.exit_codes1(2, hash_prints)
        self.exit_codes1(4, "Please find the script execution logs  ---> " + \
                         LOG_DIR1 + LOG_NAME1)
        self.exit_codes1(2, hash_prints)

    def exit_codes1(self, code, msgs):
        """
        Script Exit funtion
        Based on the code will print the
        message in different colors
        param:
               code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        """
        if code == 1:
            self.log_file_scrn1("[ERROR] " + ": " + msgs)
            self.print_logging_details()
            sys.exit(code)
        elif code == 2:
            print(self.colors1['YELLOW'] + msgs + self.colors1['END'])
        elif code == 3:
            self.log_file_scrn1("[ERROR] " + ":" + msgs)
        elif code == 4:
            print("[INFO] " + ":" + msgs)
        else:
            self.log_file_scrn1("[INFO] " + ":" + msgs)

    def summary1(self):
        """
        This function will
        save all the information
        to summary file.
        """
        with open(var1) as f:
            for phrase in f:
                if "UNHEALTHY" in phrase:
                    phrase = phrase.rstrip('\n').split(':')
                    headers = [self.precheck1, "", phrase[2], "", phrase[1], "", self.logs1, '\n']
                    with open(DATA1, 'a') as da:
                        da.writelines(headers)
                elif "HEALTHY" in phrase:
                    phrase = phrase.rstrip('\n').split(':')
                    headers1 = [self.precheck1, "", phrase[2], "", phrase[1], "", self.logs1, '\n']
                    with open(DATA2, 'a') as db:
                        db.writelines(headers1)

    def network_service(self):
        """
        This function will
        verify the status of
        network service as
        active or inactive.
        """
        try:
            print("\n")
            k, j = 0, 0
            while k == 0:
                cmd2 = os.system("systemctl is-active --quiet network.service")

                if cmd2 == 0:
                    print(" ")
                    k = k + 1
                    out2 = "systemctl status network.service".split(' ')
                    msgs = subprocess.check_output(out2)
                    self.all_services()
                else:
                    if j == 3:
                        print(" ")
                        out3 = "systemctl status network.service".split(' ')
                        msgs = subprocess.check_output(out3)
                        k=k+1
                        self.all_services()
                    else:
                        self.please_wait(30)
                        j=j+1
        except Exception as err:
            self.log_file_scrn1(err.output)

    @staticmethod
    def please_wait(a):
        """
        this function will
        print please wait
        when the services will
        be on iteration
        """
        for i in range(1, a):
            time.sleep(1)
            sys.stdout.write("\rPlease wait%s" % ('.' * i))
            sys.stdout.flush()

    def all_services(self):
        """
        this function
        will call another
        function check_iter()
        """
        self.c = 0
        while self.c <= 3:
            self.check_iter()

    def check_iter(self):
        """
        this function will
        iterate from service
        to service and
        provide the status.
        """
        cm1 = "systemctl status auditd.service"
        cm2 = "systemctl status rpc-statd.service"
        cm3 = "systemctl status rpcbind.service"
        cm4 = "systemctl status autofs.service"
        cm5 = "systemctl status dhcpd.service"
        cm7 = "systemctl status lvm2-lvmetad.service"
        cm8 = "systemctl status nfs-mountd.service"
        cm9 = "systemctl status xinetd.service"
        cm10 = "systemctl status sshd.service"
        cm11 = "systemctl status serial-getty@ttyS0.service"
        cm12 = "systemctl status tftp.service"
        cm13 = "systemctl status nfs-idmap.service"

        o2 = os.system("systemctl is-active --quiet auditd.service")
        o3 = os.system("systemctl is-active --quiet rpc-statd.service")
        o4 = os.system("systemctl is-active --quiet rpcbind.service")
        o5 = os.system("systemctl is-active --quiet autofs.service")
        o6 = os.system("systemctl is-active --quiet dhcpd.service")
        o8 = os.system("systemctl is-active --quiet lvm2-lvmetad.service")
        o9 = os.system("systemctl is-active --quiet nfs-mountd.service")
        o10 = os.system("systemctl is-active --quiet xinetd.service")
        o11 = os.system("systemctl is-active --quiet sshd.service")
        o12 = os.system("systemctl is-active --quiet serial-getty@ttyS0.service")
        o13 = os.system("systemctl is-active --quiet tftp.service")
        o14 = self.nfs_idmap()
        if ((o2 == 0) and (o3 == 0) and (o4 == 0) and (o5 == 0) and (o6 == 0) and
            (o8 == 0) and (o9 == 0) and (o10 == 0) and (o11 == 0) and
            (o12 == 0) and (o13 != 0) and (o14 == 0)) or (self.c == 3):
            print(" ")
            self.active(cm1, o2)
            self.active(cm2, o3)
            self.active(cm3, o4)
            self.active(cm4, o5)
            self.active(cm5, o6)
            self.active(cm7, o8)
            self.active(cm8, o9)
            self.active(cm9, o10)
            self.active(cm10, o11)
            self.active(cm11, o12)
            self.active(cm12, o13)
            self.active(cm13, o14)
            self.c = 4
        else:
            self.c = self.c + 1
            self.please_wait(12)

    def active(self,cm,o):
        """
        this function will
        check for active
        and inactive status of
        the services.
        """
        temp = "systemctl status "
        try:
            if o == 0:
                if "tftp" in cm:
                    cmd = cm.split(" ")
                    msgs = subprocess.check_output(cmd)
                    cm2 = cm.split(temp)
                    self.log_file_scrn1(":  {} is running  :  UNHEALTHY".format(cm2[1]))
                    self.log_file_scrn1("-" * 65)
                    self.log_file_scrn1(msgs)
                    self.log_file_scrn1("-" * 65)
                    self.exit_codes1(0, MSG2)
                    self.log_file_scrn1("-" * 65)
                else:
                    cmd = cm.split(" ")
                    msgs = subprocess.check_output(cmd)
                    cm2 = cm.split(temp)
                    self.log_file_scrn1(":  {} is running  :  HEALTHY".format(cm2[1]))
                    self.log_file_scrn1("-" * 65)
                    self.log_file_scrn1(msgs)
                    self.log_file_scrn1("-" * 65)
                    self.exit_codes1(0, MSG2)
                    self.log_file_scrn1("-" * 65)
            else:
                if "tftp" in cm:
                    cmd = cm.split(" ")
                    cm2 = cm.split(temp)
                    self.log_file_scrn1(":  {} is not running  :  HEALTHY".format(cm2[1]))
                    msgs = subprocess.check_output(cmd)
                    self.log_file_scrn1(msgs)
                else:
                    cmd = cm.split(" ")
                    cm2 = cm.split(temp)
                    self.log_file_scrn1(":  {} is not running  :  UNHEALTHY".format(cm2[1]))
                    msgs = subprocess.check_output(cmd)
                    self.log_file_scrn1(msgs)

        except Exception as err:
            self.log_file_scrn1("-" * 65)
            self.log_file_scrn1(err.output)
            self.log_file_scrn1("-" * 65)
            self.exit_codes1(3, MSG1)
            self.log_file_scrn1("-" * 65)

    @staticmethod
    def nfs_idmap():
        """
        This function will
        fetch  status of
        nfs-idmap service.
        :return:
        """
        try:
            out = "systemctl status nfs-idmap.service".split(' ')
            msgs = subprocess.check_output(out)
            if "Active: active (running)" in msgs:
                return 0
            else:
                return 1
        except Exception:
            return 1

def handler1(signum, frame):
    """
    restore the original signal
    handler in raw_input when
    CTRL+C is pressed will
    be handled by below
    """
    print("ctrl+c not allowed at this moment")


def main():
    """
    The main function to wrap all functions
    Param: None
    return: None
    """
    mwshealth = MwsHealthCheck()
    signal.signal(signal.SIGINT, handler1)
    mwshealth.log_file_scrn1("-" * 75)
    mwshealth.log_file_scrn1("*******Starting the execution of MWS Health Check Script******")
    mwshealth.log_file_scrn1("-" * 75)
    mwshealth.log_file_scrn1("\n")
    mwshealth.network_service()
    mwshealth.summary1()

if __name__ == "__main__":
    main()

