#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to MWS upgrade check for ENIQ
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
# Name      : mws_upgrade_check.py
# Purpose   : The script wil perform mws upgrade check required or not
# Exit Values:
#  0   : SUCCESS
#  146 : FAILURE : MWS server not reachable
#  145 : FAILURE : MWS upgrade required
#  147 : FAILURE : Required parameters not available
#  148 : FAILURE : Command execution failed
# ********************************************************************
"""
Modules used in the script
"""
import subprocess,os,signal,sys,paramiko,getpass,base64,re,time,logging,base64
from os import path

"""
Global variables used within the script
"""
LOG_DIRECT = '/eniq/local_logs/precheck_logs/'
LOG_NAME = os.path.basename(__file__).replace('.py', '')+'.log'
MWS = "/ericsson/config/mws_status"
NMI = "/eniq/installation/config/upgrade_params.ini"
MSG = "MWS server is not reachable or invalid credentials"
MSG1 = "Upgrade_params.ini file not present on server"
MSG2 = "MWS details not available on Upgrade_params.ini"
PASS_PHRASE_PATH="/eniq/sw/conf/strong_passphrase"

class upgrade_check(object):
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
        self.mwsip = ''
        self.uname = ''
        self.pwd = ''
        self.logger = logging.getLogger()
        self.logging_configs()
        self.sprint=''
        self.sprint_history=''
        self.arr1=[]
        self.arr2=[]

    def logging_configs(self):
        """
        Creates the custom logger for logs'
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
        if not os.path.exists(LOG_DIRECT):
            os.makedirs(LOG_DIRECT)
        s_hand12 = logging.StreamHandler()
        f_hand12 = logging.FileHandler(LOG_DIRECT+LOG_NAME)
        s_hand12.setLevel(logging.ERROR)
        f_hand12.setLevel(logging.WARNING)
        s_formats = logging.Formatter('%(message)s')
        f_formats = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_hand12.setFormatter(s_formats)
        f_hand12.setFormatter(f_formats)
        self.logger.addHandler(s_hand12)
        self.logger.addHandler(f_hand12)

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

    def temp_file_check(self):
        """
        This function will check for temporary
        """
        error_code = 0
        if os.path.exists(NMI):
            code3 = self.mws_inputs()
            if code3 != 0:
                error_code = code3
            elif (self.pwd == "") or (self.uname == "") or (self.mwsip == "") or (self.sprint == ""):
                self.log_file_scrn(MSG2, 1)
                error_code = 147
        else:
            self.log_file_scrn(MSG1, 1)
            error_code = 147
        if error_code == 0:
            try:
                subprocess.check_output(["ping", self.mwsip, "-c", "1"])
            except Exception:
                self.log_file_scrn(MSG, 1)
                error_code = 146
        if error_code == 0:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.mwsip, username=self.uname, password=self.pwd)
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
                       self.mwsip= str(data1[1]).strip()
                   if "mws_uname" in out[i]:
                       data = out[i]
                       data2 = data.split("=")
                       self.uname = str(data2[1]).strip()
                   if "mws_pwd" in out[i]:
                       data=out[i]
                       data3 = data.split("=", 1)
                       self.str_pwd = str(data3[1]).strip("\n")
                       pssword=self.decryption_func()
                       self.pwd = pssword.strip("\n")
                   if "sprint_release" in out[i]:
                       data=out[i]
                       data4=data.split("=")
                       data5 = data4[1]
                       a=data5.split("_")
                       self.sprint=str(a[0]).strip()
            return 0
        except Exception:
            self.log_file_scrn(MSG1, 1)
            return 147
    def decryption_func(self):
        if os.path.exists(PASS_PHRASE_PATH):
            file1 = open(PASS_PHRASE_PATH, "r")
            pass_phrase = file1.read().strip()
            dec = "echo \"{}\" | openssl enc -aes-256-ctr -md sha512 -a -d -salt -pass pass:{}".format(
                self.str_pwd, pass_phrase)
            pssword = os.popen(dec).read().strip()
            file1.close()
            return pssword
        else:
            print(PASS_PHRASE_PATH + "Path doesn't exist. Aborting Script...")
            sys.exit(1)
    def history_file(self):
        """
        This function will check for if the history file exists or not
        """
        code=self.temp_file_check()
        error_code=81
        if code!= 0:
            error_code=code
        try:
            self.log_file_scrn("Collecting current sprint value",1)
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.mwsip, 22, self.uname, self.pwd)
            stdin, stdout, stderr = ssh.exec_command("cat /ericsson/config/mws_status")
            out = stdout.read().split("\n")
            va = stderr.read()
            va = va.strip()
            no = 0
            if va == True:
                self.log_file_scrn("MWS status file not present on MWS server", 1)
                error_code=147
            if no != 1:
                for i in range(0,len(out)):
                    if "PATCH_OM_SPRINT" in out[i]:
                        out1=out[i]
                        out2=out1.split("-")
                        out3=out2[1].strip()
                        self.sprint_history=out3.strip("\n")
                if self.sprint_history == "":
                    self.log_file_scrn("MWS sprint release parameter not available",1)
                    no = 1
            if no == 1:
                error_code=147
            if error_code!=81:
                return error_code
            self.log_file_scrn("Current sprint value: {}".format(self.sprint_history),1)
            self.log_file_scrn("Targeted sprint value: {}".format(self.sprint),1)
            code=self.sprint_validation()
            self.log_file_scrn("Successfully completed MWS hardware pre check", 1)
            return code
        except Exception:
            self.log_file_scrn("MWS server is not reachable or invalid credentials",1)
            return 146

    def sprint_validation(self):
        """
        This function will validate the sprint details
        """
        ans = self.version_compare(self.sprint, self.sprint_history)
        if ans > 0:
            self.log_file_scrn("Current release is less than target release. MWS upgrade required",1)
            b=145
        elif ans <= 0:
            msg1="Current release is greater than or same as target release. MWS upgrade not required"
            self.log_file_scrn(msg1,1)
            b=0
        return b

    def version_compare(self, v1, v2):
        """
        This function will compare version
        """
        self.arr1 = v1.split(".")
        self.arr2 = v2.split(".")
        self.array()
        n = len(self.arr1)
        m = len(self.arr2)
        self.arr1 = [int(i) for i in self.arr1]
        self.arr2 = [int(i) for i in self.arr2]
        if n > m:
            for i in range(m, n):
                self.arr2.append(0)
        elif m > n:
            for i in range(n, m):
                self.arr1.append(0)
        for i in range(len(self.arr1)):
            if self.arr1[i] > self.arr2[i]:
                return 1
            elif self.arr2[i] > self.arr1[i]:
                return -1
        return 0

    def array(self):
        """
        This function will remove EU from sprint details
        """
        for i in range(0, len(self.arr1)):
            if "EU" in self.arr1[i]:
                self.arr1[i]=self.arr1[i].strip("EU")
        for i in range(0, len(self.arr2)):
            if "EU" in self.arr2[i]:
                self.arr2[i] = self.arr2[i].strip("EU")
def exit_gracefully_upgrade(signum, frame):
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
    signal.signal(signal.SIGINT, exit_gracefully_upgrade)
    if os.path.exists(LOG_DIRECT + LOG_NAME):
        os.remove(LOG_DIRECT + LOG_NAME)
    p=upgrade_check()
    p.log_file_scrn("Starting MWS upgrade pre check", 1)
    code=p.history_file()
    sys.exit(code)

if __name__ == "__main__":
    main()

