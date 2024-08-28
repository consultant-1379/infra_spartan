#!/usr/bin/python
"""
 -*- coding: utf-8 -*-
 ********************************************************************


 (c) Ericsson Radio Systems AB 2019 - All rights reserved.

 The copyright to the computer program(s) herein is the property
 of Ericsson Radio Systems AB, Sweden. The programs may be used
 and/or copied only with the written permission from Ericsson Radio
 Systems AB or in accordance with the terms and conditions stipulated
 in the agreement/contract under which the program(s) have been
 supplied.

 ********************************************************************
 Name      : mws_migration.py
 Purpose   : This script performs the MWS migration for MWS servers.
 Exit Values:
 ********************************************************************
"""
import time,signal,sys,os,subprocess,socket,pexpect,paramiko,getpass
import mws_post_migration as util
#Global variables used within the script
KEY = "sample_key"
LOG_DIRECT = '/var/ericsson/log/mws_migration/'
LOG_NAME = os.path.basename(__file__).replace('.py', '') + '.log'
old_inf_path='/var/tmp/old_interface_files'
cmd_exe_err="Command Execution issue"
cmd_exe_failed="Command Execution Failure"
failed_create_msg="Failed to create "
touch_cmd='touch '
failed_copy_intf="Failed to copy intf files to "
mkdir_cmd="mkdir -p "
rm_rf_cmd="rm -rf "
copy_failed="Failed to copy "
add_paramsintf_cmd="cat {0} 2> /dev/null | grep -E 'NAME|UUID|HWADDR|DEVICE' | sed -Ei 's/NAME=.*/NAME={1}/; " \
                   "s/UUID=.*/UUID={3}/; s/HWADDR=.*/HWADDR={2}/; s/DEVICE=.*/DEVICE={4}/' {0}"
VAR_TMP = "/var/tmp/"
STAGE="/var/tmp/.mws_mig_stage"
NEW_IF_FILE = VAR_TMP+".new_if"
OLD_IF_FILE = VAR_TMP+".old_if"
TMP_LOGS = "mws_mig_tmp_logs.log"
class mwsmigration(object):
    """
    Class to do MWS migration Automation
    param: None
    return: None
    """
    def __init__(self):
        """
        Function to initialise the
        class object variables
        param: None
        return: None
        """
        self.cred_file = "/var/tmp/cred"
        self.new_if_file = "/var/tmp/newif"
        self.old_if_file = "/var/tmp/oldif"
        self.new_cred_file = "/var/tmp/new_cred"
        self.new_service_ifcfg, self.new_storage_ifcfg, self.new_backup_ifcfg, self.new_mngmnt_ifcfg = "", "", "", ""
        self.old_service_ifcfg, self.old_storage_ifcfg, self.old_backup_ifcfg, self.old_mngmnt_ifcfg = "", "", "", ""
        self.new_service_ifbkp, self.new_storage_ifbkp, self.new_backup_ifbkp, self.new_mngmnt_ifbkp = "", "", "", ""
        self.old_service_ifbkp, self.old_storage_ifbkp, self.old_backup_ifbkp, self.old_mngmnt_ifbkp = "", "", "", ""
        self.new_man_interface,self.new_service_interface = "", ""
        self.new_storage_interface,self.new_backup_interface = "", ""
        self.old_backup_interface, self.old_service_interface = "", ""
        self.old_storage_interface, self.old_man_interface = "", ""
        self.interface_name_list = ['service', 'storage', 'backup', 'management']
        self.new_interface_lst = [self.new_service_interface, self.new_storage_interface, self.new_backup_interface,
                                  self.new_man_interface]
        self.old_interface_lst = [self.old_service_interface, self.old_storage_interface, self.old_backup_interface,
                                  self.old_man_interface]
        self.N = '/etc/sysconfig/network-scripts/ifcfg-'
        self.M = '/etc/network_conf_backup/ifcfg-'
        self.prev_path = '/etc/previous_network_conf/ifcfg-'
    def hardware_check_wrapper(self):
        """
        This function performs the pre MWS
        migration checks
        param: None
        return: None
        """
        try:
            self.old_mws_input()
            util.check_hardware_type(self.old_ip, self.old_password)
            util.check_userid()
            util.migration_precheck(self.old_ip, self.old_password)
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def get_input(self):
        """
        This function calls all the other functions
        which takes user input
        param: None
        return: None
        """
        try:
            self.old_mws_input()
            self.old_bkp_inf_file()
            self.new_mws_input()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def chk_old_srvr_auth(self):
        """
        Function to check password whether it's correct or not
        Param: None
        return: None
        """
        try:
            util.exit_codes(6, "Checking user authentication")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.old_ip, username=self.old_username, password=self.old_password)
            client.close()
            return True
        except paramiko.ssh_exception.AuthenticationException:
            util.exit_codes(4, "Authentication failed. please enter the correct username and password")
            return False
    @staticmethod
    def add_cred(file, cred_lst):
        """
        saving user inputs inside a file for
        backup puprose
        param: file name, credential list
        return: None
        """
        try:
            util.exit_codes(6, "Adding input details in "+file)
            if os.path.exists(file):
                os.remove(file)
            with open(file, 'a') as f:
                for i in cred_lst:
                    f.writelines(i+"\n")
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def get_cred(self):
        """
        reads the inputs from file for
        Source MWS
        param: None
        return: None
        """
        try:
            util.exit_codes(6, "Getting user input for source MWS from file")
            with open(self.cred_file, 'r') as f:
                out = f.read().splitlines()
                self.old_ip, self.old_username, password = out[0].strip(), out[1].strip(), out[2].strip()
            dec = "echo \"{}\" | openssl enc -aes-256-ctr -md sha512 -a -d -salt -pass pass:{}".format(password, KEY)
            self.old_password = os.popen(dec).read().strip()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def auth_new_cred(self):
        """
        This function validates if the input collected
        from cred file are valid
        param: None
        return: None
        """
        try:
            if self.old_ip.strip() == "" or self.old_username.strip() == "" or self.old_password.strip() == "":
                util.exit_codes(0, "Collecting fresh inputs for source MWS")
                cmd = rm_rf_cmd + self.cred_file
                if os.system(cmd) != 0:
                    util.exit_codes(1, cmd_exe_failed)
                return self.old_mws_input()
            if not self.chk_old_srvr_auth():
                os.remove(self.cred_file)
                return self.old_mws_input()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def old_mws_input(self):
        """
        This function will collect input on Source MWS.
        param: None
        return: None
        """
        try:
            if not os.path.exists(self.cred_file):
                util.exit_codes(0, "Getting user input for source MWS")
                self.old_ip = raw_input("Enter source MWS IP address: ")
                if not util.validate_ip(self.old_ip):
                    util.exit_codes(4, "Enter Valid IP Address")
                    return self.old_mws_input()
                self.old_username = raw_input("Enter source MWS username: ")
                self.old_password = getpass.getpass(prompt="Enter source MWS password: ")
                if self.chk_old_srvr_auth():
                    enc = "echo {} | openssl enc -aes-256-ctr -md sha512 -a -e -salt -pass pass:{}".format(
                        self.old_password,
                        KEY)
                    passwd = os.popen(enc).read().strip()
                    cred_lst = [self.old_ip, self.old_username, passwd]
                    self.add_cred(self.cred_file, cred_lst)
                else:
                    return self.old_mws_input()
            else:
                self.get_cred()
                self.auth_new_cred()
            if not self.old_ip or not self.old_username or not self.old_password:
                util.exit_codes(4, "Please enter all the details for source MWS properly")
                return self.old_mws_input()
            self.port = 22

        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def get_new_cred(self):
        """
        This function reads the inputs from file for
        Target MWS
        param: None
        return: None
        """
        try:
            util.exit_codes(6, "getting target MWS input from "+self.new_cred_file)
            with open(self.new_cred_file, 'r') as f:
                out = f.read().splitlines()
                self.new_host, self.new_ip = out[0].strip(), out[1].strip()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def new_mws_input(self):
        """
        This function will collect input on Target MWS.
        param: None
        return: None
        """
        try:
            if not os.path.exists(self.new_cred_file):
                self.new_host = socket.gethostname()
                if self.new_host.strip() == "":
                    util.exit_codes(1, "Unable to fetch host name")
                cmd = "cat /etc/hosts 2> /dev/null | grep " + self.new_host + " | awk '{print $1}'"
                self.new_ip = os.popen(cmd).read().strip()
                if self.new_ip.strip() == "":
                    util.exit_codes(1, "Unable to fetch host IP")
                new_cred_lst = [self.new_host, self.new_ip]
                self.add_cred(self.new_cred_file, new_cred_lst)
            else:
                self.get_new_cred()
                if self.new_host.strip() == "" or self.new_ip.strip() == "":
                    util.exit_codes(0, "Collecting fresh inputs for target MWS")
                    cmd = rm_rf_cmd+self.new_cred_file
                    if os.system(cmd) != 0:
                        util.exit_codes(1, cmd_exe_failed)
                    return self.new_mws_input()
            self.new_mws_interface_files()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def get_new_if(self):
        """
        This function reads the interface inputs from file for
        Target MWS
        param: None
        return: None
        """
        try:
            util.exit_codes(6, "Getting target MWS interface details")
            with open(self.new_if_file, 'r') as f:
                out = f.read().splitlines()
                self.new_storage_interface = out[0].strip()
                self.new_backup_interface, self.new_man_interface = out[1].strip(), out[2].strip()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def new_mws_interface_files(self):
        """
        This function will collect
        interface details on
        Target MWS.
        param: None
        return: None
        """
        try:
            util.exit_codes(6, "Collecting information of network interfaces on target MWS")
            cmd1 = "ifconfig -a | cut -d' ' -f1 2> /dev/null | grep ':' | sed 's/://g' 2> /dev/null" \
                   " | grep -v lo >/var/tmp/new_interfaces.txt"
            if os.system(cmd1) != 0:
                util.exit_codes(1, cmd_exe_failed)
            cmd = "ip a 2> /dev/null | grep " + self.new_ip + " | awk '{print $NF}'"
            service_name = os.popen(cmd).read()
            service_op = service_name.splitlines()
            service_int = service_op[0]
            with open("/var/tmp/new_interfaces.txt", 'r') as f:
                list1 = f.readlines()
                self.var5 = []
                for i in list1:
                    self.var5.append(i.replace("\n", ""))
            if service_int in self.var5:
                self.new_service_interface = service_int
                self.var5.remove(service_int)
            if os.path.exists(self.new_if_file):
                self.get_new_if()
            else:
                print("=" * 70)
                util.exit_codes(0, "Collecting information of network interfaces on target MWS")
                print("=" * 70)
                old_if = [self.old_storage_interface, self.old_backup_interface, self.old_man_interface]
                self.new_storage_interface, self.new_backup_interface, self.new_man_interface = util.get_n_if(old_if,
                                                                                                              self.var5)
                new_if_lst = [self.new_storage_interface, self.new_backup_interface, self.new_man_interface]
                self.add_cred(self.new_if_file, new_if_lst)
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def old_mws_bkp_details(self):
        """
        Step :2b,2c,6 in DOC
        This old_mws_bkp_details function
        will take backup of kickstart Medias
        and patch media on Source MWS
        """
        try:
            util.exit_codes(0, "Collecting kickstart and patch media")
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.old_ip, password=self.old_password)
            variable3 = '/ericsson/kickstart/bin/manage_upg_patch_kickstart.bsh -a list > /var/tmp/patch_media'
            variable4 = '/ericsson/kickstart/bin/manage_linux_kickstart.bsh -a list > /var/tmp/Kickstart_areas'
            stdin, stdout, stderr = client.exec_command(variable3)
            stdin, stdout, stderr = client.exec_command(variable4)
            client.close()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def new_mws_backup_dir(self):
        """
        Step: 3 in DOC
        This new_mws_backup_dir() function
        creates the previous_network_conf
        param: None
        return: None
        """
        try:
            print("=" * 80)
            util.exit_codes(0, "Started transferring configuration files from source MWS to target MWS")
            print("=" * 80)
            util.exit_codes(0, "Creating /etc/previous_network_conf on target MWS")
            self.previous_ntwrk_conf_dir1 = '/etc/previous_network_conf'
            util.check_local_dir(self.previous_ntwrk_conf_dir1)
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def network_conf_bkp(self):
        """
        Step:3
        in DOC
        This network_conf_bkp function
        takes backup of /etc/hostname
        /etc/exports /etc/network-scripts/
        to /etc/previous_network_conf on Target MWS
        param: None
        return: None
        """
        try:
            util.exit_codes(0, "Started copying configuration files under /etc to "
                               "/etc/previous_network_conf in target MWS")
            self.prv_ntwk_conf_dir1 = "/etc/previous_network_conf"
            util.check_local_dir(self.prv_ntwk_conf_dir1)
            v1 = 'cp -r /etc/hostname /etc/exports /etc/hosts* /etc/sysconfig/network-scripts/* ' \
                 '/etc/previous_network_conf'
            if os.system(v1) != 0:
                util.exit_codes(1, cmd_exe_failed)
            util.exit_codes(0, "Successfully copied configuration files to /etc/previous_network_conf in target MWS")
        except Exception as e:
            print(e)
            util.exit_codes(cmd_exe_err, 1)
    def rsync_data(self):
        """
        Step:4 in DOC
        This rsync_data() function is doing
        rsync of /JUMP directory contents
        from Source MWS to Target MWS
        param: None
        return: None
        """
        try:
            util.exit_codes(0, "Rsync started")
            util.exit_codes(0, "Please wait!....rsync execution is in progress")
            cmd = rm_rf_cmd+"/root/.ssh/known_hosts"
            if os.system(cmd) != 0:
                util.exit_codes(1, cmd_exe_failed)
            shl_cmd = "/usr/bin/rsync -avz --info=progress2 --no-inc-recursive --exclude=DHCP_CLIENTS/LINUX/ " \
                      "root@{1}:/JUMP/ /JUMP | python -c 'from {0} import read_stdin, progress_bar_wrapper; " \
                      "progress_bar_wrapper()'".format("mws_post_migration", self.old_ip)
            child = pexpect.spawn('/bin/sh', ['-c', shl_cmd], timeout=None)
            child.expect('Are you sure you want to continue connecting (yes/no)?')
            child.sendline('yes')
            child.expect('root@{}\'s password:'.format(self.old_ip))
            child.sendline(self.old_password)
            child.logfile = sys.stdout
            index = child.expect(['rsync error', pexpect.EOF])
            child.close()
            if index == 0:
                raise RuntimeError("Rsync command execution failure")
            util.exit_codes(0, "Rsync completed")
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_failed)
    def get_old_if(self):
        """
        reads the interface inputs from file for
        Source MWS
        param: None
        return: None
        """
        try:
            util.exit_codes(6, "Getting interface details from file: "+self.old_if_file)
            with open(self.old_if_file, 'r') as f:
                out = f.read().splitlines()
                self.old_storage_interface = out[0].strip()
                self.old_backup_interface, self.old_man_interface = out[1].strip(), out[2].strip()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def old_bkp_inf_file(self):
        """
        step6: in DOC
        This old_bkp_inf_file function takes names of
        service, storage and backup interfaces names
        of Source MWS
        param: None
        return: None
        """
        try:
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.old_ip, password=self.old_password)
            stdin, stdout, stderr = client.exec_command(
                "ip -o -f inet addr show | awk '/scope global/ {print $2}' >/var/tmp/old_interfaces.txt")
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1, "Failed getting source MWS interface list")
            cmd = "ip a | grep " + self.old_ip + " | awk '{print $NF}'"
            stdin, stdout, stderr = client.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1, "Failed to get Host IP")
            k = stdout.read().strip()
            self.old_service_interface = ""
            sftp = client.open_sftp()
            file = sftp.open('/var/tmp/old_interfaces.txt')
            inputs = file.read()
            var2 = inputs.splitlines()
            if k in var2:
                self.old_service_interface = k
                var2.remove(self.old_service_interface)
            if os.path.exists(self.old_if_file):
                self.get_old_if()
            else:
                print("="*70)
                util.exit_codes(0, "Collecting information of network interfaces on source MWS")
                print("="*70)
                self.old_storage_interface, self.old_backup_interface, self.old_man_interface = util.get_if('old',
                                                                                                            var2)
                old_if_lst = [self.old_storage_interface, self.old_backup_interface, self.old_man_interface]

                self.add_cred(self.old_if_file, old_if_lst)
            client.close()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def old_mws_backup_dir(self):
        """
        Step:7a in DOC
        This function will create
        network_conf_backup directory
        under /etc on Source MWS
        param: None
        return: None
        """
        try:
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.old_ip, password=self.old_password)
            util.exit_codes(6, "Creating /etc/network_conf_backup directory on source MWS")
            self.ntwrk_conf_backup_dir1 = '/etc/network_conf_backup'
            stdin, stdout, stderr = client.exec_command('mkdir -p ' + self.ntwrk_conf_backup_dir1)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1, failed_create_msg + self.ntwrk_conf_backup_dir1)
        except Exception as e:
            util.exit_codes(1, cmd_exe_err)
            print(e)
    @staticmethod
    def create_bckp(client1, file1, file2, file3, file4):
        """
        copies backup file for
        interface details
        param: None
        return: None
        """
        try:
            sftp = client1.open_sftp()
            if len(file1) > 0 and len(file2) > 0:
                file = sftp.open(file3)
                inputs = file.read()
                if inputs:
                    util.exit_codes(6, "copying interface details from " + file3 + " to " + file4)
                    cmd = 'cat ' + file3 + ' >' + file4
                    stdin, stdout, stderr = client1.exec_command(cmd)
                    exit_status = stdout.channel.recv_exit_status()
                    if exit_status != 0:
                        util.exit_codes(1, failed_copy_intf + file2)
            return True
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    @staticmethod
    def touch_old(client1, file1, file2):
        """
        creates backup files
        for interface details
        param: None
        return: None
        """
        try:
            if len(file1) > 0:
                util.exit_codes(6, "Creating " + file2)
                stdin, stdout, stderr = client1.exec_command((touch_cmd + file2))
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    print(failed_create_msg + file2)
                    util.exit_codes(1, "Failed creating the file "+file2+ " in source MWS server")
                    sys.exit(1)
            return True
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def initialize_variable(self):
        """
        This function helps initialize
        variables.
        param: None
        return: None
        """
        try:
            self.new_service_ifcfg = self.N + self.new_service_interface
            self.new_storage_ifcfg = self.N + self.new_storage_interface
            self.new_backup_ifcfg = self.N + self.new_backup_interface
            self.new_mngmnt_ifcfg = self.N + self.new_man_interface
            self.old_service_ifcfg = self.N + self.old_service_interface
            self.old_storage_ifcfg = self.N + self.old_storage_interface
            self.old_backup_ifcfg = self.N + self.old_backup_interface
            self.old_mngmnt_ifcfg = self.N + self.old_man_interface
            self.new_service_ifbkp = self.prev_path + self.new_service_interface
            self.new_storage_ifbkp = self.prev_path + self.new_storage_interface
            self.new_backup_ifbkp = self.prev_path + self.new_backup_interface
            self.new_mngmnt_ifbkp = self.prev_path + self.new_man_interface
            self.old_service_ifbkp = self.M + self.new_service_interface
            self.old_storage_ifbkp = self.M + self.new_storage_interface
            self.old_backup_ifbkp = self.M + self.new_backup_interface
            self.old_mngmnt_ifbkp = self.M + self.new_man_interface
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def old_bkp_interface_file(self):
        """
        Step: 7b,7c in DOC
        This old_bkp_interface_file function
        delete uuid, hardware, name, device
        variables from Source MWS
        param: None
        return: None
        """
        try:
            util.exit_codes(0,"Copying interface configuration from source MWS to target MWS")
            self.old_mws_backup_dir()
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.old_ip, password=self.old_password)
            self.initialize_variable()
            if not (self.touch_old(client, self.new_service_interface, self.old_service_ifbkp)
                and self.touch_old(client, self.new_storage_interface, self.old_storage_ifbkp)
                and self.touch_old(client, self.new_backup_interface, self.old_backup_ifbkp)
                and self.touch_old(client, self.new_man_interface, self.old_mngmnt_ifbkp)):
                return
            if not (self.create_bckp(client, self.old_service_interface, self.new_service_interface,
                                    self.old_service_ifcfg, self.old_service_ifbkp)
                and self.create_bckp(client, self.old_storage_interface, self.new_storage_interface,
                                    self.old_storage_ifcfg, self.old_storage_ifbkp)
                and self.create_bckp(client, self.old_backup_interface, self.new_backup_interface,
                                    self.old_backup_ifcfg, self.old_backup_ifbkp)
                and self.create_bckp(client, self.old_man_interface, self.new_man_interface, self.old_mngmnt_ifcfg,
                                    self.old_mngmnt_ifbkp)):
                return
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    @staticmethod
    def copy_old_bckp(client1, file1, file2, file3):
        """
        copying interface files to backup directory
        in Source MWS
        param: None
        return: None
        """
        try:
            if len(file1) > 0 and len(file2) > 0:
                util.exit_codes(6, "Copying " + file3 + " to " + old_inf_path)
                stdin, stdout, stderr = client1.exec_command(
                    'cp ' + file3+" "+old_inf_path)
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    util.exit_codes(1,copy_failed + file3 + " to " + old_inf_path)
            return True
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def netwk_conf_backup(self):
        """
        step :7d in DOC
        This netwk_conf_backup() function
        param: None
        return: None
        """
        try:
            util.exit_codes(6, old_inf_path + " created successfully in source MWS")
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.old_ip, password=self.old_password)
            stdin, stdout, stderr = client.exec_command(mkdir_cmd + old_inf_path)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                util.exit_codes(6, old_inf_path + " created successfully in source MWS")
            else:
                util.exit_codes(1, "Failed to create directory:")
                return
            a = self.copy_old_bckp(client, self.old_service_interface, self.new_service_interface,
                                   self.old_service_ifbkp)
            b = self.copy_old_bckp(client, self.old_storage_interface, self.new_storage_interface,
                                   self.old_storage_ifbkp)
            c = self.copy_old_bckp(client, self.old_backup_interface, self.new_backup_interface,
                                   self.old_backup_ifbkp)
            d = self.copy_old_bckp(client, self.old_man_interface, self.new_man_interface,
                                   self.old_mngmnt_ifbkp)
            if not a or not b or not c or not d:
                return

            self.copy_dir_file(remotedir=old_inf_path, localdir='/etc/sysconfig/network-scripts')
            self.copy_etc_host_path()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def copy_dir_file(self, localdir, remotedir):
        """
        Step:1 in DOC
        This copy_config_path() function
        takes back up of the clients.
        from Source MWS to Target MWS
        param: None
        return: None
        """
        try:
            util.check_local_dir(localdir)
            self.port = 22
            remote_dir = remotedir
            local_dir = localdir
            t = paramiko.Transport((self.old_ip, self.port))
            t.connect(username=self.old_username, password=self.old_password)
            sftp = paramiko.SFTPClient.from_transport(t)
            util.down_from_remote(sftp, remote_dir, local_dir)
            t.close()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def copy_etc_host_path(self):
        """
        Step: 7d in DOC
        This copy_etc_host_path() function
        copies /etc/ data from Source MWS
        to Target MWS
        param: None
        return: None
        """
        try:
            util.exit_codes(0, "Started copying configuration files under /etc from source MWS to target MWS")
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.old_ip, password=self.old_password)
            self.det = "/var/tmp/postdetails"
            stdin, stdout, stderr = client.exec_command(mkdir_cmd + self.det)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1, "Failed to make" + self.det)
            client.exec_command("cp /etc/hostname /etc/hosts* /etc/exports " + self.det)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1, "Failed to copy files under /etc")
            self.copy_dir_file(remotedir=self.det, localdir="/etc")
            stdin, stdout, stderr = client.exec_command(rm_rf_cmd + self.det)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1, "Failed to remove" + self.det)
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    @staticmethod
    def new_bkp_interface_helper(file1, file2):
        """
        This funtion is helper for replacing the variables in
        interface configuration file
        param: None
        return: None
        """
        try:
            hwadd4, uuid4, name4, device4 = util.get_net_conf(file1)
            cmd = add_paramsintf_cmd.format(
                file2, name4, hwadd4, uuid4, device4)
            if os.system(cmd) != 0:
                util.exit_codes(1, cmd_exe_failed)
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_failed)
    def new_bkp_interface_file(self):
        """
        Step: 8 in DOC
        This new_bkp_interface_file function
        adds the uuid, hardware, name,
        device variable
        to the Target MWS
        param: None
        return: None
        """
        try:
            util.exit_codes(6,
                "Started copying interface configuration files stored under /etc/network_conf_backup from source MWS "
                "to target MWS")
            if len(self.new_service_interface.strip()) > 0 and len(self.old_service_interface.strip()) > 0:
                self.new_bkp_interface_helper(self.new_service_ifbkp, self.new_service_ifcfg)
            if len(self.new_storage_interface.strip()) > 0 and len(self.old_storage_interface.strip()) > 0:
                self.new_bkp_interface_helper(self.new_storage_ifbkp, self.new_storage_ifcfg)
            if len(self.new_backup_interface.strip()) > 0 and len(self.old_backup_interface.strip()) > 0:
                self.new_bkp_interface_helper(self.new_backup_ifbkp, self.new_backup_ifcfg)
            if len(self.new_man_interface.strip()) > 0 and len(self.old_man_interface.strip()) > 0:
                self.new_bkp_interface_helper(self.new_mngmnt_ifbkp, self.new_mngmnt_ifcfg)
            util.exit_codes(6,
                "Completed copying interface configuration files stored under /etc/network_conf_backup from source MWS "
                "to target MWS")
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def node_hardening_verification(self):
        """
        Step: 9a,9b in DOC
        This node_hardening_verification function
        verifies whether the node hardening is applied or not
        on the Source MWS
        and proceeds furthur
        param: None
        return: None
        """
        try:
            util.exit_codes(0, "Starting node hardening verification")
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.old_ip, password=self.old_password)
            self.node_hardening_path1 = "/ericsson/security/compliance/NH_Compliance.py"
            stdin, stdout, stderr = client.exec_command("test -e "+self.node_hardening_path1)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                util.exit_codes(0, "Started generating compliance report, please wait this may take a while...")
                stdin, stdout, stderr = client.exec_command(
                    "/ericsson/security/compliance/NH_Compliance.py > "
                    "/ericsson/security/compliance/Reports/Compliance_Report.txt")
                exit_status = stdout.channel.recv_exit_status()
                if exit_status == 0:
                    util.exit_codes(0, "Report generated successfully")
                else:
                    util.exit_codes(1, "Issue while generating compilance report")
                client.exec_command("chmod -w /ericsson/security/compliance/Reports/Compliance_Report.txt")
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    util.exit_codes(1, "Failed to change permission for Compliance_Report.txt")
                self.copy_compliance_report()
            else:
                util.exit_codes(0, "Node hardening not applied on the source MWS")
            client.close()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def copy_compliance_report(self):
        """
        Step: 9c in DOC
        This copy_compliance_report() function
        copies the compliance report to
        Target MWS from Source MWS
        param: None
        return: None
        """
        try:
            util.exit_codes(0, "Started copying compliance report from source MWS to target MWS")
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.old_ip, password=self.old_password)
            self.cmly_dir = "/var/tmp/comply_inter"
            stdin, stdout, stderr = client.exec_command(mkdir_cmd + self.cmly_dir)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1, "Failed to make " + self.cmly_dir)
                return
            stdin, stdout, stderr = client.exec_command(
                "cp " + " /ericsson/security/compliance/Reports/Compliance_Report.txt " + self.cmly_dir)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1,
                    "Failed to copy /ericsson/security/compliance/Reports/Compliance_Report.txt " + self.cmly_dir)
                return
            self.copy_dir_file(localdir="/var/tmp", remotedir=self.cmly_dir)
            stdin, stdout, stderr = client.exec_command(rm_rf_cmd + self.cmly_dir)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1,
                    "Failed to copy /ericsson/security/compliance/Reports/Compliance_Report.txt " + self.cmly_dir)
                return
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def dhcpd_conf_file_bkp(self):
        """
        Step:10 in DOC
        This dhcp_conf_file_copy function
        caches thcopy_old_int_locale dhcpd.conf file to a
        temporary directory from Source MWS
        to Target MWS
        param: None
        return: None
        """
        try:
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.old_ip, password=self.old_password)
            self.dhcp_dir = "/var/tmp/dhcp_dir"
            stdin, stdout, stdout = client.exec_command(mkdir_cmd + self.dhcp_dir)
            util.exit_codes(0, "Started copying dhcpd.conf configurations files")
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1, failed_create_msg + self.dhcp_dir)
                return
            stdin, stdout, stdout = client.exec_command("cp /etc/dhcp/dhcpd.conf " + self.dhcp_dir)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1, "Failed to copy /etc/dhcp/dhcpd.conf to" + self.dhcp_dir)
                return
            self.copy_dir_file(localdir="/etc/dhcp/", remotedir=self.dhcp_dir)
            stdin, stdout, stdout = client.exec_command(rm_rf_cmd + self.dhcp_dir)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1, "Failed to remove" + self.dhcp_dir)
                return
            util.exit_codes(0, "Completed copying dhcpd.conf configurations files")
            self.dhcp_service_enable()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def dhcp_service_enable(self):
        """
        Step:11 in DOC
        This dhcp_service_enable() function
        enables DHCP service on new
        mws
        param: None
        return: None
        """
        try:
            util.exit_codes(0, "Enabling DHCP service on the target MWS")
            cmd = "systemctl enable dhcpd"
            if os.system(cmd) != 0:
                util.exit_codes(1, cmd_exe_failed)
            self.verify_dhcp_network()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def verify_dhcp_network(self):
        '''
        Step:12 in DOC
        This verify_dhcp_network function
        verifies whether the dhcp neteworks
        are configured or not.
        param: None
        return: None
        '''
        try:
            util.exit_codes(0, "Listing the DHCP network on target MWS")
            self.dhcp_network_list = subprocess.check_output(
                "/ericsson/kickstart/bin/manage_linux_dhcp.bsh -a list -s network".split())
            self.network_disable()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_err)
    def network_disable(self):
        '''
        Step: 14 and 5.5-1 in DOC
        This function disables the network service
        on Source MWS and shut downs the Source MWS
        param: None
        return: None
        '''
        try:
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.old_ip, password=self.old_password)
            util.exit_codes(0, "Disabling DHCP service on the source MWS")
            stdin, stdout, stdout = client.exec_command("systemctl disable network")
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1, cmd_exe_failed)
            util.exit_codes(4, "Shutting down source MWS")
            stdin, stdout, stdout = client.exec_command("shutdown")
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                util.exit_codes(1, cmd_exe_failed)
            client.close()
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_failed)
    @staticmethod
    def restart_new():
        '''
        Step: 5.5-2 in DOC
        This function restarts the Target MWS.
        param: None
        return: None
        '''
        try:
            time.sleep(5)
            cmd = "shutdown -r now"
            if os.system(cmd) != 0:
                util.exit_codes(1, cmd_exe_failed)
        except Exception as e:
            print(e)
            util.exit_codes(1, cmd_exe_failed)
def main():
    """
    The main function to wrap all functions and performing staging.
    Param: None
    return: None
    """
    try:
        stage = util.stagelist()
        if stage == 14:
            util.exit_codes(0, "MWS migration already completed")
            sys.exit(0)
        util.exit_codes(0, "Starting MWS migration")
        p = mwsmigration()
        if stage == 1:
            p.hardware_check_wrapper()
            stage = stage + 1
            with open(STAGE, 'w') as f:
                f.write(str(stage))
        if stage == 2:
            p.get_input()
            p.initialize_variable()
            stage = stage + 1
            with open(STAGE, 'w') as f:
                f.write(str(stage))
        if stage == 3:
            p.get_input()
            p.initialize_variable()
            p.new_mws_backup_dir()
            stage = stage + 1
            with open(STAGE, 'w') as f:
                f.write(str(stage))
        if stage == 4:
            p.get_input()
            p.initialize_variable()
            p.copy_dir_file(remotedir='/JUMP/LIN_MEDIA/1/kickstart/',
                            localdir='/var/tmp/dhcp_kickstart_client_details/')
            stage = stage + 1
            with open(STAGE, 'w') as f:
                f.write(str(stage))
        if stage == 5:
            p.get_input()
            p.initialize_variable()
            p.old_mws_bkp_details()
            stage = stage + 1
            with open(STAGE, 'w') as f:
                f.write(str(stage))
        if stage == 6:
            p.get_input()
            p.initialize_variable()
            p.network_conf_bkp()
            stage = stage + 1
            with open(STAGE, 'w') as f:
                f.write(str(stage))
        if stage == 7:
            p.get_input()
            p.initialize_variable()
            p.rsync_data()
            stage = stage + 1
            with open(STAGE, 'w') as f:
                f.write(str(stage))
        if stage == 8:
            p.get_input()
            p.initialize_variable()
            p.old_bkp_interface_file()
            stage = stage + 1
            with open(STAGE, 'w') as f:
                f.write(str(stage))
        if stage == 9:
            p.get_input()
            p.initialize_variable()
            p.netwk_conf_backup()
            stage = stage + 1
            with open(STAGE, 'w') as f:
                f.write(str(stage))
        if stage == 10:
            p.get_input()
            p.initialize_variable()
            p.new_bkp_interface_file()
            stage = stage + 1
            with open(STAGE, 'w') as f:
                f.write(str(stage))
        if stage == 11:
            p.get_input()
            p.initialize_variable()
            p.node_hardening_verification()
            stage = stage + 1
            with open(STAGE, 'w') as f:
                f.write(str(stage))
        if stage == 12:
            p.get_input()
            p.initialize_variable()
            p.dhcpd_conf_file_bkp()
            stage = stage + 1
            with open(STAGE, 'w') as f:
                f.write(str(stage))
        if stage == 13:
            p.get_input()
            p.initialize_variable()
            util.remove_and_replace(p.cred_file, p.new_cred_file, p.new_if_file, p.new_service_interface, p.old_if_file)
            stage = stage + 1
            with open(STAGE, 'w') as f:
                f.write(str(stage))
            util.exit_codes(0, "MWS migration successfully completed")
            util.exit_codes(4, "Restarting target MWS server")
            log_file = os.path.basename(__file__).replace('.py', '_') + time.strftime("%m_%d_%Y-%H_%M_%S")+'.log'
            util.create_log_file(log_file)
            util.exit_codes(0, "Please refer the log file {} for script's execution information".format(LOG_DIRECT
                                                                                                        +log_file))
            p.restart_new()
        signal.signal(signal.SIGINT, util.exit_gracefully_upgrade)
        sys.exit()
    except Exception as e:
        print(e)
        util.exit_codes(1, cmd_exe_failed)
def invalid_argument():
    '''
    This function is a helper function and it is called
    when the arguments which are passed to the script are wrong.
    param: None
    return: None
    '''
    try:
        print("======================================================================")
        print("[ERROR] : Invalid Request!. check and try again.")
        print("======================================================================\n\n")
        print("Usage: mws_migration.py <--action>\n\n")
        print("Valid actions are:\n")
        print("--migrate                performs mws migration\n")
        print("--post_verification      performs post verification\n")
        sys.exit(1)
    except Exception as e:
        print(e)
        util.exit_codes(1, cmd_exe_failed)
if __name__ == "__main__":
    try:
        if len(sys.argv) == 2:
            inp = sys.argv[1]
            if inp == "--migrate":
                util.logging_configs(TMP_LOGS)
                main()
            elif inp == "--post_verification":
                util.logging_configs(os.path.basename(__file__).replace('.py', '_post_verification_') +
                                     time.strftime("%m_%d_%Y-%H_%M_%S") + '.log')
                util.post_migration_verification()
            else:
                invalid_argument()
        else:
            invalid_argument()
    except Exception as e:
        print(e)
        invalid_argument()


