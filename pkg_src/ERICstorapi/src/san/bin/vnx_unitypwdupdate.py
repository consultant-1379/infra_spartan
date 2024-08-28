#!/usr/bin/python
""" This Script is used for Unity Password update """
# ********************************************************************
# Ericsson Radio Systems AB SCRIPT
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
# Name      : vnx_unitypwdupdate.py
# Purpose   : This script perform the  Unity password update.

import sys
import os
import subprocess
import re
import getpass
import logging
from os import path
import time
import pexpect
cod="\33[31m{}\033[0m"
cod1=" uemcli -d "
cod3=" -saveUser"
cod4="\33[32m{}\033[0m"
CRED_PATH = '/ericsson/storage/san/plugins/vnx/cred'
class PswdChange(object):
    """ This class to update the SAN password from the coordinator """
    def __init__(self, stor_type):
        """ This method to initialize the required variable """
        self.stor_type = stor_type
        cmd = "cat /eniq/installation/config/om_sw_locate"
        self.mws_blade_ip = subprocess.check_output(cmd, shell=True).split("@")[0]
        timestr = time.strftime("%Y%m%d-%H%M%S")
        self.fname = path.basename(__file__).strip('.py')+ "_"+ timestr + '.log'
        format_str = '%(levelname)s: %(asctime)s: %(message)s'
        os.system("mkdir -p /var/ericsson/log/storage/")
        logging.basicConfig(level=logging.DEBUG, filename="/var/ericsson"
                                                          "/log/storage/%s"\
                                                           %self.fname, format=format_str)
        self.log_path = "\33[32m{}{}\033[0m".format("Please find the log file "\
                                        "/var/ericsson/log/storage/", self.fname)
        print (self.log_path)
    @staticmethod
    def valid_ip_check(ip):
        """ This function validate the IP """
        ipv = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
        return bool(ipv) and all(map(lambda n: 0 <= int(n) <= 255, ipv.groups()))
    @staticmethod
    def empty_check():
        """ This Function checks empty input """
        print (cod.format("You have not " \
                                        "given input"))

    def ssh_login(self, blade_name):
        """ This function to login ssh """
        if self.stor_type == 'unity':
            command = cod1+self.server+" \
                       -u {} -p ".format(self.user)+self.user_password+"\
                       -saveUser"
            cmd =" /ericsson/storage/san/plugins/unity/lib/encryptdecrypt.py --encrypt {}".format(self.user_password)
            cmd2 = blade_name + cmd
            subprocess.Popen(["ssh -o StrictHostKeyChecking=no " + cmd2], shell=True, \
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            command = " /opt/Navisphere/bin/naviseccli -h {host} \
                      -addusersecurity -user {user} -password \
                      {passd} -scope 0 -secfilepath \
                      {cred}".format(host=self.server,
                                     passd=self.user_password,
                                     user=self.user,cred=CRED_PATH)
        command_1 = blade_name + command
        login_status = subprocess.Popen(["ssh -o StrictHostKeyChecking=no "+command_1], shell=True, \
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        login_status.communicate()[0]
        if login_status.returncode == 0:
            logging.info(blade_name+ " password has been updated")
        else:
            logging.info(blade_name+ " password failed to update")
        logging.info("ssh logging info :"+str(login_status))
        return login_status.returncode
    @staticmethod
    def blade_check():
        """ This function to check blade server or rack server """
        blade_check = subprocess.check_output("vgs 3>&- 4>&-", shell=True)
        if "eniq_stats_pool" in blade_check:
            return "Singleblade"
        else:
            return "Multiblade"

    def mws_pass_update(self):
        """ This function will update the multiblade_password """
        if os.path.exists('/eniq/installation/config/om_sw_locate'):
            if self.stor_type == 'unity':
                command = cod1+self.server+" -u {} -p \
                          ".format(self.user)+\
                          self.user_password+cod3
            else:
                command = ' /opt/Navisphere/bin/naviseccli -h {host} \
                              -addusersecurity -user {user} -password \
                              {passd} -scope 0'.format(host=self.server,
                                                       passd=self.user_password,
                                                       user=self.user)
            process = pexpect.spawn('ssh -o StrictHostKeyChecking=no root@'+self.mws_blade_ip)
            process.expect('.*assword: ')
            process.sendline(self.mws_password)
            process.expect('.+#.+')
            process.sendline(command)
            process.expect('.+#.+')
            process.sendline('exit')
            process.close()
            print (cod4.format("MWS password update has "\
                                            "been successfully completed"))
            logging.info("MWS password update has been successfully completed")
        else:
            print (cod.format("MWS is not configured, check the configuration"))

    def user_input(self):
        """ This function will take the user input """
        try:
            while True:
                self.mws_password = getpass.getpass("Enter the MWS "\
                                                    "password of "+self.mws_blade_ip+": ")
                if len(self.mws_password) == 0:
                    self.empty_check()
                    logging.error("MWS passowrd value is empty")
                else:
                    break

            while True:
                self.server = raw_input("Enter the storage ip: ").strip()
                if self.valid_ip_check(self.server) == True:
                    break
                else:
                    print (cod.format("You have given wrong IP, " + \
                                                    "Please provide the valid IP"))
                    logging.error("provided wrong storage  address, check the format")
            while True:
                self.user = raw_input("Enter the storage Username: ").strip()
                if len(self.user) == 0:
                    self.empty_check()
                    logging.error("storage Username is empty")
                else:
                    if re.match("^[a-zA-Z0-9_]+$", self.user):
                        break
                    else:
                        print (cod.format("Special Characters " + \
                                                  "are not allowed, " \
                                                  "Please provide " \
                                                  "the valid input"))
                        logging.error("special characters are not allowed in IP address")
            while True:
                self.user_password = getpass.getpass("Enter the storage password: ")
                if len(self.user_password) == 0:
                    self.empty_check()
                    logging.error("Inputted Empty storage password")
                else:
                    break
            self.mws_pass_update()
            if self.blade_check() == 'Singleblade':
                if self.stor_type == 'unity':
                    command = cod1+self.server+" -u \
                              {} -p ".format(self.user)+\
                              self.user_password+cod3
                    enc="/ericsson/storage/san/plugins/unity/lib/encryptdecrypt.py --encrypt {}"
                    subprocess.check_output(enc.format(self.user_password) , shell=True)
                    s_blade = subprocess.check_output(command, shell=True)
                else:
                    cd=' /opt/Navisphere/bin/naviseccli -h {host} \
                              -addusersecurity -user {user} -password \
                              {passd} -scope 0 -secfilepath \
                              {cred}'
                    command = cd.format(host=self.server,
                                             passd=self.user_password,
                                             user=self.user,cred=CRED_PATH)
                    s_blade = subprocess.check_output(command, shell=True)
                print (cod4.format("Singleblade password "\
                                                "update successfully completed"))
                logging.info("single blade password update successfully "\
                             "completed :"+str(s_blade))
                exit(0)
            else:
                return_code = []
                multiblade_list = ['engine','dwh_reader_1','dwh_reader_2']
                if self.stor_type == 'unity':
                    command = cod1+self.server+" -u {} \
                              -p ".format(self.user)+\
                              self.user_password+cod3
                    enc="/ericsson/storage/san/plugins/unity/lib/encryptdecrypt.py --encrypt {}"
                    subprocess.check_output(enc.format(self.user_password), shell=True)
                else:
                    cd=' /opt/Navisphere/bin/naviseccli -h {host} \
                              -addusersecurity -user {user} -password \
                              {passd} -scope 0 -secfilepath \
                              {cred}'
                    command = cd.format(host=self.server,
                                             passd=self.user_password,
                                             user=self.user,cred=CRED_PATH)
                co_cmd = subprocess.Popen([command], shell=True, \
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                co_cmd.communicate()
                co_return_code = str(co_cmd.returncode)
                if co_return_code == '0':
                    logging.info("Co-ordinater password has been updated")
                else:
                    logging.info("Failed to update Co-ordinater password ")
                return_code.append(co_return_code)
                for blade in multiblade_list:
                    return_code.append(str(self.ssh_login(blade)))
                logging.info("blade ssh login return status list"+str(return_code))
                if len(set(return_code)) == 1:
                    if '0' not in set(return_code):
                        print (cod.format("Failed to update "\
                                                        "the password check the logs"))
                        logging.error("failed to update password")
                    else:
                        print (cod4.format("Password update is successfully "\
                                                        "completely on all Multiblade servers"))
                        logging.info("Multiblade password update successfully completed")
                else:
                    print (cod.format("Failed to update "\
                                                    "the password check the logs"))
                    logging.error("failed to update password")
            print (self.log_path)
        except(Exception, KeyboardInterrupt) as e:
            print (cod.format("Script failed to execute, please "\
                                            "check the logs"))
            if '127' in str(e):
                logging.error("uemcli package not installed ,please check")
            logging.error(e)
            print (self.log_path)



if __name__ == "__main__":
    if len(sys.argv) == 2  and int(sys.argv[1]) == 1:
        stor_type = 'unity'
    elif len(sys.argv) == 2 and int(sys.argv[1]) == 0:
        stor_type = 'vnx'
    else:
        print ('[Error]: No parameter passed or Unsupported values passed')
        exit(1)
    pwd = PswdChange(stor_type)
    pwd.user_input()

