#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script for Pool Expansion as per target configuration"""
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
# in the agreement/contract under which the program(s) have been
# supplied.
#
# ******************************************************************************
# Name      : PoolExpansion.py
# Purpose   : The script will perform Dynamic Pool Expansion in unity
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
FILE_PATH = '/opt/ericsson/san/etc/'
LOG_DI = '/var/ericsson/log/storage/'
LOG_NAME = os.path.basename(__file__).replace('.py', '_')+time.strftime("%m_%d_%Y-%H_%M_%S")+'.log'
TMP_FILE = '/var/tmp/input_file2.txt'
JOB_DRIVE= '/var/tmp/job.txt'
CMD="uemcli -d {} -noHeader /stor/config/dg show -filter"
CMD1="ID,Drive type,Vendor size,Number of drives,Unconfigured drives"
MSG2="issue with the CLI/CMD execution and above are the actual ERROR"
CMD2='uemcli -noHeader -d {} -gmtoff +01:00 /sys/task/job -active show -filter'
CM="uemcli -d {} -noHeader /stor/config/pool show -filter"
DR1="ID,Number of drives"
class PoolExpansion(object):
    """
    This class will do the unity Storage Expansion
    JOB status will be checked
    Drives need to added will be checked
    this is class
    """
    def __init__(self):
        """
        Init for variable initialisation
        """
        self.logger = logging.getLogger()
        self.logging_config()
        self.colors = {'RED' : '\033[91m', 'END' : '\033[00m',
                       'GREEN' : '\033[92m', 'YELLOW' : '\033[93m'}
        self.ip =''
        self.config_type =''
        self.lunconfig_type = ''
        self.required_drives= ''
        self.pool_id = ''
        self.pool_name = ''
        self.out=''
        self.count=''
        self.usd_dr=''
    def logging_config(self):
        """
        Creating a custom logger for logs
        """
        if not os.path.exists(LOG_DI):
            os.makedirs(LOG_DI)
        s_handler1 = logging.StreamHandler()
        f_handler1 = logging.FileHandler(LOG_DI+LOG_NAME)
        s_handler1.setLevel(logging.ERROR)
        f_handler1.setLevel(logging.WARNING)
        s_format = logging.Formatter('%(message)s')
        f_format = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_handler1.setFormatter(s_format)
        f_handler1.setFormatter(f_format)
        self.logger.addHandler(s_handler1)
        self.logger.addHandler(f_handler1)

    def log_file_scrn(self, msg2, log_dec=0):
        """
        Logging into file and screen
        """
        if log_dec == 0:
            self.logger.error(msg2)
        else:
            self.logger.warning(msg2)

    def print_logging_details(self):
        """
        Print Logging Details with log file for exit,
        completion and start of the script
        """
        color_s = self.colors
        hash_print = '-------------------------------------------------------------------------'
        self.log_file_scrn(color_s['YELLOW']+hash_print+color_s['END'])
        msg = "Please find the script execution logs  ---> "
        self.log_file_scrn(color_s['YELLOW']+msg+LOG_DI+LOG_NAME+color_s['END'])
        self.log_file_scrn(color_s['YELLOW']+hash_print+color_s['END'])

    def exit_codes(self, code2, msg):
        """
        Script Exit function
        param:
        code --> Exit code of the script and changing type of the message
        msg --> Actual message to print on the screen
        return: None
        """
        colors = self.colors
        if code2 == 1:
            self.log_file_scrn(colors['RED']+"[ERROR] "+colors['END']+": "+msg)
            self.print_logging_details()
            sys.exit(code2)
        elif code2 == 2:
            self.log_file_scrn(colors['YELLOW']+"[WARN] "+colors['END']+ ":"+msg)
        elif code2 == 3:
            self.log_file_scrn("[" + time.strftime("%m-%d-%Y-%H:%M:%S") + "] "
                               + colors['GREEN'] + "[INFO] " + colors['END'] + ": " + msg)
        else:
            self.log_file_scrn(colors['GREEN']+"[INFO] "+colors['END']+": "+msg)
    def read_input1(self):
        """
        Takes the required input from the saved file to
        resume state in case of failure
        """
        if os.path.exists(TMP_FILE):
            with open(TMP_FILE, 'r') as f:
                out = f.readlines()
                self.pool_id = out[1].split('\n')[0].strip()
                self.pool_name = out[2].split('\n')[0].strip()
                self.ip = out[0].split('\n')[0].strip()
                self.config_type = out[3].split('\n')[0].strip()
                self.lunconfig_type = out[4].split('\n')[0].strip()
                self.required_drives= out[5].split('\n')[0].strip()
        else:
            self.exit_codes(1,"Issue with provided inputs. Try again!")
            sys.exit(1)

    def active_check(self):
        """
        This function will perform pool expansion progression
        """
        self.out=1
        for i in range(1,100):
            time.sleep(2)
            sys.stdout.write("\rPlease wait%s" %('.'*i))
            sys.stdout.flush()
        print(" ")
        self.count=''
        while self.out!=0:
            self.status_check()
    def status_check(self):
        """
        This function will check job status
        params-->None
        return --->None
        """
        try:
            cmd=CMD2.format(self.ip).split(' ')
            cmd.append("ID,Title,Percent complete,State")
            ou=subprocess.check_output(cmd)
            ou=ou.strip()
            if not ou:
                self.out = 0
            else:
                self.status()
        except Exception as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG2)
    def status(self):
        """
        Status check
        Running--->for running jobs
        Queued--->for Queued jobs
        return--->None
        params--->None
        """
        try:
            cmd1=CMD2.format(self.ip).split(' ')
            cmd1.append("ID,Title,Percent complete,State")
            out2=subprocess.check_output(cmd1)
            out2 = out2.strip()
            out2 = out2.split('\n')
            out5=out2[3].split(" = ")
            out1=out2[1].split(" = ")
            out3=out2[2].split(" = ")
            out4=out2[0].split(" = ")
            if (out5[1]=="Running") and (out1[1]=="Modify storage pool"):
                with open(JOB_DRIVE,'w') as f:
                    f.write(str(out4[1]))
                    f.write('\n')
                if out3[1] != self.count:
                    msg1= out1[1]+" Process Running"
                    print(msg1)
                    msg2 = "Percent complete:"+out3[1]
                    print(msg2)
                    self.count=out3[1]
                else:
                    for i in range(1,100):
                        time.sleep(1)
                        sys.stdout.write("\rPlease wait%s" %('.'*i))
                        sys.stdout.flush()
                    print("\n")
                self.out = 1
            elif (out5[1]=="Queued") and (out1[1]=="Modify storage pool"):
                msg3 = out1[1]+" Process Queued"
                print(msg3)
                self.out =1
            else:
                self.out = 0
        except Exception as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG2)

    def job_status(self):
        """
        This will check pool expansion status through job ID
        return -->none
        args -->none
        pass to next stage if only expansion successful
        active status will be checked by fetching which are all process running on unity
        """
        if os.path.exists(JOB_DRIVE):
            with open(JOB_DRIVE, 'r') as f:
                j_id=f.readlines()
            job_id=j_id[0].split('\n')[0].strip()
            try:
                cmd="uemcli -d {} -noHeader -gmtoff +01:00 /sys/task/job -id {} show -filter State"
                cmd1=cmd.format(self.ip,job_id).split(' ')
                out=subprocess.check_output(cmd1).split("\n")
                out=out[0].split(' = ')
                if out[1]=="Completed":
                    self.status_job()
            except subprocess.CalledProcessError as err:
                self.log_file_scrn("-"*62)
                self.log_file_scrn(err)
                self.log_file_scrn("-"*62)
                self.exit_codes(1, MSG2)
    def status_job(self):
        """
        Thsi function will check job status
        lun.configtype-->target config
        usd_dr-->used drives
        pool_id-->respective poolid
        """
        try:
            usd_dr=""
            msg="Dynamic Pool Expanded Successfully as per target config\n"
            cmd1=CM
            cmd=cmd1.format(self.ip).split(' ')
            cmd.append(DR1)
            out = subprocess.check_output(cmd).split()
            for i in range(0,len(out)):
                if str(out[i]) == str(self.pool_id):
                    usd_dr=out[i+5]
            print("")
            if (self.lunconfig_type=='F') and (int(usd_dr)>=(int(CONFIG[self.lunconfig_type][0]))):
                self.exit_codes(0,msg)
            elif (self.lunconfig_type=='G') and (int(usd_dr)>=(int(CONFIG[self.lunconfig_type][0]))):
                self.exit_codes(0,msg)
            else:
                self.exit_codes(1,"Dynamic Pool Expansion not Successful as per target config.")
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*62)
            self.log_file_scrn(err)
            self.log_file_scrn("-"*62)
            self.exit_codes(1, MSG2)
    def verification(self):
        """
        final verification
        self.ip is unity ip
        self.usd_drs-->drives used in pool
        self.lunconfig_type--->targeted configurtion
        """
        try:
            usd_drs=0
            cmd111=CM
            cmddd=cmd111.format(self.ip).split(' ')
            cmddd.append(DR1)
            outtt = subprocess.check_output(cmddd).split()
            for i in range(0,len(outtt)):
                if str(outtt[i]) == str(self.pool_id):
                    usd_drs=outtt[i+5]
            print("")
            if (self.lunconfig_type == 'F') and (int(usd_drs) >= (int(CONFIG[self.lunconfig_type][0]))):
                return 0
            elif (self.lunconfig_type == 'G') and (int(usd_drs) >= (int(CONFIG[self.lunconfig_type][0]))):
                return 0
            else:
                return 1
        except subprocess.CalledProcessError as er:
            self.log_file_scrn("-"*63)
            self.log_file_scrn(er)
            self.log_file_scrn("-"*63)
            self.exit_codes(1, MSG2)

    def pool_expansion(self):
        """
        This function will performs pool expansion
        usd_dr-->used drives
        """
        try:
            cmd=CMD.format(self.ip).split(' ')
            cmd.append(CMD1)
            chek_disk1=subprocess.check_output(cmd)
            chek_disk1=chek_disk1.split('\n')
            chek=chek_disk1[0].split()
            dg_id=str(chek[3])
            cmd1=CM
            cmd2=cmd1.format(self.ip).split(' ')
            cmd2.append(DR1)
            val = subprocess.check_output(cmd2).split()
            self.usd_dr=0
            for i in range(0,len(val)):
                if str(val[i]) == str(self.pool_id):
                    self.usd_dr=val[i+5]
            if int(self.usd_dr)>=int(CONFIG[self.lunconfig_type][0]):
                self.required_drives=0
            else:
                self.required_drives=(int(CONFIG[self.lunconfig_type][0]))-int(self.usd_dr)
            if self.required_drives >= 1:
                self.exit_codes(0,"Dynamic Pool Expansion Required.\n")
                cmd="uemcli -d {} /stor/config/pool -name {} extend -diskGroup {} -drivesNumber {}"
                child1=pexpect.spawn(cmd.format(self.ip,self.pool_name,dg_id,self.required_drives))
                child1.logfile=sys.stdout
                out1= child1.expect(".*HTTPS.*",timeout=None)
            else:
                if not os.path.exists(JOB_DRIVE):
                    print("")
                    self.exit_codes(0,"Dynamic Pool Expansion Not Required.\n")
                    return 0
            out1 = 0
            if out1 == 0:
                self.active_check()
                self.job_status()
        except Exception as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG2)
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
    return --> none
    args --> none
    signal --> to avoid ctrl+c in between
    this is Main
    """
    check_userid()
    lun = PoolExpansion()
    signal.signal(signal.SIGINT, handler)
    msg="Starting Dynamic Pool Validation and Expansion Stage"
    lun.log_file_scrn("="*70)
    lun.exit_codes(3,msg)
    lun.log_file_scrn("="*70)
    lun.print_logging_details()
    lun.read_input1()
    lun.pool_expansion()
    code=lun.verification()
    if code == 0:
        msg1="Successfully Completed Dynamic Pool Validation and Expansion Stage"
        lun.log_file_scrn("="*70)
        lun.exit_codes(3,msg1)
        lun.log_file_scrn("="*70)
    else:
        msg11 = "Dynamic Pool Expansion Stage Failed"
        lun.exit_codes(1, msg11)
if __name__ == "__main__":
    main()
sys.exit(0)

