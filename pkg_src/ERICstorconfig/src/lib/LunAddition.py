#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for Adding Luns to hosts
operations:
1.Add luns to respective hosts based on target configuration
2.The hosts are Coordinator,Engine,reader1,Reader2
3.Check for the Luns added to host properly or not post adding luns to host
4.Displays newly added luns on console
5.Creates config file for newly added LUNs
6.Creates target configfile with overall LUNs information
Hosts are:
1.Coordinator
2.Engine
3.Reader1
4.Reader2
Configurations supported are:
Configuration E
Configuration F
Configuration G
Luns are:
1.MainDB
2.TempDB
3.sysmain
4.ext4 luns
ext4 LUNS are:
ext_co
ext_reder1
ext_reader2
ext_engine
"""
# ****************************************************************************
# Ericsson Radio Systems AB                                     SCRIPT
# ****************************************************************************
# (c) Ericsson Radio Systems AB 2019 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property
# of Ericsson Radio Systems AB, Sweden. The programs may be used
# and/or copied only with the written permission from Ericsson Radio
# Systems AB or in accordance with the terms and conditions stipulated
# in the agreement/contract under which the program(s) have been
# supplied.
# ******************************************************************************
# Name      : LunAddition.py
# Purpose   : The script will perform adding LUNs to Hosts
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
CONFIG_E = {'Co':["24", 21, 1], 'En':["1", 0, 0], 'R1':["27", 21, 4], 'R2':["25", 21, 2]}
CONFIG_F = {'Co':["36", 33, 1], 'En':["1", 0, 0], 'R1':["41", 33, 6], 'R2':["37", 33, 2]}
CONFIG_G = {'Co':["53", 50, 1], 'En':["1", 0, 0], 'R1':["63", 50, 11], 'R2':["56", 50, 4]}
SYSTEM_NAME = ''
SYSTEM_NAME2 = ''
FILE_PATH = '/opt/ericsson/san/etc/'
LOG_DIR = '/var/ericsson/log/storage/'
LOG_NAME = os.path.basename(__file__).replace('.py', '_')+time.strftime("%m_%d_%Y-%H_%M_%S")+'.log'
TMP_FILE = '/var/tmp/input_file2.txt'
TEMP_FILE1= '/var/tmp/tp1.txt'
TEMP_FILE2= '/var/tmp/tp2.txt'
STAGE = '/var/tmp/stagelist2'
HST_FILE= '/var/tmp/input_file3.txt'
COR='/var/tmp/cor.txt'
RED1='/var/tmp/r1.txt'
RED2='/var/tmp/r2.txt'
MSG2="issue with the CLI/CMD execution and above are the actual ERROR"
LUNS="uemcli -d {} -noHeader /remote/host -id {} set -addLuns {}"
HOST="uemcli -d {} /remote/host/hlu -host {} show -filter LUN"
LN="uemcli -d {} -noHeader /stor/prov/luns/lun show -filter ID,Name,Size"
LN_I=":The specified LUN has already been in the access LUNs"
SYS="System name"
LUN_I='/var/tmp/ln'
class Addlunstohost(object):
    """
    This class will do the unity Storage Expansion
    Luns will be added as per target configuration
    Luns will be added to hosts
    pool expansion will be done
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
        lun --> lun related variables
        config --> existing config
        lunconfig --> targeted config
        host --> host related variables
        """
        self.logger = logging.getLogger()
        self.logging_conf()
        self.colors = {'RED' : '\033[91m', 'END' : '\033[00m',
                       'GREEN' : '\033[92m', 'YELLOW' : '\033[93m'}
        self.ip =''
        self.lunconfig_type = ''
        self.config_type=""
        self.pool_id = ''
        self.pool_name=''
        self.lun_id=''
        self.lun_id1=[]
        self.lun_name=[]
        self.lun_size=[]
        self.host_id1=''
        self.host_id3=''
        self.host_id2=''
        self.host_id4=''
        self.host=[]
        self.host_name=[]
        self.temp_id=[]
        self.main_id=[]
        self.hst_id=[]
        self.r1=[]
        self.r2=[]
        self.cor=[]
        self.cord=[]
        self.red1=[]
        self.red2=[]
        self.eng=[]
        self.m_lun=[]
        self.t_lun=[]
        self.sys_lun=[]
        self.ext_lun=[]
        self.m_id=[]
        self.t_id=[]
        self.sys_id=[]
        self.ext_id=[]
        self.hs=''
        self.lun_nm=[]
        self.lun_sz=[]
        self.lun_i=[]
    def logging_conf(self):
        """
        Creating a custom logger for logs
        It creates 2 different log handler
        StreamHandler which handles logs of
        which handles logs of WARNING level or
        Creating a custom logger for logs
        ERROR --> to display error
        WARNING --> To display warnig
        LOG_DIR --> Log dir path
        """
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        s_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(LOG_DIR+LOG_NAME)
        s_handler.setLevel(logging.ERROR)
        f_handler.setLevel(logging.WARNING)
        s_formats = logging.Formatter('%(message)s')
        f_formats = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_handler.setFormatter(s_formats)
        f_handler.setFormatter(f_formats)
        self.logger.addHandler(s_handler)
        self.logger.addHandler(f_handler)
    def log_file_scrn(self, msg3, log_dec=0):
        """
        Logging into file and screen
        based on the value of log_dec variable
        if value of log_dec is 0 it will print
        simultaneuously to screen and log file
        for log_dec value as 1 it will print to
        logfile directly
        Param:
              msg -> the actual message
              log_dec -> integer
        Return: None
        """
        if log_dec == 0:
            self.logger.error(msg3)
        else:
            self.logger.warning(msg3)
    def print_logging_detail(self):
        """
        Print Logging Details with log file for exit,
        completion and start of the script
        colors --> to print color
        args--> none
        """
        colors_s = self.colors
        hash_print = '-------------------------------------------------------------------------'
        self.log_file_scrn(colors_s['YELLOW']+hash_print+colors_s['END'])
        msg = "Please find the script execution logs  ---> "
        self.log_file_scrn(colors_s['YELLOW']+msg+LOG_DIR+LOG_NAME+colors_s['END'])
        self.log_file_scrn(colors_s['YELLOW']+hash_print+colors_s['END'])
    def exit_codes(self, code3, msg):
        """
        Script Exit funtion
        param: code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        colors --> to display letters in colors
        """
        colors = self.colors
        if code3 == 1:
            self.log_file_scrn(colors['RED']+"[ERROR] "+colors['END']+": "+msg)
            self.print_logging_detail()
            sys.exit(code3)
        elif code3 == 2:
            self.log_file_scrn(colors['YELLOW']+"[WARN] "+colors['END']+ ":"+msg)
        elif code3 == 3:
            self.log_file_scrn("[" + time.strftime("%m-%d-%Y-%H:%M:%S") + "] "
                               + colors['GREEN'] + "[INFO] " + colors['END'] + ": " + msg)
        else:
            self.log_file_scrn(colors['GREEN']+"[INFO] "+colors['END']+": "+msg)
    def read_input(self):
        """
        Takes the required input from the saved file to resume state in case of failure
        """
        global SYSTEM_NAME
        global SYSTEM_NAME2
        try:
            cmd = "uemcli -d {} -noHeader /sys/general show -filter".format(self.ip).split(' ')
            cmd.append("System name")
            system = subprocess.check_output(cmd)
            name  = system.split("=")[-1].strip()
            SYSTEM_NAME = name + "_" + self.pool_name + "_expanded_"+self.config_type+"_"+self.lunconfig_type
            SYSTEM_NAME2 = name + "_" + self.pool_name + "_expandedconfig"
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*73),self.log_file_scrn(err.output),self.log_file_scrn("-"*73)
            self.exit_codes(1, MSG2)
    def read_input1(self):
        """
        Takes the required input from the saved file to resume state in case of failure
        read all required inputs to variable for use
        Args --> None
        Return --> None
        TMP_FILE --> to save all required data for expansion by fetching from deployment and user
        """
        if os.path.exists(TMP_FILE):
            with open(TMP_FILE, 'r') as f:
                out = f.readlines()
                self.lunconfig_type = out[4].split('\n')[0].strip()
                self.ip = out[0].split('\n')[0].strip()
                self.config_type = out[3].split('\n')[0].strip()
                self.pool_id = out[1].split('\n')[0].strip()
                self.pool_name = out[2].split('\n')[0].strip()
                self.host_id1 = out[6].split('\n')[0].strip()
                self.host_id2 = out[7].split('\n')[0].strip()
                self.host_id3 = out[8].split('\n')[0].strip()
                self.host_id4 = out[9].split('\n')[0].strip()
        else:
            self.exit_codes(1,"Issue with provided inputs. Try again!")
    def add_luns_host(self):
        """
        This function will add luns to the respective host
        hosts:
        a.coordinator
        b.Engine
        c.Reader1
        d.Reader2
        return 0 or 1
        args --> none
        """
        code1=self.verification_lun()
        if code1==1:
            return 1
        out_f()
        self.log_file_scrn("*"*65)
        path="Please find the newly assigned LUN Configuration from the following path - {}"
        self.log_file_scrn(path.format(SYSTEM_NAME))
        self.log_file_scrn("*"*65)
        return 0
    def main_add_hst1(self):
        """
        This function will assign Main DB luns to Host
        Hosts:
        1.Coordinator
        2.Engine
        3.Reader1
        4.Reader2
        return -->none
        args -->none
        TEMP_FILE1 --> to fetch the main DB related information
        """
        try:
            print("Assigning LUNs to the Hosts. Please wait.. it might take few minutes.")
            with open (TEMP_FILE1,'r') as f:
                out1=f.readlines()
            for i in range (1,((int(CONFIG[self.lunconfig_type][1])-(int(CONFIG[self.config_type][1])))*2),2):
                l_id=out1[i].split('\n')[0].strip()
                try:
                    cmd=LUNS.format(self.ip,self.host_id1,l_id).split(' ')
                    subprocess.check_output(cmd)
                except Exception as err:
                    msg=l_id+LN_I
                    self.exit_codes(2,msg)
            time.sleep(5)
            self.cord=[]
            cmd=HOST.format(self.ip,self.host_id1).split(' ')
            out1=subprocess.check_output(cmd).split()
            for i in range(0,len(out1)):
                if out1[i] == "LUN":
                    self.cord.append(out1[i+2])
            if (len(self.cord)==(int(CONFIG_F['Co'][0]))) or (len(self.cord)==(int(CONFIG_G['Co'][0]))):
                self.exit_codes(0,"MainDB LUNs assigned to the Coordinator Host successfully")
            else:
                self.exit_codes(1,"MainDB LUNs not assigned to the Coordinator Host successfully")
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*73)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*73)
            self.exit_codes(1, MSG2)
    def main_add_hst2(self):
        """
        This function will assign Main DB luns to Host
        Hosts:
        1.Coordinator
        2.Engine
        3.Reader1
        4.Reader2
        return -->none
        args -->none
        TEMP_FILE1 --> to fetch the main DB related information
        """
        try:
            with open (TEMP_FILE1,'r') as f:
                out1=f.readlines()
            for i in range (1,((int(CONFIG[self.lunconfig_type][1])-(int(CONFIG[self.config_type][1])))*2),2):
                l_id=out1[i].split('\n')[0].strip()
                try:
                    cmd=LUNS.format(self.ip,self.host_id3,l_id).split(' ')
                    subprocess.check_output(cmd)
                except Exception as err:
                    msg=l_id+LN_I
                    self.exit_codes(2,msg)
            time.sleep(5)
            self.red1=[]
            cmd=HOST.format(self.ip,self.host_id3).split(' ')
            out2=subprocess.check_output(cmd).split()
            for i in range(0,len(out2)):
                if out2[i] == "LUN":
                    self.red1.append(out2[i+2])
            a=int(CONFIG_F['R1'][2])-int(CONFIG_E['R1'][2])
            b=int(CONFIG_G['R1'][2])-int(CONFIG_F['R1'][2])
            c=int(CONFIG_G['R1'][2])-int(CONFIG_E['R1'][2])
            to1=int(CONFIG_F['R1'][0])
            to2=int(CONFIG_G['R1'][0])
            if (len(self.red1)==(to1-a)) or (len(self.red1)==(to2-b)) or (len(self.red1)==(to2-c)):
                self.exit_codes(0,"MainDB LUNs assigned to the Reader1 Host successfully")
            else:
                self.exit_codes(1,"MainDB LUNs not assigned to the Reader1 Host successfully")
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*73)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*73)
            self.exit_codes(1, MSG2)
    def main_add_hst3(self):
        """
        This function will assign Main DB luns to Host
        Hosts:
        1.Coordinator
        2.Engine
        3.Reader1
        4.Reader2
        return -->none
        args -->none
        TEMP_FILE1 --> to fetch the main DB related information
        """
        try:
            with open (TEMP_FILE1,'r') as f:
                out1=f.readlines()
            for i in range (1,((int(CONFIG[self.lunconfig_type][1])-(int(CONFIG[self.config_type][1])))*2),2):
                l_id=out1[i].split('\n')[0].strip()
                try:
                    cmd=LUNS.format(self.ip,self.host_id4,l_id).split(' ')
                    subprocess.check_output(cmd)
                except Exception as err:
                    msg=l_id+LN_I
                    self.exit_codes(2,msg)
            time.sleep(5)
            self.red2=[]
            cmd=HOST.format(self.ip,self.host_id4).split(' ')
            out3=subprocess.check_output(cmd).split()
            for i in range(0,len(out3)):
                if out3[i] == "LUN":
                    self.red2.append(out3[i+2])
            a=int(CONFIG_G['R2'][2])-int(CONFIG_F['R2'][2])
            b=int(CONFIG_G['R2'][2])-int(CONFIG_E['R2'][2])
            to1=int(CONFIG_F['R2'][0])
            to2=int(CONFIG_G['R2'][0])
            if (len(self.red2)==to1) or (len(self.red2)==(to2-a)) or (len(self.red2)==(to2-b)):
                self.exit_codes(0,"MainDB LUNs assigned to the Reader2 Host successfully")
            else:
                self.exit_codes(1,"MainDB LUNs not assigned to the Reader2 Host successfully")
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*73)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*73)
            self.exit_codes(1, MSG2)
    def temp_add_hst(self):
        """
        This function will add temp DB luns to host
        return -->none
        args --> none
        """
        temp_data()
        with open (TEMP_FILE2,'r') as f:
            out2=f.readlines()
        t=int(CONFIG[self.lunconfig_type][2])
        p=int(CONFIG[self.config_type][2])
        if (len(out2)==((t-p)*2)) and (self.lunconfig_type == 'F'):
            for i in range (0,((t-(p))*2),2):
                l_id=out2[i].split('\n')[0].strip()
                l_name=out2[i+1].split('\n')[0].strip()
                with open (RED1,'a') as f:
                    f.write(l_id)
                    f.write("\n")
                    f.write(l_name)
                    f.write("\n")
                try:
                    cmd=LUNS.format(self.ip,self.host_id3,l_id).split(' ')
                    subprocess.check_output(cmd)
                except Exception:
                    msg=l_id+LN_I
                    self.exit_codes(2,msg)
        elif (len(out2)==((t-p)*2)) and (self.lunconfig_type == 'G'):
            self.tmp_add_lun()
        self.temp_check1()
        self.temp_check2()
    def temp_check2(self):
        """
        This function will checks tempDB luns added to host or not
        cord-->coordinator luns
        red1-->reader1 luns
        red2-->reader2 luns
        """
        c1=int(CONFIG_F['Co'][0])
        re1=int(CONFIG_F['R1'][0])
        re2=int(CONFIG_F['R2'][0])
        c2=int(CONFIG_G['Co'][0])
        red1=int(CONFIG_G['R1'][0])
        red2=int(CONFIG_G['R2'][0])
        conf1=((len(self.cord)==c1) and (len(self.red1)==re1) and (len(self.red2)==re2))
        conf2=((len(self.cord)==c2) and (len(self.red1)==red1) and (len(self.red2)==red2))
        if conf1 or conf2:
            self.exit_codes(0,"TempDB LUNs assigned to the Hosts successfully")
        else:
            self.exit_codes(1,"TempDB LUNs not assigned to the Hosts successfully")
    def temp_check1(self):
        """
        This function will check tempDB luns added to host properly or not
        """
        try:
            time.sleep(5)
            self.cord=[]
            self.red1=[]
            self.red2=[]
            cmd=HOST.format(self.ip,self.host_id1).split(' ')
            o1=subprocess.check_output(cmd).split()
            for i in range(0,len(o1)):
                if o1[i] == "LUN":
                    self.cord.append(o1[i+2])
            cmd=HOST.format(self.ip,self.host_id3).split(' ')
            o2=subprocess.check_output(cmd).split()
            for i in range(0,len(o2)):
                if o2[i] == "LUN":
                    self.red1.append(o2[i+2])
            cmd=HOST.format(self.ip,self.host_id4).split(' ')
            o3=subprocess.check_output(cmd).split()
            for i in range(0,len(o3)):
                if o3[i] == "LUN":
                    self.red2.append(o3[i+2])
            with open (LUN_I,'w') as f:
                f.write(str(len(self.cord)))
                f.write("\n")
                f.write(str(len(self.red1)))
                f.write("\n")
                f.write(str(len(self.red2)))
                f.write("\n")
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG2)
    def tmp_add_lun(self):
        """
        This function will add temp DB luns to host
        Hosts are:
        1.Coordinator
        2.Engine
        3.Reader1
        4.Reader2
        return -->none
        args --> none
        """
        with open (TEMP_FILE2,'r') as f:
            out2=f.readlines()
        t=int(CONFIG[self.lunconfig_type][2])
        p=int(CONFIG[self.config_type][2])
        for i in range (0,(((t-p)*2)-4),2):
            ln_id=out2[i].split('\n')[0].strip()
            ln_name=out2[i+1].split('\n')[0].strip()
            with open (RED1,'a') as f:
                f.write(ln_id)
                f.write("\n")
                f.write(ln_name)
                f.write("\n")
            try:
                cmd=LUNS.format(self.ip,self.host_id3,ln_id).split(' ')
                subprocess.check_output(cmd)
            except Exception:
                msg=ln_id+LN_I
                self.exit_codes(2,msg)
        for i in range ((((t-p)*2)-4),((t-p)*2),2):
            l_id=out2[i].split('\n')[0].strip()
            l_name=out2[i+1].split('\n')[0].strip()
            with open (RED2,'a') as f:
                f.write(l_id)
                f.write("\n")
                f.write(l_name)
                f.write("\n")
            try:
                cmd=LUNS.format(self.ip,self.host_id4,l_id).split(' ')
                subprocess.check_output(cmd)
            except Exception:
                msg=l_id+LN_I
                self.exit_codes(2,msg)
    def verification_lun(self):
        """
        This function will do post verification os luns added to hosts
        hosts that will check for:
        w.coordinator
        x.engine
        y.reader1
        z.reader2
        return -->0 or 1
        args --> none
        """
        try:
            self.eng=[]
            cmd=HOST.format(self.ip,self.host_id2).split(' ')
            out4=subprocess.check_output(cmd).split()
            for i in range(0,len(out4)):
                if out4[i] == "LUN":
                    self.eng.append(out4[i+2])
            code=self.hst_add_lun()
            if code==0:
                return 0
            else:
                return 1
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG2)
    def hst_add_lun(self):
        """
        This function will verify the luns added to the respective host
        return 1 or 0
        args -->none
        """
        self.out_f2()
        n1=int(CONFIG_F['R2'][0])
        n2=int(CONFIG_G['R2'][0])
        o1=int(CONFIG_F['En'][0])
        o2=int(CONFIG_G['En'][0])
        with open(LUN_I,'r') as f:
            out=f.readlines()
            co=out[0].split('\n')[0].strip()
            r1=out[1].split('\n')[0].strip()
            r2=out[2].split('\n')[0].strip()
        conf1=((int(co)==int(CONFIG_F['Co'][0])) and (int(r1)==int(CONFIG_F['R1'][0])) and (int(r2)==n1))
        conf2=((int(co)==int(CONFIG_G['Co'][0])) and (int(r1)==int(CONFIG_G['R1'][0])) and (int(r2)==n2))
        if  (conf1 and (len(self.eng)==o1)) or (conf2 and (len(self.eng)==o2)):
            self.exit_codes(0,"Post Configuration check completed successfully")
            msg="Successfully Completed LUN Assignment to Host"
            self.log_file_scrn("="*70),self.exit_codes(3,msg),self.log_file_scrn("="*70)
            return 0
        else:
            self.exit_codes(1,"Post Configuration check failed")
            return 1
    def out_f2(self):
        """
        This function will collect LUN Information to print on configuration file
        args -->none
        return -->none
        underline will be done for headings
        """
        end = '\033[0m'
        underline = '\033[4m'
        line1 = underline + "[[Coordinator]]\n" + end
        line2 = underline + "[[Reader1]]\n" + end
        line3 = underline + "[[Reader2]]\n" + end
        tmp="\n[TempDB]\n"
        main="[MainDB]\n"
        val1=int(CONFIG[self.lunconfig_type][1])
        val2=int(CONFIG[self.config_type][1])
        self.cor=[]
        self.r1=[]
        self.r2=[]
        with open (COR,'r') as f:
            data=f.readlines()
            for i in range(0,len(data)):
                lun=data[i].split('\n')[0].strip()
                self.cor.append(lun)
        with open (RED1,'r') as f:
            data=f.readlines()
            for i in range(0,len(data)):
                lun=data[i].split('\n')[0].strip()
                self.r1.append(lun)
        with open (RED2,'r') as f:
            data=f.readlines()
            for i in range(0,len(data)):
                lun=data[i].split('\n')[0].strip()
                self.r2.append(lun)
        with open(SYSTEM_NAME, 'w') as f:
            f.write("Pool Information:\n\n")
            f.write("Name:")
            f.write(self.pool_name)
            f.write("\nID:")
            f.write(self.pool_id)
            f.write("\n\nNewly Added LUN Information:\n")
            f.write(line1)
            f.write(main)
            for i in range(1,(val1-val2)*2,2):
                f.write(self.cor[i-1])
                f.write(":")
                f.write(self.cor[i])
                f.write("\n")
            if len(self.cor)>((val1-val2)*2):
                f.write(tmp)
                for i in range(((val1-val2)*2)+1,len(self.cor),2):
                    f.write(self.cor[i])
                    f.write(":")
                    f.write(self.cor[i-1])
                    f.write("\n")
            f.write("\n")
            f.write(line2)
            f.write(main)
            for i in range(1,(val1-val2)*2,2):
                f.write(self.r1[i-1])
                f.write(":")
                f.write(self.r1[i])
                f.write("\n")
            if len(self.r1)>((val1-val2)*2):
                f.write(tmp)
                for i in range(((val1-val2)*2)+1,len(self.r1),2):
                    f.write(self.r1[i])
                    f.write(":")
                    f.write(self.r1[i-1])
                    f.write("\n")
            f.write("\n")
            f.write(line3)
            f.write(main)
            for i in range(1,(val1-val2)*2,2):
                f.write(self.r2[i-1])
                f.write(":")
                f.write(self.r2[i])
                f.write("\n")
            if len(self.r2)>((val1-val2)*2):
                f.write(tmp)
                for i in range(((val1-val2)*2)+1,len(self.r2),2):
                    f.write(self.r2[i])
                    f.write(":")
                    f.write(self.r2[i-1])
                    f.write("\n")
    def out_file(self):
        """
        This function will collect LUNs information to print on configuration file
        args-->none
        return-->none
        host-->host data
        """
        try:
            host=[]
            with open(TMP_FILE, 'r') as f:
                out=f.readlines()
                host.append(out[6].split('\n')[0].strip())
                host.append(out[7].split('\n')[0].strip())
                host.append(out[8].split('\n')[0].strip())
                host.append(out[9].split('\n')[0].strip())
            for self.hs in range(0,(len(host))):
                a=[]
                l_id=[]
                l_name=[]
                l_size=[]
                self.lun_nm=[]
                self.lun_sz=[]
                self.lun_i=[]
                cmd2="uemcli -d {} -noHeader /remote/host/hlu -host {} show -filter LUN"
                cmd=cmd2.format(self.ip,host[self.hs]).split(' ')
                out=subprocess.check_output(cmd).split('\n')
                for i in range(0,len(out)-1,2):
                    out1=out[i].split(' = ')
                    a.append(out1[1])
                cmd3="uemcli -d {} -noHeader /stor/prov/luns/lun show -filter ID,Name,Size"
                cmd1=cmd3.format(self.ip).split(' ')
                val = subprocess.check_output(cmd1).split('\n')
                for i in range(0,len(val)-1,4):
                    val1=val[i].split(' = ')
                    l_id.append(val1[1])
                    val2=val[i+1].split(' = ')
                    l_name.append(val2[1])
                    val3=val[i+2].split(' = ')
                    va=val3[1].split()
                    l_size.append(va[0])
                for i in range(0,len(l_id)):
                    if l_id[i] in a:
                        self.lun_nm.append(l_name[i])
                        self.lun_sz.append(l_size[i])
                        self.lun_i.append(l_id[i])
                self.out_final2()
                self.out_final()
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG2)
    def out_final2(self):
        """
        This function will collect LUNs information to print on configuration file
        args-->none
        return-->none
        """
        self.m_lun=[]
        self.t_lun=[]
        self.sys_lun=[]
        self.ext_lun=[]
        self.m_id=[]
        self.t_id=[]
        self.sys_id=[]
        self.ext_id=[]
        for i in range(0,len(self.lun_nm)):
            if self.lun_sz[i]=='1319413953536':
                self.m_lun.append(self.lun_nm[i])
                self.m_id.append(self.lun_i[i])
            elif self.lun_sz[i]=="569083166720":
                self.t_lun.append(self.lun_nm[i])
                self.t_id.append(self.lun_i[i])
            elif self.lun_sz[i]=="644245094400":
                self.sys_lun.append(self.lun_nm[i])
                self.sys_id.append(self.lun_i[i])
            elif self.lun_sz[i]=="429496729600" or self.lun_sz[i]=="214748364800":
                self.ext_lun.append(self.lun_nm[i])
                self.ext_id.append(self.lun_i[i])
    def out_final(self):
        """
        This function will collect LUN information to print on configuration file
        args-->none
        return-->none
        """
        end = '\033[0m'
        underline = '\033[4m'
        line1 = underline + "[[Coordinator]]\n" + end
        line2 = underline + "[[Engine]]\n" + end
        line3 = underline + "[[Reader1]]\n" + end
        line4 = underline + "[[Reader2]]\n" + end
        ext1="\n[Ext4]\n"
        if self.hs==1:
            with open(SYSTEM_NAME2,'a') as f:
                f.write("\n")
                f.write(line2)
                f.write(ext1)
                for i in range(0,len(self.ext_lun)):
                    f.write(self.ext_lun[i])
                    f.write(":")
                    f.write(self.ext_id[i])
                    f.write("\n")
        else:
            if self.hs==0:
                with open(SYSTEM_NAME2,'a') as f:
                    f.write("\n")
                    f.write(line1)
            elif self.hs==2:
                with open(SYSTEM_NAME2,'a') as f:
                    f.write("\n")
                    f.write(line3)
            else:
                with open(SYSTEM_NAME2,'a') as f:
                    f.write("\n")
                    f.write(line4)
            self.out_tmp()
    def out_tmp(self):
        """
        This function will do saving temperaury data to file
        return -->none
        args -->none
        """
        with open(SYSTEM_NAME2,'a') as f:
            f.write("\n[MainDB]\n")
            for i in range(0,len(self.m_lun)):
                f.write(self.m_lun[i])
                f.write(":")
                f.write(self.m_id[i])
                f.write("\n")
            if len(self.t_lun)>0:
                f.write("\n[TempDB]\n")
                for i in range(0,len(self.t_lun)):
                    f.write(self.t_lun[i])
                    f.write(":")
                    f.write(self.t_id[i])
                    f.write("\n")
            f.write("\n[SysMain]\n")
            for i in range(0,len(self.sys_lun)):
                f.write(self.sys_lun[i])
                f.write(":")
                f.write(self.sys_id[i])
                f.write("\n")
            f.write("\n[ext4]\n")
            for i in range(0,len(self.ext_lun)):
                f.write(self.ext_lun[i])
                f.write(":")
                f.write(self.ext_id[i])
                f.write("\n")
    def post_verification(self):
        """
        This function will perform post verification of LUN expansion
        size --> lun size
        args -->none
        parms -->none
        return --> 0 or 1
        """
        try:
            cmd1="uemcli -d {} -noHeader /stor/prov/luns/lun show -filter"
            cmd=cmd1.format(self.ip).split(' ')
            cmd.append("ID,Size,Storage pool ID")
            out = subprocess.check_output(cmd).split()
            lun=[]
            size=[]
            main_lun=[]
            temp_lun=[]
            for i in range(0,len(out)):
                if self.pool_id == out[i]:
                    lun.append(out[i-9])
                    size.append(out[i-6])
            for i in range(0,(len(lun))):
                if size[i] == '1319413953536':
                    main_lun.append(lun[i])
                elif size[i] == '569083166720':
                    temp_lun.append(lun[i])
            lun1=int(CONFIG[self.lunconfig_type][1])
            lun2=int(CONFIG[self.lunconfig_type][2])
            conf1=((str(self.lunconfig_type)=='F') and (len(main_lun)==lun1) and (len(temp_lun)==lun2))
            conf2=((str(self.lunconfig_type)=='G') and (len(main_lun)==lun1) and (len(temp_lun)==lun2))
            if conf1 or conf2:
                print("\nCollecting the target Configuration Information...\n")
                with open(SYSTEM_NAME2,'w') as f:
                    f.write("\nPool Information:\n\n")
                    f.write("Name:")
                    f.write(self.pool_name)
                    f.write("\nID:")
                    f.write(self.pool_id)
                    f.write("\n")
                    f.write("\n\nLUN Information:\n")
                    f.write("LUN Name:LUN ID\n\n")
                self.out_file()
                self.log_file_scrn("*"*65)
                msg="Please find the Storage Configuration Information of Target Config in the following path - {}"
                self.log_file_scrn(msg.format(SYSTEM_NAME2))
                self.log_file_scrn("*"*65)
                return 0
            else:
                return 1
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG2)
def out_f():
    """
    this function will display LUN information on the screen
    msg --> lun id and name
    return none
    args --> none
    """
    with open(TEMP_FILE1,'r') as f:
        out=f.readlines(0)
        out1=[]
        for i in range(0,len(out)):
            line=out[i].split('\n')[0].strip()
            out1.append(line)
        print("\nNewly Assigned MainDB LUNs to ENIQ Hosts are:")
        for i in range(0,len(out),2):
            msg = out1[i]+":"+out1[i+1]
            print(msg)
    with open(TEMP_FILE2,'r') as f:
        out=f.readlines(0)
        out1=[]
        for i in range(0,len(out)):
            line=out[i].split('\n')[0].strip()
            out1.append(line)
        print("\nNewly Assigned TempDB LUNs to ENIQ Hosts are:")
        for i in range(0,len(out),2):
            msg = out1[i+1]+":"+out1[i]
            print(msg)
        print("")
def temp_data():
    """
    to save data to files
    """
    data=[]
    with open (TEMP_FILE1,'r') as f:
        out1=f.readlines()
    for i in range(0,len(out1)):
        d=out1[i].split('\n')[0].strip()
        data.append(d)
    with open (COR,'w') as f:
        for i in range(0,len(data)):
            f.write(str(data[i]))
            f.write("\n")
    with open (RED1,'w') as f:
        for i in range(0,len(data)):
            f.write(str(data[i]))
            f.write("\n")
    with open (RED2,'w') as f:
        for i in range(0,len(data)):
            f.write(str(data[i]))
            f.write("\n")
def handler(signum, frame):
    """
    restore the original signal handler
    in raw_input when CTRL+C is pressed will be handled by below
    """
    print("ctrl+c not allowed at this moment")
def stagelist_host():
    """
    Checks and returns which stage we are currently present at in case of failure
    Args: None
    return: int
    stage --> stage the execution going on
    """
    stages=1
    try:
        if os.path.exists(STAGE):
            with open(STAGE, 'r') as f:
                stages = int(f.read())
        return stages
    except Exception:
        return stages
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
    lun = Addlunstohost()
    signal.signal(signal.SIGINT, handler)
    msg="Starting LUN Assignment to Host"
    lun.log_file_scrn("="*70)
    lun.exit_codes(3,msg)
    lun.log_file_scrn("="*70)
    lun.print_logging_detail()
    stages = stagelist_host()
    if stages == 1:
        lun.read_input1()
        lun.main_add_hst1()
        stages = stages + 1
        with open(STAGE, 'w') as f:
            f.write(str(stages))
    if stages == 2:
        lun.read_input1()
        lun.main_add_hst2()
        stages = stages + 1
        with open(STAGE, 'w') as f:
            f.write(str(stages))
    if stages == 3:
        lun.read_input1()
        lun.main_add_hst3()
        stages = stages + 1
        with open(STAGE, 'w') as f:
            f.write(str(stages))
    if stages == 4:
        lun.read_input1()
        lun.temp_add_hst()
        stages = stages + 1
        with open(STAGE, 'w') as f:
            f.write(str(stages))
    if stages == 5:
        lun.read_input1()
        lun.read_input()
        SYSTEM_NAME = FILE_PATH + SYSTEM_NAME
        SYSTEM_NAME2 = FILE_PATH + SYSTEM_NAME2
        lun.add_luns_host()
        code=lun.post_verification()
        if code ==0:
            if os.path.exists(STAGE):
                os.remove(STAGE)
            if os.path.exists(LUN_I):
                os.remove(LUN_I)
if __name__ == "__main__":
    main()
sys.exit(0)

