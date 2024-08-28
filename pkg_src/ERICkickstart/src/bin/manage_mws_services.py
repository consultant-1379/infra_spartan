
#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for enable or disable tftp  automation
This script will replace the manual steps
used to perform enable or disable tftp automation.
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
# Name      : manage_mws_services.py
# Purpose   : The script wil perform automation for enable or disable tftp services
# ********************************************************************

#Modules used in this script
import sys
import os
import logging
import time
import subprocess as sp

#Variables which are created and assigned are global variables used in this script
firewalld_res='systemctl restart firewalld >/dev/null 2>&1'
firew_reload='firewall-cmd --reload >/dev/null 2>&1'
add_port_cmd='firewall-cmd --zone=public --add-port=69/udp --permanent >/dev/null 2>&1'
add_service_cmd='firewall-cmd --zone=public --add-service=tftp --permanent >/dev/null 2>&1'
remove_port_cmd='firewall-cmd --zone=public --remove-port=69/udp --permanent >/dev/null 2>&1'
remove_service_cmd='firewall-cmd --zone=public --remove-service=tftp --permanent >/dev/null 2>&1'
nfs_0="NFS service is in active state"
nfs_1="NFS service is not in active state"
firewall_msg_0="Firewall is in active state"
firewall_msg1="Firewall is not in active state"
port_added0="TFTP Port is in Added state"
port_added1="TFTP Port is in not Added state"
TFTP_ENABLED0="TFTP service is in active state"
TFTP_ENABLED1="TFTP service is not in active state"
boolean_0="TFTP Boolean value status is in ON State"
boolean_1="TFTP Boolean value status is in OFF State"
LOG_NAME = os.path.basename(__file__).replace('.py', '_')+time.strftime("%m_%d_%Y-%H_%M_%S")+'.log'
LOG_DIRE="/var/ericsson/log/manage_mws_services/"
not_added_status="not added"

class enable_disable(object):
    '''

    This class contains functions to do
    validation,enable,disable,logging.
    '''

    def __init__(self):
        '''

        Initializes the variables whenever the object is created
        '''
        self.nfs_status = ""
        self.firewall_check = ""
        self.port_check = ""
        self.tftp_check = ""
        self.boolean_check = ""
        self.logger = logging.getLogger()
        self.logging_configs()
        self.colors = {'RED': '\033[91m', 'END': '\033[00m', 'GREEN': '\033[92m', 'YELLOW': '\033[93m'}
        self.nfs_flag=0
        self.firew_flag=0
        self.port_flag=0
        self.tftp_flag=0
        self.bool_flag=0
        self.not_enabled_list = []
        self.not_disabled_list = []
        self.port_log_print=0
        self.nh=""

    def logging_configs(self):
        """
        Creates the custom logger for logs
        It creates 2 different log handler
        """
        if not os.path.exists(LOG_DIRE):
            os.makedirs(LOG_DIRE)
        s_hand, f_hand = logging.StreamHandler(), logging.FileHandler(LOG_DIRE + LOG_NAME)
        s_hand.setLevel(logging.ERROR)
        f_hand.setLevel(logging.WARNING)
        s_formats = logging.Formatter('%(message)s')
        f_formats = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_hand.setFormatter(s_formats)
        f_hand.setFormatter(f_formats)
        self.logger.addHandler(s_hand)
        self.logger.addHandler(f_hand)

    def log_file_scrn(self, msg1, logdec=1):
        """
        Logging into file and screen
        based on the value of log_dec variable
        if value of log_dec is 0 it will print
        simultaneously to screen and log file
        for log_dec value as 1 it will print to log file
        Return: None
        msg --> to display message
        return -->none
        args -->none
        """
        if logdec == 0:
            self.logger.error(msg1)
        else:
            self.logger.warning(msg1)


    def print_logging_detail(self):
        """

        Prints logging details with log file for exit,
        completion and start of the script
        colors --> colors print for logs
        return --> none
        """
        color, msg = self.colors, "Please find the script execution logs  ---> "
        print_hash = '------------------------------------------------------------------------------'
        print(print_hash)
        print(msg + LOG_DIRE +LOG_NAME)
        print(print_hash)

    def exit_codes(self, code_num, msg):
        """
        Script Exit function
        param: code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        colors -- >to print colors
        """
        colors = self.colors
        if code_num == 1:
            print(colors['RED']+"[ERROR] "+colors['END']+": "+msg)
        elif code_num == 3:
            print("["+time.strftime("%m-%d-%Y-%H:%M:%S")+"] "
                               + colors['GREEN'] + "[INFO] " + colors['END'] + ": " + msg)
        else:
            print(colors['GREEN']+"[INFO] "+colors['END']+": "+msg)

    def nfs_val(self):
        '''

        Checks the NFS status and assign the status to a varibale.
        '''
        try:
            n = 'systemctl status nfs >/dev/null 2>&1'
            nfs_out = os.system(n)
            if str(nfs_out) != "0":
                self.nfs_status="inactive"
                self.log_file_scrn(nfs_1)
                if self.nfs_flag==1:
                    self.not_enabled_list.append(nfs_1)
            elif str(nfs_out)=="0":
                self.nfs_status = "active"
                self.log_file_scrn(nfs_0)
        except Exception as e:
            self.script_abort(1,e)

    def is_firewall_active(self):
        '''

        Checks the Firewalld status and assign the status in a varibale.
        In Enable or Disable case firewalld must be active,if it is in inactive
        after the enable or disable operation we are appending error msg to particular lists.
        '''
        try:
            self.a = 'systemctl status firewalld >/dev/null 2>&1'
            firewall_out = os.system(self.a)
            if "0" in str(firewall_out):
                self.firewall_check = "active"
                self.log_file_scrn(firewall_msg_0)
                if self.firew_flag==1 or self.firew_flag==2:
                    self.nodeh()

            else:
                self.firewall_check="inactive"
                self.log_file_scrn(firewall_msg1)

        except Exception as ferr:
            self.script_abort(1,ferr)

    def nodeh(self):
        '''

        Check whether the node hardening is applied or not.
        '''
        try:
            disb_firew_msg="No firewall configuration found,disabling firewall service"
            ports_list = 'firewall-cmd --list-ports'.split(" ")
            services_list='firewall-cmd --list-service'.split(" ")
            stop_firewall_cmd='systemctl stop firewalld >/dev/null 2>&1'
            disb_firewall_cmd='systemctl disable firewalld >/dev/null 2>&1'
            plist=sp.check_output(ports_list)
            slist=sp.check_output(services_list)
            if plist[0]!='\n' and slist[0]!='\n':
                self.nh="yes"
                self.is_port_added()
            else:
                self.nh="no"
                self.exit_codes(0,disb_firew_msg),self.log_file_scrn(disb_firew_msg)
                os.system(stop_firewall_cmd)
                os.system(disb_firewall_cmd)
        except Exception as nherr:
            self.script_abort(1,nherr)

    def is_port_added(self):
        '''

        Checks whether the port is added or not,and assign the status in a varibale.
        '''
        try:
            self.b = 'firewall-cmd --list-ports | grep -o 69 >/dev/null 2>&1'
            self.tftp_service='firewall-cmd --list-service | grep -o tftp >/dev/null 2>&1'
            port_out = os.system(self.b)
            service_out=os.system(self.tftp_service)
            if "0" in str(port_out) and "0" in str(service_out):
                self.port_check = "added"
                self.log_file_scrn(port_added0)
                if self.port_flag==2:
                    self.not_disabled_list.append(port_added0)
            else:
                self.port_check = not_added_status
                self.log_file_scrn(port_added1)
                if self.port_flag==1:
                    self.not_enabled_list.append(port_added1)

        except Exception as port_err:
            self.script_abort(1,port_err)

    def is_tftp_enabled(self):
        '''

        Checks whether the TFTP is enabled or not,and assign the status in a variable.
        '''
        try:
            c = 'systemctl status tftp >/dev/null 2>&1'
            tftp_out = os.system(c)
            if "0" in str(tftp_out):
                self.tftp_check = "enabled"
                self.log_file_scrn(TFTP_ENABLED0)
                if self.tftp_flag==2:
                    self.not_disabled_list.append(TFTP_ENABLED0)
            else:
                self.tftp_check = "not enabled"
                self.log_file_scrn(TFTP_ENABLED1)
                if self.tftp_flag==1:
                    self.not_enabled_list.append(TFTP_ENABLED1)
        except Exception as tftp_err:
            self.script_abort(1,tftp_err)

    def is_bool(self):
        '''

        Checks the Boolean status,and assign the status in a variable.
        '''
        try:
            d = 'getsebool tftp_home_dir'.split(" ")
            e = 'getsebool tftp_anon_write'.split(" ")
            on="--> on"
            b_out1 = sp.check_output(d)
            b_out2 =sp.check_output(e)
            inp=sys.argv[1]
            if on in b_out1 and on in b_out2:
                self.boolean_check = "on"
                self.log_file_scrn(boolean_0)
                if self.bool_flag==2:
                    self.not_disabled_list.append(boolean_0)

            elif inp=="--disable" and ((on in b_out1 and on not in b_out2) or (on in b_out2 and on not in b_out1)):
                bool_0=boolean_0
                self.boolean_check = "on"
                self.log_file_scrn(bool_0)
                if self.bool_flag==2:
                    self.not_disabled_list.append(bool_0)
            else:
                self.boolean_check = "off"
                self.log_file_scrn(boolean_1)
                if self.bool_flag == 1:
                    self.not_enabled_list.append(boolean_1)
        except Exception as bool_err:
            self.script_abort(1,bool_err)

    def validate(self):
        '''

        This function is defined to call the functions those are written for getting the status.
        '''
        self.is_firewall_active()
        self.is_tftp_enabled()
        self.is_bool()


    def script_abort(self,exit_code,msg):
        '''

        This function is used to abort the script
        incase of any Exception raised inside this script.
        '''

        self.exit_codes(exit_code,msg)
        self.log_file_scrn(msg)
        self.print_logging_detail()
        sys.exit(exit_code)

    def post_validate(self,msg):
        '''

        This function will print,the services which are not enabled even after
        enable operation and the services which are not disabled even after
        the disable operation.Finally abort the script.
        '''
        if msg=='enable':
            if len(self.not_enabled_list)>0:
                for i in self.not_enabled_list:
                    self.exit_codes(1,i)
                self.exit_codes(1,"Failed to enable services,Please check and re-run the script")

        else:
            if len(self.not_disabled_list)>0:
                for i in self.not_disabled_list:
                    self.exit_codes(1,i)
                self.script_abort(1,"Failed to disable services,Please check and re-run the script")


    def activate_nfs(self):
        '''

        This function is to activate NFS service ,if it is in inactive state.
        '''
        try:
            nfs_start_msg = "NFS service is in inactive state,starting NFS service"
            nfs_active="NFS service is in active state"
            nfs_res_cmd='systemctl restart nfs >/dev/null 2>&1'
            if self.nfs_status=="inactive":
                self.exit_codes(0,nfs_start_msg),self.log_file_scrn(nfs_start_msg)
                os.system(nfs_res_cmd)
            elif self.nfs_status=="active":
                self.exit_codes(0,nfs_active),self.log_file_scrn(nfs_active)
            self.nfs_flag=1
        except Exception as nfs_err:
            self.script_abort(1,nfs_err)


    def activate_firewall_and_port(self):
        '''

        Activates the firewall if it is not in active state by restarting it.
        Add the TFTP port if it is in not added condition.once the port is added,
        firewalld  restart is must.
        '''
        f_active = "Firewall service is in inactive state,restarting Firewall service"
        port_not= "TFTP service/port is not added to the firewall configuration,adding TFTP service/port"
        f_p = "TFTP service/port is added to the firewall configuration"
        f_res = "Restarting firewall service"

        try:
            if self.firewall_check == "active":
                self.nodeh()
                if self.port_check=="added":
                    self.exit_codes(0,f_p),self.log_file_scrn(f_p)
                elif self.port_check==not_added_status:
                    self.exit_codes(0,port_not),self.log_file_scrn(port_not)
                    os.system(add_port_cmd)
                    os.system(add_service_cmd)
                    os.system(firew_reload)
                    self.exit_codes(0,f_res),self.log_file_scrn(f_res)
                    os.system(firewalld_res)

            elif self.firewall_check=="inactive":
                self.exit_codes(0,f_active),self.log_file_scrn(f_active)
                os.system(firewalld_res)
                self.is_firewall_active()
                if self.firewall_check == "active":
                    self.nodeh()
                    if self.port_check == "added":
                        self.exit_codes(0, f_p),self.log_file_scrn(f_p)
                    elif self.port_check==not_added_status:
                        self.exit_codes(0, port_not),self.log_file_scrn(port_not)
                        os.system(add_port_cmd)
                        os.system(add_service_cmd)
                        os.system(firew_reload)
                        self.exit_codes(0, f_res),self.log_file_scrn(f_res)
                        os.system(firewalld_res)
                else:
                    err_msg="Unable to start Firewall service"
                    self.script_abort(1,err_msg)
            self.firew_flag,self.port_flag=1,1
        except Exception as fp_err:
            self.script_abort(1,fp_err)

    def enable_tftp(self):
        '''

        Start and Enables the TFTP if it is in not added state.
        '''
        try:
            tftp_msg="TFTP service is in inactive state,starting TFTP service"
            tftp_start="Enabling TFTP service"
            tftp_active="TFTP service is in active state"
            start_tftp_cmd='systemctl start tftp >/dev/null 2>&1'
            enb_tftp_cmd='systemctl enable tftp >/dev/null 2>&1'
            if self.tftp_check == "not enabled":
                self.exit_codes(0,tftp_msg),self.log_file_scrn(tftp_msg)
                os.system(start_tftp_cmd)
                self.exit_codes(0,tftp_start),self.log_file_scrn(tftp_start)
                os.system(enb_tftp_cmd)
            else:
                self.exit_codes(0,tftp_active),self.log_file_scrn(tftp_active)
            self.tftp_flag=1
        except Exception as b:
            self.script_abort(1,b)


    def set_bool(self):
        '''

        Sets the Boolean status to ON,if it is in off state
        '''
        try:
            bool_set="TFTP Boolean value is set to ON"
            bool_not="TFTP Boolean value is not set to ON"
            set_bool_1='setsebool -P tftp_home_dir 1 >/dev/null 2>&1'
            set_bool1='setsebool -P tftp_anon_write 1 >/dev/null 2>&1'
            if self.boolean_check == "off":
                self.exit_codes(0,bool_set),self.log_file_scrn(bool_not)
                os.system(set_bool_1)
                os.system(set_bool1)
            else:
                self.exit_codes(0,bool_set),self.log_file_scrn(bool_set)
            self.bool_flag=1
        except Exception as c:
            self.script_abort(1,c)

    def enable(self):
        '''

        This function is defined to call the functions those are needed for
        needed for enabling TFTP.
        '''
        self.activate_nfs()
        self.activate_firewall_and_port()
        self.enable_tftp()
        self.set_bool()

    def activate_firewall_remove_port(self):
        '''

        Activates the firewalld if it is not in active state by restarting it.
        remove the TFTP port if it is in added condition.once the port is removed,
        firewalld  restart is must.
        '''
        port_rem = "TFTP service/port is added to the firewall configuration,removing TFTP service/port "
        f_res_status = "Firewall service is in inactive state,restarting Firewall service"
        no_port= "TFTP service/port is removed from the firewall configuration"
        fres = "Restarting firewall service"

        try:
            if self.firewall_check == "active":
                self.nodeh()
                if self.port_check==not_added_status:
                    self.exit_codes(0,no_port),self.log_file_scrn(no_port)
                elif self.port_check=="added":
                    self.exit_codes(0,port_rem),self.log_file_scrn(port_rem)
                    os.system(remove_port_cmd)
                    os.system(remove_service_cmd)
                    os.system(firew_reload)
                    self.exit_codes(0,fres),self.log_file_scrn(fres)
                    os.system(firewalld_res)
            elif self.firewall_check == "inactive":
                self.exit_codes(0,f_res_status ),self.log_file_scrn(f_res_status)
                os.system(firewalld_res)
                self.is_firewall_active()
                if self.firewall_check == "active":
                    self.nodeh()
                    if self.port_check=="added":
                        self.exit_codes(0, port_rem),self.log_file_scrn(port_rem)
                        os.system(remove_port_cmd)
                        os.system(remove_service_cmd)
                        os.system(firew_reload)
                        self.exit_codes(0, fres),self.log_file_scrn(fres)
                        os.system(firewalld_res)
                    elif self.port_check==not_added_status:
                        self.exit_codes(0, no_port),self.log_file_scrn(no_port)

                else:
                    error_msg = "Unable to start Firewall service"
                    self.script_abort(1,error_msg)
            self.firew_flag,self.port_flag=2,2
        except Exception as p_err:
            self.script_abort(1,p_err)

    def disable_tftp(self):
        '''

        Disables the TFTP service if it is enabled.
        Because TFTP is a weak protocol and can be vulnerable.
        '''
        try:
            tftp="TFTP service is in active state,stopping TFTP service"
            disb_tftp="Disabling TFTP service"
            tftp_not_active="TFTP service is in inactive state"
            tftp_stop_cmd='systemctl stop tftp >/dev/null 2>&1'
            tftp_disb_cmd='systemctl disable tftp >/dev/null 2>&1'
            if self.tftp_check == "enabled":
                self.exit_codes(0,tftp),self.log_file_scrn(tftp)
                os.system(tftp_stop_cmd)
                self.exit_codes(0,disb_tftp),self.log_file_scrn(disb_tftp)
                os.system(tftp_disb_cmd)
            else:
                self.exit_codes(0,tftp_not_active),self.log_file_scrn(tftp_not_active)
            self.tftp_flag=2
        except Exception as e:
            self.script_abort(1,e)

    def disable_bool(self):
        '''

        disables the Boolean values if it is ON.
        '''
        try:
            no_bool = "TFTP Boolean value is set to 0"
            bool_set_0= "TFTP Boolean value is not set to 0,setting the TFTP Boolean value to 0"
            set_bool_0='setsebool -P tftp_home_dir 0 >/dev/null 2>&1'
            set_bool0='setsebool -P tftp_anon_write 0 >/dev/null 2>&1'
            if self.boolean_check == "on":
                self.exit_codes(0,no_bool),self.log_file_scrn(bool_set_0)
                os.system(set_bool_0)
                os.system(set_bool0)
            else:
                self.exit_codes(0,no_bool),self.log_file_scrn(no_bool)
            self.bool_flag=2
        except Exception as f:
            self.script_abort(1,f)


    def disable(self):
        '''

        This function is defined to call the functions to activate firewalld,
        remove TFTP port and to disable the TFTP service.
        '''
        self.activate_firewall_remove_port()
        self.disable_tftp()
        self.disable_bool()


def main():
    '''

    This main function will be executed first.
    this function will call and perform enable or disable
    according to the second argument which is passesd by user.
    '''

    if ip == "--enable":
        enb_msg="Enabling essential services for installation"
        val_enb="Validating current services state and Enabling inactive services"
        enb_complete_msg="Enabling essential services completed successfully"
        post_val_msg="Performing validation post enabling services"
        success_msg="Successfully enabled the services"
        obj = enable_disable()
        obj.exit_codes(0,enb_msg),obj.log_file_scrn(enb_msg)
        obj.exit_codes(0,val_enb),obj.log_file_scrn(val_enb)
        obj.nfs_val()
        obj.validate()
        obj.enable()
        obj.exit_codes(0,enb_complete_msg),obj.log_file_scrn(enb_complete_msg)
        obj.exit_codes(0,post_val_msg),obj.log_file_scrn(post_val_msg)
        obj.nfs_val()
        obj.validate()
        obj.post_validate('enable')
        obj.exit_codes(0,success_msg),obj.log_file_scrn(success_msg)
        obj.print_logging_detail()
        sys.exit(0)
    elif ip == "--disable":
        disb_msg="Disabling services"
        val_disb="Validating current services state and Disabling active services"
        disb_complete_msg="Disabling services completed successfully"
        post_val_msg="Performing validation post disabling services"
        success_msg="Successfully disabled the services"
        obj1 = enable_disable()
        obj1.exit_codes(0,disb_msg),obj1.log_file_scrn(disb_msg)
        obj1.exit_codes(0, val_disb), obj1.log_file_scrn(val_disb)
        obj1.validate()
        obj1.disable()
        obj1.exit_codes(0,disb_complete_msg), obj1.log_file_scrn(disb_complete_msg)
        obj1.exit_codes(0, post_val_msg), obj1.log_file_scrn(post_val_msg)
        obj1.validate()
        obj1.post_validate('disable')
        obj1.exit_codes(0, success_msg), obj1.log_file_scrn(success_msg)
        obj1.print_logging_detail()
        sys.exit(0)

def invalid_argv():
    '''

    This Function is called when the arguments which are passed to the script are wrong.
    argumets should be '--enable' to perform automation of enable process,
    and '--disable' to perform automation of disable process.
    '''
    print("======================================================================")
    print("[ERROR] : Invalid Request!. check and try again.")
    print("======================================================================\n\n")
    print("Usage: manage_mws_services.py <--action>\n\n")
    print("Valid actions are:\n")
    print("--enable          Enables services essential for installation\n")
    print("--disable         Disables TFTP service")
    sys.exit(1)

if __name__ == "__main__":
    try:
        if len(sys.argv) == 2:
            ip = sys.argv[1]
            if ip == "--enable" or ip == "--disable":
                main()
            else:
                invalid_argv()
        else:
            invalid_argv()
    except Exception:
        invalid_argv()


