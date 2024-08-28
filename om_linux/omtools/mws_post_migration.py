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
 Name      : mws_post_migration.py
 Purpose   : The script is a helper script for mws_migration.py script
 Exit Values:
 ********************************************************************
"""
import re
import sys
import logging
import os
import subprocess
import paramiko
import pexpect
import time
from stat import S_ISDIR as isdir

COLORS = {'RED': '\033[91m', 'END': '\033[00m', 'GREEN': '\033[92m', 'YELLOW': '\033[93m'}
STAGE='/var/tmp/.mws_mig_stage'
LOGGER = logging.getLogger()
LOG_DIRECT = '/var/ericsson/log/mws_migration/'
log_file = ""
cmd_exec_error="Command execution issue"
yes_list = {'yes'}
no_list = {'no'}
TMP_LOG = "mws_mig_tmp_logs.log"
cmd_exe_failed = "Command Execution Failure"
NEW_IF_FILE = "/var/tmp/.new_if"
rm_rf_cmd="rm -rf "
cmd_exe_err="Command Execution issue"

def read_stdin():
    """
    This function acts as a generator function
    for getting one line at a time from logs.
    param: None
    return: None
    """
    try:
        line = ''
        while sys.stdin:
            c = sys.stdin.read(1)
            if c == '\r' or c == '\n':
                # line is being updated
                yield line
                line = ''
            elif c == '':
                break
            else:
                line += c
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exe_failed)
def progress_bar(progress, total):
    """
    This function prints the progress bar
    for rsync command execution.
    param: progress -> int, total -> int
    return: None
    """
    try:
        percent = 100 * (progress / float(total))
        bar = '#' * int(percent) + '-' * (100 - int(percent))
        print ("\r|{0}| {1:.0f} %           ".format(bar, percent)),
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exe_failed)
def progress_bar_wrapper():
    """
    The wrapper function for displaying
    the progress bar
    param: None
    return: None
    """
    try:

        progress_bar(0, 100)
        for line in read_stdin():
            parts = line.split()
            if len(parts) == 6 and parts[1].endswith('%') and (parts[-1].startswith('to-chk=')
                                                               or parts[-1].startswith('ir-chk=')):
                total = int(parts[-1].replace(')', '').split("=")[1].split('/')[1])
                progress = total - int(parts[-1].replace(')', '').split("=")[1].split('/')[0])
                progress_bar(progress, total)
        progress_bar(100, 100)
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exe_failed)

def logging_configs(name):
    """
    Creates the custom logger for logs'
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
    try:
        global log_file
        log_file = name
        if not os.path.exists(LOG_DIRECT):
            os.makedirs(LOG_DIRECT)
        s_hand12 = logging.StreamHandler()
        f_hand12 = logging.FileHandler(LOG_DIRECT + name)
        s_hand12.setLevel(logging.ERROR)
        f_hand12.setLevel(logging.WARNING)
        s_formats = logging.Formatter('%(message)s')
        f_formats = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_hand12.setFormatter(s_formats)
        f_hand12.setFormatter(f_formats)
        LOGGER.addHandler(s_hand12)
        LOGGER.addHandler(f_hand12)
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exec_error)

def create_log_file(name):
    """
    This function creates the log file at the end
    after migration is performed successfully.
    param:
        name->string
    return: None
    """
    try:
        if os.system('cat '+LOG_DIRECT+TMP_LOG+" > "+LOG_DIRECT+name):
            exit_codes(1, "Failed creating log File")
        os.system('rm -rf '+LOG_DIRECT+TMP_LOG)
    except Exception as e:
        print(e)
        exit_codes(1, "Failed creating final logfile for MWS migration process")

def log_file_scrn(mesg, log_decs=0):
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
    try:
        a = log_decs
        if a == 0:
            LOGGER.error(mesg)
        else:
            LOGGER.warning(mesg)
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exec_error)

def check_local_dir(local_dir_name):
    """
    whether the local folder exists, create if it does not exist
    param:
        local_dir_name -> string
    return: None
    """
    try:
        if not os.path.exists(local_dir_name):
            os.makedirs(local_dir_name)
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exec_error)


def down_from_remote(sftp_obj, remote_dir_name, local_dir_name):
    """
    This function will help to copy
    the contents from directory to
    directory between two server.
    param:
        sftp_obj -> object ,
        remote_dir_name -> string,
        local_dir_name -> string

    return: None
    """
    try:
        # download files remotely
        exit_codes(6, "copying " + remote_dir_name + " to " + local_dir_name)
        remote_file = sftp_obj.stat(remote_dir_name)
        if isdir(remote_file.st_mode):
            # Folder, can't download directly, need to continue cycling
            check_local_dir(local_dir_name)
            exit_codes(6, 'Start downloading folder: ' + remote_dir_name)
            for remote_file_name in sftp_obj.listdir(remote_dir_name):
                sub_remote = os.path.join(remote_dir_name, remote_file_name)
                sub_remote = sub_remote.replace('\\', '/')
                sub_local = os.path.join(local_dir_name, remote_file_name)
                sub_local = sub_local.replace('\\', '/')
                down_from_remote(sftp_obj, sub_remote, sub_local)
        else:
            # Files, downloading directly
            exit_codes(6, 'Start downloading file: ' + remote_dir_name)
            sftp_obj.get(remote_dir_name, local_dir_name)
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exec_error)


def validate_ip(ip):
    """
    This function is to test if user provided a valid IP
    address and its reachable.
    param:
        ip -> IP address
    return:None
    """
    try:
        exp = r'^\s*(?:[0-9]{1,3}\.){3}[0-9]{1,3}\s*$'
        if not re.search(exp, ip):
            print("Invalid IP Address Entered, try again\n")
            return False
        code = subprocess.call(["ping", ip, "-c", "2"], stdout=subprocess.PIPE, shell=False)
        if code:
            print("Server not reachable. Please make sure the IP address {} is correct".format(ip))
            return False
        else:
            return True
    except Exception as e:
        print(e)
        exit_codes(1, "Issue with commands or unable to reach source MWS")


def validate_host(host_name):
    """
    This function validates if the provided host name
    is valid and reachable
    param:
        host_name -> string
    return: none
    """
    try:
        code = subprocess.call(["ping", host_name, "-c", "2"], stdout=subprocess.PIPE, shell=False)
        if code:
            print("Server not reachable. Please make sure the host name {} is correct".format(host_name))
            return False
        else:
            return True
    except Exception as e:
        print(e)
        exit_codes(1, "Issue with commands or unable to reach source MWS server")


def exit_gracefully_upgrade(signum, frame):
    """
    restore the original signal handler
    in raw_input when CTRL+C is pressed,
    and our signal handler is not reentrant
    Param: None
    return: None
    """
    print("ctr+c not allowed at this moment")


def check_userid():
    """
    This function checks whether root only
    executing the script or not
    param: None
    return: None
    """
    try:
        if os.getuid() != 0:
            print("ERROR: only root can execute the script...")
            sys.exit(1)
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exec_error)


def check_hardware_type(old_ip, old_password):
    """
    This function will check hardware type. It
    will exit if any of the MWS server is
    Gen10 Plus or else will continue
    Param:
        old_ip -> string
        old_password -> string
    return: None
    """
    try:
        exit_codes(0, "Started hardware check for MWS migration")
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(old_ip, password=old_password)
        cmd = "dmidecode -t system 2> /dev/null | grep -w 'Product Name' | cut -d ':' -f2 | cut -d ' ' -f4,5"
        stdin, stdout, stderr = client.exec_command(cmd)
        old = stdout.read()
        new = os.popen(cmd).read().strip()
        if 'Gen10 Plus' in old or 'Gen10 Plus' in new:
            exit_codes(1, "Gen10 plus is not supported for MWS migration")
        client.close()
        exit_codes(0, "Successfully completed hardware check for MWS migration")
    except Exception as e:
        print(e)
        exit_codes(1, "Command execution issue for H/W check")

def get_param_files(client_name, kick_path):
    """
    This Function will get parameter required for
    adding DHCP clients from {client}_ks_cfg.txt
    and merge it with {client}_installation_param_details
    file to get another file with all parameter.
    Param:
        client_name -> string,
        kick_path -> string
    return: None
    """
    try:
        flag = 0
        exit_codes(6, "Getting required parameters for adding DHCP client {}".format(client_name))
        if not os.path.exists("{0}/{1}/{1}_installation_param_details".format(kick_path, client_name)):
            exit_codes(5, "Failed adding DHCP client {0}: Couldn't find file {0}_installation_param_details"
                          "file, please manually add DHCP client {0}".format(client_name))
            flag = 1
        if not os.path.exists("{0}/{1}/{1}_ks_cfg.txt".format(kick_path, client_name)):
            exit_codes(5, "Failed adding DHCP client {0}: Couldn't find file {0}_ks_cfg.txt, please manually add DHCP "
                          "client {0}".format(client_name))
            flag = 1
        cmd = "cat {0}/{1}/{1}_installation_param_details 2> /dev/null | grep -v locate".format(kick_path, client_name)
        param = os.popen(cmd).read().replace('\n', ' ')
        if os.system("cat {0}/{1}/{1}_ks_cfg.txt 2> /dev/null | grep -v -e '^$' > "
                     "/var/tmp/{1}_dhcp_client_params".format(kick_path, client_name)):
            exit_codes(5, "Failed Copying {0} ks_cfg.txt file, please manually add DHCP client {0}".format(client_name))
            flag = 1
        if os.system("echo {0} >> /var/tmp/{1}_dhcp_client_params".format("CLIENT_INSTALL_PARAMS="+param, client_name)):
            exit_codes(5, "Failed copying install param to temp files, please manually add DHCP "
                          "client {}".format(client_name))
            flag = 1
        if flag == 1:
            return False
        cmd1 = "cat {0}/{1}/{1}_ks_cfg.txt 2> /dev/null | grep CLIENT_BOOT_MODE".format(kick_path, client_name)
        if "CLIENT_BOOT_MODE" not in os.popen(cmd1).read():
            cmd_output = os.system("echo {0} >> "
                                   "/var/tmp/{1}_dhcp_client_params".format("CLIENT_BOOT_MODE=Legacy", client_name))
            if cmd_output:
                exit_codes(5, "Failed copying install param to temp files, please manually add DHCP client {} after "
                              "verification".format(client_name))
                flag = 1
        exit_codes(6, "Successfully got all required parameters for adding DHCP client {}".format(client_name))
        if flag == 1:
            return False
        return True
    except Exception as e:
        print(e)
        exit_codes(1, "Failed getting parameter files for adding DHCP clients")

def add_dhcp_clients_wrapper(client):
    """
    Executes Command to add DHCP clients
    with -f paramter
    Param:
        client -> string
    return: None
    """
    try:
        exit_codes(6, 'Started adding DHCP client ' + client)
        script_path = "/ericsson/kickstart/bin/manage_linux_dhcp_clients.bsh"
        cmd = "{0} -a add -c {1} -f /var/tmp/{1}_dhcp_client_params".format(script_path, client)
        child = pexpect.spawn(cmd, timeout=30)
        child.sendline("Yes")
        out = child.read()
        child.expect(pexpect.EOF)
        if "ERROR" in out:
            exit_codes(5, "Failed adding DHCP client " + client)
            exit_codes(5, out.split("Script aborted...")[1].strip())
        else:
            exit_codes(6, 'Successfully Added DHCP client ' + client)
    except Exception as e:
        print(e)
        exit_codes(1, "Failed adding dhcp client {}".format(client))


def add_dhcp_clients():
    """
    This function add all DHCP clients which were
    added for Source MWS
    Param: None
    return: None
    """
    try:
        exit_codes(0, "Started adding DHCP clients")
        lin_media_path = "/JUMP/LIN_MEDIA/"
        dir_lst = os.listdir(lin_media_path)
        client_lst = []
        for i in dir_lst:
            if os.path.exists(lin_media_path + i) and os.path.exists(lin_media_path + i + '/kickstart'):
                kickstart_path = lin_media_path+i+"/kickstart/"
                for client in os.listdir(kickstart_path):
                    client_lst.append([client, kickstart_path])
        for i in client_lst:
            if get_param_files(i[0], i[1]):
                add_dhcp_clients_wrapper(i[0])
        exit_codes(0, "Completed adding DHCP clients")
    except Exception as e:
        print(e)
        exit_codes(1, "Failed adding DHCP clients")
def get_net_conf(file):
    """
    This function gets all the required
    details and returns it
    Param:
        file -> string
    return: None
    """
    try:
        hwadd4, uuid4, name4, device4 = '', '', '', ''
        with open(file, "r") as f:
            out = f.readlines()
            for i in range(0, len(out)):
                if "HWADDR" in out[i]:
                    data = out[i]
                    data1 = data.split("=")
                    hwadd4 = str(data1[1]).strip()
                if "UUID" in out[i]:
                    data = out[i]
                    data2 = data.split("=")
                    uuid4 = str(data2[1]).strip()
                if "NAME" in out[i]:
                    data = out[i]
                    data2 = data.split("=")
                    name4 = str(data2[1]).strip()
                if "DEVICE" in out[i]:
                    data = out[i]
                    data2 = data.split("=")
                    device4 = str(data2[1]).strip()
        return hwadd4, uuid4, name4, device4
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exec_error)

def get_if_helper(type, lst, i, yes_list, no_list):
    """
    This function gets the Interface details from user for
    source MWS
    Param:
        type -> string,
        lst -> list,
        i -> string,
        yes_list -> list,
        no_list -> list
    return: None
    """
    try:
        port = {'old': 'source', 'new': 'target'}
        while True:
            choice1 = raw_input("Is the " + i + " interface configured on " + port[type] + " MWS? [yes/no] ")
            if choice1.lower() in yes_list:
                exit_codes(7, "List of configured interfaces available on source MWS: ")
                for ind, j in enumerate(lst):
                    print(j)
                interface = raw_input("Please select the " + i + " interface from above list: ")
                if interface not in lst:
                    print("Please enter correct interface, {} is not valid".format(interface))
                else:
                    return interface
            elif choice1.lower() in no_list:
                return ""
            else:
                print("Please enter the valid input, {} is not valid input".format(choice1.lower()))
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exec_error)

def get_if(type, lst):
    """
    This function gets Interface details for Source MWS
    Param:
        type -> string
        lst -> list
    return: None
    """
    try:
        old_storage_interface, old_backup_interface, old_man_interface = "", "", ""
        interface_name_list = ['service', 'storage', 'backup', 'management']

        for i in interface_name_list:
            if len(lst) <= 0:
                break
            if i == 'service':
                continue
            interface = get_if_helper(type, lst, i, yes_list, no_list)
            if i == 'storage':
                old_storage_interface = interface
            elif i == 'backup':
                old_backup_interface = interface
            elif i == 'management':
                old_man_interface = interface
            if not interface == "":
                lst.remove(interface)
        return old_storage_interface, old_backup_interface, old_man_interface
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exec_error)


def get_new_if_helper(i, lst):
    """
    This function gets the Interface details from user for
    target MWS
    Param: None
    return: None
    """
    try:
        while True:
            exit_codes(7, "List of available interfaces on target MWS: ")
            for ind, j in enumerate(lst):
                print(j)
            interface = raw_input('Select the {} interface to be configured on target MWS from above list: '.format(i))
            if interface in lst:
                choice = raw_input("Do you want {} as {} interface?[yes/no] ".format(interface, i))
                if choice in no_list:
                    continue
                elif choice in yes_list:
                    return interface
                else:
                    print("Please enter valid input[yes/no] ")
            else:
                print("Please Enter the valid interface name from the list")
    except Exception as e:
        print(e)
        exit_codes(1, "Failed getting interface details for target MWS")

def get_n_if(lst_old, lst_new):
    """
    This function gets Interface details for new MWS
    Param:
        lst_old -> string
        lst_new -> string
    return: None
    """
    try:
        new_storage_interface, new_backup_interface, new_man_interface = "", "", ""
        interface_name_list = ['storage', 'backup', 'management']

        for ind, i in enumerate(interface_name_list):
            if len(lst_new) <= 0:
                break

            if not lst_old[ind].strip() == "":
                interface = get_new_if_helper(i, lst_new)
                if i == 'storage':
                    new_storage_interface = interface
                elif i == 'backup':
                    new_backup_interface = interface
                elif i == 'management':
                    new_man_interface = interface
                if not interface == "":
                    lst_new.remove(interface)

        return new_storage_interface, new_backup_interface, new_man_interface
    except Exception as e:
        print(e)
        exit_codes(1, "Failed getting interface details for target MWS")

def stagelist():
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
        return stage
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exec_error)

def migration_precheck(host_ip, passwd):
    """
    This function will verify if enough space
    is available in Target MWS under /JUMP
    directory for MWS migration.
    Param:
        host_ip -> string
        passwd -> -> string
    return: None
    """
    try:
        exit_codes(0, "Started pre-migration check for MWS migration")
        client = paramiko.client.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host_ip, password=passwd)
        cmd = "df -h /JUMP | tail -n 1 | awk '{print $2}'"
        stdin, stdout, stderr = client.exec_command(cmd)
        var = stdout.read()
        old_mws_jump_storage = int(var.replace("G", " ").strip())
        var1 = os.popen(cmd).read()
        new_mws_jump_storage = int(var1.replace("G", " ").strip())
        if new_mws_jump_storage < old_mws_jump_storage:
            exit_codes(4, "Enough /JUMP storage is not available for MWS migration")
            exit_codes(0, "Required /JUMP storage : " + var + "\n" + "available /JUMP storage : " + var1)
            sys.exit(1)
        exit_codes(0, "Done pre-migration check for MWS migration")
    except Exception as e:
        print(e)
        exit_codes(1, "Failed to do pre migration verification")

def get_valid_ip(ip_addr):
    """
    This function removes double qoutes around
    the IP address, and return it
    Param:
        ip_addr -> string
    return: None
    """
    try:
        if '"' in ip_addr:
            ip_new = ip_addr.replace('"', "")
        else:
            ip_new = ip_addr
        return ip_new
    except Exception as e:
        print(e)
        exit_codes(1, "Failed getting valid gateway IP address")


def vlan_gateway_check(args, interface):
    """
    This function executes command to performs
    ping for each configured Interface.
    Param: args -> string
            interface -> string
    return: None
    """
    try:
        ifcfg_path = "/etc/sysconfig/network-scripts/ifcfg-{}".format(interface)
        if os.path.exists(ifcfg_path):
            with open(ifcfg_path, "r") as f:
                ifcfg_file = f.readlines()
            gate_ip = ""
            for i in ifcfg_file:
                if "GATEWAY" in i:
                    gate_ip = get_valid_ip(i.split("=")[1].strip())
                    break
            code = subprocess.call(["ping", "-I", interface, gate_ip, "-c", "2"], stdout=subprocess.PIPE, shell=False)
            if code:
                if args == "Service":
                    exit_codes(1, "{} gateway not reachable.".format(args))
                else:
                    exit_codes(5, "{} gateway not reachable.".format(args))
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exec_error+": couldn't ping vlan gateway")


def post_migration_verification():
    """
    This function verifies the availablility
    of all configured Interfaces and checks
    the status all required services
    Param: None
    return: None
    """
    try:
        exit_codes(0, "Started post MWS migration verification")
        vlan_interfaces = "/var/tmp/.new_if"
        if os.path.exists(vlan_interfaces):
            with open(vlan_interfaces, "r") as f:
                file_details = f.readlines()
            service_interface = file_details[0].strip()
            storage_interface = file_details[1].strip()
            backup_interface = file_details[2].strip()
            management_interface = file_details[3].strip()
            vlan_gateway_check("Service", service_interface)
            vlan_gateway_check("Storage", storage_interface)
            vlan_gateway_check("Back-up", backup_interface)
            vlan_gateway_check("Management", management_interface)
            cmd1 = "systemctl status dhcpd"
            cmd2 = "systemctl status nfs"
            cmd3 = "systemctl status network"
            dhcpd_status = os.popen(cmd1).read()
            nfs_status = os.popen(cmd2).read()
            network_status = os.popen(cmd3).read()
            flag, active_status = 0, "Active: active"
            if active_status not in dhcpd_status:
                exit_codes(5, "dhcpd service not active")
                flag = flag + 1
            else:
                exit_codes(0, "dhcpd service active")
            if active_status not in nfs_status:
                exit_codes(5, "nfs service is not active")
                flag = flag + 1
            else:
                exit_codes(0, "nfs service active")
            if active_status not in network_status:
                exit_codes(5, "network service not active")
                flag = flag + 1
            else:
                exit_codes(0, "network service active")
            if flag != 0:
                exit_codes(1, "Please activate the services and re-run post verification")
            else:
                add_dhcp_clients()
                exit_codes(0, "Successfully completed post MWS migration verification")
                exit_codes(0, "Please refer the log file {} for script's execution information".format(LOG_DIRECT
                                                                                                            + log_file))
        else:
            exit_codes(1, "File {} not present".format(vlan_interfaces))
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exec_error+": Failed while post migration verification")


def exit_codes(code_num, msg):
    """
    Script Exit function
    param: code --> Exit code of the script and changing type of the message
           msg --> Actual message to print on the screen
    return: None
    colors -- >to print colors
    """
    try:
        if code_num == 1:
            msg = COLORS['RED']+"[ERROR] "+COLORS['END']+": "+msg
            print(msg)
            log_file_scrn(msg, 1)
            sys.exit(1)
        elif code_num == 3:
            msg = "["+time.strftime("%m-%d-%Y-%H:%M:%S")+"] "+ COLORS['GREEN'] + "[INFO] " + COLORS['END'] + ": " + msg
            print(msg)
            log_file_scrn(msg, 1)
        elif code_num == 4:
            msg = COLORS['YELLOW'] + "[WARNING] " + COLORS['END'] + ": " + msg
            print(msg)
            msg =  "["+time.strftime("%m-%d-%Y-%H:%M:%S")+"] "+msg
            log_file_scrn(msg, 1)
        elif code_num == 5:
            msg = COLORS['RED'] + "[ERROR] " + COLORS['END'] + ": " + msg
            print(msg)
            log_file_scrn(msg, 1)
        elif code_num == 6:
            msg = COLORS['GREEN']+"[INFO] "+COLORS['END']+": "+msg
            log_file_scrn(msg, 1)
        elif code_num == 7:
            msg = COLORS['GREEN'] + "[INFO] " + COLORS['END'] + ": " + msg
            print(msg)
        else:
            msg = COLORS['GREEN']+"[INFO] "+COLORS['END']+": "+msg
            print(msg)
            log_file_scrn(msg, 1)
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exe_failed)

def make_if_hidden(new_service_interface, new_if_file, old_if_file):
    """
    This function creates hidden .new_if file which
    is used for post migration verification for
    fetching network Interface details
    Param: new_service_interface -> string,
            new_if_file -> string,
            old_if_file -> string
    return: None
    """
    try:
        cmd = "echo " + new_service_interface + " > " + NEW_IF_FILE
        if os.system(cmd) != 0:
            exit_codes(1, cmd_exe_failed)
        cmd = "cat " + new_if_file + " >> " + NEW_IF_FILE
        if os.system(cmd) != 0:
            exit_codes(1, cmd_exe_failed)
        cmd = rm_rf_cmd + new_if_file + " " + old_if_file
        if os.system(cmd) != 0:
            exit_codes(1, cmd_exe_failed)
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exe_failed)
def remove_and_replace(cred_file, new_cred_file, new_if_file, new_service_interface, old_if_file):
    '''
    Removes the cred files and replace interface details
    with other files.
    Param: cred_file -> string,
        new_cred_file -> string,
        new_if_file -> string,
        new_service_interface -> string,
        old_if_file -> string
    return: None
    '''
    try:
        exit_codes(6, "Removing credentials files and replace interface files")
        if os.path.exists(cred_file):
            cmd1 = rm_rf_cmd + cred_file
            if os.system(cmd1) != 0:
                exit_codes(1, cmd_exe_failed)
        if os.path.exists(new_cred_file):
            cmd1 = rm_rf_cmd + new_cred_file
            if os.system(cmd1) != 0:
                exit_codes(1, cmd_exe_failed)
        if os.path.exists(STAGE):
            cmd1 = rm_rf_cmd + STAGE
            if os.system(cmd1) != 0:
                exit_codes(1, cmd_exe_failed)
        if not os.path.exists(new_if_file):
            exit_codes(1, "Cannot get network interface details, cannot do post verification")
        else:
            make_if_hidden(new_service_interface, new_if_file, old_if_file)
    except Exception as e:
        print(e)
        exit_codes(1, cmd_exe_err)
