#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for MWS upgrade automation
This script will replace the manual steps
used to perform MWS upgrade and will also
handle the reboot scenarios.
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
# Name      : mws_upgrade.py
# Purpose   : The script wil perform mws upgrade automatically
# ********************************************************************
"""
Modules used in the script
"""
import subprocess, os, pexpect, signal, sys, getpass, re, time, logging, base64
from os import path
from mws_function import check_service, console_check, iso_path,remove_files, get_ip,call_method,\
    fun2,exit_gracefully,check_uid,mws_pre_check,loc_log,re_run_om_media,\
    error_service,restart_service,checkcustomservice,pre_check_identity,stagelist,mws_status_file,paramiko_check,\
    remove_snap
paramiko_check()
import paramiko
"""
Global variables used within the script
"""
LOG_DIRE,path= '/var/ericsson/log/mws_upgrade/','/update_patch_mount_point'
LOG_NAME = os.path.basename(__file__).replace('.py', '_')+time.strftime("%m_%d_%Y-%H_%M_%S")+'.log'
FILE_PATH,time_for,temp_om_detail = "/var/tmp/temp.txt","%m-%d-%Y-%H:%M:%S","/var/tmp/om_detail.txt"
temp_patch_detail,hist_loc,CONSTANT2= "/var/tmp/patch_detail",'/ericsson/config/mws_history','.*password.*'
curr_media_loc,IP_FILE,CONSTANT3,skipit='/ericsson/config/mws_status',"/var/tmp/temp_ip",'ls -t',"skip\n"
TEMP_PATH,tem_log_loc,STAGE= "/var/tmp/custom_service.bsh","/var/tmp/temp_log_upgrade",'/var/tmp/stagelists'
divider,divider2,omtol,t_path,EQL="-"*100,("-"*100)+'\n',"/omtools",'/var/tmp/p_path','/var/tmp/equals'
pass_key_dir = '/ericsson/config/'
class autoupdate(object):
    """
    Class to do MWS upgrade automation
    this will wrap the multiple
    sub scripts to perform mws upgrade in the mws server
    by collecting the inputs from the user
    """
    def __init__(self):
        """
        Function to initialise the
        class object variables
        colors-->to format the log messages and print messages
        param: None
        return: None
        """
        self.logger = logging.getLogger()
        self.colors = {'RED' : '\033[91m', 'END' : '\033[00m','GREEN' : '\033[92m', 'YELLOW' : '\033[93m'}
        self.patch_iso,self.o_m_media,self.username,self.nfs_ip,self.choice,self.patch_path='','','','','',''
        self.password,self.temp_path,self.b,self.va ,self.om= '','','','',''
        if not os.path.exists(pass_key_dir):
            print("Pass key path not found. Verify mws configuration")
            sys.exit(1)
        self.file_path = os.path.join(pass_key_dir, "pass_key")
        command1 = "hostname"
        host_name = os.popen(command1).read()
        with open(self.file_path, 'w') as file:
            file.write(host_name)
        os.chmod(self.file_path, 0o755)
    def logging_configs(self):
        """
        Creates the custom logger for logs
        It create 2 different log handler
        StreamHandler which generally handles logs of
        ERROR level and FileHandler
        which handles logs of WARNING level or
        create a custom logger for logs.
        ERROR --> to display error
        WARNING --> To display warning
        return -->none
        args -->none
        LOG_DIRE --> Log dir path
        """
        if not os.path.exists(LOG_DIRE):
            os.makedirs(LOG_DIRE)
        s_handlers3 = logging.StreamHandler()
        f_handlers4 = logging.FileHandler(LOG_DIRE+LOG_NAME)
        s_handlers3.setLevel(logging.ERROR)
        f_handlers4.setLevel(logging.WARNING)
        s_formats = logging.Formatter('%(message)s')
        f_formats = logging.Formatter('%(message)s')
        s_handlers3.setFormatter(s_formats)
        f_handlers4.setFormatter(f_formats)
        self.logger.addHandler(s_handlers3)
        self.logger.addHandler(f_handlers4)
    def log_file_scrn(self, msg1, log_dec=0):
        """
        Logging into file and screen based
        on the value of log_dec variable
        if value of log_dec is 0 it will
        print simultaneously to screen and log file
        for log_dec value as 1 it will
        print to logfile directly
        Param:
              msg -> the actual message
              log_dec -> integer
        Return: None
        msg --> to display message
        return -->none
        args -->none
        """
        for i in msg1:
            a= log_dec
            if a == 0:
                self.logger.error(i)
            else:
                self.logger.warning(i)
    def print_logging_detail(self):
        """
        Prints logging details with log file for exit,
        completion and start of the script
        colors --> colors print for logs
        return --> none
        """
        self.exit_codes(3,divider)
        msg="Please find the path for MWS Upgrade script execution logs  ---> "
        self.exit_codes(3,msg+LOG_DIRE+LOG_NAME)
        self.exit_codes(3, divider2)
    def print_status(self,msgg):
        """
        dividers line function
        dividers will be used to differentiate the messages from other messages
        """
        self.exit_codes(3,divider)
        msg=msgg
        self.exit_codes(0,msg)
        self.exit_codes(3, divider2)
    def exit_codes(self, code, msg):
        """
        Script Exit function
        param: code --> Exit code of the script and
        changing type of the message
               msg --> Actual message to print on the screen
        return: None
        """
        colors = self.colors
        if code == 1:
            print(colors['RED']+"[ERROR] "+colors['END']+": "+msg)
        elif code == 2:
            print(colors['YELLOW']+"[WARNING] "+colors['END']+":"+msg)
        elif code == 3:
            print( msg)
        elif code == 4:
            print(colors['RED'] + msg + colors['END'])
        else:
            print(colors['GREEN']+"[INFO] "+colors['END']+":"+msg +colors['END'])
    def take_input(self):
        """
        The function takes input in case the script is
        executed first time, otherwise reads it from a file.
        in case of failure in any media path, next
        time it will only ask for that particular media.
        The temporary file will get deleted once script
        executed successfully.
        param: None
        return: None
        """
        if os.path.exists(FILE_PATH):
            fout = open(FILE_PATH, "r")
            out = fout.readlines()
            fout.close()
            va2=out[0].split('\n')[0].strip()
            if va2 == "skip":
                self.take_input11()
            else:
                self.o_m_media = out[0].split('\n')[0].strip()
            va=out[1].split('\n')[0].strip()
            if va == "skip":
                self.take_input1()
            else:
                self.patch_iso = out[1].split('\n')[0].strip()
            self.nfs_ip = out[2].split('\n')[0].strip()
            password = out[3].split('\n')[0].strip()
            with open(self.file_path,'r') as file1:
                dec_pass_key=file1.read().strip()
            dec = "echo \"{}\" | openssl enc -aes-256-ctr -md sha512 -a -d -salt -pass pass:{}".format(password,dec_pass_key)
            self.password = os.popen(dec).read().strip()
            self.username = out[4].split('\n')[0].strip()
            self.patch_path = out[5].split('\n')[0].strip()
        else:
            self.take_input2()
    def take_input11(self):
        """
        This function will take input for O&M Media,
        and validate the input,
        please note that we have to provide
        the mounted path only.
        return = None
        pram = None
        """
        try:
            self.temp_path= ''
            if not os.path.exists(self.temp_path):
                k1 = subprocess.check_output('pwd')
                if omtol in k1:
                    self.temp_path = k1.replace(omtol, '')
                else:
                    self.exit_codes(4, divider)
                    self.exit_codes(3, 'Script is running from invalid path. Please run from valid location')
                    self.exit_codes(4, divider2)
                    error_service()
                    self.log_fun()
                    sys.exit(1)
        except Exception:
            self.except_log("Script is running from invalid path or issue with command")
    def take_input1(self):
        """
        This function will take input for patch,
        and validate the input.
        If the path is not valid it will ask again
        """
        a = 1
        while a == 1:
            self.patch_iso = raw_input("Enter the location of patch iso: ")
            print("\n")
            var = raw_input("Please validate Patch ISO path {} Y/N : ".format(self.patch_iso))
            if var == "Y":
                a = 2
                with open(FILE_PATH, 'r') as f:
                    lines = f.readlines()
                    lines[1] = self.patch_iso + "\n"
                with open(FILE_PATH, 'w') as f:
                    f.writelines(lines)
                iso_path(self.patch_iso)
            elif var == 'N':
                self.patch_iso = ''
            else:
                print("Please enter only Y or N ")
    def take_input2(self):
        """
        This function will take input
        from user, and validate the input.
        In case of invalid input given as an input
        prams = None
        return = None
        """
        self.b = 0
        while self.b == 0:
            self.take_input21()
            self.input_ip()
            self.check_password()
            print("\nUser Provided inputs : \nPatch ISO Path : {}".format(self.patch_iso))
            print("NFS IP : {}\n".format(self.nfs_ip))
            self.take_input22()
    def take_input21(self):
        """
        This function will take input
        from user in case of invalid input
        it will ask the user again after re-run
        return = None
        prams = None
        """
        try:
            if os.path.exists(temp_om_detail):
                os.remove(temp_om_detail)
            if os.path.exists(temp_patch_detail):
                os.remove(temp_patch_detail)
            if os.path.exists(FILE_PATH):
                os.remove(FILE_PATH)
            if os.path.exists(self.temp_path):
                self.temp_path = ''
            if os.path.exists(self.patch_iso):
                self.patch_iso = ''
            if not os.path.exists(self.temp_path):
                self.take_input11()
                self.exit_codes(0, 'Enter Required Inputs for MWS Upgrade:\n')
            a=0
            while not os.path.exists(self.patch_iso):
                if a>0:
                    self.exit_codes(2,'Please enter correct patch ISO path\n')
                self.patch_iso = raw_input("Enter the location of patch iso: ")
                if '.iso' not in self.patch_iso or 'ENIQ_OS_Patch_Set' not in self.patch_iso:
                    self.patch_iso = ''
                a=a+1
            iso_path(self.patch_iso)
        except Exception:
            self.except_log("Script is running from invalid path or issue with provided command")
    def take_input22(self):
        """
        This function will take
        input from user, and validate it.
        Incase of invalid input it will ask
        again in re-run
        params = None
        return = None
        """
        val = 0
        while val == 0:
            usr = raw_input("Is the above provided input correct <yes/no/quit>: ")
            if usr not in ['yes', 'no', 'quit']:
                print("Please enter only between yes or no or quit ")
            else:
                val = 1
        if usr == "yes":
            self.b = 1
        elif usr == "no":
            print("\nEnter the required inputs again.\n")
        elif usr == 'quit':
            if os.path.exists(FILE_PATH):
                os.remove(FILE_PATH)
            sys.exit(1)
    def input_ip(self):
        """
        Function to take NFS server
        IP and check the server reachability,
        Incase of invalid input it will ask again
        in re-run
        Args: None
        return: None
        """
        try:
            while True:
                exp=r'^\s*(?:[0-9]{1,3}\.){3}[0-9]{1,3}\s*$'
                self.nfs_ip = raw_input("Enter remote NFS Server IP Address for Backup : ")
                if not re.search(exp, self.nfs_ip):
                    self.exit_codes(2, "Invalid IP Address Entered, try again\n")
                    continue
                code =  subprocess.call(["ping", self.nfs_ip, "-c", "2"], stdout=subprocess.PIPE, shell=False)
                if code:
                    self.exit_codes(2, "Server not reachable. Please make sure the correct ip is entered")
                else:
                    break
        except Exception:
            self.except_log("Issue with commands or unable to reach nfs server")
    def write_file(self):
        '''
        This function will create temp file,
        and skip the entry for om media path.
        Incase of invalid input it will ask again
        in re-run
        return = None
        prams = None
        '''
        with open(self.file_path,'r') as file1:
            enc_pass_key=file1.read().strip()
        enc = "echo {} | openssl enc -aes-256-ctr -md sha512 -a -e -salt -pass pass:{}".format(self.password,enc_pass_key)
        password = os.popen(enc).read().strip()
        self.skip='skip'
        var=[self.skip,'\n',self.patch_iso,'\n',self.nfs_ip,'\n',password,'\n',self.username,'\n',self.skip,'\n']
        fout = open(FILE_PATH, "w")
        fout.writelines(var)
        fout.close()
    def check_password(self):
        """
        Function to take the password and
        check whether it's correct or not
        Param: None
        return: None
        """
        try:
            self.username = raw_input('Enter NFS server username: ')
            self.password = getpass.getpass("Enter the NFS server password: ")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.nfs_ip, username=self.username, password= self.password)
            client.close()
        except paramiko.ssh_exception.AuthenticationException:
            self.exit_codes(2,"Authentication Failed. Please enter the correct username and password")
            self.check_password()
    def get_o_m_media_path(self):
        """
        Function to take the OM Media path and
        write all the required input to file
        Param: None
        return: None
        """
        try:
            omtol, txt = '/omtools', '/JUMP/OM_LINUX_MEDIA/'
            k1 = subprocess.check_output('pwd')
            if omtol in k1:
                om_identity_file = k1.replace(omtol, '')
            om_identity_file = om_identity_file.strip() + '/.om_linux'
            om_sprint = os.popen('cat {}'.format(om_identity_file)).read().split()
            for i in om_sprint:
                if 'media_dir=' in i:
                    om_sprint_value = i.split('=')[1].strip()
            self.o_m_media = txt + om_sprint_value + "/om_linux/"
            if os.path.exists(FILE_PATH):
                fout = open(FILE_PATH, "r")
                out = fout.readlines()
                fout.close()
                va2=out[0].split('\n')[0].strip()
                if va2 == "skip":
                    with open(FILE_PATH, 'r') as f:
                        lines = f.readlines()
                        lines[0] = self.o_m_media + "\n"
                    with open(FILE_PATH, 'w') as f:
                        f.writelines(lines)
        except Exception:
            self.except_log("issue with command or unable to find om media path")
    def update_o_m_media(self):
        """
        This function caches the om media
        this function will also upgrade the OM Media
        this function will also update the mws history file
        Param: None
        return: None
        """
        try:
            self.exit_codes(3,divider)
            loc_log("Started Caching O&M Media")
            self.exit_codes(0,"Started Caching O&M Media")
            self.exit_codes(3,divider2)
            self.write_file()
            child = pexpect.spawn('/ericsson/kickstart/bin/manage_nfs_media.bsh')
            child.logfile = sys.stdout
            child.expect('.*NFS Media you wish to manage.*')
            child.sendline('3')
            child.expect('.*Media action you wish to perform.*')
            child.sendline('1')
            child.expect('.* full path to the location of the O&M_Linux.*')
            child.sendline(self.temp_path)
            data1='.* is already installed in.*'
            data2='.*Are you sure you wish to add the area specified.*'
            i = child.expect([data1, data2])
            if i == 0:
                self.exit_codes(3,divider)
                self.exit_codes(2, "Media already cached")
                self.exit_codes(3,divider2)
            if i == 1:
                child.sendline('Yes')
                child.expect('.*number of the Media action you wish to perform.*')
                child.sendline('q')
                child.expect('.*NFS Media you wish to manage or.*')
                child.sendline('q')
                self.print_status("Successfully Cached O&M Media")
                self.exit_codes(3,divider2)
                loc_log("Successfully Cached O&M Media")
            self.get_o_m_media_path()
            self.print_status("Started O&M Media Upgrade")
            loc_log("Started O&M Media Upgrade")
            cmd = "{}/omtools/upgrade_om.bsh -p {} -a mws".format(self.o_m_media, self.o_m_media).split(' ')
            subprocess.call(cmd, stdout=sys.stdout)
            self.print_status("Successfully Completed O&M media Upgrade")
            loc_log("Successfully Completed O&M media Upgrade")
            self.history_file(1)
        except Exception:
            re_run_om_media()
            self.except_log("OM media caching failed")
    def mws_backup(self):
        """
        This function takes the MWS backup on the NFS server
        backup will be created on NFS server
        Param: None
        return: None
        """
        try:
            self.print_status("Started Creating Backup Directory on NFS Server")
            loc_log("Started Creating Backup Directory on NFS Server")
            hostname = get_ip()
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname=self.nfs_ip,username=self.username,password=self.password,look_for_keys=False)
            stdin,stdout,stderr = ssh_client.exec_command("sed -i /{}/d /etc/exports".format(hostname))
            lines = stderr.readlines()
            if "sed: can't read /etc/exports: No such file or directory\n" in lines:
                stdin,stdout,stderr = ssh_client.exec_command("touch /etc/exports")
            stdin,stdout,stderr = ssh_client.exec_command("mkdir -p /OS_BACK_UP/{}".format(hostname))
            stdin,stdout,stderr = ssh_client.exec_command('cd /OS_BACK_UP/{}'.format(hostname))
            cmd = "echo \"/OS_BACK_UP {}(rw,sync,no_root_squash)\" >> /etc/exports"
            stdin,stdout,stderr = ssh_client.exec_command(cmd.format(hostname))
            stdin,stdout,stderr = ssh_client.exec_command("exportfs -a")
            ssh_client.close()
            self.print_status("Successfully Created Backup Directory on NFS Server")
            loc_log("Successfully Created Backup Directory on NFS Server")
        except Exception:
            re_run_om_media()
            self.exit_codes(1,"Issue while creating backup directory on NFS server")
            loc_log("[ERROR]: Issue while creating backup directory on NFS server")
            self.log_fun()
    def history_file(self,act=1):
        """
        this function will crete history file
        this function will take care of history file updating
        only new entries of history and current upgrade will be present
        """
        try:
            z = self.o_m_media.split('/')
            y = z[3] + '/' + z[4]
            if act==1:
                with open(temp_om_detail, 'w') as f:
                    a = 'MWS_OM_MEDIA_STATUS - {}\n'.format(y)
                    self.om=a
                    named_tuple = time.localtime()
                    ti = time.strftime(time_for, named_tuple)
                    b = 'INST_DATE             {}\n\n'.format(ti)
                    f.writelines(a)
                    f.writelines(b)
            else:
                a = 'ls -la {}'.format(self.patch_path)
                a = a.split(' ')
                z1 = subprocess.check_output(a)
                if '.upgrade_patch_boot_media' in z1:
                    var = 'cat {}/.upgrade_patch_boot_media'.format(self.patch_path)
                    var = var.split(' ')
                    c = subprocess.check_output(var)
                c = c.split('\n')
                sp_rel,sp_bun = '',''
                for i in range(0, len(c) - 1):
                    if 'sprint_release' in c[i]:
                        sp_rel = sp_rel + c[i]
                    if 'bundle_version' in c[i]:
                        sp_bun = sp_bun + c[i]
                with open(temp_patch_detail,'w') as f:
                    self.va = 'MWS_PATCH_UPDATE_MEDIA_STATUS -       {}   {}\n'.format(sp_rel,sp_bun)
                    va1 = 'OM_MEDIA_USED_FOR_PATCHUPDATE -       {}\n'.format(y)
                    named_tuple = time.localtime()
                    ti = time.strftime(time_for, named_tuple)
                    va2 = 'INST_DATE                             {}\n'.format(ti)
                    va3= '==============================================================\n'
                    f.writelines(self.va)
                    f.writelines(va1)
                    f.writelines("PATCH_OM_SPRINT               -       {}\n".format(z[4]))
                    f.writelines(va2)
                    f.writelines(va3)
        except Exception:
            self.except_log("Issue while fetching patch and Om media details or updating mws history file")
    def mws_history(self):
        """
        this function will perform history file updating
        if history file creating for first time,
        mws status file will be read and updated in history file
        will be updated if anu upgrade happening else not
        """
        try:
            if not os.path.exists(hist_loc):
                cm = 'touch /ericsson/config/mws_history'.split(' ')
                subprocess.check_output(cm)
                os.system("chmod +755 {}".format(hist_loc))
                if os.path.exists('/ericsson/config/mws_status'):
                    file = open("/ericsson/config/mws_status", "r")
                    data2 = file.read()
                    file.close()
                    fout1 = open('/ericsson/config/mws_history', "a")
                    fout1.write(data2)
                    fout1.close()
            z = self.o_m_media.split('/')
            y = z[3] + '/' + z[4]
            a = 'MWS_OM_MEDIA_STATUS - {}\n'.format(y)
            self.om=a
            b = self.patch_path
            a = 'ls -la {}'.format(b)
            a = a.split(' ')
            z = subprocess.check_output(a)
            if '.upgrade_patch_boot_media' in z:
                var = 'cat {}/.upgrade_patch_boot_media'.format(b)
                var = var.split(' ')
                c = subprocess.check_output(var)
            c = c.split('\n')
            sp_rel,sp_bun = '',''
            for i in range(0, len(c) - 1):
                if 'sprint_release' in c[i]:
                    sp_rel = sp_rel + c[i]
                if 'bundle_version' in c[i]:
                    sp_bun = sp_bun + c[i]
            va = '{}'.format(sp_bun)
            with open(hist_loc,'r') as f:
                lines=f.readlines()
                k=str(lines)
                if self.om not in lines:
                    f =open(temp_om_detail,'r')
                    out = f.readlines()
                    with open(hist_loc,'a') as f:
                        f.writelines(out)
                if va not in k:
                    f = open(temp_patch_detail,'r')
                    out1=f.readlines()
                    with open(hist_loc,'a') as f:
                        f.writelines(out1)
        except Exception:
            self.except_log("Issue while fetching patch and Om media details or updating MWS history file")
    def rm_mount(self):
        '''
        this function will delete iso mount path
        '''
        if os.path.exists(path):
            os.system('umount -l {} >/dev/null 2>&1'.format(path))
        if not os.path.exists(path):
            os.system("mkdir {} >/dev/null 2>&1".format(path))
        cmd = "mount -t iso9660 -o loop {} {} >/dev/null 2>&1".format(self.patch_iso, path)
        os.system(cmd)
    def patch_caching(self):
        """
        Function to cache the patch
        this function will run subscript to cache the patch media
        step will be skiped if media already cached
        Param: None
        return: None
        """
        try:
            checkcustomservice(1)
            self.print_status("Started Caching Patch Media")
            loc_log("Started Caching Patch Media")
            self.rm_mount()
            child = pexpect.spawn("/ericsson/kickstart/bin/manage_upg_patch_kickstart.bsh -a add")
            child.maxsize = 1
            child.logfile = sys.stdout
            child.expect(".*full path to the location of the Upgrade Patch.*")
            child.sendline(path)
            stmt,stmt1 = "ERROR: Script aborted... ERROR: Script aborted...","full path to the location of the"
            val1,val2 = ".*Are you sure you wish.*", ".*Failed to read parameter media.*"
            i = child.expect([val1, ".*ERROR: Script aborted... This media is already inst.*", stmt,stmt1,val2])
            if i == 0:
                child.sendline("Yes")
                child.expect('.*/JUMP/UPGRADE_PATCH_MEDIA/.*', timeout=None)
                k = str(child.after)
                k = k.split()
                for i in k:
                    if '/JUMP/UPGRADE_PATCH_MEDIA/' in i:
                        k = i.strip()
                with open(t_path,'w') as f:
                    f.writelines(k)
                child.expect(pexpect.EOF,timeout=None)
                child.close()
            elif i == 1:
                k = str(child.after)
                k = k.split()
                for i in k:
                    if '/JUMP/UPGRADE_PATCH_MEDIA/' in i:
                        k = i.strip()
                with open(t_path,'w') as f:
                    f.writelines(k)
                child.expect(pexpect.EOF,timeout=None)
                child.close()
                self.exit_codes(3,divider)
                self.exit_codes(2, "The media is already cached")
                loc_log("The media is already cached")
                self.exit_codes(3,divider2)
                return
            elif i == 2 or i == 3 or i == 4:
                a=2/0
                print(a)
            self.print_status("Successfully Cached Patch Media")
            loc_log("Successfully Cached Patch Media")
            self.del_iso()
        except Exception:
            with open(FILE_PATH, 'r') as f:
                lines = f.readlines()
                lines[1] = skipit
            with open(FILE_PATH, 'w') as f:
                f.writelines(lines)
            self.except_log("Unable to cache patch media")
    @staticmethod
    def del_iso():
        '''
        this function will unmount temp mounted path
        '''
        if os.path.exists(path):
            os.system('umount -l {}'.format(path))
    def patch_update(self, stage):
        """
        This function does the patch upgrade
        this function will run subscript to perform patch upgrade
        subscript errors will be handled by exceptions
        Param: None
        return: None
        """
        try:
            with open (IP_FILE,'w') as f:
                f.write(str(self.nfs_ip))
            with open (t_path,'r') as f:
                patch_path=f.readlines()
                self.patch_path=patch_path[0].strip()
            with open(FILE_PATH, 'r') as f:
                lines = f.readlines()
                lines[5] = self.patch_path + "\n"
            with open(FILE_PATH, 'w') as f:
                f.writelines(lines)
            if os.path.exists(EQL):
                msgg = "Provided Patch bundle version is same as currently Installed version." \
                       " Hence skipping Patch upgrade\n"
                self.exit_codes(0, msgg)
                return
            self.print_status("Started Patch Media Upgrade")
            loc_log("Started Patch Media Upgrade")
            cmd="{}patch/bin/mws_upgrade_patchrhel.bsh -p {} " \
                "-a update -o {}".format(self.o_m_media, self.patch_path, self.o_m_media)
            child= pexpect.spawn(cmd,timeout=None)
            child.logfile = sys.stdout
            child.expect('.*Do you wish to continue.*')
            child.sendline('Yes')
            child.expect('.* the NFS shared Server IP.*')
            child.sendline(str(self.nfs_ip))
            u,v,w,x,y='.*patch upgrade is completed.*','.*failed.*','.*RHEL version is lower.*','.*ERROR.*','.*Error.*'
            k= child.expect(['.*Update is not required.*',u,v,w,x,y],timeout=None)
            if k == 0:
                with open('/var/tmp/patch_check','w') as f:
                    """No action required"""
                child.expect(pexpect.EOF,timeout=None)
                child.close()
            elif k == 1:
                stage = stage + 1
                with open(STAGE, 'w') as f:
                    f.write(str(stage))
                self.exit_codes(3,divider)
                self.exit_codes(2,'The system is going for reboot')
                self.exit_codes(3,divider2)
                time.sleep(5)
                subprocess.call(["init", "6"])
                child.expect(pexpect.EOF,timeout=None)
                child.close()
            elif k==2 or k==4 or k==5:
                stage = 2
                with open(STAGE, 'w') as f:
                    f.write(str(stage))
                self.except_log("Patch media upgrade failed")
            elif k==3:
                child.expect(pexpect.EOF)
                child.close()
                self.exit_codes(4, divider)
                self.exit_codes(3, 'RHEL version is lower in the  media...'
                                   'Please re-run the script with supported media')
                self.exit_codes(4, divider2)
                loc_log('[ERROR] RHEL version is lower in the  media')
                a = "rm -rf {}".format(self.patch_path).split(' ')
                subprocess.check_output(a)
                stage = 2
                with open(STAGE, 'w') as f:
                    f.write(str(stage))
                with open(FILE_PATH, 'r') as f:
                    lines = f.readlines()
                    lines[1] = skipit
                with open(FILE_PATH, 'w') as f:
                    f.writelines(lines)
                self.log_fun()
            return
        except Exception:
            stage = 2
            with open(STAGE, 'w') as f:
                f.write(str(stage))
            self.except_log("Patch media upgrade failed")
    def post_patch_update(self):
        """
        This function is called for post-patch update
        this function will run sub script to perform post patch upgrade operations
        Param: None
        return: None
        """
        try:
            self.history_file(2)
            self.mws_history()
            mws_status_file()
            if os.path.exists(EQL):
                return
            if os.path.exists('/var/tmp/patch_check'):
                return
            self.print_status("Started Patch Media Post Update")
            loc_log("Started Patch Media Post Update")
            cmd = "{}patch/bin/mws_upgrade_patchrhel.bsh -a postupgrade".format(self.o_m_media)
            child = pexpect.spawn(cmd,timeout=None)
            child.logfile = sys.stdout
            child.expect('.*patch bundle version.*',timeout=None)
            child.expect(pexpect.EOF,timeout=None)
            child.close()
            self.exit_codes(3,divider)
            self.exit_codes(0,"Successfully Completed Patch Media Upgrade and Patch Media Post Update")
            loc_log("Successfully Completed Patch Media Post Update")
            self.exit_codes(3,divider2)
        except Exception:
            stage = 3
            with open(STAGE, 'w') as f:
                f.write(str(stage))
            self.except_log("Unable to perform Patch Media Post Update. Please do Rollback and re_run the script")
    def remove_nfs_share(self):
        """
        This function removed the nfs shares after post patch update
        NFS shares will be removed by connecting to NFS server
        Param: None
        return: None
        """
        try:
            self.print_status("Started Removing NFS shares")
            loc_log("Started Removing NFS shares")
            hostname = get_ip()
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname=self.nfs_ip,username=self.username,password=self.password)
            stdin,stdout,stderr = ssh_client.exec_command("sed -i /{}/d /etc/exports".format(hostname))
            ssh_client.close()
            self.print_status("Successfully removed NFS shares")
            loc_log("Successfully removed NFS shares")
            checkcustomservice(2)
        except Exception:
            self.except_log("issue while removing NFS shares")
    def except_log(self,msg):
        """
        log function
        reads the temporary file and append data to logs
        unmasking and starting the services
        exception logs function
        logging will be done in-case of failure
        """
        self.exit_codes(4, divider)
        self.exit_codes(1, msg)
        self.exit_codes(4, divider2)
        loc_log(msg)
        self.log_fun()
    def log_fun(self):
        """
        log function
        reads the temporary file and append data to logs
        logging will be done in-case of failure
        unmasking and starting the services
        """
        self.logging_configs()
        with open(tem_log_loc, 'r') as f:
            val = f.readlines()
            self.log_file_scrn(val, 1)
        self.print_logging_detail()
        error_service()
        sys.exit(1)
def main():
    """
    The main function to wrap all functions
    stages are provided to perform re run support
    stage1:
        1.mws health checking
        2.collecting inputs
        3.pre checking the identity files of OM media and Patch media
        4.om media caching and upgrading
        5.removing snapshot
        6.backup to nfs
    stage2:
        1.reading user provided inputs from temporary file
        2.patch caching
        3.patch upgrade
    stage3:
        1.reading user provided inputs from temporary file
        2.post patch update
    stage4:
        1.reading user provided inputs from temporary file
        2.remove snap shot
        3.remove nfs shares
    removing temporary files used
    starting the services
    Param: None
    return: None
    """''
    au = autoupdate()
    print("\n")
    au.exit_codes(3,"#"*50)
    au.exit_codes(3,"Starting the execution of mws_upgrade.py")
    au.exit_codes(3,"#"*50)
    signal.signal(signal.SIGINT, exit_gracefully)
    check_uid()
    stage = stagelist()
    if stage == 1:
        mws_pre_check()
        au.take_input()
        pre_check_identity()
        au.update_o_m_media()
        remove_snap()
        au.mws_backup()
        stage = stage + 1
        with open(STAGE, 'w') as f:
            f.write(str(stage))
    if stage == 2:
        au.take_input()
        au.patch_caching()
        stage = 3
        with open(STAGE, 'w') as f:
            f.write(str(stage))
        au.patch_update(stage)
    if int(stage) == 3:
        au.take_input()
        stage = stage + 1
        with open(STAGE, 'w') as f:
            f.write(str(stage))
        au.post_patch_update()
    if stage == 4:
        au.take_input()
        remove_snap()
        au.remove_nfs_share()
    print("\n")
    au.exit_codes(3,"-"*100)
    au.exit_codes(0,"------------------Successfully completed MWS Upgrade----------------")
    loc_log("Successfully completed MWS Upgrade")
    au.logging_configs()
    au.exit_codes(3,"-"*100)
    with open(tem_log_loc,'r') as f:
        val=f.readlines()
        au.log_file_scrn(val,1)
    au.print_logging_detail()
    os.popen("rm {}".format(au.file_path))
    remove_files()
    time.sleep(5)
    os.system("systemctl start serial-getty@ttyS0.service")
if __name__ == "__main__":
    """
    function to call main
    re-start the services
    checking the services
    """
    restart_service()
    check_service()
    main()

