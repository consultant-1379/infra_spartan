#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for Unity block configuration
This script will be called from StorageConfiguration.py
This script will be performing the following tasks:
1. Selecting profile and disk group for pool creation
2. Checking whether the Unconfigured drives are sufficient to
   create the pool based on the config type selected by the customer
3. Checking for any previously built Pool named ENIQ and cleaning if it exists
4. Creating a new Pool named ENIQ
5. Checking for any previously built consistency group named CG_ENIQ and
   cleaning it
5. Creating a new consistency group named CG_ENIQ
6. Cleaning previous maindb luns(if any)
7. Creating maindb luns named MainDB[i]
    a. Comparing the size of each maindb lun with the documented
       size
    b. Checking whether the number of maindb luns created are as
       per document
8. Cleaning previous tempdb luns(if any)
9. Creating tempdb luns named TempDB[i]
    a. Comparing the size of each tempdb lun with the documented
       size
    b. Checking whether the number of tempdb luns created are as
       per document
10. Cleaning previous sysmain or ext4 luns(if any)
11. Creating sysmain and ext4 luns named SysMain and Ext4_[i]
    a. Comparing the size of sysmain and ext4 luns with the documented
       size
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
# in the agreement/contract under which the program(s) have been
# supplied.
#
# ******************************************************************************
# Name      : BlockConfiguration.py
# Purpose   : The script will perform block configuration in unity
# ******************************************************************************
"""
Modules used at various
stages in the script
"""
import subprocess
import re
import sys
import os
import getpass
import logging
import signal
import time
"""
Global variables required within
the script at different stages
Some constant messages and commands
which are being used at multiple places
Along with the information regarding
locations of logs and temporary files
which will be used at various stages
in the execution of the script
"""
POOL_NAME = 'ENIQ'
GROUP_NAME = 'CG_ENIQ'
MAINDB_NAME = 'MainDB'
TEMPDB_NAME = 'TempDB'
SYSMAIN = 'SysMain'
PL = "Please wait.."
LUN_TYPE = ['Ext4_CO', 'Ext4_Engine', 'Ext4_RD1', 'Ext4_RD2']
CONFIG = {'E':["29", 21, 7], 'F':["43", 33, 9], 'G':["62", 50, 16]}
SYSTEM_NAME = ''
FILE_PATH = '/opt/ericsson/san/etc/'
LOG_DIR = '/var/ericsson/log/storage/blockconfig_log/'
LOG_NAME = os.path.basename(__file__).replace('.py', '_')+time.strftime("%m_%d_%Y-%H_%M_%S")+'.log'
TMP_FILE = '/var/tmp/tmp.config'
STAGE = '/var/tmp/stagelist'
CMD1 = "uemcli -d {} -noHeader /stor/prov/luns/lun show -filter"
CMD3 = "ID, Name, Size"
CMD2 = "uemcli -noHeader -d {} /stor/prov/luns/lun -id {} delete"
MSG1 = "issue with the CLI/CMD execution and above are the actual ERROR"
MSG2 = 'Created %s: %s'
REGEX = 'sv_[0-9]+'
MSG3 = " Please check and try again.\nExiting the script..."
class LunBlockConfig(object):
    """
    This class will do the unity block configuration
    which will be used durng II stage
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
        self.colors = {'RED' : '\033[91m', 'END' : '\033[00m',
                       'GREEN' : '\033[92m', 'YELLOW' : '\033[93m'}
        self.ip = sys.argv[1]
        self.config_type = sys.argv[2]
        self.pool_id = ''
        self.group_id = ''
        self.disk = ''
        self.ID = ''
    def logging_config(self):
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
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        s_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(LOG_DIR+LOG_NAME)
        s_handler.setLevel(logging.ERROR)
        f_handler.setLevel(logging.WARNING)
        s_format = logging.Formatter('%(message)s')
        f_format = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        self.logging_config1(s_format, f_format, s_handler, f_handler)
    def logging_config1(self, s_format, f_format, s_handler, f_handler):
        """
        Continuation of the custom logger
        function
        Param:
              s_format -> StreamHandler object
              f_format -> FileHandler object
        Return -> None
        """
        s_handler.setFormatter(s_format)
        f_handler.setFormatter(f_format)
        self.logger.addHandler(s_handler)
        self.logger.addHandler(f_handler)
    def log_file_scrn(self, msg, log_dec=0):
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
            self.logger.error(msg)
        else:
            self.logger.warning(msg)
    def print_logging_details(self):
        """
        Print Logging Details with log file for exit,
        completion and start of the script
        Param: None
        Return: None
        """
        colors = self.colors
        hash_print = '-----------------------------------------------------------------------'
        self.log_file_scrn(colors['YELLOW']+hash_print+colors['END'])
        self.log_file_scrn(colors['YELLOW']+\
                            "Please find the script execution logs  ---> "+\
                            LOG_DIR+LOG_NAME+colors['END'])
        self.log_file_scrn(colors['YELLOW']+hash_print+colors['END'])
    def exit_codes(self, code10, msg):
        """
        Script Exit funtion
        Based on the code will print the message in different colors
        param:
               code --> Exit code of the scriot and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        """
        colors = self.colors
        if code10 == 1:
            self.log_file_scrn(colors['RED']+"[ERROR] "+colors['END']+": "+msg)
            self.print_logging_details()
            sys.exit(code10)
        elif code10 == 2:
            self.log_file_scrn(colors['YELLOW']+"[WARN] "+colors['END']+ ":"+msg)
        elif code10 == 3:
            self.log_file_scrn('[' + time.strftime("%d-%b-%y-%H:%M:%S") + '] '
                               + colors['GREEN'] + "[INFO] " + colors['END'] + ": " + msg)
        else:
            self.log_file_scrn(colors['GREEN']+"[INFO] "+colors['END']+": "+msg)
    def input_f(self):
        """
        This function provides the required output to the user
        It will be prnting the number of drives which will be
        required and also the number of maindb and tempdb luns
        which will be created based on the config selected by
        the user
        Args: num -> None
        return: None
        """
        self.exit_codes(0,"Selected Configuration is {}".format(self.config_type))
        self.exit_codes(0,"Number of Disks to be used for"
                           " Dynamic pool creation is {}".format(CONFIG[self.config_type][0]))
        msg1 = "Number of MainDB LUNs under this configuration is {}"
        self.exit_codes(0,msg1.format(CONFIG[self.config_type][1]))
        msg2 = "Number of TempDB LUNs under this configuration is {}\n"
        self.exit_codes(0,msg2.format(CONFIG[self.config_type][2]))
    def read_input(self):
        """
        Takes the required input from the saved file to resume state in case of failure
        Param: None
        Return: None
        """
        global SYSTEM_NAME
        if os.path.exists(TMP_FILE):
            with open(TMP_FILE, 'r') as f:
                out = f.readlines()
                if len(out) == 1:
                    self.pool_id = out[0].split('\n')[0].strip()
                if len(out) > 1:
                    self.pool_id = out[0].split('\n')[0].strip()
                    self.group_id = out[1].split('\n')[0].strip()
        cmd = "uemcli -d {} -noHeader /sys/general show -filter".format(self.ip).split(' ')
        cmd.append("System name")
        system = subprocess.check_output(cmd)
        name  = system.split("=")[-1].strip()
        SYSTEM_NAME = name + "_" + POOL_NAME + "_config"
    def check_diskspace(self):
        """
        This function selects profile and disk group
        for pool creation and calls the function which
        will create the pool
        Param: None
        Return: None
        """
        try:
            cmd1 = 'uemcli -d {} -noHeader /stor/config/dg show -filter'
            cmd1 = cmd1.format(self.ip).split(' ')
            cmd1.append("ID,Drive type,Vendor size,Number of drives,Unconfigured drives")
            msg1 = 'SAS-Flash Validation Done'
            msg2 = 'Invalid Drive type'
            msg3 = "The number of required drives are {}. Currently the unconfigured drives are {}"
            path = "/var/tmp/temp.config"
            self.log_file_scrn('Selecting profile and disk group for pool creation', 1)
            config_type = self.config_type
            cmd2 = 'uemcli -d {} -noHeader /stor/config/profile show'.format(self.ip).split(' ')
            chk_pro=subprocess.check_output(cmd2)
            chk_pro = ''.join(chk_pro)
            chk_pro=[k for k in chk_pro.split('\n') if  len(k)>4]
            p=[]
            for i in chk_pro:
                k=i.translate(None, ' \n\t\r')
                p.append(k)
            c = self.check_diskspace2(p)
            new_chk_pro={}
            for k in c:
               new_chk_p={k.split('=')[0].strip() : k.split('=')[1].strip()}
               new_chk_pro.update(new_chk_p)
            ID=(new_chk_pro["ID"])
            drive_type_pro = (new_chk_pro['Drivetype'])
            chk_disksp=subprocess.check_output(cmd1).split('\n')
            chk_disksp.pop()
            chk_disksp = [k+'\n' for k in chk_disksp]
            b = self.check_diskspace3(chk_disksp)
            for i in range(0,1):
                x=b[i]
                x=x[2:]
                b[0]=x
            chk_disksp={}
            for k in b:
                chk_disk={k.split("=")[0].strip() : k.split("=")[1].strip()}
                chk_disksp.update(chk_disk)
            dri_type='SASFlash'
            if dri_type == drive_type_pro:
                self.log_file_scrn(msg1, 1)
            else:
                self.exit_codes(1, msg2)
            n=int(chk_disksp['Unconfigureddrives'])
            if n<int(CONFIG[config_type][0]):
                if os.path.exists(path):
                    os.remove(path)
                self.exit_codes(1, msg3.format(CONFIG[config_type][0], n))
            self.log_file_scrn('Selected profile and disk group for pool creation', 1)
            self.ID = ID
            self.disk = chk_disksp["ID"]
        except (OSError, subprocess.CalledProcessError) as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG1)
    @staticmethod
    def check_diskspace2(p):
        """
        Continuation of the function which selects
        profile and disk group for pool creation
        Param:
             p -> an iteratable object
        Return:
             c -> an iteratable object
        """
        sas_positon=p.index("Description=SASFlashRAID5(12+1)")
        c = []
        for i in range(sas_positon-2,sas_positon+5):
            z=p[i]
            c.append(z)
        for i in range(0,1):
            x=c[i]
            x=x[2:]
            c[0]=x
        return c
    @staticmethod
    def check_diskspace3(chk_disksp):
        """
        Continuation of the function which selects
        profile and disk group for pool creation
        Param:
             chk_disksp -> an iteratable object
        Return:
             b -> an iteratable object
        """
        x=[]
        for i in chk_disksp:
            m=i.translate(None,' \n\t\r')
            x.append(m)
        b=[]
        for i in range(0,len(x)-1):
            b.append(x[i])
        return b
    def create_pool(self):
        """
        This function creates pool
        and stores the ID of the pool
        if created successsfully
        Param: None
        Return: None
        """
        try:
            self.exit_codes(0,"Creating Dynamic pool")
            sys.stdout.write("Please wait...\n")
            cmd = "uemcli -noHeader -d {} /stor/config/pool create -name {} -descr \"storage-pool\""
            cmd += " -diskGroup {} -drivesNumber {} -storProfile {}"
            cmd = cmd.format(self.ip, POOL_NAME, self.disk, CONFIG[self.config_type][0], self.ID)
            cmd = cmd.split(' ')
            pool = subprocess.check_output(cmd)
            pool_id = re.findall(r'pool_[0-9]+', pool)
            self.pool_id = pool_id[0]
            cmd1 = "uemcli -noHeader -d {} /stor/config/pool show -filter \"ID\"".format(self.ip).split(' ')
            pool2 = subprocess.check_output(cmd1)
            pool_id = re.findall(r'pool_[0-9]+', pool2)
            if self.pool_id not in pool_id:
                msg = 'Dynamic pool is not created successfully'
                self.log_file_scrn(msg)
                self.log_file_scrn("="*50)
                self.exit_codes(1, "Dynamic pool is not created successfully, exiting the script")
            end = '\033[0m'
            underline = '\033[4m'
            line = underline + "Block Configuration\n\n" + end
            with open(SYSTEM_NAME, 'w') as f:
                f.write(line)
                f.write("[Dynamic Pool Information]\n")
                f.write("Name:")
                f.write(POOL_NAME)
                f.write("\nID:")
                f.write(self.pool_id)
            with open(TMP_FILE, 'w') as f:
                f.write(self.pool_id)
                f.write("\n")
            self.exit_codes(0, "Dynamic pool creation is successful.\n")
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG1)
    def cggroup_creation(self):
        """
        This function creates consistency group
        and saves the ID if created successfully
        Param: None
        Return: None
        """
        try:
            self.exit_codes(0,"Creating consistency group")
            cmd = "uemcli -noHeader -d {} /stor/prov/luns/group create -name {} -descr"
            cmd = cmd.format(self.ip, GROUP_NAME).split(' ')
            cmd.append("Consistency group for ENIQ")
            cg_gp = subprocess.check_output(cmd)
            group_id = re.findall(r'res_[0-9]+', cg_gp)
            self.group_id = group_id[0]
            cmd1 = "uemcli -noHeader -d {} /stor/prov/luns/group show -filter \"ID\"".format(self.ip).split(' ')
            cg_gp2 = subprocess.check_output(cmd1)
            group_ids = re.findall(r'res_[0-9]+', cg_gp2)
            if self.group_id not in group_ids:
                msg = 'Consistency Group is not created successfully'
                self.log_file_scrn(msg)
                self.log_file_scrn("="*50)
                self.exit_codes(1, "Consistency Group is not created successfully, exiting the script")
            with open(SYSTEM_NAME, 'a') as f:
                f.write("\n\n")
                f.write("[CG Information]\n")
                f.write("Name:")
                f.write(GROUP_NAME)
                f.write("\nID:")
                f.write(self.group_id)
            with open(TMP_FILE, 'a') as f:
                f.write(self.group_id)
                f.write("\n")
            self.exit_codes(0, "Consistency Group creation is successful.\n")
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG1)
    def create_main(self):
        """
        This function creates Main DB depending on selected config
        and saved the ID if created successfully
        It also checks the number of maindb luns created should be
        as per config type selected and also the size of the main db luns
        created should be as per config type
        Param: None
        Return: None
        """
        try:
            self.exit_codes(0,"Started MainDB LUNs creation...")
            print(PL)
            sp = ["spa", "spb"]
            j = 0
            maindb = []
            num = CONFIG[self.config_type][1]
            cmd = "uemcli -noHeader -d {} /stor/prov/luns/lun create -name {} "
            cmd += "-type primary -thin yes -pool {} -size {} -spOwner {} -group {}"
            for i in range(1, num+1):
                name = MAINDB_NAME + str(i)
                cmd2 = cmd.format(self.ip, name, self.pool_id, '1.2T', sp[j%2], self.group_id)
                cmd2 = cmd2.split(' ')
                lun = subprocess.check_output(cmd2)
                j = j + 1
                lun_id = re.findall(REGEX, lun)
                with open(TMP_FILE, 'a') as f:
                    f.write(lun_id[0])
                    f.write("\n")
                l = [name, lun_id[0]]
                maindb.append(l)
                msg = MSG2%(name, lun_id[0])
                self.log_file_scrn(msg, 1)
                percent = (float(i)/num)*100
                sys.stdout.write('\r{} percent completed'.format(int(percent)))
                sys.stdout.flush()
            msg = '\nSufficient storage is not available to create the MainDB LUNs.'
            msg += MSG3
            if len(maindb) != num:
                self.exit_codes(1,msg)
            cmd2 = CMD1.format(self.ip).split(' ')
            cmd2.append(CMD3)
            output = subprocess.check_output(cmd2).split('\n')
            for i in range(0, len(output)-1, 4):
                for j in range(num):
                    if maindb[j][1] in output[i+0] and str(1319413953536) not in output[i+2]:
                            self.exit_codes(1,msg)
            with open(SYSTEM_NAME, 'a') as f:
                f.write("\n\n[LUN Information]\n[MainDB LUNs]\n")
                for i in range(len(maindb)-1):
                    f.write(maindb[i][0])
                    f.write(",")
                f.write(maindb[len(maindb)-1][0])
                f.write("\n")
                for i in range(len(maindb)-1):
                    f.write(maindb[i][1])
                    f.write(",")
                f.write(maindb[len(maindb)-1][1])
                f.write("\n\n")
            sys.stdout.write('\n')
            self.exit_codes(0, "MainDB LUNs creation is successful.\n")
            return 0
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG1)
    def create_temp(self):
        """
        This function creates Temp DB depending on selected config
        and saved the ID if created successfully
        It also checks the number of tempdb luns created should be
        as per config type selected and also the size of the tempdb luns
        created should be as per config type
        Param: None
        Return: None
        """
        try:
            self.exit_codes(0,"Started TempDB LUNs creation...")
            print(PL)
            sp = ["spa", "spb"]
            j = 0
            tempdb = []
            num = CONFIG[self.config_type][2]
            cmd = "uemcli -noHeader -d {} /stor/prov/luns/lun create -name"
            cmd += " {} -type primary -thin yes -pool {} -size {} -spOwner {}"
            for i in range(1, num+1):
                name = TEMPDB_NAME + str(i)
                cmd1 = cmd.format(self.ip, name, self.pool_id, '530G', sp[j%2])
                cmd1 = cmd1.split(' ')
                lun = subprocess.check_output(cmd1)
                j = j + 1
                lun_id = re.findall(REGEX, lun)
                with open(TMP_FILE, 'a') as f:
                    f.write(lun_id[0])
                    f.write("\n")
                l = [name, lun_id[0]]
                tempdb.append(l)
                msg = MSG2%(name, lun_id[0])
                self.log_file_scrn(msg, 1)
                percent = (float(i)/num)*100
                sys.stdout.write('\r{} percent completed'.format(int(percent)))
                sys.stdout.flush()
            msg = '\nSufficient storage is not available to create the TempDB LUNs.'
            msg += MSG3
            if len(tempdb) != num:
                self.exit_codes(1,msg)
            cmd2 = CMD1.format(self.ip).split(' ')
            cmd2.append(CMD3)
            output = subprocess.check_output(cmd2).split('\n')
            for i in range(0, len(output)-1, 4):
                for j in range(num):
                    if tempdb[j][1] in output[i+0] and str(569083166720) not in output[i+2]:
                            self.exit_codes(1,msg)
            with open(SYSTEM_NAME, 'a') as f:
                f.write("[TempDB LUNs]\n")
                for i in range(len(tempdb)-1):
                    f.write(tempdb[i][0])
                    f.write(": ")
                    f.write(tempdb[i][1])
                    f.write("\n")
                f.write(tempdb[len(tempdb)-1][0])
                f.write(": ")
                f.write(tempdb[len(tempdb)-1][1])
                f.write("\n\n")
            sys.stdout.write('\n')
            self.exit_codes(0, "TempDB LUNs creation is successful.\n")
            return 0
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG1)
    def create_luns(self):
        """
        This Function creates the remaining luns
        and saved the ID if created successfully
        It also checks the number of sysmain and
        ext4 luns created should be as per config
        type selected and also the size of the
        luns created should be as per config type
        created should be as per config type
        Param: None
        Return: None
        """
        try:
            self.exit_codes(0,"Started SysMain and EXT4 LUN creation...")
            print(PL)
            lun_info = {}
            sp = ["spa", "spb"]
            j = 0
            cmd = "uemcli -noHeader -d {} /stor/prov/luns/lun create -name {} "
            cmd += "-type primary -thin yes -pool {} -size {} -spOwner {} -group {}"
            cmd = cmd.format(self.ip, SYSMAIN, self.pool_id, '600G', sp[j%2], self.group_id)
            cmd = cmd.split(' ')
            lun = subprocess.check_output(cmd)
            lun_id = re.findall(REGEX, lun)
            msg = 'Created SysMain: %s'%(lun_id[0])
            self.log_file_scrn(msg, 1)
            with open(TMP_FILE, 'a') as f:
                f.write(lun_id[0])
                f.write("\n")
            lun_info["SysMain"] = lun_id[0]
            cmd2 = CMD1.format(self.ip).split(' ')
            cmd2.append(CMD3)
            output = subprocess.check_output(cmd2).split('\n')
            for i in range(0, len(output)-1, 4):
                if SYSMAIN in output[i+1] and str(644245094400) not in output[i+2]:
                    msg = '\nSufficient storage is not available to create the SysMain LUN.'
                    msg += MSG3
                    self.exit_codes(1, msg)
            self.exit_codes(0, "SysMain LUN creation is successful")
            lun_size = ['400G', '400G', '200G', '200G']
            cmd3 = "uemcli -noHeader -d {} /stor/prov/luns/lun create -name {} -type "
            cmd3 += "primary -thin no -pool {} -size {} -spOwner {}"
            for i in range(4):
                name = LUN_TYPE[i]
                size = lun_size[i]
                cmd4 = cmd3.format(self.ip, name, self.pool_id, size, sp[j%2])
                cmd4 = cmd4.split(' ')
                lun = subprocess.check_output(cmd4)
                j = j + 1
                lun_id = re.findall(REGEX, lun)
                with open(TMP_FILE, 'a') as f:
                    f.write(lun_id[0])
                    f.write("\n")
                lun_info[name] = lun_id[0]
                msg = MSG2%(name, lun_id[0])
                self.log_file_scrn(msg, 1)
                self.exit_codes(0, "{} LUN creation is successful".format(name))
            self.check_extluns()
            with open(SYSTEM_NAME, 'a') as f:
                f.write("[SysMain LUN]\n")
                f.write(SYSMAIN)
                f.write(": ")
                f.write(lun_info["SysMain"])
                f.write("\n\n")
                f.write("[EXT4 LUNs]\n")
                for i in range(3):
                    f.write(LUN_TYPE[i])
                    f.write(": ")
                    f.write(lun_info[LUN_TYPE[i]])
                    f.write("\n")
                f.write(LUN_TYPE[3])
                f.write(": ")
                f.write(lun_info[LUN_TYPE[3]])
                f.write("\n")
            self.log_file_scrn("")
            self.log_file_scrn("*"*65)
            msg = "Please refer to the following file for SAN configuration information - {}"
            self.log_file_scrn(msg.format(SYSTEM_NAME))
            self.log_file_scrn("*"*65)
            sys.stdout.write('\n')
            self.exit_codes(3, "--------------Block Configuration completed Successfully---------------------\n")
            return 0
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG1)
    def check_extluns(self):
        """
        This function checks whether the sizes for Ext luns are correct or not
        This is a continuation of the previous function
        Param: None
        Return: None
        """
        try:
            cmd = CMD1.format(self.ip).split(' ')
            cmd.append(CMD3)
            output = subprocess.check_output(cmd).split('\n')
            for i in range(0, len(output)-1, 4):
                msg = '\nSufficient storage is not available to create the {} LUN. '
                msg += 'Please check and try again.'
                msg += '\nExiting the script...'
                if LUN_TYPE[0] in output[i+1] and str(429496729600) not in output[i+2]:
                    self.exit_codes(1, msg.format(LUN_TYPE[0]))
                if LUN_TYPE[1] in output[i+1] and str(429496729600) not in output[i+2]:
                    self.exit_codes(1, msg.format(LUN_TYPE[1]))
                if LUN_TYPE[2] in output[i+1] and str(214748364800) not in output[i+2]:
                    self.exit_codes(1, msg.format(LUN_TYPE[2]))
                if LUN_TYPE[3] in output[i+1] and str(214748364800) not in output[i+2]:
                    self.exit_codes(1, msg.format(LUN_TYPE[3]))
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG1)
    def cleanup_pool(self):
        """
        This function does pool cleanup in case of failure
        It will checks whether Pool name "ENIQ" is existing
        and will remove it to create a new pool name ENIQ
        Param: None
        Return: None
        """
        try:
            flag = 1
            self.log_file_scrn('Checking for existing Dynamic pool',1)
            cmd = "uemcli -noHeader -d {} /stor/config/pool show -filter \"ID,Name\"".format(self.ip).split(' ')
            out = subprocess.check_output(cmd).split('\n')
            if len(out) == 0:
                self.log_file_scrn('No existing Dynamic pool',1)
                return
            for i in range(0, len(out)-1, 3):
                if POOL_NAME in out[i+1]:
                    flag = 0
                    self.exit_codes(0,'Existing Dynamic pool present, Started cleaning up the Dynamic pool')
                    pool_id = out[i+0].split('=')[-1].strip()
                    cmd1 = 'uemcli -d {} /stor/config/pool -id {} delete'.format(self.ip, pool_id).split(' ')
                    subprocess.check_output(cmd1)
                    self.exit_codes(0,'Cleaned previous existing Dynamic pool')
            if flag == 1:
                self.log_file_scrn('No existing Dynamic pool',1)
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG1)
    def cleanup_consistency_group(self):
        """
        This function does conistency group cleanup in case of failure
        It checks for consistency group named 'CG_ENIQ' and deletes it
        in order to create a new consistency group named CG_ENIQ
        Param: None
        Return: None
        """
        try:
            flag = 1
            self.log_file_scrn('Checking for existing consistency group',1)
            cmd = "uemcli -noHeader -d {} /stor/prov/luns/group show -filter \"ID,Name\"".format(self.ip).split(' ')
            out = subprocess.check_output(cmd).split('\n')
            if len(out) == 0:
                self.log_file_scrn('No existing consistency group',1)
                return
            for i in range(0, len(out)-1, 3):
                if GROUP_NAME in out[i+1]:
                    flag = 0
                    self.exit_codes(0,'Found existing consistency group, started cleaning')
                    cg_id = out[i+0].split('=')[-1].strip()
                    cmd1='uemcli -d {} /stor/prov/luns/group -id {} delete -deleteSnapshots yes'
                    cmd1 = cmd1.format(self.ip, cg_id).split(' ')
                    subprocess.check_output(cmd1)
                    self.exit_codes(0,'Cleaned previous existing consistency Group')
            if flag == 1:
                self.log_file_scrn('No existing consistency group',1)
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG1)
    def cleanup_mainluns(self):
        """
        This function does maindb luns
        cleanup in case of failure
        It will cleanup all the unnecessary luns and will call the
        create main luns function again for
        maindb lun creation
        Param: None
        Return: None
        """
        try:
            flag = 1
            self.log_file_scrn('Checking for existing MainDB LUNs',1)
            with open(TMP_FILE, 'r') as f:
                pool_id = f.readline()
                cg_id = f.readline()
                output = f.readlines()
            cmd = "uemcli -d {} -noHeader /stor/prov/luns/lun show -filter \"ID,Name\"".format(self.ip).split(' ')
            out = subprocess.check_output(cmd).split('\n')
            if len(out) == 0:
                self.log_file_scrn('No existing MainDB LUNs found',1)
                return
            if len(output) != 0:
                self.exit_codes(0,'Found some existing MainDB LUNs, started cleaning')
                flag = 0
            for i in range(0, len(out)-1, 3):
                if MAINDB_NAME in  out[i+1]:
                    for k in range(1, 4):
                        time.sleep(1)
                        sys.stdout.write("\rPlease wait%s" %('.'*k))
                        sys.stdout.flush()
                    sys.stdout.write("\rPlease wait   \n")
                    sys.stdout.flush()
                    main_id = out[i+0].split('=')[-1].strip()
                    cmd2 = CMD2.format(self.ip, main_id).split(' ')
                    subprocess.check_output(cmd2)
            if flag == 1:
                self.log_file_scrn('No existing MainDB LUNs found',1)
            else:
                self.exit_codes(0,'Cleaned up existing MainDB LUNs')
            with open(TMP_FILE, 'w') as f:
                f.write(pool_id)
                f.write(cg_id)
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG1)
    def cleanup_templuns(self):
        """
        This function does tempdb luns
        cleanup in case of failure
        It will clean all the unnecesary
        luns and will run the create
        temp luns function again
        Param: None
        Return: None
        """
        try:
            global CMD2
            flag = 1
            self.log_file_scrn('Checking for existing TempDB LUNs',1)
            maindb = []
            num = CONFIG[self.config_type][1]
            with open(TMP_FILE, 'r') as f:
                pool_id = f.readline()
                cg_id = f.readline()
                for i in range(num):
                    maindb.append(f.readline())
                output = f.readlines()
            cmd = "uemcli -noHeader -d {} /stor/prov/luns/lun -standalone show -filter \"ID,Name\""
            cmd = cmd.format(self.ip).split(' ')
            out = subprocess.check_output(cmd).split('\n')
            if len(out) == 0:
               self.log_file_scrn('No existing TempDB LUNs found',1)
               return
            if len(output) != 0:
                self.exit_codes(0,'Found some existing TempDB LUNs, started cleaning')
                flag = 0
            for i in range(0, len(out)-1, 3):
                if TEMPDB_NAME in  out[i+1]:
                    for k in range(1, 4):
                        time.sleep(1)
                        sys.stdout.write("\rPlease wait%s" %('.'*k))
                        sys.stdout.flush()
                    sys.stdout.write("\rPlease wait   \n")
                    sys.stdout.flush()
                    temp_id = out[i+0].split('=')[-1].strip()
                    cmd2 = CMD2.format(self.ip, temp_id).split(' ')
                    subprocess.check_output(cmd2)
            if flag == 1:
                self.log_file_scrn('No existing TempDB LUNs found',1)
            else:
                self.exit_codes(0,'Cleaned up existing TempDB LUNs')
            with open(TMP_FILE, 'w') as f:
                f.write(pool_id)
                f.write(cg_id)
                for i in range(num):
                    f.write(maindb[i])
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG1)
    def cleanup_otherluns(self):
        """
        This function does sysmain and
        ext luns cleanup in case of failure
        Will cleanup all the unnecessary
         luhns and try to create them again
        Param: None
        Return: None
        """
        try:
            self.log_file_scrn('Checking for existing SysMain and EXT4 LUNs',1)
            flag = 1
            maindb = []
            tempdb = []
            num1 = CONFIG[self.config_type][1]
            num2 = CONFIG[self.config_type][2]
            with open(TMP_FILE, 'r') as f:
                pool_id = f.readline()
                cg_id = f.readline()
                for i in range(num1):
                    maindb.append(f.readline())
                for i in range(num2):
                    tempdb.append(f.readline())
            cmd = "uemcli -noHeader -d {} /stor/prov/luns/lun show -filter \"ID,Name\"".format(self.ip).split(' ')
            out = subprocess.check_output(cmd).split('\n')
            for i in range(0, len(out)-1, 3):
                if SYSMAIN in out[i+1]:
                    flag = 0
                    self.exit_codes(0,'Found existing SysMain LUN, started cleaning')
                    lun_id = out[i+0].split('=')[-1].strip()
                    cmd2 = CMD2.format(self.ip, lun_id).split(' ')
                    subprocess.check_output(cmd2)
                for j in range(4):
                    if LUN_TYPE[j] in out[i+1]:
                        flag = 0
                        self.exit_codes(0,'Found existing {} LUN, started cleaning'.format(LUN_TYPE[j]))
                        lun_id = out[i+0].split('=')[-1].strip()
                        cmd3 = CMD2.format(self.ip, lun_id).split(' ')
                        subprocess.check_output(cmd3)
            if flag == 1:
                self.log_file_scrn('No existing SysMain and EXT4 LUNs found',1)
            else:
                self.exit_codes(0,'Cleaned up existing SysMain and EXT4 LUNs')
            with open(TMP_FILE, 'w') as f:
                f.write(pool_id)
                f.write(cg_id)
                for i in range(num1):
                    f.write(maindb[i])
                for i in range(num2):
                    f.write(tempdb[i])
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG1)
def handler(signum, frame):
    """
    restore the original signal handler
    in raw_input when CTRL+C is pressed will be handled by below
    """
    print("ctrl+c not allowed at this moment")
def stagelist():
    """
    Checks and returns which stage we are currently present at in case of failure
    Args: None
    return:
          int -> representing the current stage of the execution
    """
    stage = 1
    try:
        if os.path.exists(STAGE):
            with open(STAGE, 'r') as f:
                stage = int(f.read())
        return stage
    except Exception:
        return stage
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
    This will be the first function to be called
    when the script will be executed
    args-->none
    parms-->none
    """
    if not os.path.exists(FILE_PATH):
        os.mkdir('/opt/ericsson/san/etc')
    global SYSTEM_NAME
    check_userid()
    block = LunBlockConfig()
    signal.signal(signal.SIGINT, handler)
    block.print_logging_details()
    stage = stagelist()
    if stage == 1:
        block.input_f()
        block.read_input()
        SYSTEM_NAME = FILE_PATH + SYSTEM_NAME
        block.check_diskspace()
        block.cleanup_pool()
        block.create_pool()
        stage = stage + 1
        with open(STAGE, 'w') as f:
            f.write(str(stage))
    if stage == 2:
        block.read_input()
        SYSTEM_NAME = FILE_PATH + SYSTEM_NAME
        block.cleanup_consistency_group()
        block.cggroup_creation()
        stage = stage + 1
        with open(STAGE, 'w') as f:
            f.write(str(stage))
    if stage == 3:
        block.read_input()
        SYSTEM_NAME = FILE_PATH + SYSTEM_NAME
        block.cleanup_mainluns()
        block.create_main()
        stage = stage + 1
        with open(STAGE, 'w') as f:
            f.write(str(stage))
    if stage == 4:
        block.read_input()
        SYSTEM_NAME = FILE_PATH + SYSTEM_NAME
        block.cleanup_templuns()
        block.create_temp()
        stage = stage + 1
        with open(STAGE, 'w') as f:
            f.write(str(stage))
    if stage == 5:
        block.read_input()
        SYSTEM_NAME = FILE_PATH + SYSTEM_NAME
        block.cleanup_otherluns()
        block.create_luns()
        os.remove(TMP_FILE)
        os.remove(STAGE)
if __name__ == "__main__":
    main()
sys.exit(0)
