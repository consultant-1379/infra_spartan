#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for creating additional LUNs as per target configuration
1.checking for any incomplete LUN creation as part of current operation
2.Deleting inclomplete LUNs and creating again
3.MainDB LUNs creation
4.TempDB LUNs creation
Main DB LUNS will be created as per target configuration
by taking existing configuration as referance
Temp DB LUNS will be created as per target configuration
by taking existing configuration as referance
staging can be performed to provide rerun support
"""
# ****************************************************************************
# Ericsson Radio Systems AB                                     SCRIPT
# ****************************************************************************
#
#
# (c) Ericsson Radio Systems AB 2019 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property
# of Ericsson Radio Systems AB, Sweden. The programs may be used
# and/or copied only with the written permission from Ericsson Radio
# Systems AB or in accordance with the terms and conditions stipulated
# in the agreement/contract under which the program(s) havei been
# supplied.
#
# ******************************************************************************
# Name      : LunCreation.py
# Purpose   : The script will perform additional Luns creation as per target config
# ******************************************************************************

import pexpect
import subprocess
import re
import sys
import os
import getpass
import logging
import signal
import time

CONFIG = {'E':["29", 21, 7], 'F':["43", 33, 9], 'G':["62", 50, 16]}
SYSTEM_NAME = ''
SYSTEM_NAME2 = ''
FILE_PATH = '/opt/ericsson/san/etc/'
LOG_DIRECT = '/var/ericsson/log/storage/'
LOG_NAME = os.path.basename(__file__).replace('.py', '_')+time.strftime("%m_%d_%Y-%H_%M_%S")+'.log'
TMP_FILE = '/var/tmp/input_file2.txt'
TEMP_FILE1= '/var/tmp/tp1.txt'
TEMP_FILE2= '/var/tmp/tp2.txt'
STAGE = '/var/tmp/stagelist1'
MSG2="issue with the CLI/CMD execution and above are the actual ERROR"
CMD2="uemcli -noHeader -d {} /stor/prov/luns/lun -id {} delete"
TP1="/var/tmp/tmp1"
TP2="/var/tmp/tmp2"
class LunExpansion(object):
    """
    This class will do the unity Storage Expansion
    """
    def __init__(self):
        """
        Init for variable initaliation
        colors --> to print colors
        loggig --> for capturing logs
        args --> no args
        return --> none
        """
        self.logger = logging.getLogger()
        self.logging_config()
        self.colors = {'RED' : '\033[91m', 'END' : '\033[00m',
                       'GREEN' : '\033[92m', 'YELLOW' : '\033[93m'}
        self.ip =''
        self.lunconfig_type = ''
        self.config_type=""
        self.pool_id = ''
        self.lun_id=''
        self.main_name=''
        self.temp_name=''
        self.pool_name=''
        self.temp_id=[]
        self.main_id=[]
        self.luns_id=[]
        self.luns_name=[]
        self.l_id=[]
        self.l_name=[]
    def logging_config(self):
        """
        It creates different log handler
        StreamHandler which handles logs of
        ERROR level above and FileHandler
        which handles logs of WARNING level or
        Creating the custom logger for logs
        ERROR -->  display error
        WARNING --> To display warnings
        return -->none
        arg -->none
        LOG_DIRE --> Log dir path
        Creating a custom logger for logs
        """
        if not os.path.exists(LOG_DIRECT):
            os.makedirs(LOG_DIRECT)
        s_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(LOG_DIRECT+LOG_NAME)
        s_handler.setLevel(logging.ERROR)
        f_handler.setLevel(logging.WARNING)
        s_formate = logging.Formatter('%(message)s')
        f_formate = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_handler.setFormatter(s_formate)
        f_handler.setFormatter(f_formate)
        self.logger.addHandler(s_handler)
        self.logger.addHandler(f_handler)

    def log_file_scrn(self, msg4, log_dec=0):
        """
        Logging into file and screen
        """
        if log_dec == 0:
            self.logger.error(msg4)
        else:
            self.logger.warning(msg4)

    def print_logging_details(self):
        """
        Print Logging Details with log file for exit,
        completion and start of the script
        params-->none
        return-->none
        """
        colors = self.colors
        h_print = '---------------------------------------------------------------------------'
        self.log_file_scrn(colors['YELLOW']+h_print+colors['END'])
        msg = "Please find the script execution logs  ---> "
        self.log_file_scrn(colors['YELLOW']+msg+LOG_DIRECT+LOG_NAME+colors['END'])
        self.log_file_scrn(colors['YELLOW']+h_print+colors['END'])

    def exit_codes(self, code4, msg1):
        """
        Script Exit funtion
        param: code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        msg-->print msg
        code-->to capture code for success,error,warning
        """
        colors = self.colors
        if code4 == 1:
            self.log_file_scrn(colors['RED']+"[ERROR] "+colors['END']+": "+msg1)
            self.print_logging_details()
            sys.exit(code4)
        elif code4 == 2:
            self.log_file_scrn(colors['YELLOW']+"[WARN] "+colors['END']+ ":"+msg1)
        elif code4 == 3:
            self.log_file_scrn("[" + time.strftime("%m-%d-%Y-%H:%M:%S") + "] "
                               + colors['GREEN'] + "[INFO] " + colors['END'] + ": " + msg1)
        else:
            self.log_file_scrn(colors['GREEN']+"[INFO] "+colors['END']+": "+msg1)
    def read_input1(self):
        """
        Takes the required input from the saved file to resume state in case of failure
        TMP_FILE-->tempfile
        """
        if os.path.exists(TMP_FILE):
            with open(TMP_FILE, 'r') as f:
                out = f.readlines()
            self.config_type = out[3].split('\n')[0].strip()
            self.ip = out[0].split('\n')[0].strip()
            self.lunconfig_type = out[4].split('\n')[0].strip()
            self.pool_id = out[1].split('\n')[0].strip()
            self.pool_name = out[2].split('\n')[0].strip()
            self.required_drives= out[5].split('\n')[0].strip()
            self.main_name = out[10].split('\n')[0].strip()
            self.temp_name = out[11].split('\n')[0].strip()
        else:
            self.exit_codes(1,"Issue with provided inputs. Try again!")
            sys.exit(1)
    def lun_info(self):
        """
        This function will collects all the LUNs ID's of existing configuration
        TP1-->temp1
        TP2-->temp2
        """
        self.luns_id=[]
        self.luns_name=[]
        with open (TP1,'w') as f:
            """
            No action Required
            """
            pass
        with open (TP2,'w') as f:
            """
            No action Required
            """
            pass
        try:
            cmd1="uemcli -d {} -noHeader /stor/prov/luns/lun show -filter"
            cmd=cmd1.format(self.ip).split(' ')
            cmd.append("ID,Name,Storage pool ID")
            out = subprocess.check_output(cmd).split()
            for i in range(0,len(out)):
                if out[i]==self.pool_id:
                    self.luns_id.append(out[i-8])
                    self.luns_name.append(out[i-5])
            for i in range(0,len(self.luns_id)):
                with open (TP1,'a') as f:
                    f.write(str(self.luns_id[i]))
                    f.write("\n")
                with open (TP2,'a') as f:
                    f.write(str(self.luns_name[i]))
                    f.write("\n")
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG2)
    def lun_cleanup(self):
        """
        This function will collects all the LUNs ID's of existing configuration
        """
        self.l_id=[]
        self.l_name=[]
        self.luns_id=[]
        self.luns_name=[]
        try:
            with open (TP1,'r') as f:
                out=f.readlines()
            with open (TP2,'r') as f:
                out1=f.readlines()
            for i in range(0,len(out)):
                data1=out[i].split('\n')[0].strip()
                data2=out1[i].split('\n')[0].strip()
                self.luns_id.append(data1)
                self.luns_name.append(data2)
            cmd1="uemcli -d {} -noHeader /stor/prov/luns/lun show -filter"
            cmd=cmd1.format(self.ip).split(' ')
            cmd.append("ID,Name,Storage pool ID")
            out = subprocess.check_output(cmd).split()
            for i in range(0,len(out)):
                if out[i]==self.pool_id:
                    self.l_id.append(out[i-8])
                    self.l_name.append(out[i-5])
            if len(self.l_name)> len(self.luns_name):
                print("Found some newly added LUNs as part of current request. Cleaning up.")
                for i in range(0,len(self.l_name)):
                    if self.l_name[i] not in self.luns_name:
                        cmd2 = CMD2.format(self.ip, self.l_id[i]).split(' ')
                        subprocess.check_output(cmd2)
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG2)
    def add_main(self):
        """
        This function creates MainDB depending on selected configuration
        maindb name->>MainDB with number
        """
        try:
            print("")
            self.exit_codes(0,"Started MainDB LUNs creation...")
            sp = ["spa", "spb"]
            maindb = []
            no = int(CONFIG[self.config_type][1])
            j=no+1
            num = int(CONFIG[self.lunconfig_type][1])
            with open(TEMP_FILE1, 'w'):
                '''
                No action required
                '''
                pass
            for i in range(no+1, num+1):
                name = self.main_name + str(i)
                str1="uemcli -noHeader -d {} /stor/prov/luns/lun create"
                str2=" -name {} -type primary -thin yes -pool {} -size {} -spOwner {}"
                cmd1=str1+str2
                cmd=cmd1.format(self.ip, name, self.pool_id, '1.2T', sp[j%2]).split(' ')
                lun = subprocess.check_output(cmd)
                j = j + 1
                lun_id = re.findall(r'sv_[0-9]+', lun)
                self.main_id.append(lun_id)
                with open(TEMP_FILE1, 'a') as f:
                    f.write(name)
                    f.write("\n")
                    f.write(lun_id[0])
                    f.write("\n")
                l = [name, lun_id[0]]
                maindb.append(l)
                msg = 'Created %s: %s'%(name, lun_id[0])
                self.log_file_scrn(msg, 1)
                percent = ((int(i)/num)*100)
                sys.stdout.write('\r{} percent completed'.format(int(percent)))
                sys.stdout.flush()
            if len(maindb) != (num-no):
                return 1
            code=self.add_main1()
            if code ==1:
                return 1
            else:
                return 0
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG2)

    def add_main1(self):
        """
        This function will collect main Db information post adding luns as per targeted configuration
        l_id --> lun ids
        l_name --> lun name
        l_size --> lun size
        """
        try:
            cmd1="uemcli -d {} -noHeader /stor/prov/luns/lun show -filter ID,Name,Size"
            cmd=cmd1.format(self.ip).split(' ')
            out = subprocess.check_output(cmd).split()
            l_id=[]
            l_name=[]
            l_size=[]
            lm=[]
            for i in range(0,len(out)):
                if out[i] == "ID":
                    l_id.append(out[i+2])
                if out[i] == "Name":
                    l_name.append(out[i+2])
                if out[i] == "Size":
                    l_size.append(out[i+2])
            for i in range(0,len(l_size)):
                if l_size[i] == "1319413953536":
                    lm.append(l_name[i])
            if len(lm)!= CONFIG[self.lunconfig_type][1]:
                return 1
            print("")
            self.exit_codes(0, "MainDB LUNs creation successful.")
            return 0
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG2)

    def add_temp(self):
        """
        This function creates Temp DB depending on targeted config
        name --> newly added lun names
        lun_id --> lun ids
        percent --> completion percent
        """
        try:
            print("")
            self.exit_codes(0,"Started TempDB LUNs creation...")
            sp = ["spa", "spb"]
            tempdb = []
            no = int(CONFIG[self.config_type][2])
            j=no+1
            num = int(CONFIG[self.lunconfig_type][2])
            with open(TEMP_FILE2, 'w'):
                '''No action required'''
                pass
            for i in range(no+1, num+1):
                name = self.temp_name + str(i)
                str1="uemcli -noHeader -d {} /stor/prov/luns/lun create"
                str2=" -name {} -type primary -thin yes -pool {} -size {} -spOwner {}"
                cmd1=str1+str2
                cmd=cmd1.format(self.ip, name, self.pool_id, '530G', sp[j%2]).split(' ')
                lun = subprocess.check_output(cmd)
                j = j + 1
                lun_id = re.findall(r'sv_[0-9]+', lun)
                self.temp_id.append(lun_id)
                with open(TEMP_FILE2, 'a') as f:
                    f.write(lun_id[0])
                    f.write("\n")
                    f.write(name)
                    f.write("\n")
                l = [name, lun_id[0]]
                tempdb.append(l)
                msg = 'Created %s: %s'%(name, lun_id[0])
                self.log_file_scrn(msg, 1)
                percent = ((int(i)/num)*100)
                sys.stdout.write('\r{} percent completed'.format(int(percent)))
                sys.stdout.flush()
            if len(tempdb) != (num-no):
                return 1
            code=self.add_temp1()
            if code==0:
                return 0
            else:
                return 1
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG2)
    def add_temp1(self):
        """
        This function will collect the newly TempDb Luns
        ln_id-->lun ids
        ln_name-->lun names
        ln_size-->lun sizes
        """
        cmd2="uemcli -d {} -noHeader /stor/prov/luns/lun show -filter ID,Name,Size"
        cmd=cmd2.format(self.ip).split(' ')
        out = subprocess.check_output(cmd).split()
        ln_id=[]
        ln_name=[]
        ln_size=[]
        lm=[]
        for i in range(0,len(out)):
            if out[i] == "ID":
                ln_id.append(out[i+2])
            if out[i] == "Name":
                ln_name.append(out[i+2])
            if out[i] == "Size":
                ln_size.append(out[i+2])
        for i in range(0,len(ln_size)):
            if ln_size[i] == "569083166720":
                lm.append(ln_name[i])
        if len(lm)!= CONFIG[self.lunconfig_type][2]:
             return 1
        print("")
        self.exit_codes(0, "TempDB LUNs creation successful.\n")
        return 0
def stagelist():
    """
    Checks and returns which stage we are currently present at in case of failure
    Args: None
    return: int
    stage --> stage the execution going on
    """
    stage=1
    try:
        if os.path.exists(STAGE):
            with open(STAGE, 'r') as f:
                stage = int(f.read())
        return stage
    except Exception:
        return stage
def handler(signum, frame):
    """
    restore the original signal handler
    in raw_input when CTRL+C is pressed will be handled by below
    """
    print("ctrl+c not allowed at this moment")

def check_userid():
    """
    This funtion is to check the user id,
    if user id not root then exit the script
    Param: None
    Return: None
    """
    if os.getuid() != 0:
        print("ERROR: Only Root can execute the script...")
        sys.exit(1)
def main():
    """
    Main Function to wrap all the functions
    stage --> stages
    return --> none
    args --> none
    signal --> to avoid ctrl+c in between
    """
    global SYSTEM_NAME
    global SYSTEM_NAME2
    check_userid()
    lun = LunExpansion()
    signal.signal(signal.SIGINT, handler)
    msg="Starting Additional LUNs Creation"
    lun.log_file_scrn("="*70)
    lun.exit_codes(3,msg)
    lun.log_file_scrn("="*70)
    lun.print_logging_details()
    stage = stagelist()
    if stage == 1:
        lun.read_input1()
        lun.lun_info()
        stage = stage + 1
        with open(STAGE, 'w') as f:
            f.write(str(stage))
    if stage == 2:
        lun.read_input1()
        lun.lun_cleanup()
        lun.add_main()
        code=lun.add_temp()
        if code == 0:
            if os.path.exists(TP1):
                os.remove(TP1)
            if os.path.exists(TP2):
                os.remove(TP2)
            if os.path.exists(STAGE):
                os.remove(STAGE)
        msg1="Successfully Completed Additional LUNs Creation"
        lun.log_file_scrn("="*70)
        lun.exit_codes(3,msg1)
        lun.log_file_scrn("="*70)
if __name__ == "__main__":
    main()
sys.exit(0)

