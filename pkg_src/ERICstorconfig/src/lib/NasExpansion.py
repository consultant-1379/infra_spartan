#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for NAS Pool expansion automation
This script will replace the manual steps
used to perform NAS pool expansion automation.
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
# Name      : NASpoolExpansion.py
# Purpose   : The script wil perform Expansion of NAS pool
# ********************************************************************
import os, sys, paramiko, subprocess, logging, pexpect, time, re
pool_list_cmd,rmrf,cmd_ex= 'uemcli -d {} /stor/config/pool show -filter "ID"','rm -rf ',"Command execution failed"
ssh_support_cmd = "/usr/bin/ssh -o StrictHostKeyChecking=no -n support@nasconsole {}".format('\\')
audit_script_cmd = ' "ssh -o StrictHostKeyChecking=no -n support@nasconsole {}\"/opt/ericsson/NASconfig' \
                   '/bin/nasAudit.py"{}"\""'.format('\\', '\\')
ssh_master_cmd,dc=' "ssh -o StrictHostKeyChecking=no -n support@nasconsole {}\"/opt/VRTSnas/clish' \
                '/bin/clish -u master -c'.format('\\'),'uemcli -d {} /stor/prov/luns/lun show -filter "ID,Name,Size"'
storadm,reg_exp,strg_pool_list = 'su storadm -c','ID = ([^\s]+)'," 'storage pool list'{}\"\"".format('\\')
strg_scbus,strg_disk_list = " 'storage scanbus'{}\"\"".format('\\'),"'storage disk list detail'{}\"\"".format('\\')
disk_create,destroy_pool = " 'storage pool create dummy {}'{}\"\""," 'storage pool destroy dummy'{}\"\"".format('\\')
disk_grow,pool_details = " 'storage disk grow {}'{}\"\""," 'storage pool free'{}\"\"".format('\\')
Target_size ,disk_remove,inp_msg = "3.4T"," 'storage disk remove {}'{}\"\"","Input file not found"
get_host_cmd,stg2= 'uemcli -d {} /stor/prov/luns/lun -id {} show -detail',"Starting Dummy Lun and Pool creation stage"
verify_lun_nashost = 'uemcli -d {} /remote/host -id {} show -filter "Accessible LUNs"'
nas_lun_id_cmd = 'uemcli -d {} /stor/prov/luns/lun show -filter "ID,Name,Size"'
exp_lun_cmd,dlist_fail='uemcli -d {} -noheader /stor/prov/luns/lun -id {} set -size {}',"Disk list command failed"
verify_lun_size = 'uemcli -d {} -noheader /stor/prov/luns/lun -id {} show -filter "Size"'
check_dummy_lun,start_msg = 'uemcli -d {} /stor/prov/luns/lun  -id {} show',"Starting Expansion Pre check stage"
del_dummy_lun,tmp_log = 'uemcli -d {} /stor/prov/luns/lun -id {} delete','/var/tmp/nas_pool_exp_temp.txt'
msg,f_msg,scanbus_failed= "Operation completed successfully","Failed to get disk list details","Failed to run scanbus"
LOG_DIRE,STAGE,codeployed ="/var/ericsson/log/nas_pool_expansion/",'/var/tmp/stage_nase.txt',''
req_ids_file,temp_id_file,value_file='/var/tmp/req_ids.txt','/var/tmp/temp_id_file.txt',"/var/tmp/value.txt"
input1_file,input2_file,nas_file='/var/tmp/input_file1.txt','/var/tmp/input_file2.txt','/var/tmp/nas_lun_detail.txt'
LOG_NAME = os.path.basename(__file__).replace('.py', '_') + time.strftime("%m_%d_%Y-%H_%M_%S") + '.log'
class nas_poolexpansion(object):
    '''

    Class with methods to perform NAS pool expansion
    '''
    def __init__(self):
        """

        Function to initialise the
        class object variables
        param: None
        return: None
        """
        self.colors = {'RED': '\033[91m', 'END': '\033[00m', 'GREEN': '\033[92m', 'YELLOW': '\033[93m','b':'\033[90m'}
        self.logger = logging.getLogger()
        self.cord_ip, self.cord_username, self.cord_pwd,self.unity_ip, self.flag,self.i = '', '', '', '',0,''
        self.unity_pool_id, self.dummy_lunid, self.nas_lun_id, self.nas_pool, self.pool_size = '', '', '', '', ''
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
        f_formats = logging.Formatter()
        s_hand.setFormatter(s_formats)
        f_hand.setFormatter(f_formats)
        self.logger.addHandler(s_hand)
        self.logger.addHandler(f_hand)
    def log_file_scrn(self, msg1, log_dec=1):
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
        if log_dec == 0:
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
        color, meseg = self.colors, "Please find the script execution logs  ---> "
        print_hash = '------------------------------------------------------------------------------'
        print(print_hash+'\n'+meseg+LOG_DIRE + LOG_NAME+'\n'+print_hash)
    @staticmethod
    def loc_log(msge):
        """

        this function will update log file
        logs will be updated
        """
        if not os.path.exists(tmp_log):
            cmd = 'touch '+tmp_log
            os.system(cmd)
        with open(tmp_log, 'a') as f:
            named_tuple = time.localtime()
            ti = time.strftime("%m_%d_%Y-%H_%M_%S", named_tuple)
            f.writelines(ti + '  ' + str(msge) + '\n')
    def log_fun(self):
        """

        log function
        reads the temporary file and append data to logs
        logging will be done in-case of failure
        """
        self.logging_configs()
        with open(tmp_log, 'r') as f:
            val = f.readlines()
            for i in val:
                self.log_file_scrn(i.strip(), 1)
        self.print_logging_detail(),sys.exit(1)
    def exit_codes(self, code_num, msg):
        """

        Script Exit function
        param: code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        """
        colors = self.colors
        if code_num == 0:
            print(colors['GREEN'] + "[INFO] " + colors['END'] + ": " + msg)
            self.loc_log(msg)
        elif code_num == 1:
            print(colors['RED'] + "[ERROR] " + colors['END'] + ": " + str(msg))
            self.loc_log(msg),self.log_fun()
        elif code_num == 2:
            print(colors['YELLOW'] + "[WARNING] " + colors['END'] + ": " + str(msg))
            self.loc_log(msg)
        elif code_num == 3:
            print("[" + time.strftime("%m-%d-%Y-%H:%M:%S") + "] "
                  + colors['GREEN'] + "[INFO] " + colors['END'] + ": " + msg)
            self.loc_log(msg)
        elif code_num == 4:
            self.loc_log(msg)
        elif code_num==5:
            print(colors['RED'] + "[ERROR] " + colors['END'] + ": " + str(msg))
            self.loc_log(msg)
        elif code_num==6:
            print("=" * 70)
            print("["+time.strftime("%m-%d-%Y-%H:%M:%S") +"] "+ colors['GREEN'] + "[INFO] " + colors['END'] + ": " +msg)
            print("=" * 70)
    def stagelist(self):
        """

        Checks and returns which stage we are
        currently present at in case of failure
        Args: None
        return: int
        """
        try:
            stage = 1
            if os.path.exists(STAGE):
                with open(STAGE, 'r') as f:
                    stage = int(f.read())
            if stage==1:
                self.exit_codes(0, "Starting NAS Pool expansion ")
            elif stage==6:
                self.exit_codes(0,"NAS pool expansion already completed")
            elif stage>1:
                self.exit_codes(0,"Resuming NAS pool Expansion")
            return stage
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Issue in reading stage level")
    def exit_status_check(self,err_msg,n=0):
        '''
        Function to check the exit status of the command
        and abort in case exit status not  equal to 0
        '''
        if n!=0:
            self.exit_codes(1,err_msg)
    def exp_precheck(self):
        '''
        Function to check whether expansion required or not
        '''
        try:
            self.exit_codes(0, "Starting NAS Pool Expansion precheck")
            existing_list,target_list = ['D', 'E', 'F', 'G'],['F', 'G']
            if self.config_type not in existing_list:
                self.exit_codes(1, 'Existing Configuration Type ({}) is invalid'.format(self.config_type))
            elif (self.config_type == "D" and self.target_config == "E") or (
                self.config_type == "F" and self.target_config == "G"):
                self.exit_codes(1, "NAS pool expansion not required from " \
                                       "{} to {}".format(self.config_type, self.target_config))
            elif self.target_config not in target_list:
                msg = 'Target Configuration Type ({}) is invalid'.format(self.target_config)
                self.exit_codes(1, msg)
            elif self.target_config == self.config_type:
                self.exit_codes(1, "NAS Pool expansion not required from {} to {}".format(self.config_type,
                                                                                         self.target_config))
            elif self.target_config > self.config_type:
                self.exit_codes(0, "NAS pool expansion required from {} to {}".format(self.config_type,
                                                                                          self.target_config))
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1, "NAS Pool Expansion precheck failed")
    def get_exp_inputs(self):
        '''

        Function to get the required inputs for expansion
        req inputs-unity ip,unity pool id,config type,taget config
        '''
        try:
            if self.flag==0:
                self.exit_codes(4, "Collecting inputs required for expansion from input file")
                if os.path.exists(input2_file):
                    with open(input2_file, 'r') as f:
                        df = f.read().splitlines()
                        self.unity_ip = df[0].strip()
                        self.unity_pool_id = df[1].strip()
                        self.config_type = df[3].strip()
                        self.target_config = df[4].strip()
                else:
                    self.exit_codes(1,inp_msg)
                cmd1 = "uemcli -d {} -noHeader /sys/general show -filter Model".format(self.unity_ip)
                unity_id7 = os.popen(cmd1).read()
                if 'Unity 480F' in unity_id7:
                    self.exit_codes(1, "Requested Configuration can be performed only on Unity")
                elif 'Unity 450F' in unity_id7:
                    self.exit_codes(4,"Storage model is unity")
                else:
                    self.exit_codes(4,unity_id7),self.exit_codes(1,"storage type checking command failed")
                if os.path.exists(nas_file):
                    with open(nas_file, 'r') as f:
                        nf = f.read().splitlines()
                        self.nas_lun_id=nf[0].strip()
                else:
                    self.exit_codes(1, inp_msg)
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Failed to collect required inputs for expansion from input file")
    def get_inputs(self):
        '''

        Function to get the required inputs from file
        req inputs-codeployed,cord ip,user name,pwd,pwd key
        '''
        try:
            if self.flag==0:
                self.exit_codes(0,"Collecting required inputs from input file")
                if os.path.exists(input1_file):
                    with open(input1_file, 'r') as f:
                        op = f.readlines()
                        global codeployed
                        codeployed = op[1].split('\n')[0].strip().split(':')[-1]
                        self.cord_ip = op[2].split('\n')[0].strip().split(':')[-1]
                        self.cord_username = op[3].split('\n')[0].strip().split(':')[-1]
                        self.eniq_enc_pwd = op[4].split('\n')[0].strip().split(':')[-1]
                        self.key = op[5].split('\n')[0].strip().split(':')[-1]
                        dec_pwd = "echo \"{}\" | openssl enc -aes-256-ctr -md sha512 -a -d -salt -pass " \
                        "pass:{}".format(self.eniq_enc_pwd,self.key)
                        self.cord_pwd = os.popen(dec_pwd).read().strip()
                else:
                    self.exit_codes(1, "Issue with provided inputs.Try again!")
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1, "Failed to collect inputs from file")
    def req_ids_from_file(self):
        '''

        Function to get all the required details of nas pool and nas host ids
        from a file
        param: None
        return: None
        '''
        try:
            self.exit_codes(4, "Getting required ids for expansion from file")
            with open(req_ids_file, 'r') as f:
                op = f.read().splitlines()
                self.nas_pool = op[0].strip()
                self.nas1 = op[2].strip()
                self.nas2 = op[3].strip()
                self.disk_name=op[1].strip()
            f.close()
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Failed to get required ids from file")
    def write_to_file(self,v):
        '''
        Function to write the required id details in to a file
        param: v-id or name
        return: None
        '''
        try:
            with open(req_ids_file,'a') as f:
                f.writelines(v+'\n')
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Failed to write inputs in to a file")
    def get_disk_name(self):
        '''
        Function to get the NAS pool's disk name
        param: None
        return: None
        '''
        try:
            self.exit_codes(4,"getting nas disk name")
            if len(self.nas_pool_list) == 0:
                self.exit_codes(1, "No NAS pool with 3TB size found")
            elif len(self.nas_pool_list) > 1:
                self.exit_codes(1, "More than one NAS pool found with 3Tb Size")
            else:
                self.nas_pool = self.nas_pool_list[0]
                if not self.nas_pool:
                    self.exit_codes(1,"Failed to get NAS pool name")
                self.exit_codes(4, "Got NAS pool name")
            if self.dlist_op:
                for i in self.dlist_op:
                    if self.nas_pool in i:
                        self.disk_name = i.split()[0]
                        break
                    else:
                        continue
                if not self.disk_name:
                    self.exit_codes(1,"Failed to get NAS disk name")
                self.exit_codes(4, "Got NAS disk name")
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Failed to get NAS disk name")
    def pool_size_append(self):
        '''

        Function to append the pool sizes with 3TB
        param: None
        return: None
        '''
        self.size = self.i.split()[2]
        if self.size == '3.00T':
            self.nas_pool_list.append(self.i.split()[0])
    def get_nas_pool_name(self):
        '''
        Function to get the NAS pool name
        param: None
        return: True or False
        '''
        try:
            self.exit_codes(4, "Getting NAS pool name")
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.cord_ip, username=self.cord_username, password=self.cord_pwd)
            stdin, stdout, stderr = client.exec_command(storadm + ssh_master_cmd + pool_details,timeout=None)
            exit_status = stdout.channel.recv_exit_status()
            denied_msg = stderr.read().splitlines()
            if (exit_status != 0) and ("Permission denied, please try again." in denied_msg) :
                self.exit_codes(1,"Please set up passwordless connection between ENIQ and NAS!Then re run the script")
            self.exit_status_check("Storage pool free command failed",exit_status)
            pool_list_op = stdout.read().splitlines()
            stdin, stdout, stderr = client.exec_command(storadm + ssh_master_cmd + strg_disk_list,timeout=None)
            exit_status = stdout.channel.recv_exit_status()
            self.exit_status_check(f_msg,exit_status)
            self.dlist_op=stdout.read().splitlines()
            client.close()
            self.nas_pool_list = []
            if pool_list_op:
                for self.i in pool_list_op:
                    if self.i:
                        self.pool_size_append()
                    else:
                        continue
                self.get_disk_name()
                return True
            else:
                return False
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Failed to get NAS Pool name")
    def get_req_ids(self):
        '''
        Function to get all the NAS id details
        -nas pool name
        -nas pool disk name
        -host ids
        param: None
        return: None
        '''
        try:
            self.exit_codes(4, "Collecting required ids for expansion")
            if not self.get_nas_pool_name():
                self.exit_codes(1, "Issue in getting nas pool name")
            self.exit_codes(4, "Getting NAS host ids")
            get_host_ids = get_host_cmd.format(self.unity_ip, self.nas_lun_id)
            hostid_output = os.popen(get_host_ids).read()
            if re.search(r'LUN access hosts.*', hostid_output):
                self.host_id_list = re.findall(r'LUN access hosts.*', hostid_output)
                l = self.host_id_list[0].split("=")[-1].strip()
                self.nas1, self.nas2 = l.split(',')[0].strip(), l.split(',')[1].strip()
                if not self.nas1 or not self.nas2:
                    self.exit_codes(1, "Issue in getting nas host ids")
            else:
                self.exit_codes(4,hostid_output),self.exit_codes(1,"NAS host ids list command failed")
            self.write_to_file(self.nas_pool), self.write_to_file(self.disk_name)
            self.write_to_file(self.nas1), self.write_to_file(self.nas2)
            self.flag=1
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Failed to get NAS host ids")
    def req_ids(self):
        '''
        Function to get required id
        -reads inputs from file,if file is present
        -else,call get_req_ids function to collect inputs
        '''
        try:
            if self.flag==0:
                if os.path.exists(req_ids_file):
                    self.req_ids_from_file()
                else:
                    self.get_req_ids()
            self.flag=1
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1, "Failed to get inputs")
    def audit_report(self, check=0):
        '''

        Function to execute the audit script
        and check the health of NAS
        aborts in case any warning or error found
        '''
        try:
            if os.path.exists(value_file):
                os.system('rm -rf /var/tmp/value.txt')
            if not os.path.exists(value_file):
                client = paramiko.client.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.cord_ip, username=self.cord_username, password=self.cord_pwd)
                self.exit_codes(0, 'Executing NAS audit script')
                self.exit_codes(0, 'Please wait.....NAS audit script execution is in progress')
                stdin, stdout, stderr = client.exec_command(storadm + audit_script_cmd)
                a = stdout.read()
                client.close()
                with open(value_file, 'w') as f:
                    f.writelines(a)
            else:
                self.exit_codes(1, "Issue in deleting /var/tmp/value.txt")
            if os.path.exists(value_file):
                cat_cmd = 'cat /var/tmp/value.txt | tail -1'
                value_op = os.popen(cat_cmd).read()
                if 'Return code: 0, Message: No errors/warnings encountered.' not in value_op:
                    grep_cmd = "cat /var/tmp/value.txt | grep 'Report generated'"
                    mesg = os.popen(grep_cmd).read().strip()
                    mesg1 = "Path of audit log file: " +mesg+self.colors['END']
                    if check == 1:
                        self.exit_codes(5,"NAS health check failed")
                        self.exit_codes(0, mesg1),self.log_fun()
                    self.exit_codes(5, "NAS health check failed,Please fix and re run the script....")
                    self.exit_codes(0,mesg1),self.log_fun()
                else:
                    self.exit_codes(0,"NAS audit completed")
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Issue while executing NAS audit script")
    def create_dummylun_unity(self):
        '''

        Function to create 1G dummy LUN in unity
        Param: None
        return: None
        '''
        create_dummy_lun = "uemcli -d {} /stor/prov/luns/lun create -name 1gdummy" \
                           " -type primary -thin no -pool {} -size 1G -spOwner spb"
        get_wwn='uemcli -d {} -noheader /stor/prov/luns/lun -id {} show -filter "WWN"'
        try:
            if not os.path.exists(temp_id_file):
                create_dummy_lun = create_dummy_lun.format(self.unity_ip, self.unity_pool_id).split()
                self.exit_codes(0, "Starting 1Gb dummy LUN creation")
                dummy_lun_op = subprocess.check_output(create_dummy_lun)
                if msg in dummy_lun_op and re.search(r'sv_[0-9]+', dummy_lun_op):
                    self.dummy_lunid = re.findall(r'sv_[0-9]+', dummy_lun_op)[0]
                    self.exit_codes(0, "Dummy LUN creation successful")
                    get_wwn=get_wwn.format(self.unity_ip,self.dummy_lunid).split()
                    getwwn=subprocess.check_output(get_wwn)
                    self.WWN=getwwn.strip().split("=")[-1].strip().replace(":","")
                    with open(temp_id_file, 'a') as f:
                        f.writelines(self.dummy_lunid + '\n')
                        f.writelines(self.WWN + '\n')
                    f.close()
                else:
                    self.exit_codes(4,dummy_lun_op),self.exit_codes(1,"Issue in creating dummy LUN")
            else:
                self.exit_codes(0,"Already created 1Gb dummy LUN")
        except subprocess.CalledProcessError as err:
            self.exit_codes(4,err.output),self.exit_codes(1, "Dummy LUN creation failed")
    def validation_post_assign(self):
        '''
        Function to validate whether lun is
        assigned to hosts
        '''
        try:
            self.exit_codes(4, "Validation post assigning LUN to the NAS host")
            verify_op=subprocess.check_output(self.verify_lun_nashost)
            if self.dummy_lunid in verify_op:
                return True
            else:
                return False
        except subprocess.CalledProcessError as err:
            self.exit_codes(4,err.output),self.exit_codes(1,"Dummy LUN validation command failed")
    def assign_dummylun_to_host(self):
        '''
        Function to assign the dummy
        lun to hosts
        param : None
        return : None
        '''
        add_lun_to_nashosts = 'uemcli -d {} /remote/host -id {} set -addLuns {}'
        try:
            if os.path.exists(temp_id_file):
                with open(temp_id_file, 'r') as f:
                    of = f.read().splitlines()
                    self.dummy_lunid = of[0].strip()
                    self.WWN=of[1].strip()
                f.close()
            else:
                self.exit_codes(1, "Issue in getting dummy Lun id from file")
            self.exit_codes(0, "Starting dummy LUN Assignment to Hosts")
            for host_id in [self.nas1, self.nas2]:
                self.verify_lun_nashost=verify_lun_nashost.format(self.unity_ip,host_id).split()
                verify_op=subprocess.check_output(self.verify_lun_nashost)
                if self.dummy_lunid not in verify_op:
                    self.exit_codes(0,"Assigning dummy 1G LUN ['ID: {}'] "\
                            "to the NAS host ['ID: {}']".format(self.dummy_lunid,host_id))
                    self.add_to_nashosts=add_lun_to_nashosts.format(self.unity_ip, host_id, self.dummy_lunid).split()
                    add_op=subprocess.check_output(self.add_to_nashosts)
                    if msg not in add_op:
                        self.exit_codes(1,"Failed to assign dummy lun to host")
                    if not self.validation_post_assign():
                        self.exit_codes(1,"Dummy LUN ['ID: {}'] assignment to the"\
                         " NAS host 'ID: {}' failed.".format(self.dummy_lunid, host_id))
                    else:
                        self.exit_codes(0, "Successfully assigned Dummy 1G LUN ['ID: {}']"\
                        " to the NAS host ['ID: {}']".format(self.dummy_lunid, host_id))
                else:
                    self.exit_codes(0, "Dummy 1G LUN ['ID: {}'] already assigned to the NAS"\
                            " host ['ID: {}']".format(self.dummy_lunid, host_id))
        except subprocess.CalledProcessError as err:
            self.exit_codes(4,err.output),self.exit_codes(1,"Failed to assign Dummy LUN to hosts")
    def dummy_check_helper(self):
        '''
        helper function to check dummy pool is there
        or not
        param : None
        return : True or False
        '''
        try:
            for i in self.disk_detail:
                if ('1.0G' in i) and ('dummy' in i) and (self.WWN in i):
                    d_det = i
                    self.d_name = d_det.split()[0]
                    if not self.d_name:
                        self.exit_codes(1, "Issue in getting disk name")
                    self.exit_codes(0,"Dummy Pool already created")
                    return False
                else:
                    continue
            return True
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Dummy pool check failed")
    def lun_check_helper(self,f=0):
        '''
        helper function to check dummy lun is there
        or not
        param : None
        return : True or False
        '''
        try:
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.cord_ip, username=self.cord_username, password=self.cord_pwd)
            stdin, stdout, stderr = client.exec_command(storadm + ssh_master_cmd + strg_disk_list,timeout=None)
            exit_status = stdout.channel.recv_exit_status()
            self.exit_status_check(dlist_fail,exit_status)
            self.disk_detail = stdout.read().splitlines()
            client.close()
            self.d_name=''
            for i in self.disk_detail:
                if ('1.0G' in i) and (i.split()[1].strip() == '-') and (self.WWN in i):
                    self.d_name = i.split()[0]
                    if not self.d_name:
                        self.exit_codes(1, "Issue in getting disk name")
                continue
            if self.d_name:
                return True
            return False
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Dummy LUN check failed")
    def validate_dummypool_nas(self,f=0):
        '''
        Function to check dummy pool
        is present on NAS or not
        '''
        try:
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.cord_ip, username=self.cord_username, password=self.cord_pwd)
            if f==0:
                stdin, stdout, stderr = client.exec_command(storadm + ssh_master_cmd + strg_scbus,timeout=None)
                exit_status = stdout.channel.recv_exit_status()
                self.exit_status_check(scanbus_failed,exit_status)
            stdin, stdout, stderr = client.exec_command(storadm + ssh_master_cmd + strg_disk_list,timeout=None)
            exit_status = stdout.channel.recv_exit_status()
            self.exit_status_check(dlist_fail,exit_status)
            self.disk_detail = stdout.read().splitlines()
            client.close()
            if not self.dummy_check_helper():
                return False
            if self.lun_check_helper(f):
                return True
            if f==0:
                self.exit_codes(1, "Dummy lun not visible to the NAS hosts")
            else:
                return False
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Dummy LUN or pool check failed")
    def post_validate_dummypool(self):
        '''
        Function to check dummy pool is create or not
        param: None
        return: None
        '''
        try:
            self.exit_codes(4, "Started Validation post dummy pool creation")
            stdin, stdout, stderr = self.client.exec_command(storadm + ssh_master_cmd + strg_disk_list,timeout=None)
            exit_status = stdout.channel.recv_exit_status()
            self.exit_status_check("Failed to validate dummy pool creation",exit_status)
            self.disk_detail = stdout.read().splitlines()
            self.client.close()
            for i in self.disk_detail:
                if ('1.0G' in i) and ('dummy' in i) and (self.WWN in i):
                    return True
                else:
                    continue
            for i in self.disk_detail:
                if ('1.0G' not in i) and ('dummy' not in i) and (self.WWN not in i):
                    return False
                else:
                    continue
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1, "Dummy pool creation validation failed")
    def create_dummypool_nas(self):
        '''
        Function to create dummy pool
        on NAS
        param: None
        return: None
        '''
        try:
            self.client = paramiko.client.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.cord_ip, username=self.cord_username, password=self.cord_pwd)
            self.exit_codes(0, "Starting dummy pool creation")
            self.disk_create=disk_create.format(self.d_name,'\\')
            stdin, stdout, stderr = self.client.exec_command(storadm + ssh_master_cmd + self.disk_create,timeout=None)
            exit_status = stdout.channel.recv_exit_status()
            self.exit_status_check(scanbus_failed,exit_status)
            op=stdout.read()
            if "Created pool dummy successfully" in op:
                if self.post_validate_dummypool():
                    self.exit_codes(0, "Dummy pool creation successful")
                else:
                    self.exit_codes(1, "Dummy pool creation failed.")
            else:
                self.exit_codes(1, "Dummy pool creation failed.")
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Dummy pool creation failed")
    def lun_exp_validation(self):
        '''
        Function to validate lun expanded to target size
        param: None
        return: None
        '''
        try:
            self.exit_codes(4, "Started Validation post NAS LUN expansion")
            exp_lunsize =subprocess.check_output((verify_lun_size.format(self.unity_ip, self.nas_lun_id)).split())
            if Target_size not in exp_lunsize:
                self.exit_codes(1, "NAS lun expansion not successful as per target config")
            elif Target_size in exp_lunsize:
                self.exit_codes(0, "NAS lun expanded successfully to target config")
        except subprocess.CalledProcessError as err:
            self.exit_codes(4,err.output),self.exit_codes(1, "NAS LUN size validation command failed")
    def lun_expansion_main(self):
        '''
        Function to perform NAS lun expansion
        param: None
        return: None
        '''
        try:
            exp_size = os.popen(verify_lun_size.format(self.unity_ip, self.nas_lun_id)).read()
            if Target_size in exp_size:
                self.exit_codes(0, "Already expanded the NAS lun")
            elif '3.0T' in exp_size:
                self.exit_codes(3, "Starting NAS data LUN ['ID: {}'] expansion".format(self.nas_lun_id))
                child1 = pexpect.spawn(exp_lun_cmd.format(self.unity_ip, self.nas_lun_id, Target_size), timeout=None)
                child1.expect('yes / no:')
                child1.sendline('yes')
                child1.expect(pexpect.EOF)
                child1.close()
                self.lun_exp_validation()
            else:
                self.exit_codes(4,exp_size),self.exit_codes(1,"Issue in checking the NAS LUN size")
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1, "NAS LUN expand command failed")
    def pool_validation(self):
        '''

        Function validate Pool expanded as per target config
        param: None
        return: None
        '''
        try:
            self.exit_codes(4, "Started Validation of NAS Pool expansion")
            client = paramiko.client.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.cord_ip, username=self.cord_username, password=self.cord_pwd)
            stdin, stdout, stderr = client.exec_command(storadm + ssh_master_cmd + pool_details,timeout=None)
            exit_status = stdout.channel.recv_exit_status()
            self.exit_status_check("Failed to validate pool expansion",exit_status)
            tmp_list = stdout.read().splitlines()
            client.close()
            for i in tmp_list:
                i = i.split()
                if self.nas_pool in i:
                    self.pool_size = i[1]
                    break
            if '3.40T' not in self.pool_size:
                return False
            else:
                return True
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Failed to validate pool size")
    def pool_expansion(self):
        '''

        Function to expand NAS pool from existing size
        to target size
        param: None
        return: None
        '''
        try:
            if not self.pool_validation():
                client = paramiko.client.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(self.cord_ip, username=self.cord_username, password=self.cord_pwd)
                self.exit_codes(3, "Starting NAS Pool expansion")
                self.disk_grow=disk_grow.format(self.disk_name,'\\')
                stdin, stdout, stderr = client.exec_command(storadm + ssh_master_cmd + strg_scbus,timeout=None)
                exit_status = stdout.channel.recv_exit_status()
                self.exit_status_check(scanbus_failed,exit_status)
                stdin, stdout, stderr = client.exec_command(storadm + ssh_master_cmd + self.disk_grow,timeout=None)
                exit_status = stdout.channel.recv_exit_status()
                exp_op = stdout.read()
                self.exit_status_check("NAS pool expand command failed",exit_status)
                client.close()
                if (self.disk_name in exp_op) and ('completed successfully' in exp_op):
                    if self.pool_validation():
                        self.exit_codes(4, "Validation post NAS Pool expansion completed")
                        self.exit_codes(0, "NAS Pool Expanded successfully to target config")
                else:
                    self.exit_codes(1, "NAS Pool Expansion not Successful as per target config.")
            else:
                self.exit_codes(0,"Already Expanded the NAS pool")
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Pool expand command failed")
    def delete_disk(self):
        '''

        Function to remove the dummy disk
        is present on NAS
        param: None
        return: None
        '''
        try:
            stdin, stdout, stderr = self.client.exec_command(storadm + ssh_master_cmd + strg_disk_list,timeout=None)
            exit_status = stdout.channel.recv_exit_status()
            self.exit_status_check(f_msg,exit_status)
            self.disk_detail = stdout.read().splitlines()
            for i in self.disk_detail:
                if ('1.0G' in i) and ('-' in i) and (self.WWN in i):
                    d_det = i
                    self.d_name = d_det.split()[0]
                    self.disk_remove=disk_remove.format(self.d_name,'\\')
                    stdin,stdout,stderr=self.client.exec_command(storadm+ssh_master_cmd+self.disk_remove,timeout=None)
                    exit_status = stdout.channel.recv_exit_status()
                    self.exit_status_check("Failed to execute disk remove command",exit_status)
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"disk remove command failed")
    def destroy_pool(self):
        '''

        Function to destroy the dummy pool
        present on NAS
        param: None
        return: None
        '''
        try:
            if os.path.exists(temp_id_file):
                with open(temp_id_file, 'r') as f:
                    of = f.read().splitlines()
                    self.dummy_lunid = of[0].strip()
                    self.WWN = of[1].strip()
            already_deleted_check=0
            self.client = paramiko.client.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.cord_ip, username=self.cord_username, password=self.cord_pwd)
            stdin, stdout, stderr = self.client.exec_command(storadm + ssh_master_cmd + strg_scbus,timeout=None)
            exit_status = stdout.channel.recv_exit_status()
            self.exit_status_check(scanbus_failed,exit_status)
            stdin, stdout, stderr = self.client.exec_command(storadm + ssh_master_cmd + strg_disk_list,timeout=None)
            self.disk_detail = stdout.read().splitlines()
            for i in self.disk_detail:
                if ('1.0G' in i) and ('dummy'in i) and (self.WWN in i):
                    self.exit_codes(0, "Starting dummy Pool deletion")
                    already_deleted_check=1
                    stdin,stdout,stderr= self.client.exec_command(storadm + ssh_master_cmd + destroy_pool,timeout=None)
                    exit_status = stdout.channel.recv_exit_status()
                    self.exit_status_check("Failed to execute pool destroy command",exit_status)
                    if self.validate_dummypool_nas(1):
                        self.exit_codes(0, "Dummy Pool deletion successful")
                        break
                    else:
                        self.exit_codes(1, "Failed to delete dummy pool")
                else:
                    continue
            if already_deleted_check==0:
                self.exit_codes(0,"Already deleted dummy pool")
            self.delete_disk()
            if not self.validate_dummypool_nas(1):
                self.exit_codes(0, "Successfully removed the disk")
            else:
                self.exit_codes(1, "Failed to remove the disk")
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Pool deletion or disk remove command failed")
    def validation_post_unmap(self):
        '''

        Function to check dummy lun is unmapped from the hosts
        post unmapping it
        param: None
        return: None
        '''
        try:
            self.exit_codes(4, "Performing validation post dummy LUN removal from NAS host")
            verify_op=subprocess.check_output(self.verify_lun_nashost)
            if self.dummy_lunid not in verify_op:
                return True
            else:
                return False
        except subprocess.CalledProcessError as err:
            self.exit_codes(4,err.output),self.exit_codes(1,"Failed to validate post LUN removal from hosts")
    def unmap_lun(self):
        '''

        Function to unmap the dummy from the hosts
        param: None
        return: None
        '''
        try:
            self.exit_codes(0, "Removing dummy LUN mapping from NAS Hosts")
            remove_lun_host = 'uemcli -d {} /remote/host -id {} set -removeLuns {}'
            if os.path.exists(temp_id_file):
                with open(temp_id_file, 'r') as f:
                    of = f.read().splitlines()
                    self.dummy_lunid = of[0].strip()
                    self.WWN = of[1].strip()
                f.close()
            for host_id in [self.nas1, self.nas2]:
                self.verify_lun_nashost = verify_lun_nashost.format(self.unity_ip, host_id).split()
                verify_op=subprocess.check_output(self.verify_lun_nashost)
                if self.dummy_lunid in verify_op:
                    self.exit_codes(0,"Removing dummy 1G LUN ['ID: {}'] from the NAS host"\
                    " ['ID: {}']".format(self.dummy_lunid, host_id))
                    self.remove_lun_host = remove_lun_host.format(self.unity_ip, host_id, self.dummy_lunid).split()
                    remove_op=subprocess.check_output(self.remove_lun_host)
                    if msg not in remove_op:
                        self.exit_codes(1,"Failed to remove dummy lun from the host")
                    if not self.validation_post_unmap():
                        self.exit_codes(1, "Failed to remove dummy LUN ['ID: {}'] from the" \
                                        " NAS host ['ID: {}']".format(self.dummy_lunid, host_id))
                    self.exit_codes(0, "Sucessfully removed dummy LUN ['ID: {}'] from the" \
                    " NAS host ['ID: {}']".format(self.dummy_lunid, host_id))
                else:
                    self.exit_codes(0, "Dummy 1G LUN ['ID: {}'] already removed from the NAS" \
                            " host ['ID: {}']".format(self.dummy_lunid, host_id))
        except subprocess.CalledProcessError as err:
            self.exit_codes(4,err.output),self.exit_codes(1,"Failed to unmap dummy LUN from hosts")
    def validation_post_del(self):
        '''
        Function to validate there is dummy lun or not in unity
        post deleteion
        param: None
        return: None
        '''
        try:
            self.exit_codes(4, "Performing validation post dummy LUN deletion")
            verify_op=os.popen(check_dummy_lun.format(self.unity_ip, self.dummy_lunid)).read()
            if self.msg in verify_op:
                return True
            elif self.dummy_lunid in verify_op:
                return False
            else:
                self.exit_codes(4,verify_op),self.exit_codes(1,"dummy LUN validate command failed")
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1,"Failed to validate dummy LUN deletion")
    def delete_dummy_lun(self):
        '''
        Function to delete the dummy
        lun in unity
        param: None
        return: None
        '''
        try:
            self.msg = "The specified storage resource not found."
            if os.path.exists(temp_id_file):
                with open(temp_id_file, 'r') as f:
                    of = f.read().splitlines()
                    self.dummy_lunid = of[0].strip()
                    self.WWN = of[1].strip()
            verify_op=os.popen(check_dummy_lun.format(self.unity_ip, self.dummy_lunid)).read()
            if self.msg in verify_op:
                self.exit_codes(0,"Already deleted dummy LUN")
            elif self.dummy_lunid in verify_op:
                self.exit_codes(0, "Starting dummy LUN deletion")
                del_op=subprocess.check_output((del_dummy_lun.format(self.unity_ip, self.dummy_lunid)).split())
                if msg not in del_op:
                    self.exit_codes(1,"Failed to delete dummy LUN")
                if not self.validation_post_del():
                    self.exit_codes(1, "Failed to delete dummy LUN ['ID: {}'].".format(self.dummy_lunid))
                self.exit_codes(0, "Successfully deleted dummy LUN")
            else:
                self.exit_codes(4,verify_op),self.exit_codes(1,"Issue in checking dummy lun exist or not")
        except subprocess.CalledProcessError as err:
            self.exit_codes(4,err),self.exit_codes(1,"Failed to delete dummy LUN")
    def delete_files(self):
        '''
        Function to delete the temporary files created for
        expansion
        param: None
        return: None
        '''
        try:
            self.exit_codes(4,"Removing temporary id files")
            if os.path.exists(req_ids_file):
                cmd1 = rmrf + req_ids_file
                if os.system(cmd1) != 0:
                    self.exit_codes(1,cmd_ex)
            if os.path.exists(temp_id_file):
                cmd1 = rmrf + temp_id_file
                if os.system(cmd1) != 0:
                    self.exit_codes(1, cmd_ex)
            self.exit_codes(0, "NAS pool expansion completed successfully")
            self.logging_configs()
            if os.system('cat ' + tmp_log + " > " + LOG_DIRE+LOG_NAME):
                self.exit_codes(1, "Failed creating log File")
            os.system('rm -rf {} {} {} {}'.format(tmp_log,STAGE,nas_file,value_file)),self.print_logging_detail()
        except Exception as err:
            self.exit_codes(4,err),self.exit_codes(1, "Failed creating final logfile for NAS Pool expansion")
def main():
    '''
    This is main function to call desired function calls
    for performing required tasks
    '''
    obj1 = nas_poolexpansion()
    stage = obj1.stagelist()
    if stage == 1:
        obj1.exit_codes(6,start_msg),obj1.get_inputs(),obj1.get_exp_inputs(),obj1.exp_precheck(),obj1.req_ids()
        obj1.audit_report()
        if codeployed == 'Y':
            stage = 3
        elif codeployed == 'N':
            stage = stage + 1
        with open(STAGE, 'w') as f:
            f.write(str(stage))
        obj1.exit_codes(6, "Expansion Pre check stage completed successfully")
    if stage == 2:
        obj1.exit_codes(6, stg2),obj1.get_inputs(),obj1.get_exp_inputs(),obj1.req_ids()
        obj1.create_dummylun_unity(),obj1.assign_dummylun_to_host()
        if obj1.validate_dummypool_nas():
            obj1.create_dummypool_nas()
        stage = stage + 1
        with open(STAGE, 'w') as f:
            f.write(str(stage))
        obj1.exit_codes(6, "Dummy Lun and Pool creation stage completed successfully")
    if stage == 3:
        obj1.exit_codes(6, "Starting NAS LUN Expansion stage"),obj1.get_inputs(),obj1.get_exp_inputs(),obj1.req_ids()
        obj1.lun_expansion_main()
        stage = stage + 1
        with open(STAGE, 'w') as f:
            f.write(str(stage))
        obj1.exit_codes(6, "NAS Lun Expansion stage completed successfully")
    if stage == 4:
        obj1.exit_codes(6, "Starting NAS Pool Expansion stage"),obj1.get_inputs(),obj1.get_exp_inputs(),obj1.req_ids()
        obj1.pool_expansion()
        obj1.audit_report(1)
        obj1.exit_codes(6, "NAS Pool Expansion stage completed successfully")
        if codeployed == 'Y':
            obj1.delete_files()
            sys.exit(0)
        elif codeployed == 'N':
            stage = stage + 1
        with open(STAGE, 'w') as f:
            f.write(str(stage))
    if stage == 5:
        obj1.exit_codes(6, "Starting Clean up stage"),obj1.get_inputs(),obj1.get_exp_inputs(),obj1.req_ids()
        obj1.destroy_pool(),obj1.unmap_lun(),obj1.delete_dummy_lun()
        obj1.exit_codes(6, "Clean up stage completed successfully"),obj1.delete_files()
if __name__ == "__main__":
    main()
sys.exit(0)

