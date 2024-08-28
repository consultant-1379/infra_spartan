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
# Name      : mws_functions.py
# Purpose   : The script wil perform mws upgrade automatically
# ********************************************************************
"""
Modules used in the script
"""
import subprocess, os, pexpect, signal, sys, getpass, re, time, logging, base64
from os import path

LOG_DIRE = '/var/ericsson/log/mws_upgrade/'
LOG_NAME = os.path.basename(__file__).replace('.py', '_')+time.strftime("%m_%d_%Y-%H_%M_%S")+'.log'
FILE_PATH,time_for,temp_om_detail = "/var/tmp/temp.txt","%m-%d-%Y-%H:%M:%S","/var/tmp/om_detail.txt"
temp_patch_detail,hist_loc,CONSTANT2= "/var/tmp/patch_detail",'/ericsson/config/mws_history','.*password.*'
curr_media_loc,IP_FILE,CONSTANT3,skipit='/ericsson/config/mws_status',"/var/tmp/temp_ip",'ls -t',"skip\n"
TEMP_PATH,tem_log_loc,STAGE= "/var/tmp/custom_service.bsh","/var/tmp/temp_log_upgrade",'/var/tmp/stagelists'
divider,divider2,iso_p="#"*100,("#"*100)+'\n','/var/tmp/iso_patch.txt'
file1,remo,EQ="/var/tmp/health_check","rm -rf {}",'/var/tmp/equals'
def check_service():
    '''
    this function will check the services required to run the script.
    var-->0 if no action required
    var-->768 or 1024 to perform so sort of action
    '''
    try:
        var=os.system("systemctl status autoreboot.service >/dev/null 2>&1")
        if var == 0:
            """
            no action required
            """
            pass
        elif (var == 1024) or (var == 768):
            console_check()
    except Exception as err:
        print(err)

def console_check():
    '''
    This function will check whether if script is running on ILO or not.
    script will be aborted if script not running from ilo console
    expected ttys0 if script running from ilo
    pts if not running from ilo console
    '''
    out=subprocess.check_output("/usr/bin/tty")
    if "ttyS0" in out:
        """no action required"""
        pass
    elif "pts" in out:
        at.exit_codes(1,'Please run this script through ILO Console only')
        os.system("systemctl start serial-getty@ttyS0.service >/dev/null 2>&1")
        sys.exit(0)
    else:
        at.exit_codes(1,'Script running from invalid console..Please run this script through ILO Console only')
        os.system("systemctl start serial-getty@ttyS0.service >/dev/null 2>&1")
        sys.exit(0)
def iso_path(path):
    """
    saving patch iso path
    patch iso will be saved to temporary path
    """
    with open(iso_p,'w') as f:
        f.write(path)
def remove_files():
    """
    Removes the unnecessary files after the script is completed
    all temporary fle will be removed to support new run without any effect
    Param: None
    return: None
    """
    if os.path.exists(tem_log_loc):
        os.remove(tem_log_loc)
    if os.path.exists(FILE_PATH):
        os.remove(FILE_PATH)
    if os.path.exists(TEMP_PATH):
        os.remove(TEMP_PATH)
    if os.path.exists(STAGE):
        os.remove(STAGE)
    if os.path.exists(temp_patch_detail):
        os.remove(temp_patch_detail)
    if os.path.exists(temp_om_detail):
        os.remove(temp_om_detail)
    if os.path.exists(iso_p):
        os.remove(iso_p)
    if os.path.exists(IP_FILE):
        os.remove(IP_FILE)
    if os.path.exists('/var/tmp/p_path'):
        os.remove('/var/tmp/p_path')
    if os.path.exists('/var/tmp/path_check'):
        os.remove('var/tmp/path_check')
    if os.path.exists(EQ):
        os.remove(EQ)

def get_ip():
    """
    This function provides the ip of
    the server for backup related purpose
    Param: None
    return: IP of the MWS server
    """
    hostname = subprocess.check_output("hostname")
    hostname=hostname.strip("\n")
    hostname = hostname.strip()
    return hostname
def call_method(command):
    """
    This function runs the shell commands
    through subprocess with Shell as False
    Param: command to be executed
    return: output of the command
    """
    output = subprocess.check_output(command)
    return output
def fun1():
    """
    This function will check for snapshots
    1.rootsnap
    2.varsnap
    """
    count=0
    DEVNULL = open(os.devnull, 'wb')
    cmd11 = "lvs | grep rootsnap | awk -F\" \" '{ print $2 }'"
    cmd22 = "lvs | grep varsnap | awk -F\" \" '{ print $2 }'"
    out1 = subprocess.check_output(cmd11, shell=True, stderr=DEVNULL).split('\n')[0].strip()
    out2 = subprocess.check_output(cmd22, shell=True, stderr=DEVNULL).split('\n')[0].strip()
    if len(out1) != 0:
        at.exit_codes(0,"Started removing rootsnap ")
        stmt1 = "lvremove /dev/mapper/{}-rootsnap --y".format(out1).split(' ')
        subprocess.call(stmt1, stderr=DEVNULL)
        count=count+1
    else:
        at.exit_codes(0,"No rootsnap present to be removed")
    if len(out2) != 0:
        at.exit_codes(0,"Started removing varsnap")
        stmt2 = "lvremove /dev/mapper/{}-varsnap --y".format(out2).split(' ')
        subprocess.call(stmt2, stderr=DEVNULL)
        count=count+1
    else:
        at.exit_codes(0,"No varsnap present to be removed \n")
    return count
def fun2():
    """
    This function will check for snapshots
    1.rootsnap
    2.varsnap
    3.homesnap
    4.vartempsnap
    5.varlogsnap
    """
    count1=0
    DEVNULL = open(os.devnull, 'wb')
    cmd1 = "lvs | grep rootsnap | awk -F\" \" '{ print $2 }'"
    cmd2 = "lvs | grep varsnap | awk -F\" \" '{ print $2 }'"
    cmd3 = "lvs | grep homesnap | awk -F\" \" '{ print $2 }'"
    cmd4 = "lvs | grep vartmpsnap | awk -F\" \" '{ print $2 }'"
    cmd5 = "lvs | grep varlogsnap | awk -F\" \" '{ print $2 }'"
    out1 = subprocess.check_output(cmd1, shell=True, stderr=DEVNULL).split('\n')[0].strip()
    out2 = subprocess.check_output(cmd2, shell=True, stderr=DEVNULL).split('\n')[0].strip()
    out3 = subprocess.check_output(cmd3, shell=True, stderr=DEVNULL).split('\n')[0].strip()
    out4 = subprocess.check_output(cmd4, shell=True, stderr=DEVNULL).split('\n')[0].strip()
    out5 = subprocess.check_output(cmd5, shell=True, stderr=DEVNULL).split('\n')[0].strip()
    if len(out1) != 0:
        at.exit_codes(0,"Started removing rootsnap")
        stmt1 = "lvremove /dev/mapper/{}-rootsnap --y".format(out1).split(' ')
        subprocess.call(stmt1, stderr=DEVNULL)
        count1=count1+1
    else:
        at.exit_codes(0,"No rootsnap present to be removed")
    if len(out2) != 0:
        at.exit_codes(0,"Started removing varsnap")
        stmt2 = "lvremove /dev/mapper/{}-varsnap --y".format(out2).split(' ')
        subprocess.call(stmt2, stderr=DEVNULL)
        count1 = count1 + 1
    else:
        at.exit_codes(0,"No varsnap present to be removed")
    if len(out3) != 0:
        at.exit_codes(0,"Started removed homesnap")
        stmt3 = "lvremove /dev/mapper/{}-homesnap --y".format(out3).split(' ')
        subprocess.call(stmt3, stderr=DEVNULL)
        count1 = count1 + 1
    else:
        at.exit_codes(0,"No homesnap present to be removed")
    if len(out4) != 0:
        at.exit_codes(0,"Started removing vartmpsnap")
        stmt4 = "lvremove /dev/mapper/{}-vartmpsnap --y".format(out4).split(' ')
        subprocess.call(stmt4, stderr=DEVNULL)
        count1 = count1 + 1
    else:
        at.exit_codes(0,"No vartmpsnap present to be removed")
    if len(out5) != 0:
        at.exit_codes(0,"Started removing varlogsnap")
        stmt5 = "lvremove /dev/mapper/{}-varlogsnap --y".format(out5).split(' ')
        subprocess.call(stmt5, stderr=DEVNULL)
        count1 = count1 + 1
    else:
        at.exit_codes(0,"No varlogsnap present to be removed \n")
    return count1

def exit_gracefully(signum, frame):
    """
    restore the original signal handler as
    otherwise evil things will happen
    in raw_input when CTRL+C is pressed,
    and our signal handler is not re-entrant
    Param: None
    return: None
    """
    at.exit_codes(2,"ctr+c not allowed at this moment")
def check_uid():
    """
    This function checks whether root is
    executing the script or not
    param: None
    return: None
    """
    if os.getuid() != 0:
        at.exit_codes(1,"Only root can execute the script.")
        sys.exit(1)
def mws_pre_check():
    """
    mws pre check for health state of mws
    1.Healthy count
    2.Warning count
    3.Unhealty count
    """
    loc_log("Starting MWS Health check")
    mws_check2()
    if os.path.exists('{}/opt/ericsson/mwshealthcheck/bin/'.format(file1)):
        try:
            os.system("python {}/opt/ericsson/mwshealthcheck/bin/mws_health_check.py".format(file1))
        except Exception:
            at.exit_codes(1,"MWS health check unable to perform. Check and rerun the script")
            loc_log("[ERROR]: MWS health check unable to perform. Check and rerun the script")
            log_fun1()
            sys.exit(1)
        mws_check5()
        os.system(remo.format(file1))
        loc_log("Successfully completed MWS Health check")
    else:
        at.exit_codes(1,"Unable to find the mws_health check script")
        loc_log("[ERROR]: Unable to find the mws_health check script")
        log_fun1()
        sys.exit(1)
def mws_check5():
    """
    mws precheck continuation
    if unhealthy in data script will be aborted till issue fixed and make mws healthy
    """
    if os.path.exists('/var/tmp/mws_health_check_failure_summary'):
        with open('/var/tmp/mws_health_check_failure_summary', 'r') as f:
            out = f.readlines()
            for i in range(0, len(out)):
                if "UNHEALTHY" in out[i]:
                    at.exit_codes(1,"MWS Health Check Failed. Please fix the reported issues and re run the script")
                    loc_log("[ERROR]: MWS Health Check Failed. Please fix the reported issues and re run the script")
                    log_fun1()
                    sys.exit(1)
            mws_check4(out)
    else:
        at.exit_codes(1,"Unable to identify the mws health check summary file")
        loc_log("[ERROR]: Unable to identify the mws health check summary file")
        log_fun1()
        sys.exit(1)
def mws_check4(out):
    """
    mws pre check continuation
    user conformation will be taken if any Warnings in mws health check
    """
    a = 0
    for i in range(0, len(out)):
        if "WARNING" in out[i]:
            a = 1
    while a == 1:
        b = raw_input("Do you want to proceed for MWS upgrade with the warnings displayed:<Y/N>: ")
        if b == 'Y':
            at.exit_codes(0,'Proceeding further with Warnings\n')
            loc_log("[WARNING]: Proceeding further with Warnings")
            a = 2
        elif b == 'N':
            at.exit_codes(1,"MWS Health Check Failed. Please fix the reported issues and re run the script")
            loc_log("[ERROR]: MWS Health Check Failed. Please fix the reported issues and re run the script")
            log_fun1()
            sys.exit(1)
        else:
            at.exit_codes(2,"Invalid input entered. Choose input among <yes/no>")
            a = 1
def mws_check2():
    """
    mws pre check continuation
    this function will check for the mws heath rpm location
    and script running location
    """
    k=sys.argv[0]
    if ('/omtools' in k) or ('omtools' in k):
        at.exit_codes(1, "Script is running from invalid path. Please run from valid location")
        loc_log("[ERROR]: Script is running from invalid path. Please run from valid location")
        log_fun1()
        sys.exit(1)
    else:
        j=subprocess.check_output('pwd')
        b = os.path.dirname(j)
        file2=b+'/mwshealthcheck'
    if os.path.exists(file2):
        mws_check3(file2)
    else:
        at.exit_codes(1,"Unable to find MWS Health check package")
        loc_log("[ERROR]: Unable to find MWS Health check package")
        log_fun1()
        sys.exit(1)
def mws_check3(file2):
    '''
    this function is the continuation of mws_check2 function.
    this function will perform mws health check rpm extraction to perofrom mws health check
    '''
    cmd = 'ls {}'.format(file2)
    cmd = cmd.split(" ")
    out = subprocess.check_output(cmd)
    out1 = out.split()
    for i in range(0, len(out1)):
        if "ERICmwshealthcheck" in out1[i]:
            pkg = out1[i]
            if not os.path.exists(file1):
                os.mkdir(file1)
            os.system("cp {}/{} {}".format(file2, pkg, file1))
            try:
                os.system('rpm2cpio {}/{} | (cd {}; cpio -idmv) >/dev/null 2>&1'.format(file1, pkg, file1))
            except Exception:
                at.exit_codes(1, "Unable to perform mws health check RPM extraction")
                loc_log("[ERROR]: Unable to perform mws health check RPM extraction")
                log_fun1()
                sys.exit(1)
def remove_snap():
    """
    This function checks and remove any snapshots,
    it will work for Gen8,Gen9,Gen10 and Gen10 plus servers
    Param: None
    return: None
    """
    try:
        at.print_status("Started Removing Snapshot")
        loc_log("Started Removing Snapshot")
	cm = 'dmidecode -t system'.split(' ')
        cm2 = subprocess.check_output(cm)
        if "Gen10 Plus" in cm2:
            count = fun2()
        elif "Gen8" in cm2 or "Gen9" in cm2 or "Gen10" in cm2:
            count=fun1()
        else:
            count=fun2()
        if count != 0:
            at.print_status("Successfully Removed Snapshot")
            loc_log("Successfully Removed Snapshot")
    except Exception:
        re_run_om_media()
        at.except_log("Unable to remove snapshot")
def paramiko_check():
    '''
    this function will install paramiko package if not present
    '''
    try:
        b = os.system('rpm -qa | grep paramiko >/dev/null 2>&1')
        if b!=0:
            os.system('yum install -y python-paramiko >/dev/null 2>&1')
    except Exception:
        at.exit_codes(1, "Paramiko Module not found and Unable to install")
        loc_log("[ERROR]: Paramiko Module not found")
        log_fun1()
        sys.exit(1)
def mws_status_file():
    """
    This function will update the mws_status file
    will read the data from temporary file and append to mws_status file
    """
    if os.path.exists(curr_media_loc):
        os.remove(curr_media_loc)
    cmd='touch {}'.format(curr_media_loc)
    cmd = cmd.split(' ')
    subprocess.check_output(cmd)
    with open(temp_om_detail,'r') as f:
        var=f.readlines()
    with open(temp_patch_detail,'r') as f:
        var1=f.readlines()
    with open(curr_media_loc,'a') as f:
        f.writelines(var)
        f.writelines(var1)
def patch_check(rel_no):
    """
    patch media version pre check function
    this function will check patch media status in status file
    :return:
    """
    d2=''
    if not os.path.exists(curr_media_loc):
        return 1
    if os.path.exists(curr_media_loc):
        with open(curr_media_loc,"r") as f:
            data=f.readlines()
        for i in range(0,len(data)):
            if 'MWS_PATCH_UPDATE_MEDIA_STATUS' in data[i]:
                d1=data[i].split('-')
                d1=d1[1].strip()
                d1=d1.strip("\n")
                d1=d1.split()
                d2=d1[1].split('=')
                d2=d2[1].strip()
    b,c='',''
    for i in d2:
        if i.isdigit() == True:
            b = b +i
    for j in rel_no:
        if j.isdigit() == True:
            c=c+j
    c1='/var/tmp/temp_mount/'
    unmt="umount -l {} >/dev/null 2>&1"
    if (int(c)) < (int(b)):
        at.exit_codes(1,"Provided Patch bundle version is lower than currently Installed version.")
        loc_log("[ERROR]: Provided Patch bundle version is lower than currently Installed version.")
        log_fun1()
        os.system(unmt.format(c1))
        os.system(remo.format(c1))
        sys.exit(1)
    if (int(c)) == (int(b)):
        with open('/var/tmp/equals','w') as f:
            """No action required"""
        loc_log("[INFO]: Provided Patch bundle version is same as currently Installed version.")
        os.system(unmt.format(c1))
        os.system(remo.format(c1))
def loc_log(msg):
    """
    this function will update log file
    logs will be updated
    """''
    if not os.path.exists(tem_log_loc):
        cmd='touch /var/tmp/temp_log_upgrade'.split(' ')
        subprocess.check_output(cmd)
    with open(tem_log_loc,'a') as f:
        named_tuple = time.localtime()
        ti = time.strftime(time_for, named_tuple)
        f.writelines(ti+'  '+msg+'\n')
def re_run_om_media():
    """
    re run support provided for om media inputs taking
    skip if not required
    return:none
    params:none
    """
    if path.exists(FILE_PATH):
        with open(FILE_PATH, 'r') as f:
            lines = f.readlines()
            lines[0] = "skip" + "\n"
        with open(FILE_PATH, 'w') as f:
            f.writelines(lines)
def log_fun1():
    """
    logs will be read from temporary file
    log data will be appended to the main log file
    retur:none
    params:none
    """
    at.logging_configs()
    with open(tem_log_loc, 'r') as f:
        val = f.readlines()
        at.log_file_scrn(val, 1)
    at.print_logging_detail()
    error_service()
    sys.exit(1)
def error_service():
    '''
    this function will reset the service after failure
    '''
    os.system('systemctl unmask serial-getty@ttyS0.service >/dev/null 2>&1')
    os.system('systemctl start serial-getty@ttyS0.service >/dev/null 2>&1')
def restart_service():
    '''
    this function will reset the services after reboot.
    start-->to start the service
    status--> to check the status of the service
    '''
    a=os.system('systemctl status autoreboot.service >/dev/null 2>&1')
    if a == 786:
        b=os.system('systemctl start autoreboot.service >/dev/null 2>&1')
        if b==0:
            var = os.system('systemctl status autoreboot.service >/dev/null 2>&1')
            if var == 786:
                at.exit_codes(3,"Issue With autoreboot service..... Going for reboot")
                os.system('reboot')
            else:
                os.system('systemctl mask serial-getty@ttyS0.service >/dev/null 2>&1')
def checkcustomservice(action=1):
    """
    This function creates or remove
    auto service to handle reboot,
    in case of any failure please fix
    the issue manually.
    Param: int
    return: None
    """
    try:
        service = '/etc/systemd/system/serial-getty@ttyS0.service'
        reboot_service = '/etc/systemd/system/autoreboot.service'
        if action == 2:
            os.system('systemctl disable autoreboot')
            if path.exists(reboot_service):
                os.remove(reboot_service)
            os.system("systemctl unmask serial-getty@ttyS0.service")
            os.system("systemctl daemon-reload")
            sys.stdout.write("Removed the services")
            return
        if path.exists(reboot_service):
            os.remove(reboot_service)
        if not path.exists(reboot_service):
            if os.path.exists(FILE_PATH):
                fout = open(FILE_PATH, "r")
                out = fout.readlines()
                fout.close()
                va2 = out[0].split('\n')[0].strip()
                if va2 == "skip":
                    at.exit_codes(1, 'OM Media cached path not found')
                    sys.exit(1)
                else:
                    o_m_media = out[0].split('\n')[0].strip()
            print("Creating the required services")
            fi = open(TEMP_PATH, 'w')
            fi.write("#!/bin/bash\nEXEC_SHELL_CMD=\"exec /bin/bash -o emacs\"\necho \"From Custom Service File\"\n")
            fi.write("echo \"From Custom Service File\"\npkill sulogin > /dev/null 2>&1\n")
            fi.write("python {}/omtools/mws_upgrade.py > /dev/ttyS0".format(o_m_media))
            fi.close()
            os.system("chmod +755 {}".format(TEMP_PATH))
            cmd1 = "cat /etc/default/grub | sed -i 's/GRUB_TERMINAL_OUTPUT="
            cmd2 = "\"console\"/GRUB_TERMINAL=\"console serial\"/' /etc/default/grub"
            cmd3 = "echo \"GRUB_SERIAL_COMMAND=serial --speed 115200 "
            cmd4 = "--unit=0 --word=8 --parity=no --stop=1\" >> /etc/default/grub"
            cd5="cat /etc/default/grub | sed -i 's/rhgb quiet/rhgb quiet console=ttyS0,115200n8/' /etc/default/grub"
            os.system("cp /etc/default/grub /etc/default/grub.org")
            val1="echo \"GRUB_CMDLINE_LINUX_DEFAULT=console=ttyS0 console=ttyS0,115200n8\" >> /etc/default/grub"
            os.system(val1)
            os.system(cmd1+cmd2)
            os.system(cmd3+cmd4)
            os.system("cat /etc/default/grub | sed -i 's/crashkernel=128M/crashkernel=180M/' /etc/default/grub")
            os.system(cd5)
            DEVNULL = open(os.devnull, 'wb')
            subprocess.call("grub2-mkconfig -o /boot/grub2/grub.cfg".split(' '), stderr=DEVNULL)
            fin = open(reboot_service, 'w')
            fin.write("[Unit]\nDescription=Start of Unit\nAfter=basic.target network.target\n")
            fin.write("Requires=multi-user.target\n\n[Service]\nType=simple\n")
            fin.write("ExecStart=/bin/bash /var/tmp/custom_service.bsh\nTimeoutStartSec=0\n\n[Install]\n")
            fin.write("WantedBy=network.target")
            fin.close()
            os.system("chmod +644 {}".format(reboot_service))
            if path.exists(service):
                os.system("systemctl unmask serial-getty@ttyS0.service")
            os.system("systemctl mask serial-getty@ttyS0.service")
            os.system("systemctl daemon-reload")
            os.system("systemctl enable autoreboot.service")
            print("Created the required services")
    except Exception:
        at.exit_codes(1,"Issue while enabling and disabling custom services")
def pre_check_identity():
    '''
    will check for identity files
    It will check identity file pre om and patch caching
    :return:
    '''
    print('\n')
    at.exit_codes(0,'Starting MWS Precheck\n')
    temp_path=''
    k1 = subprocess.check_output('pwd')
    if "/omtools" in k1:
        temp_path = k1.replace("/omtools", '')
        temp_path=temp_path.strip("\n")
    cmd='ls -la {}'.format(temp_path)
    cmd=cmd.split(' ')
    a=subprocess.check_output(cmd)
    if '.om_linux' not in a:
        at.exit_codes(1,"Unable to find O&M Media Identity file. Please use the correct media")
        loc_log("[ERROR]: Unable to find O&M Media Identity file. Please use the correct media")
        log_fun1()
        sys.exit(1)
    c="/var/tmp/temp_mount"
    if not os.path.exists(c):
        os.mkdir("/var/tmp/temp_mount")
    if os.path.exists(iso_p):
        with open(iso_p,'r') as f:
            var=f.readlines()
    cd=("mount -t iso9660 -o loop {} {} >/dev/null 2>&1".format(var[0],c))
    os.system(cd)
    a='ls {}/RHEL'.format(c).split(' ')
    va1=subprocess.check_output(a)
    va1=va1.split()
    k=[]
    for i in va1:
        if 'RHEL' in i:
            k.append(i)
    for i in k:
        if 'RHEL_' in i:
            '''
            no action required
            '''
            pass
        else:
            patch_path(k1,c,i)
def patch_path(k1,c,i):
    '''
    this function will provide the patch media path to other functions.
    to read the patch media path
    '''
    kick_rpm=''
    val2=i
    c1=c+'/'
    val2=val2.split('-')
    rel_num=val2[1]
    patch_check(rel_num)
    k1=k1.strip("\n")
    os.system("umount -l {} >/dev/null 2>&1".format(c1))
    os.system(remo.format(c1))
    val33='ls {}/eric_kickstart'.format(k1).split(' ')
    val3=subprocess.check_output(val33).split()
    for o in range(0,len(val3)):
        if 'ERICkickstart' in val3[o]:
            kick_rpm=val3[o]
    lv='/var/tmp/temp_kick'
    if not os.path.exists(lv):
        os.system('mkdir {}'.format(lv))
    os.system('cp {}/eric_kickstart/{} {}'.format(k1,kick_rpm,lv))
    os.system('rpm2cpio {}/{} | (cd {}; cpio -idmv) >/dev/null 2>&1'.format(lv,kick_rpm,lv))
    cmd1='ls {}/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT'.format(lv).split(' ')
    out=subprocess.check_output(cmd1)
    if rel_num not in out:
        at.exit_codes(1,'Unable to find Patch media identity file. Please use the correct media')
        loc_log("[ERROR]: Unable to find Patch media identity file.")
        log_fun1()
        sys.exit(1)
    if os.path.exists(lv):
        os.system(remo.format(lv))
    at.exit_codes(0, 'Mws Precheck Successful\n')
    loc_log("Mws Precheck Successful")

def stagelist():
    """
    Checks and returns which stage we are
    currently present at in case of failure
    Args: None
    return: int
    """
    stage = 1
    if os.path.exists(STAGE):
        with open(STAGE, 'r') as f:
            stage = int(f.read())
    return stage

from mws_upgrade import autoupdate
at=autoupdate()
signal.signal(signal.SIGINT, exit_gracefully)

