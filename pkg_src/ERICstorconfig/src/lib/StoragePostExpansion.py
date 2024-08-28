#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for Post Storage Expansion
pre_checks:
a:unity IP accessibility check
b:uemcli check
c:unity check
d:user name and password validation
e:snapshots validation
f:snapshots deletion
g.adding LUNs to consistency group
h.updating the unity.conf file
in Coordinator, Reader1 and Reader2
Hosts available:
1.Coordinator
2.Engine
3.Reader1
4.Reader2
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
# Name      : StorageExpansion.py
# Purpose   : The script will perform Storage Expansion in unity XT
# ******************************************************************************
import subprocess,re,sys,os,getpass,optparse,time,logging,signal,paramiko
TMP_FILE = '/var/tmp/input_file2.txt'
STAGE='/var/tmp/progress'
FILE_PATH = '/opt/ericsson/san/etc/'
HST_FILE = '/var/tmp/input_file3.txt'
LOG_DIRE = '/var/ericsson/log/storage/'
TIME = "%m_%d_%Y-%H_%M_%S"
LOG_NAME = os.path.basename(__file__).replace('.py', '_')+time.strftime(TIME)+'.log'
MSG2="issue with the CLI/CMD execution and above are the actual ERROR"
TEMP_FILE1= '/var/tmp/temp_file.txt'
BLKCLI='/ericsson/storage/san/bin/blkcli --action listluns'
UNITY_CONF='/ericsson/storage/san/plugins/unity/etc/unity.conf'
LUN_STR="\'lunids\'"
SNAP="/var/tmp/snap_ids"

class storage_post(object):
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
        self.colors = {'RED' : '\033[91m', 'END' : '\033[00m',
                       'GREEN' : '\033[92m', 'YELLOW' : '\033[93m'}
        self.snap_id=''
        self.cons_id=''
        self.main_lun=[]
        self.temp_lun=[]
        self.data1=[]

    def logging_configs(self):
        """
        Creates the custom logger for logs
        It creates 2 different log handler
        StreamHandler which handles logs of
        ERROR level or above and FileHandler
        which handles logs of WARNING level or
        Creating a custom logger for logs
        ERROR --> to display error
        WARNING --> To display warning
        return -->none
        args -->none
        LOG_DIRE --> Log dir path
        """
        if not os.path.exists(LOG_DIRE):
            os.makedirs(LOG_DIRE)
        s_handle10 = logging.StreamHandler()
        f_handle10 = logging.FileHandler(LOG_DIRE+LOG_NAME)
        s_handle10.setLevel(logging.ERROR)
        f_handle10.setLevel(logging.WARNING)
        s_formats = logging.Formatter('%(message)s')
        f_formats = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_handle10.setFormatter(s_formats)
        f_handle10.setFormatter(f_formats)
        self.logger.addHandler(s_handle10)
        self.logger.addHandler(f_handle10)

    def log_file_scrn(self, msg2, log_dec=0):
        """
        Logging into file and screen
        based on the value of log_dec variable
        if value of log_dec is 0 it will print
        simultaneously to screen and log file
        for log_dec value as 1 it will print to
        logfile directly
        Param:
              msg -> the actual message
              log_dec -> integer
        Return: None
        msg --> to display message
        return -->none
        args -->none
        """
        if log_dec == 0:
            self.logger.error(msg2)
        else:
            self.logger.warning(msg2)

    def print_logging_detail(self):
        """
        Prints logging details with log file for exit,
        completion and start of the script
        colors --> colors print for logs
        return --> none
        """
        color1 = self.colors
        hash_print1 = '---------------------------------------------------------------------'
        self.log_file_scrn(color1['YELLOW']+hash_print1+color1['END'])
        msg="Please find the script execution logs  ---> "
        self.log_file_scrn(color1['YELLOW']+msg+LOG_DIRE+LOG_NAME+color1['END'])
        self.log_file_scrn(color1['YELLOW']+hash_print1+color1['END'])

    def exit_codes(self, code19, msg):
        """
        Script Exit function
        param: code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        colors -- >to print colors
        """
        colors = self.colors
        if code19 == 1:
            self.log_file_scrn(colors['RED']+"[ERROR] "+colors['END']+": "+msg)
            self.print_logging_detail()
            sys.exit(code19)
        elif code19 == 2:
            self.log_file_scrn(colors['YELLOW']+"[WARN] "+colors['END']+": "+msg)
        else:
            self.log_file_scrn(colors['GREEN']+"[INFO] "+colors['END']+": "+msg)

    def cg_check(self):
        """
        This function will check the consistency group id
        params-->None
        return--->None
        """
        try:
            cmd1 = "uemcli -noHeader -d {} /stor/prov/luns/group show -filter \"ID\"".format(self.ip).split(' ')
            cg_gp = subprocess.check_output(cmd1)
            g_id=[]
            group_id = cg_gp.split()
            for i in range(0,len(group_id)):
                if "res_" in group_id[i]:
                    gp_id=group_id[i].strip()
                    g_id.append(gp_id)
            if len(g_id)!=1:
                self.exit_codes(1,"Existing configuration is not standard configuration")
            self.cons_id = g_id[0]
            with open(TEMP_FILE1, "w") as f:
                f.write(str(self.cons_id))
                f.write("\n")
        except subprocess.CalledProcessError as err:
            self.log_file_scrn("-"*73)
            self.log_file_scrn(err.output)
            self.log_file_scrn("-"*73)
            self.exit_codes(1, MSG2)

    def snap_shotid(self,count=0):
        """
        This function will check the snap id
        If snapshots present on system than
        stage2 will be performed
        if no snapshots identified
        stage3 will be performed
        """
        try:
            cmd="uemcli -noHeader -d {} " \
                "/prot/snap -source {} show -filter 'ID,Name'".format(self.ip,self.cons_id).split(' ')
            snap = subprocess.check_output(cmd)
            snap=snap.strip()
            sp_id = snap.split()
            if len(sp_id)<=1:
                if count == 0:
                    self.exit_codes(0,"No snapshots to delete\n")
                stag = 4
                with open(STAGE, "w") as f:
                    f.write(str(stag))
                return 0
            snap_list = []
            for i in range(0, len(sp_id)):
                if "ID" in sp_id[i]:
                    sp = sp_id[i + 2].strip()
                    snap_list.append(sp)
                if "Name" in sp_id[i]:
                    sp = sp_id[i + 2].strip()
                    snap_list.append(sp)
            with open(SNAP,'w') as f:
                for i in range(0,len(snap_list)):
                    f.write(str(snap_list[i]))
                    f.write("\n")
            if count!=0:
                stag = 3
            else:
                stag = 2
            with open(STAGE, "w") as f:
                f.write(str(stag))
        except Exception as err:
            self.log_file_scrn("-"*73)
            self.log_file_scrn(err)
            self.log_file_scrn("-"*73)
            self.exit_codes(1, MSG2)

    def snap_detach(self):
        """
        This function will detach snap shot id
        detaching the snap shot id will be performed
        """
        self.exit_codes(0,"Snapshots present on server. Performing cleanup of snapshots")
        if os.path.exists(SNAP):
            with open(SNAP,"r") as f:
                out=f.readlines()
            for i in range(0,len(out),2):
                snap_id1=out[i].split('\n')[0].strip()
                snap_name1=out[i+1].split('\n')[0].strip()
                try:
                    cmd1 = "uemcli -noHeader -d {} /prot/snap -id {} detach".format(self.ip,snap_id1).split(' ')
                    subprocess.check_output(cmd1)
                    self.log_file_scrn("{} Snapshot detached".format(snap_name1),1)
                except Exception:
                    self.exit_codes(1,"Unable to detach snapshot {}".format(snap_name1))

    def snap_del_check(self):
        """
        checking for snapshot destruction
        status of deletion will be monitored
        """
        try:
            cmd = "uemcli -noHeader -d {} " \
                  "/prot/snap -source {} show -filter 'Name'".format(self.ip, self.cons_id).split(' ')
            snaps = subprocess.check_output(cmd)
            snaps = snaps.strip()
            sp1_id = snaps.split()
            if len(sp1_id)==0:
                return
            for i in range(0, len(sp1_id)):
                if "Destroying" in sp1_id[i]:
                    time.sleep(1)
                    sys.stdout.write("\rPlease wait%s" %('.'*i))
                    sys.stdout.flush()
                    self.snap_del_check()
                else:
                    count=2
                    self.snap_shotid(count)
        except Exception as err:
            self.log_file_scrn("-" * 73)
            self.log_file_scrn(err)
            self.log_file_scrn("-" * 73)
            self.exit_codes(1, MSG2)
    def snap_deletion(self):
        """
        This function will delete the snap shot id
        snapshotes will be deletedone by one
        args--->none
        params---->none
        """
        if os.path.exists(SNAP):
            with open(SNAP,"r") as f:
                out=f.readlines()
            for i in range(0,len(out),2):
                snap_id=out[i].split('\n')[0].strip()
                snap_name=out[i+1].split('\n')[0].strip()
                try:
                    self.exit_codes(0, "Started deleting {} snapshot".format(snap_name))
                    cmd3 = "uemcli -noHeader -d {} /prot/snap -id {} delete".format(self.ip,snap_id).split(' ')
                    subprocess.check_output(cmd3)
                    self.exit_codes(0,"{} Snapshot deleted".format(snap_name))
                except Exception:
                    self.exit_codes(1, "Unable to delete snapshot {}".format(snap_name))
            self.snap_del_check()
        print("")
        self.exit_codes(0,"Snapshots cleanup successful")

    def check_flagfile(self):
        """
        This file will verify flag file created after storage expansion
        """
        try:
            file_to_check = "/var/tmp/db_expansion_completed"
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname=self.cord_ip, username=self.usename, password=self.pswd)
            ssh_client.open_sftp()
            stdin, stdout, stderr = ssh_client.exec_command('test -e {0} && echo exists'.format(file_to_check))
            errs = stderr.read()
            if errs:
                return False
            file_exits = stdout.read().strip() == 'exists'
            return file_exits
        except Exception:
            return False
    def new_luns(self):
        """
        This function will collect the new luns to add to consistency group
        :return:--->none
        Only MainDb luns will be added to Consistency group
        LUN types:
        1. maindb Lun
        2. Tempdb Lun
        3. ext4 Lun
        4. sysmain Lun
        """
        try:
            cmd = 'uemcli -d {} -noHeader /stor/prov/luns/lun show -filter "ID,Name,Group,Size"'.format(self.ip)
            cmd=cmd.split(" ")
            a = subprocess.check_output(cmd).split('\n')
            data = []
            self.data1 = []
            for i in range(2, len(a), 5):
                if 'res_' not in a[i] and 'Group' in a[i]:
                    data.append(a[i - 2])
                    data.append(a[i + 1])
            if len(data) > 0:
                for i in range(1, len(data), 2):
                    if '1319413953536' in data[i]:
                        da = data[i - 1].split()
                        self.data1.append(da[3])
            if len(self.data1) > 0:
                return 0
            else:
                return 1
        except Exception as err:
            self.log_file_scrn("-" * 73)
            self.log_file_scrn(err)
            self.log_file_scrn("-" * 73)
            self.exit_codes(1, MSG2)

    def cg_add_main(self):
        """
        This function will add Maindb LUNs to consistency group
        Luns will be added to Consistency group
        """
        print("")
        self.exit_codes(0,"Adding LUNs to consistency group")
        self.new_luns()
        if len(self.data1)==0:
            self.exit_codes(1,"No LUNs found to add to consistency group")
            return 1
        for i in range(0, len(self.data1)):
            l_id = self.data1[i]
            try:
                cm = "uemcli -d {} /stor/prov/luns/lun -id {} set -group {}".format(self.ip, l_id, self.cons_id)
                cm=cm.split(' ')
                subprocess.check_output(cm)
                percent = (float(i+1)/len(self.data1))*100
                sys.stdout.write('\r{} percent completed'.format(int(percent)))
                sys.stdout.flush()
            except subprocess.CalledProcessError as err:
                self.log_file_scrn("-" * 73)
                self.log_file_scrn(err.output)
                self.log_file_scrn("-" * 73)
                self.exit_codes(1, MSG2)
            except Exception:
                self.exit_codes(2,"Failed to add {} LUN ID in consistency group".format(l_id))
        print("")
        self.exit_codes(0,"Successfully added LUNs to consistency group\n")

    def cord_update(self):
        """
        This function will do coordinator config file updating
        backup of corrdinator file will be created
        latest file will have expanded luns will previous luns details
        """
        try:
            self.exit_codes(0,"Updating unity.conf in Coordinator")
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname=self.cord_ip, username=self.usename, password=self.pswd)
            sftp_client = ssh_client.open_sftp()
            cmd1='cp /ericsson/storage/san/plugins/unity/' \
                 'etc/unity.conf /ericsson/storage/san/plugins/unity/etc/unity.conf_bkp_{}'.format(time.strftime(TIME))
            stdin, stdout, stderr = ssh_client.exec_command(cmd1)
            stdin, stdout, stderr = ssh_client.exec_command(BLKCLI)
            out = stdout.readlines()
            st, out1 = [], []
            for i in range(0, len(out)):
                data = out[i].split(";")
                st.append(data[0])
            remote_file = sftp_client.open(UNITY_CONF, 'r')
            try:
                for line in remote_file:
                    out1.append(line)
                k, o = "                       " + LUN_STR + " => ", ""
                for i in range(0, len(st)):
                    o = o + st[i] + ","
                o=o.strip(",")
                o = "\'{}\'".format(o)
                o = k + o + ","
                for i in range(0, len(out1)):
                    if "sv_" in out1[i]:
                        out1[i] = o + "\n"
                remote_file = sftp_client.open(UNITY_CONF, 'w')
                remote_file.writelines(out1)
                self.exit_codes(0, "Successfully updated unity.conf in Coordinator")
            except Exception as err:
                self.exit_codes(1,err)
            finally:
                remote_file.close()
                ssh_client.close()
        except Exception as err:
            self.log_file_scrn("-" * 73)
            self.log_file_scrn(err)
            self.log_file_scrn("-" * 73)
            self.exit_codes(1, MSG2)
    def reader_update(self,host):
        """
        This function will Reader1 config file updating
        Backup of old file will be taken
        new fill will have old and new luns
        """
        try:
            old_lun_data=''
            new_lundata=''
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname=self.cord_ip, username=self.usename, password=self.pswd)
            cmd1 = 'cp /ericsson/storage/san/plugins/unity/etc/' \
                   'unity.conf /ericsson/storage/san/plugins/unity/etc/unity.conf_bkp_{}'.format(time.strftime(TIME))
            cmd2="ssh -o StrictHostKeyChecking=no"
            stdin, stdout, stderr = ssh_client.exec_command("{} {} {}".format(cmd2,host,cmd1))
            cmd="ssh -o StrictHostKeyChecking=no {} 'cat {}'".format(host,UNITY_CONF)
            stdin, stdout, stderr = ssh_client.exec_command(cmd)
            vari = stderr.read()
            vari = vari.strip()
            if vari==True:
                self.exit_codes(1,"Unable to connect to {} Server".format(host))
            out2 = stdout.read()
            data=out2.split("\n")
            for i in range(0,len(data)):
                if "lunids" in data[i]:
                    luns=data[i].split("=>")
                    old_lun_data=luns[1].strip()
                    old_lun_data=old_lun_data.strip(",")
            cmd2="ssh -o StrictHostKeyChecking=no {} {}".format(host,BLKCLI)
            stdin, stdout, stderr = ssh_client.exec_command(cmd2)
            var = stderr.read()
            var = var.strip()
            if var==True:
                self.exit_codes(1,"Unable to connect to {} Server".format(host))
            out = stdout.readlines()
            new_str=""
            st=[]
            for i in range(0, len(out)):
                data_s = out[i].split(";")
                st.append(data_s[0])
                new_str=new_str+str(data_s[0])+","
            new_str=new_str.strip(',')
            new_lundata="'"+new_str+"'"
            cmd3="ssh -o StrictHostKeyChecking=no {} \"cat {} | sed -i '/'lunids'/ s/{}/{}/' {}\"".\
                format(host,UNITY_CONF,old_lun_data,new_lundata,UNITY_CONF)
            stdin, stdout, stderr = ssh_client.exec_command(cmd3)
            if host=='dwh_reader_1':
                self.exit_codes(0, "Successfully updated unity.conf in Reader1")
            if host=='dwh_reader_2':
                self.exit_codes(0, "Successfully updated unity.conf in Reader2")
            ssh_client.close()
        except Exception as err:
            self.log_file_scrn("-" * 73)
            self.log_file_scrn(err)
            self.log_file_scrn("-" * 73)
            self.exit_codes(1, MSG2)
    def read_input(self):
        """
        This function is used to read the inputs
        """
        if os.path.exists(TMP_FILE):
            with open (TMP_FILE,"r") as f:
                out=f.readlines()
                self.ip = out[0].split('\n')[0].strip()
            with open (HST_FILE,'r') as f2:
                out2=f2.readlines()
                self.host1 = out2[0].split('\n')[0].strip()
                self.host2 = out2[2].split('\n')[0].strip()
                self.host3 = out2[4].split('\n')[0].strip()
                self.host4 = out2[6].split('\n')[0].strip()
            with open ('/var/tmp/input_file1.txt','r') as f1:
                out1=f1.readlines()
                pwd,key='',''
                for i in out1:
                    if "ENIQ_IP" in i:
                        self.cord_ip = i.split('::')[1].strip()
                    elif "ENIQ_username" in i:
                        self.usename = i.split('::')[1].strip()
                    elif "ENIQ_password_key" in i:
                        keyy=i.split('::')[1].strip()
                    elif "ENIQ_password" in i:
                        pwd = i.split('::')[1].strip()
                if pwd!='' and keyy!='':
                    var1='echo {} | openssl enc -aes-256-ctr -md sha512 -a -d -salt -pass pass:{}'.format(pwd,keyy)
                    self.pswd = os.popen(var1).read()
                else:
                    self.exit_codes(1,'Password or Key Value not found, exiting the script')
        else:
            self.exit_codes(1,"Input details not available. Check and Re run the script")
    def read_input2(self):
        """
        This Function will Read consistency group id and snap shot id
        """
        if os.path.exists(TEMP_FILE1):
            with open (TEMP_FILE1,"r") as f:
                out=f.readlines()
                self.cons_id = out[0].split('\n')[0].strip()
        else:
            self.read_input()
            self.cg_check()
def handler(signum, frame):
    """
    restore the original signal handler
    in raw_input when CTRL+C is pressed will be handled by below
    """
    print("ctrl+c not allowed at this moment")

def check_userid():
    """
    This function is to check the user id,
    if user id not root then exit the script
    Param: None
    Return: None
    """
    if os.getuid() != 0:
        print("ERROR: Only Root can execute the script...")
        sys.exit(1)
def stagelist_post():
    """
    Checks and returns which stage we are currently present at in case of failure
    Args: None
    return: int
    stage --> stage the execution going on
    """
    stag=1
    if not os.path.exists(STAGE):
        with open(STAGE,"w") as f:
            f.write(str(stag))
    else:
        with open(STAGE, 'r') as f:
            stag = int(f.read())
    return stag
def main():
    """
    This is main function
    stage1: inputs validation and collecting Cg id and snap id validations
    stage2:detaching the snapshots
    stage3:deleting the snapshots
    stage4:adding luns to consistency group
    stage5:coordinator unity.conf file update
    stage6:reader1 unity.conf file update
    stage7:reader2 unity.conf file update
    """
    stag=stagelist_post()
    po=storage_post()
    po.print_logging_detail()
    check_userid()
    if stag == 1:
        po.read_input()
        val=po.check_flagfile()
        if val == False:
            po.exit_codes(1, "Storage Expansion not performed on server. Check and rerun the script")
        code=po.new_luns()
        if code !=0:
            po.exit_codes(1,"Storage Expansion not performed on server. Check and rerun the script")
        po.cg_check()
        po.snap_shotid()
        stag=stagelist_post()
    if stag == 2:
        po.read_input()
        po.read_input2()
        po.snap_detach()
        stag = stag + 1
        with open(STAGE, "w") as f:
            f.write(str(stag))
    if stag == 3:
        po.read_input()
        po.read_input2()
        po.snap_deletion()
        stag = stag+1
        with open(STAGE, "w") as f:
            f.write(str(stag))
    if stag == 4:
        po.read_input()
        po.read_input2()
        po.cg_add_main()
        stag = stag + 1
        with open(STAGE, "w") as f:
            f.write(str(stag))
    if stag == 5:
        po.read_input()
        po.read_input2()
        po.cord_update()
        stag = stag + 1
        with open(STAGE, "w") as f:
            f.write(str(stag))
    if stag == 6:
        po.read_input()
        po.read_input2()
        po.exit_codes(0,"Updating unity.conf in Reader1")
        po.reader_update("dwh_reader_1")
        stag = stag + 1
        with open(STAGE, "w") as f:
            f.write(str(stag))
    if stag == 7:
        po.read_input()
        po.read_input2()
        po.exit_codes(0,"Updating unity.conf in Reader2")
        po.reader_update("dwh_reader_2")
        print("")
if __name__ == "__main__":
    main()
sys.exit(0)

