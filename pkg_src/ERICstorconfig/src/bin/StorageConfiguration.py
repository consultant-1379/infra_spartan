#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script for Unity XT file and block configuration"""
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
# Name      : StorageConfiguration.py
# Purpose   : The script will wrap  block, file configuration and Storage Expansion in unity XT
# ******************************************************************************

import subprocess
import re
import sys
import os
import getpass
import optparse
import time
import logging
import signal

TMP_FILE="/var/tmp/temp.config"
TEMP1="/var/tmp/stagelist.txt"
LOG_DIR = '/var/ericsson/log/storage/'
LOG_NAME = os.path.basename(__file__).replace('.py', '_')+time.strftime("%m_%d_%Y-%H_%M_%S")+'.log'
POOL_NAME = 'ENIQ_POOL'
EXP = r'^\s*(?:[0-9]{1,3}\.){3}[0-9]{1,3}\s*$'
IP_USR=''
PATH1='/opt/emc/uemcli/bin/'
PATH2='/opt/dellemc/uemcli/bin/'

class stor_config(object):
    """
    this class will do the input validation
    """
    def __init__(self):
        """
        Init for variable initialization
        colors --> to print colors
        logging --> for capturing logs
        args --> no args
        return --> none
        """
        self.logger = logging.getLogger()
        self.logging_config()
        self.colors = {'RED' : '\033[91m', 'END' : '\033[00m',
                       'GREEN' : '\033[92m', 'YELLOW' : '\033[93m'}
        self.ip = ""
        self.uname = ""
        self.password = ""
        self.nas_ip = []
        self.netmask = ''
        self.gateway_ip = ''
        self.config_type=""
        self.code1=""
        self.code2=""
        self.usr_input=""
        self.lunconfig_type=""
        self.path=''

    def logging_config(self):
        """
        Creating a custom logger for logs
        ERROR --> to display error message
        WARNING --> to display Warning message
        args --> no args
        return --> none
        """
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        s_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(LOG_DIR+LOG_NAME)
        s_handler.setLevel(logging.ERROR)
        f_handler.setLevel(logging.WARNING)
        s_format = logging.Formatter('%(message)s')
        f_format = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_handler.setFormatter(s_format)
        f_handler.setFormatter(f_format)
        self.logger.addHandler(s_handler)
        self.logger.addHandler(f_handler)

    def log_file_scrn(self, msg, log_dec=0):
        """
        Logging into file and screen
        args -->msg
        args     --log_dec
        msg --> to display message
        log_dec -- >log code
        return --> none
        """
        if log_dec == 0:
            self.logger.error(msg)
        else:
            self.logger.warning(msg)

    def print_logging_details(self):
        """
        Prints logging details with log file for exit,
        completion and start of the script
        colors --> colors print for logs
        return --> none
        """
        colors = self.colors
        hash_print = '--------------------------------------------------------------------'
        self.log_file_scrn(colors['YELLOW']+hash_print+colors['END'])
        msg="Please find the script execution logs  ---> "
        self.log_file_scrn(colors['YELLOW']+msg+LOG_DIR+LOG_NAME+colors['END'])
        self.log_file_scrn(colors['YELLOW']+hash_print+colors['END'])

    def exit_codes(self, code, msg):
        """
        Script Exit function
        param: code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        colors -- >to print colors
        """
        colors = self.colors
        if code == 1:
            self.log_file_scrn(colors['RED']+"[ERROR] "+colors['END']+": "+msg)
            self.print_logging_details()
            sys.exit(code)
        elif code == 2:
            self.log_file_scrn(colors['YELLOW']+"[WARN] "+colors['END']+ ":"+msg)
        elif code == 3:
            self.log_file_scrn(colors['YELLOW']+"[WARN] "+colors['END']+ ":"+msg)
        elif code == 4:
            self.log_file_scrn(colors['RED']+"[ATTENTION] "+colors['END']+": "+msg)
        elif code ==5:
            self.log_file_scrn(colors['RED']+"[ERROR] "+colors['END']+": "+msg)
        elif code ==6:
            self.log_file_scrn('['+time.strftime("%d-%b-%y-%H:%M:%S")+'] '
                               +colors['GREEN']+"[INFO] "+colors['END']+": "+msg)
        else:
            self.log_file_scrn(colors['GREEN'] + "[INFO] " + colors['END'] + ": " + msg)

    def verify_uemcli(self):
        """
        This function verifies whether uemcli is installed or not
        return --> none
        args --> none
        """
        msg = "uemcli is not installed\n Please install and try again"
        msg1 = "uemcli is installed\n"
        try:
            val="find {} -type f -name setlevel.sh".format(PATH2)
            value = val.split(' ')
            file1 = subprocess.check_output(value)
            if file1:
                self.path = PATH2
                self.log_file_scrn(msg1,1)
        except Exception:
            try:
                val = "find {} -type f -name setlevel.sh".format(PATH1)
                value = val.split(' ')
                file2 = subprocess.check_output(value)
                if file2:
                    self.path = PATH1
                    self.log_file_scrn(msg1,1)
                else:
                    self.log_file_scrn("="*50)
                    self.exit_codes(1, msg)
            except Exception:
                self.log_file_scrn("="*50)
                self.exit_codes(1, msg)
    def unity_check(self):
        """
        This function will allow script to execute only on Unity XT server
        Model -- > Unity Model
        return --> none
        args --> none
        """
        unity_id=''
        cmd="uemcli -d {} -noHeader /sys/general show -filter Model".format(self.ip).split(' ')
        unity_id= subprocess.check_output(cmd)
        unity_id =unity_id.split(":")
        unity_id.pop(0)
        new_unity_id ={k.split('=')[0].strip() :k.split('=')[1].strip() for k in unity_id}
        unity_id=new_unity_id["Model"]
        if unity_id == 'Unity 480F':
            """
            No action required
            """
            pass
        else:
            os.remove(TMP_FILE)
            msg = "Requested Configuration can be performed only on Unity XT "
            self.log_file_scrn("="*50)
            self.exit_codes(1, msg)

    def input_ip(self, num):
        """
        Function to check the server reachability
        function will validate server ip provided by user
        Args: num -> int
        return: None
        """
        while True:
            self.ip = raw_input("Enter the Unity IP Address: ")
            if not re.search(r'^\s*(?:[0-9]{1,3}\.){3}[0-9]{1,3}\s*$', self.ip):
                self.exit_codes(2, "Invalid IP Address Entered, try again\n")
            else:
                break
        code =  subprocess.call(["ping", self.ip, "-c", "2"], stdout=subprocess.PIPE)
        if code!=0:
            sys.stdout.write("Server unreachable\nTry again\n")
            sys.stdout.flush()
            if num == 3:
                msg = "\nServer Unreachable\nExiting the script"
                self.log_file_scrn("="*50)
                self.exit_codes(1, msg)
            self.input_ip(num+1)

    def input_f(self, flag=0, num=1):
        """
        This function takes the required input from the user
        uname --> user name
        password --> password from user
        this function will save user to system
        Args: num -> int
        return: None
        """
        if flag == 0:
            try:
                cmd11="uemcli -d {} -noHeader /sys/general show -filter".format(self.ip).split(' ')
                cmd11.append("System name")
                subprocess.check_output(cmd11)
                with open(TMP_FILE, 'w') as f:
                    f.write(str(self.ip))
                    f.write("\n")
            except subprocess.CalledProcessError:
                flag=flag+1
                self.input_f(flag,1)
        else :
            self.uname = raw_input("Enter Username: ")
            self.password = getpass.getpass("Enter Password: ")
            try:
                cmd4="uemcli -d {} -u {} -p {} -noHeader /sys/general show -filter"
                cmd12=cmd4.format(self.ip, self.uname, self.password).split(' ')
                cmd12.append("System name")
                val="{}setlevel.sh l".format(self.path)
                cmd13=val.split(' ')
                subprocess.call(cmd13, stdout=subprocess.PIPE)
                subprocess.check_output(cmd12)
                cmd10 = "uemcli -d {} -u {} -p {} -saveUser".format(self.ip, self.uname, self.password).split(' ')
                subprocess.call(cmd10, stdout=subprocess.PIPE)
                with open(TMP_FILE, 'w') as f:
                    f.write(str(self.ip))
                    f.write("\n")
            except subprocess.CalledProcessError:
                self.exit_codes(2, "Username or Password incorrect. Please try again...\n\n")
                if num == 4:
                    self.exit_codes(1, "Exceeded attempts to retry!\nExiting...")
                self.input_f(1,num+1)

    def input_conf(self):
        """
        This function will take configuration type from user
        conf_types --> supported configuration types2
        return --> none
        args --> none
        """
        self.config_type = raw_input("Enter the Configuration type (E/F/G): ")
        conf_types=['E','F','G']
        if self.config_type in conf_types:
            with open(TMP_FILE, 'a') as f:
                f.write(str(self.config_type))
                f.write("\n")
        else:
            msg = "Entered Configuration Type is incorrect!!!. Enter Configuration Type again..."
            self.log_file_scrn("="*50)
            self.exit_codes(3,msg)
            self.input_conf()

    def input_f1(self):
        """
        This function will take nas ip from user
        This function will perform nas ip validation
        args --> none
        return --> none
        """
        self.nas_ip = []
        nas_ip=self.input_f11()
        self.nas_ip.append(nas_ip)
        nas_ip=self.input_f12()
        self.nas_ip.append(nas_ip)
        if self.nas_ip[0]==self.nas_ip[1]:
            msg="Entered NAS1 IP and NAS2 IP are same. Enter NAS1 IP and NAS2 IP again.."
            self.log_file_scrn("="*50)
            self.exit_codes(3,msg)
            self.input_f1()
        else:
            with open(TMP_FILE, 'a') as f:
                f.write(self.nas_ip[0])
                f.write("\n")
                f.write(self.nas_ip[1])
                f.write("\n")

    def input_f12(self):
        """
        This function will take nas ip2 from user
        validation of nas ip will be done in this function
        This function will also checks nas ip reachability weather it is in use or not
        return --> nas_ip2
        """
        while True:
            nas_ip = raw_input("Enter NAS2 IP Address: ")
            if not re.search(EXP,nas_ip):
                msg="Entered  NAS1 IP is incorrect!. Enter NAS2 IP again.."
                self.log_file_scrn("="*50)
                self.exit_codes(3,msg)
            else:
                break
        value=["ping", nas_ip, "-c", "2"]
        code =  subprocess.call(value, stdout=subprocess.PIPE)
        if code!=1:
            msg="Entered  NAS2 IP Address is in use!. Enter NAS2 IP Address again.."
            self.log_file_scrn("="*50)
            self.exit_codes(3,msg)
            nas_ip=self.input_f12()
        return nas_ip

    def input_f11(self):
        """
        This function will take nas ip1 from user
        validation of nas ip will be done in this function
        This function will also checks nas ip reachability weather it is in use or not
        return --> nas_ip1
        """
        while True:
            nas_ip = raw_input("Enter NAS1 IP Address: ")
            if not re.search(EXP,nas_ip):
                msg="Entered  NAS1 IP Address is incorrect!. Enter NAS1 IP Address again.."
                self.log_file_scrn("="*50)
                self.exit_codes(3,msg)
            else:
                break
        value=["ping", nas_ip, "-c", "2"]
        code =  subprocess.call(value, stdout=subprocess.PIPE)
        if code!=1:
            msg="Entered NAS1 IP Address is in use!. Enter NAS1 IP Address again.."
            self.log_file_scrn("="*50)
            self.exit_codes(3,msg)
            nas_ip=self.input_f11()
        return nas_ip

    def input_f2(self):
        """
        This function will take netmask address from user
        This function will validate netmask address
        return --> none
        """
        self.netmask = ""
        self.netmask = raw_input("Enter NAS Server Netmask: ")
        if not re.search(EXP,self.netmask):
            msg="Entered incorrect Netmask !. Enter Netmask again.."
            self.log_file_scrn("="*50)
            self.exit_codes(3,msg)
            self.input_f2()
        else:
            with open(TMP_FILE, 'a') as f:
                f.write(str(self.netmask))
                f.write("\n")

    def input_f3(self):
        """
        This function will take gateway IP from user
        This function will validate gateway Ip
        return --> none
        """
        self.gateway_ip = ""
        self.gateway_ip = raw_input("Enter NAS Server Gateway: ")
        if not re.search(EXP,self.gateway_ip):
            msg="Entered incorrect Gateway !. Enter Gateway again.."
            self.log_file_scrn("="*50)
            self.exit_codes(3,msg)
            self.input_f3()
        else:
            with open(TMP_FILE, 'a') as f:
                f.write(str(self.gateway_ip))
                f.write("\n")

    def input_f4(self):
        """
        this function will do input validation of file configuration
        validations done as nas ips belongs to same subnet or not
        return --> none
        This function will provide rerun support if user entered wrong inputs
        """
        anded1 =list()
        anded2 =list()
        anded3 =list()
        with open(TMP_FILE, 'r') as f:
            out=f.readlines()
        if len(out)==6:
            nas_ip1=out[2].strip()
            nas_ip2=out[3].strip()
            netmask=out[4].strip()
            gateway_ip=out[5].strip()
        for ip, m in zip(str(gateway_ip).rsplit('.'),str(netmask).rsplit('.')):
            anded1.append(str(int(ip) & int(m)))
        subnet1 = '.'.join(anded1)
        for ip, m in zip(str(nas_ip1).rsplit('.'),str(netmask).rsplit('.')):
            anded2.append(str(int(ip) & int(m)))
        subnet2 = '.'.join(anded2)
        for ip, m in zip(str(nas_ip2).rsplit('.'),str(netmask).rsplit('.')):
            anded3.append(str(int(ip) & int(m)))
        subnet3 = '.'.join(anded3)
        if subnet1 == subnet2 == subnet3:
            """
            No action required
            """
            pass
        else:
            msg = "Entered inputs does not belong to same Subnet. Enter inputs again"
            self.log_file_scrn("="*50)
            self.exit_codes(3,msg)
            with open(TMP_FILE,'w') as f:
                f.write(str(self.ip))
                f.write("\n")
            if IP_USR=='--file':
                self.fl_fn()
            else:
                with open(TMP_FILE,'a') as f:
                    f.write(str(self.gateway_ip))
                    f.write("\n")
                self.fl_fn()
    def fl_fn(self):
        """
        This function will perform input collection
        inputs includes nas ip's netmask and gatewayip
        return --> none
        """
        self.input_f1()
        self.input_f2()
        self.input_f3()
        self.input_f4()

    def input_f5(self):
        """
        This function will take confirmation from user to proceed with the inputs given by user
        yes --> to proceed forward
        no --> to retake the inputs from user
        quit --> to abort the script
        return --> none
        displays user inputs on console
        """
        print('')
        print("Please find the provided inputs:")
        with open(TMP_FILE, 'r') as f:
            out=f.readlines()
        msg1="Is the above inputs correct <yes/no/quit>: "
        msg2="Enter the required inputs again: "
        msg3="Entered  input  is incorrect!. Enter input among <yes/no/quit> try again.."
        ip2=out[0].strip()
        config_type1=out[1].strip()
        nas_ip11=out[2].strip()
        nas_ip22=out[3].strip()
        netmask=out[4].strip()
        gateway_ip1=out[5].strip()
        print('')
        print("Unity IP Address: {}".format(ip2))
        print("Configuration type: {}".format(config_type1))
        print("NAS1 IP Address: {}".format(nas_ip11))
        print("NAS2 IP Address: {}".format(nas_ip22))
        print("NAS Server Netmask: {}".format(netmask))
        print("NAS Server Gateway: {}".format(gateway_ip1))
        print('')
        self.usr_input=raw_input(msg1)
        print("")
        if self.usr_input=="yes":
            """
            no action required
            """
            pass
        elif self.usr_input=="no":
            print ('\n')
            print (msg2)
            print ('\n')
            self.input_ip(1)
            with open(TMP_FILE,'w') as f:
                f.write(str(self.ip))
                f.write("\n")
            self.input_conf()
            self.fl_fn()
            self.input_f5()
        elif self.usr_input=="quit":
            os.remove(TMP_FILE)
            sys.exit(1)
        else:
            self.log_file_scrn("="*50)
            self.exit_codes(3,msg3)
            self.input_f5()
    def nas_config(req):
        """
        This is wrapper function
        return wrapper request
        """
        def wrapper_function(self):
            """
            This function will wrap the different functions depends on user input
            """
            return req(self)
        return wrapper_function

    @nas_config
    def block(self):
        """
        This function will do the block configuration
        Block configuration script will be called based on provided inputs
        self.code1 --> to take the status of block script execution
        return --> none
        """
        try:
            with open(TMP_FILE, 'r') as f:
                out=f.readlines()
            ip1=out[0].strip()
            config_type=out[1].strip()
            self.exit_codes(6,"Starting the  Block Configuration..")
            cmd="python /opt/ericsson/san/lib/BlockConfiguration.py {} {}".format(ip1, config_type).split(' ')
            self.code1=subprocess.call(cmd)
        except Exception as err:
            self.log_file_scrn("=" * 50)
            self.exit_codes(1, err)

    @nas_config
    def file(self):
        """
        This function will do file configuration
        File configuration script will be called based on provided inputs
        self.code12 --> to take the status of file script execution
        return --> none
        """
        try:
            with open(TMP_FILE, 'r') as f:
                out=f.readlines()
            if len(out)==6:
                ip=out[0].strip()
                nas_ip1=out[2].strip()
                nas_ip2=out[3].strip()
                netmask=out[4].strip()
                gateway_ip=out[5].strip()
            else:
                print("required inputs not provided. Try again")
                if os.path.exists(TMP_FILE):
                    os.remove(TMP_FILE)
                if os.path.exists(TEMP1):
                    os.remove(TEMP1)
                sys.exit(1)
            self.exit_codes(6,"Starting the  file configuration..")
            cmd2="python /opt/ericsson/san/lib/FileConfiguration.py {} {} {} {} {}"
            cmd1=cmd2.format(ip, nas_ip1, nas_ip2, netmask, gateway_ip).split(' ')
            self.code2=subprocess.call(cmd1)
        except Exception as err:
            self.log_file_scrn("=" * 50)
            self.exit_codes(1, err)
    @nas_config
    def create(self):
        """
        This function will do both file and block configuration
        stage --> to perform staging block by file
        return --> none
        args --> none
        """
        stage=create_stages()
        if stage==1:
            self.block()
            if self.code1==0:
                stage=stage+1
                with open(TEMP1,'w') as f:
                    f. write(str(stage))
        if stage==2:
            self.file()
            if self.code2==0:
                msgg="--------Block and File Configuration Completed Successfully---------"
                self.exit_codes(6,msgg)
                os.remove(TEMP1)
                os.remove(TMP_FILE)
def help_fn():
    """
    Help function to guid user with available actions
    return --> none
    args --> none
    """
    print('')
    print("Usage: StorageConfiguration.py <--action>")
    print('\n')
    print("Valid actions are:")
    print('')
    print("--create          Performs Block and File storage Configurations")
    print ('')
    print("--help            Show this help message and exit\n")

def handler(signum, frame):
    """
    restore the original signal handler
    in raw_input when CTRL+C is pressed will be handled by below
    """
    print("ctrl+c not allowed at this moment")

def create_stages():
    """
    This function will handle the steps to execute block and file functions to complete create function
    stage --> to perform staging
    return --> stage
    args --> none
    """
    stage=1
    try:
        if os.path.exists(TEMP1):
            with open(TEMP1, 'r') as f:
                stage = int(f.read())
        return stage
    except Exception:
        return stage
def main():
    """
    This is main function to call desired function calls for performing requirement
    performs configuration as per user request
    return --> none
    provides rerun incase of improper inputs provided by user
    args --> none
    """
    signal.signal(signal.SIGINT, handler)
    wrap_var=stor_config()
    if len(sys.argv)==2:
        IP_USR=str(sys.argv[1])
    elif len(sys.argv)!=2:
        msg1="Invalid Request!. check and try again."
        wrap_var.log_file_scrn("="*70)
        wrap_var.exit_codes(5,msg1)
        wrap_var.log_file_scrn("="*70)
        help_fn()
        sys.exit(1)
    wrap_var.print_logging_details()
    exc="Try again after cleanup."
    msg11 = "Enter required inputs for block and file configuration."
    if IP_USR=='--create':
        msg="This Script will perform Unity Block and File Configuration"
        wrap_var.log_file_scrn("="*70)
        wrap_var.exit_codes(0,msg)
        wrap_var.log_file_scrn("="*70)
        wrap_var.verify_uemcli()
        try:
            if os.path.exists(TMP_FILE):
                with open(TMP_FILE, 'r') as f:
                    out1 = f.readlines()
                if len(out1)==6:
                    wrap_var.input_f4()
                    wrap_var.input_f5()
                    wrap_var.create()
                else:
                    os.remove(TMP_FILE)
                    print(msg11)
                    wrap_var.input_ip(1)
                    wrap_var.input_f(0,1)
                    wrap_var.unity_check()
                    wrap_var.input_conf()
                    wrap_var.fl_fn()
                    wrap_var.input_f5()
                    wrap_var.create()
            else:
                print(msg11)
                wrap_var.input_ip(1)
                wrap_var.input_f(0,1)
                wrap_var.unity_check()
                wrap_var.input_conf()
                wrap_var.fl_fn()
                wrap_var.input_f5()
                wrap_var.create()
        except Exception as err:
            print(err)
            print(exc)
    elif IP_USR in ['--help','-h']:
        help_fn()
    else:
        msg2="Invalid Request!. check and try again."
        wrap_var.log_file_scrn("="*70)
        wrap_var.exit_codes(5,msg2)
        wrap_var.log_file_scrn("="*70)
        help_fn()
        sys.exit(1)

if __name__ == "__main__":
    main()
sys.exit(0)

