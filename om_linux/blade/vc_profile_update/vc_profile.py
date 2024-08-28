#!/usr/bin/python
""" This Script is used for add the network to the profile """
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
# Name      : vc_profile.py
# Purpose   : This Script is used for add the network to the profile.

import os
import sys
from os import path
import re
import getpass
from re import findall, search
import time
import logging
import pexpect

class VC_Profile:
    """ This class is to connect the Virtual Connect Configuration"""

    def __init__(self):
        """ This method is to initialize the variable """
        timestr = time.strftime("%Y%m%d-%H%M%S")
        self.fname = path.basename(__file__).strip('.py')+ "_"+ timestr + '.log'
        format_str = '%(levelname)s: %(asctime)s: %(message)s'
        os.system("mkdir -p /ericsson/vc_profile_update/log/")
        logging.basicConfig(level=logging.DEBUG, filename="/ericsson/vc_profile_update"
                                                          "/log/%s"\
                                                           %self.fname, format=format_str)
        self.log_path = "\33[32m{}{}\033[0m".format("Please find the log file "\
                                        "/ericsson/vc_profile_update/log/", self.fname)
        print self.log_path


    def user_input(self):
        """ This method to take the user input """
        try:
            while True:
                self.server = raw_input("Please provide HP Virtual"\
                                        " Connect IP Address: ").strip()
                if self.valid_ip_check(self.server) == True:
                    break
                else:
                    print "\33[31m{}\033[0m".format("You have given wrong IP, " + \
                                                    "Please provide the valid IP")
                    logging.error("provided wrong VC IP  address")
            while True:
                self.user_password = getpass.getpass("Enter the HP Virtual"\
                                                     " Connect password: ")
                if len(self.user_password) == 0:
                    print "You have not given the Input"
                    logging.error("Inputted Empty VC password")
                else:
                    break
            self.verify_user_login()

        except(Exception, KeyboardInterrupt, EOFError) as e:
            logging.error(e)
	    logging.error("Script execution interrupted")
            print "\33[31m{}\033[0m".format("Script execution interrupted, please "\
                                            "check the logs")
            exit(1)

    def verify_user_login(self):
        """ This function is to verify the user login """
        try:
            cmd = "show network"
            text_search = "In-Use"
            ssh_output = self.ssh_login(cmd)
            if text_search in ssh_output:
                print "Login Successful..."
                logging.info("Login Successful")
            else:
                print "SSH Login failed,check Username/Password"
                logging.error("Login has failed")
                exit(1)
        except (Exception, KeyboardInterrupt, EOFError) as e:
            logging.error(e)
            print "\33[31m{}\033[0m".format("Script execution interrupted, please "\
                                            "check the logs")
            exit(1)

    def valid_ip_check(self, ip):
        """This function validate the IPV4"""
        ipv = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
        return bool(ipv) and all(map(lambda n: 0 <= int(n) <= 255, ipv.groups()))
 
    def user_profile_input(self):
        """ This function is for user profile input """
        try:
            self.server_name = raw_input("Enter the server "\
                                          "name: ").strip()
            logging.info("Inputted Server name "+self.server_name)
        except(Exception, KeyboardInterrupt, EOFError) as e:
            logging.error(e)
            print "\33[31m{}\033[0m".format("Script execution interrupted, please "\
                                            "check the logs")
            exit(1)

    def power_on_status(self):
        """ This function return the poweron status of the server  """
        try:
            flag = 0
            pattern = 'Server ID'
            self.output = self.ssh_login("show server *\r")
            self.info = self.server_status(pattern, self.output)
            for key, value in self.info.items():
                if self.server_name in value['Server Name']:
                    self.profile_name = value['Server Profile']
                    self.power_status = value['Power']
                    self.server_id = value['Server ID']
                    flag = 1
            if flag != 1:
                print "Server profile which you entered is not found, please enter again"
                logging.info("Server profile not found")
                self.user_profile_input()
                self.power_on_status()
            if self.power_status == 'On':
                choice = raw_input("[Note]: Before applying "\
                      "the configuration, "\
                      "server needs to be powered off. "\
                      "Do you want to continue (y/n): ").lower()
                promt_return_value = self.user_promt_yes_no(choice)
                if promt_return_value == True:
                    cmd = "poweroff server "+self.server_id
                    print "Powering Off..."
                    print self.ssh_login(cmd)
                    time.sleep(5)
                    self.power_on_status()
                else:
                    print "User selected no, exiting the script"
                    logging.info("user poweroff option no")
                    exit(1)
            else:
                self.network_status()
                self.list_network()
        except(Exception, KeyboardInterrupt, EOFError) as e:
            print "\33[31m{}\033[0m".format("Script execution interrupted, please "\
                                            "check the logs")
            logging.error(e)

    def network_status(self):
        """ This function return the network status """
        pattern = 'Name'
        self.output = self.ssh_login("show network *\r")
        self.network_info = self.server_status(pattern, self.output)

    def vlan_name_input_1(self):
        """ This function takes the vlan name 1"""
        flag = 0
        self.vlan_name_1 = raw_input("Enter the network name: "\
                                     "(example: ENM_TEST): ").strip()
        self.vlan_name_1 = self.vlan_name_1+"_A"
        self.vlan_name_2 = self.vlan_name_1[:-1]+"B"
        logging.info(" VLAN Name 1 "+self.vlan_name_1)
        for key, value in self.network_info.items():
            if self.vlan_name_1 == value['Name']:
                flag = 1
        if flag == 1:
            if self.profile_match(self.vlan_name_1) != True:
                print "The network already exists in the enclosure"
                self.vlan_name_input_1()
            else:
                print "The following Network already exists in Profile, Try again"
                logging.info("The following Network already exists")
                self.vlan_name_input_1()
        else:
            self.uplink_list()
            self.add_network_1()

    def vlan_name_input_2(self):
        """ This function takes the vlan name 1"""
        flag = 0
        logging.info(" VLAN Name 2 "+self.vlan_name_2)
        for key, value in self.network_info.items():
            if self.vlan_name_2 == value['Name']:
                flag = 1
        if flag == 1:
            if self.profile_match(self.vlan_name_2) != True:
                choice = raw_input("The following VLAN Name "+self.vlan_name_2+\
                                   " already exists,"\
                                   "Do you still want to continue (y/n)").lower()
                promt_return_value = self.user_promt_yes_no(choice)
                if promt_return_value == True:
                    print "Please wait, adding the network ..."
                    command = "add enet-connection "+self.profile_name+\
                              " Network="+self.vlan_name_2
                    print self.ssh_login(command)
                else:
                    print "User option No"
                    self.vlan_name_input_2()
            else:
                print "The following Network already exists,Try again"
                logging.info("The following Network already exists")
                self.vlan_name_input_2()
        else:
            self.add_network_2()

    def vlan_id_input(self):
        """ This function is check the duplicate of the vlan id """
        print "\33[32m{}\033[0m".format("[Note]: To add "\
              "new network to the profile, Provide new VLAN ID ")
        print "\33[32m{}\033[0m".format("[Note]: To add "\
              "existing network to the profile, Provide respective "\
	      "VLAN ID from the list ")
        while True:
            try:
                self.vlan_id = int(raw_input("\nEnter the VLAN ID "\
                                             " (Enter value between 1 to 4094): "))
                if self.vlan_id >= 1 and self.vlan_id <= 4094:
                    break
                else:
                    print "Invalid Input, valid values range from 1 to 4094"
                    self.vlan_id_input()
            except ValueError:
                print "Enter the Integer Value Only"
                continue
        flag = 0
        count = 0
        self.vlan_id = str(self.vlan_id).strip()
        vlan_lst = []
        for key, value in self.network_info.items():
            if self.vlan_id == value['VLAN ID']:
                vlan_lst.append(value['Name'])
                vlan_id = value['VLAN ID'] 
                flag = 1
                count += 1
        if flag == 1:
            self.profile_match(vlan_lst[0])
            if count == 2:
                if self.profile_match(vlan_lst[0]) != True:
                    print "The provided VLAN ID is already assigned"\
		      " to "+str(vlan_lst)+" in the enclosure"
                    choice = raw_input("Do you want to continue "\
                                       "and add to the profile(y/n): ").lower()
                    promt_return_value = self.user_promt_yes_no(choice)
                    if promt_return_value == True:
                        command = "add enet-connection "+self.profile_name+\
                                  " Network="+vlan_lst[0]
                        print "Addding the network 1 to the Profile, Please wait..."
                        print self.ssh_login(command)
                        command1 = "add enet-connection "+self.profile_name+\
                                   " Network="+vlan_lst[1]
                        print "Addding the network 2 to the Profile, Please wait..."
                        print self.ssh_login(command1)
                        cmd = "show profile "+self.profile_name
                        print self.ssh_login(cmd)
                        logging.info("Added existing network")
                    else:
                        self.vlan_id_input()
                else:
                    print "The following Network "\
                          "already exists in Profile, Try with diffrent VLAN ID"
                    logging.info("The following Network already exists")
                    self.vlan_id_input()

            if count == 1:
               print "only single uplink set is there, aborting script"
               exit(1) 
        else:
            logging.info("adding new vlan id")
            self.vlan_name1 = self.vlan_name_input_1()
            self.vlan_name2 = self.vlan_name_input_2()

    def list_network(self):
    	""" This function adds the netowrk to the profile """
        print "The following Ethernet Network Connections are present in your enclosure"
        print "-"*30
        print "Network Name"+"\t\t"+"VLAN ID" 
        print "-"*30
        for key, value in self.network_info.items():
            print  value['Name']+"\t\t"+ value['VLAN ID']
        print "-"*30
        self.vlan_id_input()
    
    def uplink_set_1(self):
        """ This function is to select the uplink """        
        while True:
            try:
                self.option_1 = int(raw_input("\nSelect the UplinkSet"\
				   	      " option for network "+self.vlan_name_1+ 
                                              " (Enter value between 1 to 4): "))
                if self.option_1 > 0 and self.option_1 <= 4:
                    self.uplink_A = self.uplnk_list[self.option_1].strip()
                    break
                else:
                    print "Invalid Input,Valid values range from 1 to 4"
                    self.uplink_option()
            except ValueError:
                print "Enter the Integer Value Only"
                continue

    def uplink_set_2(self):
        """ This function is to select the uplink """
        while True:
            try:
                self.option_2 = int(raw_input("\nSelect the UplinkSet"\
				              " option for network "+self.vlan_name_2+
                                              " (Enter value between 1 to 4): "))
                if self.option_2 > 0 and self.option_2 <= 4:
                    self.uplink_B = self.uplnk_list[self.option_2].strip()
                    break
                else:
                    print "Invalid Input,Valid values range from 1 to 4"
                    self.uplink_option()
            except ValueError:
                print("Enter the Integer Value Only")
                continue

    def add_network_1(self):
        """ This function is to add the first network """
        print "Please wait, adding the network 1..."
        command = "add network "+self.vlan_name_1+" UplinkSet="\
                  +self.uplink_A+" VLANId="+str(self.vlan_id)
        result = self.ssh_login(command)
        print result
        if 'SUCCESS' in result:
            print "Addding the network to the Profile, Please wait..."
            command_1 = 'add enet-connection '+self.profile_name+' Network='+self.vlan_name_1
            intf_result = self.ssh_login(command_1)
            print intf_result
        else:
            print "The fllowing vlan id or vlan name already "\
                  "exists,exiting the script"
            exit(1)

    def add_network_2(self):
        """ adding the newtwork2 """
        print "Please wait, adding the network 2..."
        command = "add network "+self.vlan_name_2+" UplinkSet="+self.uplink_B+" VLANId="+str(self.vlan_id)
        result = self.ssh_login(command)
        print result
        if 'SUCCESS' in result:
            print "Addding the network to the Profile,Please wait..."
            command_1 = 'add enet-connection '+self.profile_name+' Network='+self.vlan_name_2
            intf_result = self.ssh_login(command_1)
            print intf_result
            cmd = "show profile "+self.profile_name
            print self.ssh_login(cmd)
            logging.info("added network to the profile")
        else:
            logging.error("failed to add the network")
            print "The fllowing vlan name already exists,exiting the script"
            exit(1)

    def power_on_server(self):
        """ To poweron the server """
        try:
            print "\33[32m{}\033[0m".format("Script execution complete, "\
                  "powering on the server, please wait...")
            cmd_1 = "poweron server "+self.server_id
            print self.ssh_login(cmd_1)
            logging.info("powered on the server")
        except(Exception, KeyboardInterrupt, EOFError) as e:
            logging.error(e)
            print "\33[31m{}\033[0m".format("Script execution interrupted, please "\
                                            "check the logs")
            exit(1)   
   
    def user_promt_yes_no(self, choice):
        """ This function returns the yes or no based on user input """
        yes = {'yes', 'y', 'ye', ''}
	no = {'no', 'n'}

	if choice in yes:
	   return True
        elif choice in no:
           return False
	else:
           print "Invalid Choice"
	   return False
            
    def server_status(self, pattern, output):
        """ This function is to verify the server status """
        reg_search = r'({}.*\n(\w.*\n)*)'.format(pattern)
        return self.pattern_match(output, reg_search, pattern)

    def profile_match(self, name):
        """ Function to check existing profile """
        cmd = "show profile "+self.profile_name
        res = self.ssh_login(cmd).splitlines()
        regx = r'(?<!\S){}(?!\S)'.format(name)
        flag = 0
        for i in res:
            if i.startswith('8'):
                flag = 1
                print "\33[31m{}\033[0m".format("Port is not "\
                      "available to add the network, "\
                      "exiting the script")
                exit(0)
        if flag == 0:         
            for i in res:
                if name in i:
                    if re.search(regx, i):
                        return True

    def pattern_match(self, output, reg_search, pattern):
        """ This function search the pattern and return the search result """
        matches = findall(reg_search, output)
        meta_dict = {}
        for match in matches:
            serverinfo_dict = dict()
            lines_list = ''.join(match).splitlines()
            for line in lines_list:
                tokens = search('^([\w ]+)[ ]+:(.*)', line)
                if tokens is not None:
        	    try:
            	        serverinfo_dict[tokens.group(1).strip()] = \
                        tokens.group(2).strip()
        	    except AttributeError as e:
            	        print "Error occurred parsing VC server output"
                        logging.error("Error occurred parsing VC server output")
            meta_dict[serverinfo_dict[pattern]] = serverinfo_dict
        return meta_dict

    def uplink_list(self):
        """This function for uplinkset selction """
        uplink_command = "show uplinkset *"
        res = self.ssh_login(uplink_command)
        reg_search = r'({}.*\n(\w.*\n)*)'.format('Name')
        rex = r'(?<!\S){}(?!\S)'.format(":")
        matches = findall(reg_search, res)
        count = 1
        self.uplnk_list = {}
        for i in matches:
            serverinfo_dict = dict()
            lines_list = ''.join(i).splitlines()
            for line in lines_list:
                if 'Name' in line:
                    if re.search(rex, line):
                        self.uplnk_list[count] = line.split(':')[1]
                        count += 1
        print "\nThe following uplinksets are present in your enclosure:"
        print "Option"+"\t"+" Uplink Name"
        for key, value in self.uplnk_list.items():
            print str(key)+"\t"+value
        self.uplink_set_1()
        self.uplink_set_2()

    def ssh_login(self, cmd):
        """ This function is to login to the VC """
        try:
            self.vc_ip = self.server
            vc_login = pexpect.spawn('ssh -o StrictHostKeyChecking=no root@'+self.server)
            vc_login.expect('.*assword: ')
            vc_login.sendline(self.user_password)
            vc_login.expect('->')
            vc_login.sendline(cmd)
            vc_login.expect('->')
            return vc_login.before
        except Exception as e:
            print "SSH Login failed,check Username/Password and Login again"
            logging.error(e)
            exit(1)

if __name__ == "__main__":
    obj = VC_Profile()
    obj.user_input()
    obj.user_profile_input()
    obj.power_on_status()
    obj.power_on_server()
