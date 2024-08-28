#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for ENIQ Snapshot deletion
"""
# ****************************************************************************
# Ericsson Radio Systems AB                                     SCRIPT
# ****************************************************************************
#
# (c) Ericsson Radio Systems AB 2019 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property
# of Ericsson Radio Systems AB, Sweden. The programs may be used
# and/or copied only with the written permission from Ericsson Radio
# Systems AB or in accordance with the terms and conditions stipulated
# in the agreement/contract under which the program(s) have been
# supplied.
# ******************************************************************************
# Name      : snapshot_deletion.py
# Purpose   : The script will perform Storage Expansion in unity XT
# ******************************************************************************
import subprocess,sys,os,time,logging,signal
LOG_DIRE11 = '/var/ericsson/log/patch/'
TIME = "%m_%d_%Y-%H_%M_%S"
LOG_NAME = os.path.basename(__file__).replace('.py', '_')+time.strftime(TIME)+'.log'
MSG2="issue with the CLI/CMD execution and above are the actual ERROR"

class snapdel(object):
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
        self.logging_configs()
        self.colors = {'RED' : '\033[91m', 'END' : '\033[00m','GREEN' : '\033[92m', 'YELLOW' : '\033[93m'}

    def logging_configs(self):
        """
        Creates the custom logger
         for logs
        It creates 2 different
        log handler
        StreamHandler which handles logs of
        ERROR level or
         above and FileHandler
        which handles logs of WARNING level or
        Creating a custom
         logger for logs
        ERROR --> to display error,  WARNING --> To display warning
        return -->none,  args -->none
        LOG_DIRE11 --> Log dir path
        """
        if not os.path.exists(LOG_DIRE11):
            os.makedirs(LOG_DIRE11)
        s_handle17 = logging.StreamHandler()
        f_handle17 = logging.FileHandler(LOG_DIRE11+LOG_NAME)
        s_handle17.setLevel(logging.ERROR)
        f_handle17.setLevel(logging.WARNING)
        s_formats17 = logging.Formatter('%(message)s')
        f_formats17 = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_handle17.setFormatter(s_formats17)
        f_handle17.setFormatter(f_formats17)
        self.logger.addHandler(s_handle17)
        self.logger.addHandler(f_handle17)

    def log_file_scrn(self, msg22, log_dec=0):
        """
        Logging into file and screen
        based on the value of log_dec variable if value of log_dec is 0 it will print
        simultaneously to screen and log file for log_dec value as 1 it will print to
        logfile directly
        Param:
              msg -> the actual message, log_dec -> integer
        Return: None
        msg22--> to display message
        return-->none
        args-->none
        """
        if log_dec == 0:
            self.logger.error(msg22)
        else:
            self.logger.warning(msg22)

    def print_logging_detail(self):
        """
        Prints logging details with log file for exit,
        completion and start of the script, colors --> colors print for logs
        return --> none
        args --->none
        """
        color12 = self.colors
        hash_print1 = '---------------------------------------------------------------------'
        print(color12['YELLOW']+hash_print1+color12['END'])
        msg="Please find the script execution logs  ---> "
        print(color12['YELLOW']+msg+LOG_DIRE11+LOG_NAME+color12['END'])
        print(color12['YELLOW']+hash_print1+color12['END'])

    def exit_codes(self, code1, msg):
        """
        Script Exit function
        param: code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        colors -- >to print colors
        """
        colors = self.colors
        if code1 == 1:
            self.log_file_scrn(colors['RED']+"[ERROR] "+colors['END']+": "+msg)
            self.print_logging_detail()
            sys.exit(code1)
        elif code1 == 2:
            self.log_file_scrn(colors['YELLOW']+"[WARN] "+colors['END']+": "+msg)
        elif code1 == 3:
            self.log_file_scrn(colors['GREEN']+"[INFO] "+colors['END']+": "+msg, 1)
        else:
            self.log_file_scrn(colors['GREEN']+"[INFO] "+colors['END']+": "+msg)

    def fun1(self):
        """
        This function will check for snapshots
        1.rootsnap
        2.varsnap
        """
        try:
            DEVNULL = open(os.devnull, 'wb')
            cmd11 = "lvs | grep rootsnap | awk -F\" \" '{ print $2 }'"
            cmd22 = "lvs | grep varsnap | awk -F\" \" '{ print $2 }'"
            out11 = subprocess.check_output(cmd11, shell=True, stderr=DEVNULL).split('\n')[0].strip()
            out22 = subprocess.check_output(cmd22, shell=True, stderr=DEVNULL).split('\n')[0].strip()
            if (len(out11) == 0) and (len(out22) == 0):
                self.exit_codes(0,"No Snapshots present to be removed")
            else:
                if len(out11) != 0:
                    self.exit_codes(0,"Started removing rootsnap ")
                    stmt1 = "lvremove /dev/mapper/{}-rootsnap --y".format(out11).split(' ')
                    subprocess.call(stmt1, stderr=DEVNULL)
                    self.exit_codes(3,'Logical volume "rootsnap" successfully removed')
                else:
                    self.exit_codes(0,"No rootsnap present to be removed")
                if len(out22) != 0:
                    self.exit_codes(0,"Started removing varsnap")
                    stmt2 = "lvremove /dev/mapper/{}-varsnap --y".format(out22).split(' ')
                    subprocess.call(stmt2, stderr=DEVNULL)
                    self.exit_codes(3,'Logical volume "varsnap" successfully removed')
                else:
                    self.exit_codes(0,"No varsnap present to be removed ")
                print(" ")
                self.exit_codes(0, "Successfully Removed Snapshot")
        except Exception as err:
            self.log_file_scrn("-" * 73)
            self.log_file_scrn(err)
            self.log_file_scrn("-" * 73)
            self.exit_codes(1, MSG2)

    def fun2(self):
        """
        This function will check for snapshots
        1.rootsnap
        2.varsnap
        3.homesnap
        4.vartempsnap
        5.varlogsnap
        """
        try:
            DEVNULL = open(os.devnull, 'wb')
            cmd1 = "lvs | grep rootsnap | awk -F\" \" '{ print $2 }'"
            cmd2 = "lvs | grep varsnap | awk -F\" \" '{ print $2 }'"
            cmd3 = "lvs | grep homesnap | awk -F\" \" '{ print $2 }'"
            cmd4 = "lvs | grep vartmpsnap | awk -F\" \" '{ print $2 }'"
            cmd5 = "lvs | grep varlogsnap | awk -F\" \" '{ print $2 }'"
            self.out1 = subprocess.check_output(cmd1, shell=True, stderr=DEVNULL).split('\n')[0].strip()
            self.out2 = subprocess.check_output(cmd2, shell=True, stderr=DEVNULL).split('\n')[0].strip()
            self.out3 = subprocess.check_output(cmd3, shell=True, stderr=DEVNULL).split('\n')[0].strip()
            self.out4 = subprocess.check_output(cmd4, shell=True, stderr=DEVNULL).split('\n')[0].strip()
            self.out5 = subprocess.check_output(cmd5, shell=True, stderr=DEVNULL).split('\n')[0].strip()
            if (len(self.out1)==0) and (len(self.out2)==0) and (len(self.out3)==0) and (len(self.out4)==0) and\
                    (len(self.out5)==0):
                self.exit_codes(0, "No Snapshots present to be removed")
            else:
                self.delete1()
        except Exception as err:
            self.log_file_scrn("-" * 73)
            self.log_file_scrn(err)
            self.log_file_scrn("-" * 73)
            self.exit_codes(1, MSG2)

    def delete1(self):
        """delete snapshots for gen10 plus"""
        try:
            DEVNULL = open(os.devnull, 'wb')
            if len(self.out1) != 0:
                self.exit_codes(0, "Started removing rootsnap")
                stmt1 = "lvremove /dev/mapper/{}-rootsnap --y".format(self.out1).split(' ')
                subprocess.call(stmt1, stderr=DEVNULL)
                self.exit_codes(3,'Logical volume "rootsnap" successfully removed')
            else:
                self.exit_codes(0, "No rootsnap present to be removed")
            if len(self.out2) != 0:
                self.exit_codes(0, "Started removing varsnap")
                stmt2 = "lvremove /dev/mapper/{}-varsnap --y".format(self.out2).split(' ')
                subprocess.call(stmt2, stderr=DEVNULL)
                self.exit_codes(3,'Logical volume "varsnap" successfully removed')
            else:
                self.exit_codes(0, "No varsnap present to be removed")
            if len(self.out3) != 0:
                self.exit_codes(0, "Started removed homesnap")
                stmt3 = "lvremove /dev/mapper/{}-homesnap --y".format(self.out3).split(' ')
                subprocess.call(stmt3, stderr=DEVNULL)
                self.exit_codes(3,'Logical volume "homesnap" successfully removed')
            else:
                self.exit_codes(0, "No homesnap present to be removed")
            if len(self.out4) != 0:
                self.exit_codes(0, "Started removing vartmpsnap")
                stmt4 = "lvremove /dev/mapper/{}-vartmpsnap --y".format(self.out4).split(' ')
                subprocess.call(stmt4, stderr=DEVNULL)
                self.exit_codes(3,'Logical volume "vartmpsnap" successfully removed')
            else:
                self.exit_codes(0, "No vartmpsnap present to be removed")
            if len(self.out5) != 0:
                self.exit_codes(0, "Started removing varlogsnap")
                stmt5 = "lvremove /dev/mapper/{}-varlogsnap --y".format(self.out5).split(' ')
                subprocess.call(stmt5, stderr=DEVNULL)
                self.exit_codes(3,'Logical volume "varlogsnap" successfully removed')
            else:
                self.exit_codes(0, "No varlogsnap present to be removed ")
            print(" ")
            self.exit_codes(0, "Successfully Removed Snapshot")
        except Exception as err:
            self.log_file_scrn("-" * 73)
            self.log_file_scrn(err)
            self.log_file_scrn("-" * 73)
            self.exit_codes(1, MSG2)

    def remove_snap(self):
        """
        This function checks and remove any snapshots,
        it will work for Gen8,Gen9,Gen10 and Gen10 plus servers
        Param: None
        return: None
        """
        try:
            self.exit_codes(0,"Started Removing Snapshot")
            print(" ")
	    cm = 'dmidecode -t system'.split(' ')
            cm2 = subprocess.check_output(cm)
            if "Gen10 Plus" in cm2:
		self.fun2()
	    elif "Gen8" in cm2 or "Gen9" in cm2 or "Gen10" in cm2:
                self.fun1()
            else:
                self.fun2()
        except Exception as err:
            self.log_file_scrn("-" * 73)
            self.log_file_scrn(err)
            self.log_file_scrn("-" * 73)
            self.exit_codes(1, MSG2)

def handler(signum, frame):
    """
    restore the original signal handler
    in raw_input when CTRL+C is pressed will be handled by below
    """
    print("ctrl+c not allowed at this moment")


def main():
    """
    This is main function
    """
    sn=snapdel()
    sn.exit_codes(0,"This script will perform Snapshot deletion")
    sn.print_logging_detail()
    signal.signal(signal.SIGINT, handler)
    sn.remove_snap()


if __name__ == "__main__":
    main()
sys.exit(0)

