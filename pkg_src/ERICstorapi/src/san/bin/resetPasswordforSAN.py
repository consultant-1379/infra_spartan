#!/usr/bin/python
# -*- coding: utf-8 -*-
""" Script for SAN Copy migration """
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
# Name      : resetPasswordforSAN.py
# Purpose   : The script will perform reset password for unity and vnx
# ********************************************************************
import re
import getpass
import sys
from os import path
import subprocess
import signal
import pexpect
import time
PWD_UPDATE = '/ericsson/storage/san/bin/vnx_unitypwdupdate.py'
class ResetPasswd(object):
    """
    Description: Class is to reset the password for vnx,unity and UnityXT with CLI
    """
    def __init__(self):
        """
        Init function to initialize the class variable
        """
        self.storage_uconf = '/ericsson/storage/san/plugins/unity/etc/unity.conf'
        self.storage_vconf = '/ericsson/storage/san/plugins/vnx/etc/clariion.conf'
    @staticmethod
    def exe_cmd(cmd):
        """
        Function to execute the system commands
        """
        try:
           subprocess.check_output('{}'.format(cmd), shell=True)
           return 0
        except subprocess.CalledProcessError as err:
           print ('#'*40)
           print (err.output)
           print ('#'*40)
           print ("ERROR: Password did not changed")
           exit(1)
    def get_storage_ip(self, stype):
        """
        Function to get the storage IP from uniy.conf and clarrion.conf
        """
        if stype == 'Unity' or stype == 'UnityXT':
            stype = self.storage_uconf
        else:
            stype = self.storage_vconf
        if not  path.exists(stype):
            print ('[Error]:Storage is not configured, Please check')
            exit(1)
        with open(stype, 'r') as conf_file:
            output = conf_file.read().splitlines()
        storage_ip = ''.join([i.split('=>')[1] for \
                              i in output if 'sp' in i])
        #storage_ip = re.search(r'((\d{1,3}.)+\d{1,3})', storage_ip).group(0)
        storage_ip =  re.findall(r'((\d{1,3}.)+\d{1,3})', storage_ip)
        return storage_ip
    def reset_password(self, storage_type):
        """
        Reset password for unity, UnityXT and vnx
        Storage Type:
        0 = vnx
        1 = Unity and UnityXT
        """
        while True:
            admin_name = raw_input('Enter admin User name : ')
            if len(admin_name) == 0 or ' ' in admin_name:
                print ('[Error]: User name can\'t be empty or with space')
                continue
            curr_passwrd = getpass.getpass('Enter Current Password : ')
            break
        new_passwrd = self.check_policy(storage_type)
        storage_ip1 = self.get_storage_ip(storage_type)
        om_pth = "/eniq/installation/config/om_sw_locate"
        mws_blade_ip = subprocess.check_output('cat %s'%(om_pth),
                                                shell=True).split("@")[0]
        mws_password = getpass.getpass("Enter the MWS "+ \
                                       "password of "+mws_blade_ip+": ")
        flag = 0
        for storage_ip in storage_ip1:
            storage_ip = storage_ip[0]
            if storage_type == 'Unity' or storage_type =='UnityXT':
                 cmd = 'uemcli -d {sip} -u {adm} \
                       -p {cpass} /user/account -id \
                       user_{adm} set -passwd {npass} \
                       -oldpasswd {cpass}'.format(sip=storage_ip,adm=admin_name,cpass=curr_passwrd,npass=new_passwrd)
            else:
                 cmd = '/opt/Navisphere/bin/naviseccli  -h \
                       {sip} -User {adm} -Password {cpass} \
                       -Scope 0 security -changepassword \
                       -newpassword {npass} -o'.format(sip=storage_ip,
                                                       adm=admin_name,cpass=curr_passwrd,npass=new_passwrd)
            if flag == 0:
                if self.exe_cmd(cmd) == 0:
                    print (' [INFO]: Successfully changed the '+ \
                          'password for {}({})'.format(storage_type, storage_ip))
                flag = 1
            else:
                time.sleep(10)
            print (' [INFO]: Please wait, Updating password all over ENIQ servers and MWS for %s'%(storage_ip))
            self.script_pexpect_handler(storage_type, admin_name,new_passwrd, storage_ip,mws_blade_ip, mws_password)
    @staticmethod
    def script_pexpect_handler(storage_type, admin_name,
                               new_passwrd, storage_ip,
                               mws_blade_ip, mws_password):
        """
        Function to run the password update script
        """
        if not path.exists("/eniq/installation/config/om_sw_locate"):
            print ('[Error]: /eniq/installation/config/om_sw_locate'+ \
                  'file not found password resetted but not updated')
            exit(1)
        if storage_type == 'Unity' or storage_type == 'UnityXT':
            stype = 1
        else:
            stype = 0
        try:
            pass_update_handler = pexpect.spawn('{} {}'.format(PWD_UPDATE, stype))
            pass_update_handler.expect('Enter the MWS password of.+')
            pwd_update_log = pass_update_handler.before.split(' ')[5]
            pass_update_handler.sendline(mws_password)
            pass_update_handler.expect('.+Enter the storage ip:.+')
            pass_update_handler.sendline(storage_ip)
            pass_update_handler.expect('.+Enter the storage Username.+')
            pass_update_handler.sendline(admin_name)
            pass_update_handler.expect('.+Enter the storage password:.+')
            pass_update_handler.sendline(new_passwrd)
            pass_update_handler.expect(pexpect.EOF)
            if re.search('[fF]ailed', pass_update_handler.before):
                print (' [Error]: Failed to update the '\
                      "Storage Password over Eniq Server\'s or MWS")
                print ('Please check the log for more details %s'%(pwd_update_log.strip()))
                exit(1)
        except Exception:
             print (' [Error]: Failed to update the '\
                   "Storage Password over Eniq Server\'s or MWS")
             print ('Please check the log for more details %s'%(pwd_update_log.strip()))
             exit(1)
        print (' [INFO]: Storage Password updated Successfully on ENIQ server and MWS')
    @staticmethod
    def check_policy(storage_type):
        """
        description: Function to Check and
                     confirm the password policy
        return: <str> new password
        """
        pattern = r'[\'\\><"|)(&`\s;!$]'
        while True:
            newpass1 = getpass.getpass('Enter new password: ')
            if storage_type == 'Unity' or storage_type == 'UnityXT':
                if not (re.search(r'.{8,40}$', newpass1) \
                    and re.search(r'[A-Z]', newpass1) \
                    and re.search(r'[a-z]', newpass1) \
                    and re.search(r'[\d]', newpass1) \
                    and re.search(r'[@#%^*?_~]', newpass1) \
                    and not re.search(pattern, newpass1) \
                    and re.search(r'^[A-Za-z0-9]', newpass1)):
                    print ('[Error]: Password is not met with a policy requirements, Try again')
                    continue
            else:
                if not (re.search(r'.{8,40}$', newpass1) \
                    and re.search(r'^[A-Za-z0-9]', newpass1) \
                    and not re.search(pattern, newpass1)):
                    print ('[Error]: Password is not met with a policy requirements, Try again')
                    continue
            userpass = getpass.getpass('Retype new password: ')
            if newpass1 != userpass:
                print ('[Error]: Sorry, passwords do not match, Try again')
                continue
            break
        return userpass
def main():
    """
    Main function to wrap the all class funtion
    """
    print ("1: VNX\n2: Unity\n3: UnityXT\n4: EXIT")
    try:
         res = input('Enter your choice(EX: 1 or 2 or 3 or 4 ): ')
    except Exception:
         print ('[Error] :Invalid Selection')
         exit(1)
    if res == 4:
        exit(1)
    elif res == 1:
        print ('[INFO]: Changing password for VNX')
        print (' NOTE : Password policy as below')
        print ('        *  Length should be 8 to 40 characters\n'+ \
               r'        *  Should not contain any special character from \'$!;\><\"|)(&`space')
        storage_type = 'vnx'
    elif res == 2 or res == 3:
        cmd={2:"Unity",3:"UnityXT"}
        val=cmd[res]
        print ('[INFO]: Changing password for {}'.format(val))
        print (" NOTE : Password policy as below")
        print("        *  Length should be 8 to 40 characters\n"+ \
              "        *  Should contain at least \"one upper and lower case\"\n"+ \
              "        *  Should start with \"Alphabet or number\"\n"+ \
              "        *  Should contain at least \"one number\" and "+ \
                        "\"one special character\" from @#%^*?_~\n")
        storage_type = '{}'.format(val)
    else:
        print ('[Error] :Invalid Selection')
        exit(1)
    resetobj = ResetPasswd()
#    resetObj.script_pexpect_handler('unity', 'test', 'Vigu@1234', '10.45.56.129')
    resetobj.reset_password(storage_type)
def exit_gracefully(signum, frame):
    """
        restore the original signal handler as otherwise evil things will happen
        in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
    """
    print ("Script Exiting Abnormally")
    exit(1)
if __name__ == '__main__':
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exit_gracefully)
    main()
exit(0)

