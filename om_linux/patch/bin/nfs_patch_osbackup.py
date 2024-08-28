#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script to add or remove hosts entry from /etc/exports file in MWS server for OS Backup
"""
# ********************************************************************
# Ericsson Radio Systems AB                                     SCRIPT
# ********************************************************************
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
# Name      : nfs_patch_osbackup.py
# Purpose   : Script to add or remove hosts entry from /etc/exports file in MWS server for OS Backup
# ********************************************************************

import subprocess, os, pexpect, signal, sys, getpass, re, time, logging, base64, paramiko
NM='/eniq/installation/config/upgrade_params.ini'
class os_backup(object):
    '''
    This class will perform os backup
    '''

    def __init__(self):
        self.host_passer=''
        self.engine,self.cord,self.read1,self.read2 = '', '', '', ''
        self.mwsip,self.uname,self.pwd,self.om_path,self.task='','','','',''
    def os_back_up_fun(self):
        '''
        this function will take the argument and pass it to the subscript.
        '''
        try:
            self.a= sys.argv[1]
            if self.a=='add':
                self.task='add'
            elif self.a=='remove':
                self.task='remove'
            if self.a!='add' and self.a!='remove':
                self.help_fun()
        except Exception:
            self.help_fun()
    @staticmethod
    def help_fun():
        '''
        This function will display the arguments option to the user.
        Params : None
        '''
        print('===============================================================================================\n')
        print('   Please Pass Arguments  : Example (python nfs_patch_osbackup.py {add/remove})           \n\n')
        print('add            to add hosts in /etc/exports file\n')
        print('remove         to remove hosts from /etc/exports file\n')
        print('===============================================================================================\n')
        sys.exit(1)
    def read_hosts(self):
        '''
        This function will take and filter out the hosts.
        Params : None
        '''
        try:
            hosts=[]
            if not os.path.exists('/etc/hosts'):
                print('Hosts file not present under /etc/hosts')
                sys.exit(1)
            with open('/etc/hosts','r') as f:
                val=f.readlines()
                for i in val:
                    if 'engine' in i or 'webserver' in i or 'dwh_reader_1' in i or 'dwh_reader_2' in i:
                        j=i.strip('\n')
                        hosts.append(j)
            if len(hosts)<=0:
                print('No Hosts found...... Exiting the Script')
                sys.exit(1)
            self.dep_type(hosts)
        except Exception as err:
            print(err)
            sys.exit(1)
    def dep_type(self,hosts):
        '''
        This function will check the deployment type.
        Params : None
        '''
        try:
            if len(hosts)==1:
                for i in hosts:
                    i=i.split()
                    self.host_passer=self.host_passer+i[1]
            elif len(hosts)>=2:
                for i in hosts:
                    if 'engine' in i:
                        self.engine=self.engine+i
                        self.engine=self.engine.split()
                    elif 'webserver' in i:
                        self.cord=self.cord+i
                        self.cord=self.cord.split()
                    elif 'dwh_reader_1' in i:
                        self.read1=self.read1+i
                        self.read1=self.read1.split()
                    elif 'dwh_reader_2' in i:
                        self.read2=self.read2+i
                        self.read2=self.read2.split()
                self.single_or_multi()
        except Exception as err:
            print(err)
            sys.exit(1)
    def single_or_multi(self):
        '''
        This function will check for single or multibalde server.
        params : None
        '''
        if self.engine[1] == self.cord[1] and self.engine[0]==self.cord[0]:
            self.host_passer=self.host_passer+self.engine[1]
        else:
            self.host_passer=self.host_passer+self.engine[1]+' '+self.cord[1]+' '+self.read1[1]+' '+self.read2[1]
    def connect_to_mws(self):
        '''
        This function will connect to mws and perform os backup.
        Params :None
        '''
        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname=self.mwsip, username=self.uname, password=self.pwd, look_for_keys=False)
            stdin, stdout, stderr = ssh_client.exec_command('{}'.format(self.om_path))
            log_error = stdout.read().decode().strip()
            if 'ERROR' in log_error:
                print(log_error)
                sys.exit(2)
        except Exception as err:
            print(err)
            sys.exit(1)
    def mws_inputs(self):
        """
        This function will collect the inputs from the ENIQ input file
        params :NONE
        """
        try:
            with open(NM,"r") as f:
                out=f.readlines()
                for i in range(0,len(out)):
                   if "mws_ip" in out[i]:
                       data = out[i]
                       data1 = data.split("=")
                       self.mwsip= str(data1[1]).strip()
                   if "mws_uname" in out[i]:
                       data = out[i]
                       data2 = data.split("=")
                       self.uname = str(data2[1]).strip()
                   if "mws_pwd" in out[i]:
                       data=out[i]
                       data3 = data.split("=", 1)
                       pwd = str(data3[1]).strip("\n")
                       pssword = base64.b64decode(pwd)
                       self.pwd = pssword.strip("\n")
                   if "om_sw" in out[i]:
                       data=out[i]
                       data4=data.split("=")
                       data5 = data4[1]
                       a = data5.split('JUMP')
                       z=a[1].strip()
                       self.slash_add(z)
        except Exception as err:
            print(err)
            sys.exit(1)
    def slash_add(self,z):
        '''
        This function will add slash at the end of mws path
        params : Yes
        return : NONE
        '''
        if z[-1] != '/':
            z = z + '/'
        self.om_path = '/JUMP' + z + 'om_linux/patch/bin/nfs_patch_osbackup' \
                                     ' -a {} -c \"{}\"'.format(self.task, self.host_passer)
        print(self.om_path)

def main():
    '''
    This is the main function
    return : NONE
    Params : None
    '''
    at=os_backup()
    at.os_back_up_fun()
    at.read_hosts()
    at.mws_inputs()
    at.connect_to_mws()
if __name__ == "__main__":
    main()
    sys.exit(0)

