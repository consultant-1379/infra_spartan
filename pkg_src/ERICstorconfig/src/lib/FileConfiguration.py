#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for Unity file configuration
This script will be performing the following tasks:
1. Checking for any previously built FSN and cleaning it
2. Creating a new FSN
3. Checking for any previously built NAS server with same
   name and cleaning it
4. Creating NAS servers on Pool named as ENIQ
5. Attaching the IP with the NAS
6. Enabling nfs-v3
7. Disabling nfs-v4
8. Post verification checks which include:
    a. Health check for NAS
    b. Connectivity between server and gateway
    c. NFS configuration of NAS
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
# Name      : FileConfiguration.py
# Purpose   : The script will perform file configuration in unity
# ******************************************************************************
"""
The modules used in the script
at various point of stages
"""
import subprocess
import os
import sys
import re
import logging
import time
import signal
"""
Global variables used within the script
"""
FILE_PATH = '/opt/ericsson/san/etc/'
SYSTEM_NAME = ''
LOG_DIR = '/var/ericsson/log/storage/fileconfig_log/'
LOG_NAME = os.path.basename(__file__).replace('.py', '_')+time.strftime("%m_%d_%Y-%H_%M_%S")+'.log'
NAS_NAME = ["NASa1", "NASb1"]
POOL_NAME = 'ENIQ'
TMP_FILE = '/var/tmp/tmp_1.config'
STAGE = '/var/tmp/stagelist_1'
MSG = "issue with the CLI/CMD execution and above are the actual ERROR"
class LunFileConfig(object):
    """
    This class will do the unity file configuration
    """
    def __init__(self):
        """
        Init for variable initialisation
        and starting the logging object
        Param: None
        Return: None
        """
        self.logger = logging.getLogger()
        self.logging_config()
        self.colors = {'RED' : '\033[91m', 'END' : '\033[00m',
                       'GREEN' : '\033[92m', 'YELLOW' : '\033[93m'}
        self.ip = sys.argv[1]
        self.nas_ip = []
        self.nas_ip.append(sys.argv[2])
        self.nas_ip.append(sys.argv[3])
        self.netmask = sys.argv[4]
        self.gateway_ip = sys.argv[5]
        self.ports = []
        self.nas_id = []
        self.fsn_ids = []
        self.ip_id = []
    def logging_config(self):
        """
        Creating a custom logger for logs
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
    def log_file_scrn(self, msg, log_dec=0):
        """
        Logging into file and screen
        based on the value of log_dec
        Param: msg -> actual message
               log_dec -> int
        Return: None
        """
        if log_dec == 0:
            self.logger.error(msg)
        else:
            self.logger.warning(msg)
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
    def print_logging_details(self):
        """
        Prints logging details with log file for exit,
        completion and start of the script
        Param: None
        Return: None
        """
        colors = self.colors
        hash_print = '-------------------------------------------------------------------------'
        self.log_file_scrn(colors['YELLOW']+hash_print+colors['END'])
        self.log_file_scrn(colors['YELLOW']+\
                            "Please find the script execution logs  ---> "+\
                            LOG_DIR+LOG_NAME+colors['END'])
        self.log_file_scrn(colors['YELLOW']+hash_print+colors['END'])
    def exit_codes(self, code12, msg):
        """
        Script Exit funtion
        Will be printing exit messages with different colors
        based on the input code
        param: code --> Exit code of the scriot and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        """
        colors = self.colors
        if code12 == 1:
            self.log_file_scrn(colors['RED']+"[ERROR] "+colors['END']+": "+msg)
            self.print_logging_details()
            sys.exit(code12)
        elif code12 == 2:
            self.log_file_scrn(colors['YELLOW']+"[WARN] "+colors['END']+ ":"+msg)
        elif code12 == 3:
            self.log_file_scrn('[' + time.strftime("%d-%b-%y-%H:%M:%S") + '] '
                               + colors['GREEN'] + "[INFO] " + colors['END'] + ": " + msg)
        else:
            self.log_file_scrn(colors['GREEN']+"[INFO] "+colors['END']+": "+msg)
    def read_input(self):
        """
        Takes the required input from a temporary file to resume in case of failure
        Args: None
        return: None
        """
        global SYSTEM_NAME
        if os.path.exists(TMP_FILE):
            with open(TMP_FILE, 'r') as f:
                out = f.readlines()
                if len(out) == 2:
                    self.fsn_ids.append(out[0].split('\n')[0].strip())
                    self.fsn_ids.append(out[1].split('\n')[0].strip())
                if len(out) > 2:
                    self.fsn_ids.append(out[0].split('\n')[0].strip())
                    self.fsn_ids.append(out[1].split('\n')[0].strip())
                    self.nas_id.append(out[2].split('\n')[0].strip())
                    self.nas_id.append(out[3].split('\n')[0].strip())
        cmd = "uemcli -d {} -noHeader /sys/general show -filter".format(self.ip).split(' ')
        cmd.append("System name")
        system = subprocess.check_output(cmd)
        name = system.split("=")[-1].strip()
        SYSTEM_NAME = name + "_" + POOL_NAME + "_config"
    def config(self):
        """
        This function lists ethernet ports and filter out ports for FSN
        Param: None
        return: None
        """
        try:
            self.exit_codes(0,"Configuring FSN")
            cmd1 = "uemcli -noHeader -d {} /net/port/eth show -filter".format(self.ip).split(' ')
            cmd1.append("ID,Speed,Health state")
            output = subprocess.check_output(cmd1).split(":")
            result = []
            a = []
            b = []
            for i in range(1,len(output)-1):
                l = output[i].split("\n")
                l.pop()
                result.append(l)
            l = output[len(output)-1].split("\n")
            result.append(l)
            for i in range(0, len(result)-1):
                result[i].pop()
            for i in result:
                if "spa_ocp_0_eth" in i[0] and "OK" in i[2]:
                    speed = i[1].split("=")[-1].strip()
                    if len(speed) != 0:
                        a.append(i[0].split("=")[-1].strip())
                elif "spb_ocp_0_eth" in i[0] and "OK" in i[2]:
                    speed = i[1].split("=")[-1].strip()
                    if len(speed) != 0:
                        b.append(i[0].split("=")[-1].strip())
            self.port_select(a, b)
            cmd2="uemcli -noHeader -d {} /net/fsn create -primaryPort {} -secondaryPorts {}"
            cmd2=cmd2.format(self.ip,self.ports[0],self.ports[1])
            cmd2 = cmd2.split(' ')
            fsn = subprocess.check_output(cmd2).split("\n")
            self.fsn_ids.append(fsn[0].split('=')[-1].strip())
            self.fsn_ids.append(fsn[1].split('=')[-1].strip())
            with open(TMP_FILE, 'w') as f:
                f.write(self.fsn_ids[0])
                f.write("\n")
                f.write(self.fsn_ids[1])
                f.write("\n")
            self.exit_codes(0, "FSN Configuration is successful.\n")
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG)
    def port_select(self, a, b):
        """
        This function lists ethernet ports and filter out ports for FSN
        This is a continuation of the above function
        Based on the length of a and b will call
        particular function to get the ethernet port
        to build FSN upon
        Param: a -> Ethernet ports on side A
               b -> Ethernet ports on side B
        Return: None
        """
        if len(a) == 2 and len(b) == 2:
            self.port_select2(a, b)
        elif len(a) == 2 and len(b) != 2:
            self.port_select1(b, a)
        elif len(a) != 2 and len(b) == 2:
            self.port_select1(a, b)
        else:
            msg = "No healthy ports are available for FSN creation!!!\nExiting"
            self.exit_codes(1, msg)
    def port_select2(self, a, b):
        """
        This function lists ethernet ports and filter out ports for FSN
        This is a continuation of the above function
        Param: a -> Ethernet ports on side A
               b -> Ethernet ports on side B
        Return: None
        """
        flag = 0
        msg = "Cabling is wrongly done, please correct it and run the script again!!!\nExiting"
        for i in range(2):
            text = a[i].split('_')[-1]
            for j in range(2):
                if text in b[j]:
                    flag = 1
            if flag == 0:
                self.exit_codes(1, msg)
            flag = 0
        self.ports.append(a[0])
        self.ports.append(a[1])
    def port_select1(self, a, b):
        """
        This function lists ethernet ports and filter out ports for FSN
        This is a continuation of above function
        Param: a -> Ethernet ports on side A
               b -> Ethernet ports on side B
        Return: None
        """
        flag = 0
        msg = "Cabling is wrongly done, please correct it and run the script again!!!\nExiting"
        if len(a) == 1:
            self.exit_codes(1, msg)
        else:
            for i in range(2):
                text = b[i].split('_')[-1]
                for j in a:
                    if text in j:
                        flag = 1
            if flag == 0:
                self.exit_codes(1, msg)
            flag = 0
        self.ports.append(b[0])
        self.ports.append(b[1])
    def nas_creation(self):
        """
        This function create nas servers and will attach nas ip's to the NAS servers
        Param: None
        Return: None
        """
        try:
            self.exit_codes(0,"Creating NAS servers and configuring IP for NAS servers")
            pool_id = ""
            sp = ["spa", "spb"]
            if os.path.exists(SYSTEM_NAME):
                with open(SYSTEM_NAME, 'r') as f:
                    for i in range(5):
                        f.readline()
                    pool_id = f.readline().split(':')[-1].strip()
            if len(pool_id) == 0:
                cmd1 = "uemcli -noHeader -d {} /stor/config/pool show -filter \"ID,Name\"".format(self.ip).split(' ')
                out = subprocess.check_output(cmd1).split('\n')
                if len(out) == 0:
                    self.exit_codes(1, "Pool is not created!!")
                for i in range(0, len(out)-1, 3):
                    if POOL_NAME in out[i+1]:
                        pool_id = out[i+0].split('=')[-1].strip()
            print("Please wait...")
            for i in range(2):
                for k in range(1, 4):
                    k=k+1
                    k=k-1
                    time.sleep(1)
                cmd2="uemcli -noHeader -d {} /net/nas/server create -name {} -sp {} -pool {}"
                cmd2=cmd2.format(self.ip,NAS_NAME[i],sp[i],pool_id).split(' ')
                nas = subprocess.check_output(cmd2)
                nas_id = re.findall(r'nas_[0-9]+', nas)
                self.nas_id.append(nas_id[0])
                cmd3="/usr/bin/uemcli -noHeader -d {} /net/nas/if create -server "
                cmd3 += "{} -port {} -addr {} -netmask {} -gateway {}"
                cmd3=cmd3.format(self.ip,self.nas_id[i],self.fsn_ids[i],self.nas_ip[i],self.netmask,self.gateway_ip)
                cmd3 = cmd3.split(' ')
                out = subprocess.check_output(cmd3).split('\n')
                ip_id = out[0].split('=')[-1].strip()
                self.ip_id.append(ip_id)
                percent = (float(i+1)/2)*100
                sys.stdout.write("\r{} percent completed".format(int(percent)))
                sys.stdout.flush()
            sys.stdout.write("\n")
            self.exit_codes(0, "NAS Server creation and IP configuration for NAS servers is successful.\n")
            end = '\033[0m'
            underline = '\033[4m'
            line = underline + "\nFile Configuration\n" + end
            with open(SYSTEM_NAME, 'a') as f:
                f.write(line)
                f.write("\n[NAS A]")
                f.write("\n    IP Address: ")
                f.write(self.nas_ip[0])
                f.write("\n    ID: ")
                f.write(self.nas_id[0])
                f.write("\n[NAS B]")
                f.write("\n    IP Address: ")
                f.write(self.nas_ip[1])
                f.write("\n    ID: ")
                f.write(self.nas_id[1])
                f.write("\n")
            with open(TMP_FILE, 'a') as f:
                f.write(self.nas_id[0])
                f.write("\n")
                f.write(self.nas_id[1])
                f.write("\n")
                f.write(self.ip_id[0])
                f.write("\n")
                f.write(self.ip_id[1])
                f.write("\n")
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG)
    def post_verification(self):
        """
        This function does the post verification checks
        Param: None
        Return: None
        """
        try:
            self.exit_codes(0,"Started post verification")
            with open(TMP_FILE, 'r') as f:
                f.readline()
                f.readline()
                f.readline()
                f.readline()
                self.ip_id.append(f.readline().strip())
                self.ip_id.append(f.readline().strip())
            cmd1 = "/usr/bin/uemcli -noHeader -d {} /net/nas/if show".format(self.ip).split(' ')
            out = subprocess.check_output(cmd1).split(':')
            nas_server = []
            result = []
            for i in range(1,len(out)-1):
                l = out[i].split("\n")
                result.append(l)
            l = out[len(out)-1].split("\n")
            result.append(l)
            for i in range(len(result)):
                result[i].pop()
                result[i].pop()
                server =  result[i][1].split("=")[-1].strip()
                if server in self.nas_id and 'OK' not in result[i][-1]:
                    self.exit_codes(1, "Health is not ok\n")
                nas_server.append(server)
            cmd2="uemcli -noHeader -d {} /net/util ping -srcIf {} -addr {}"
            cmd2 = cmd2.format(self.ip,self.ip_id[0],self.gateway_ip).split(' ')
            out = subprocess.check_output(cmd2)
            if "successful" not in out:
                self.exit_codes(1, "Connectivity between server and gateway is not verified!!!\n")
            ip = result[0][4].split('=')[-1].strip()
            code = subprocess.call(["ping", ip, "-c", "2"], stdout=subprocess.PIPE)
            if code:
                self.exit_codes(1,"Server unreachable\n")
            cmd3 = "uemcli -noHeader -d {} /net/util ping -srcIf {} -addr {}"
            cmd3 = cmd3.format(self.ip, self.ip_id[1], self.gateway_ip).split(' ')
            out = subprocess.check_output(cmd3)
            if "successful" not in out:
                self.exit_codes(1, "Connectivity between server and gateway is not verified!!!\n")
            ip = result[1][4].split('=')[-1].strip()
            code = subprocess.call(["ping", ip, "-c", "2"], stdout=subprocess.PIPE)
            if code:
                self.exit_codes(1,"Server unreachable\n")
            self.nfsconfig_post(nas_server)
            self.exit_codes(0, "Post validation completed successfully.\n")
            self.log_file_scrn("*"*65)
            msg = "Please refer to the following file for SAN configuration information - {}"
            self.log_file_scrn(msg.format(SYSTEM_NAME))
            self.log_file_scrn("*"*65)
            sys.stdout.write('\n')
            self.exit_codes(3, "-------------File Configuration completed Successfully---------------------\n")
            return 0
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG)
            self.exit_codes(2, "issue with the CLI/CMD execution")
    def nfsconfig_post(self, nas_server):
        """
        This function does the post verification checks
        This is the continuation of above function
        Param: nas_server -> List containing NAS server information
        Return: None
        """
        try:
            for i in range(len(nas_server)):
                cmd = "/usr/bin/uemcli -noHeader -d {} /net/nas/nfs -server {} show"
                cmd = cmd.format(self.ip, nas_server[i]).split(' ')
                out = subprocess.check_output(cmd).split('\n')
                nfs_server = {}
                out.pop()
                out.pop()
                for j in out:
                    nfs_server[j.split('=')[0].strip()] = j.split('=')[1].strip()
                var1 = nfs_server['NFSv3 enabled']
                var2 = nfs_server['NFSv4 enabled']
                var3 = nfs_server['Secure NFS enabled']
                if var1!='yes' or var2!='no' or var3!='no':
                    msg = '"There is some issue with nfs configuraton of NAS ID: {}'
                    self.exit_codes(1,msg.format(nfs_server['NAS server']))
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG)
            self.exit_codes(2, "issue with the CLI/CMD execution")
    def cleanup_fsn(self):
        """
        Cleanup of fsn in case of failure
        Param: None
        Return: None
        """
        try:
            self.log_file_scrn('Checking for existing FSN',1)
            cmd1 = 'uemcli -d {} -noHeader /net/fsn show'.format(self.ip).split(' ')
            fsn_list = subprocess.check_output(cmd1).split('\n')
            if len(fsn_list) == 1:
                self.log_file_scrn('No existing FSN found',1)
                return
            self.exit_codes(0,'Found existing FSN, started cleaning')
            fsn_id = fsn_list[0].split('=')[-1].strip()
            cmd2 = "uemcli -d {} /net/fsn -id {} delete".format(self.ip, fsn_id).split(' ')
            subprocess.check_output(cmd2)
            self.exit_codes(0,'Cleaned existing FSN')
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG)
    def cleanup_nas(self):
        """
        Cleanup of nas in case of failure
        Param: None
        Return: None
        """
        try:
            flag = 1
            self.log_file_scrn('Checking for existing NAS Servers',1)
            cmd1 = "uemcli -noHeader -d {} /stor/config/pool show -filter \"ID,Name\"".format(self.ip).split(' ')
            out = subprocess.check_output(cmd1).split('\n')
            if len(out) == 0:
                self.exit_codes(1, "Pool is not created!!")
            for i in range(0, len(out)-1, 3):
                if POOL_NAME in out[i+1]:
                    pool_id = out[i+0].split('=')[-1].strip()
            cmd2 = "uemcli -noHeader -d {} /net/nas/server show -filter".format(self.ip).split(' ')
            cmd2.append("ID,Name,Storage pool")
            nas_details = subprocess.check_output(cmd2).split('\n')
            for i in range(0, len(nas_details)-1, 4):
                if pool_id in nas_details[i+2] and NAS_NAME[0] in nas_details[i+1]:
                    flag = 0
                    self.exit_codes(0,'Found existing NAS Server with name {}, started cleaning'.format(NAS_NAME[0]))
                    nasid = nas_details[i+0].split('=')[-1].strip()
                    cmd3 = "uemcli -noHeader -d {} /net/nas/server -id {} delete".format(self.ip, nasid).split(' ')
                    subprocess.check_output(cmd3)
                elif pool_id in nas_details[i+2] and NAS_NAME[1] in nas_details[i+1]:
                    flag = 0
                    self.exit_codes(0,'Found existing NAS Server with name {}, started cleaning'.format(NAS_NAME[1]))
                    nasid = nas_details[i+0].split('=')[-1].strip()
                    cmd4 = "uemcli -noHeader -d {} /net/nas/server -id {} delete".format(self.ip, nasid).split(' ')
                    subprocess.check_output(cmd4)
            if flag == 1:
                self.log_file_scrn('No existing NAS Server found',1)
            if flag == 0:
                self.exit_codes(0,'Successfully removed existing nas server')
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*65)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*65)
            self.exit_codes(1, MSG)
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
def stagelist():
    """
    Checks and returns which stage we are
    currently present at in case of failure
    Args: None
    return: int
    """
    stage = 1
    try:
        if os.path.exists(STAGE):
            with open(STAGE, 'r') as f:
                stage = int(f.read())
        return stage
    except Exception:
        return stage
def main():
    """
    Main Function to wrap all the functions
    This will the first function to be called
    and in turn will call the rest of the
    functions
    Param: None
    Return: None
    """
    global SYSTEM_NAME
    check_userid()
    file = LunFileConfig()
    signal.signal(signal.SIGINT, handler)
    file.print_logging_details()
    stage = stagelist()
    if stage == 1:
        file.read_input()
        SYSTEM_NAME = FILE_PATH + SYSTEM_NAME
        file.cleanup_fsn()
        file.config()
        stage = stage + 1
        with open(STAGE, 'w') as f:
            f.write(str(stage))
    if stage == 2:
        file.read_input()
        SYSTEM_NAME = FILE_PATH + SYSTEM_NAME
        file.cleanup_nas()
        file.nas_creation()
        stage = stage + 1
        with open(STAGE, 'w') as f:
            f.write(str(stage))
    if stage == 3:
        file.read_input()
        SYSTEM_NAME = FILE_PATH + SYSTEM_NAME
        file.post_verification()
        os.remove(TMP_FILE)
        os.remove(STAGE)
if __name__ == "__main__":
    main()
sys.exit(0)

