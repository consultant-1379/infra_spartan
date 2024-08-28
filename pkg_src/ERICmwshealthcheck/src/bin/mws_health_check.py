#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for MWS Health Check automation
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
# Name      : mws_health_check.py
# Purpose   : The script wil perform mws health check automatically
# ********************************************************************


import subprocess
import os
import sys
import time
import re
import datetime

a = subprocess.check_output("hostname").split()
b = 'mws_health_report-'+ str(a[0])
if os.path.exists('/var/tmp/'):
    path = os.path.join('/var/tmp/', b)
    if not os.path.exists(path):
        os.mkdir(path)
else:
    print("/var/tmp directory does not exist!")
    sys.exit(1)

"""
Global variables used within the script
"""
DATA = '/var/tmp/mwshealth'
DIR = '/var/tmp/mws_health_check_failure_summary'
DIR1 = '/var/tmp/mws_health_check_summary'
TEMP = '/var/tmp/mws_health'

LOG_DIR = path + '/'
cmd = 'touch {}'


def exit_codes(code, msg):
    """
    Script Exit funtion
    param: code --> Exit code of the script and
    changing type of the message
           msg --> Actual message to print on the screen
    return: None
    """

    colors = {'RED': '\033[91m', 'END': '\033[00m', 'GREEN': '\033[92m', 'YELLOW': '\033[93m'}
    if code == 1:
        print(colors['RED']+"[ERROR] "+colors['END']+": "+msg)
    elif code == 2:
        print(colors['YELLOW']+"[WARN] "+colors['END']+":"+msg)
    elif code == 3:
        print(colors['YELLOW']+ msg +colors['END'])
    elif code == 4:
        print(colors['GREEN']+"[INFO] "+colors['END']+":" +msg +colors['END'])

def wrapper_test():
    """
    This is the wrapper function
    It will run all the script which
    are kept in /opt/ericsson
    /mwshealthcheck/lib folder.
    """
    val2 = ''
    a = sys.argv[0]
    if a == 'bin/mws_health_check.py':
        val2 = ''
    elif a == 'mws_health_check.py':
        val2 = '../'
    else:
        val2 = os.path.dirname(os.path.dirname(a))
        val2 = val2 + '/'
    out1 = 'python {}lib/mws_verify_hw.py >/dev/null 2>&1'.format(val2)
    out2 = 'python {}lib/mws_verify_boot_modes.py >/dev/null 2>&1'.format(val2)
    out3 = 'python {}lib/mws_check_grub_cfg.py >/dev/null 2>&1'.format(val2)
    out4 = 'python {}lib/mws_check_kernel_index.py >/dev/null 2>&1'.format(val2)
    out  =  'python {}lib/mws_check_services.py >/dev/null 2>&1'.format(val2)
    out6 = 'python {}lib/mws_nfs_details.py >/dev/null 2>&1'.format(val2)
    out7 = 'python {}lib/mws_verify_volumes.py >/dev/null 2>&1'.format(val2)
    out8 = 'python {}lib/mws_verify_networking.py >/dev/null 2>&1'.format(val2)
    out9 = 'python {}lib/mws_check_time_sync.py >/dev/null 2>&1'.format(val2)
    out10 = 'python {}lib/mws_verify_firewall.py >/dev/null 2>&1'.format(val2)
    out11 = 'python {}lib/mws_package_repo.py >/dev/null 2>&1'.format(val2)
    out13 = 'python {}lib/mws_disk_usage.py >/dev/null 2>&1'.format(val2)
    out14 = 'python {}lib/mws_inode_usage.py >/dev/null 2>&1'.format(val2)
    out15 = 'python {}lib/mws_swap_details.py >/dev/null 2>&1'.format(val2)
    out16 = 'python {}lib/mws_processor_utilization.py >/dev/null 2>&1'.format(val2)
    out17 = 'python {}lib/mws_load_average.py >/dev/null 2>&1'.format(val2)
    out18 = 'python {}lib/mws_reboot_status.py >/dev/null 2>&1'.format(val2)
    out19 = 'python {}lib/mws_shutdown_status.py >/dev/null 2>&1'.format(val2)
    out20 = 'python {}lib/mws_memory_utilization.py >/dev/null 2>&1'.format(val2)
    out21 = 'python {}lib/mws_cpu_utilization.py >/dev/null 2>&1'.format(val2)
    out22 = 'python {}lib/mws_verify_kernel.py >/dev/null 2>&1'.format(val2)
    os.system(out1)
    os.system(out2)
    os.system(out3)
    os.system(out4)
    os.system(out6)
    os.system(out7)
    os.system(out8)
    os.system(out9)
    os.system(out10)
    os.system(out11)
    os.system(out13)
    os.system(out14)
    os.system(out15)
    os.system(out16)
    os.system(out17)
    os.system(out18)
    os.system(out19)
    os.system(out20)
    os.system(out21)
    os.system(out22)
    os.system(out)

def log_deletion():
    """
    This function will
    help in deletetion of
    log files that are older
    than 15 days.
    """
    dir_path = LOG_DIR
    now = time.time()
    for f in os.listdir(dir_path):
        f = os.path.join(dir_path, f)
        if os.stat(f).st_mtime < now - 15 * 86400 and os.path.isfile(f):
            os.remove(os.path.join(dir_path, f))

def formatted_logs_us():
    """
    This function will
    format the logs in
    formatted way.
    """
    headers = [ 'PRECHECK ', 'STATUS ', 'REMARKS ', 'LOGS ', '\n']
    if not os.path.exists(DATA):
        os.system(cmd.format(DATA))
    if not os.path.exists(DIR):
        os.system(cmd.format(DIR))
    with open(DATA, 'r+') as da:
        datatable = [line.split('  ') for line in da.read().splitlines()]
        widths = [max(len(value) for value in col) for col in zip(*(datatable + [headers]))]
        # Print heading followed by the data in datatable.
        # (Uses '<' to right-justify the data in some columns.)
        format_spec = '{:<{widths[0]}}       {:<{widths[1]}}   {:<{widths[2]}}        {:<{widths[3]}} '
        with open(DIR,'w') as f:
            out = format_spec.format(*headers, widths=widths) + '\n'
            f.writelines(out)
        for fields in datatable:
            out2 = format_spec.format(*fields, widths=widths) + '\n'
            with open(DIR , 'a') as f:
                f.writelines(out2)
        with open(DIR ,'r') as d:
            var = d.readlines()
            var = str(var)
            if 'UNHEALTHY' not in var and 'WARNING' not in var:
                with open(DIR, 'w') as w:
                    w.writelines(' ')

def formatted_logs_hs():
    """
    This function will
    format the logs in
    formatted way.
    """
    headers = ['PRECHECK ', 'STATUS ', 'REMARKS ', 'LOGS ', '\n']
    if not os.path.exists(TEMP):
        os.system(cmd.format(TEMP))
    if not os.path.exists(DIR1):
        os.system(cmd.format(DIR1))
    with open(TEMP, 'r+') as ta:
        datatables = [line.split('  ') for line in ta.read().splitlines()]
        widths = [max(len(value) for value in col) for col in zip(*(datatables + [headers]))]
        # Print heading followed by the data in datatable.
        # (Uses '<' to right-justify the data in some columns.)
        format_specs = '{:<{widths[0]}}       {:<{widths[1]}}    {:<{widths[2]}}          {:<{widths[3]}} '
        with open(DIR1, 'w') as f1:
            out1 = format_specs.format(*headers, widths=widths) + '\n'
            f1.writelines(out1)
        for fields in datatables:
            out3 = format_specs.format(*fields, widths=widths) + '\n'
            with open(DIR1, 'a') as f1:
                f1.writelines(out3)

def common_file():
    """
    This function
    stores the data for
    healthy and unhealthy
    services.
    """
    if os.path.exists(DIR):
        with open(DIR, 'r') as cf:
            val = cf.readlines()
            del val[0]
    if os.path.exists(DIR1):
        with open(DIR1,'a') as cf1:
            cf1.writelines(val)
    if not os.path.exists(DIR):
        print("Summary file not found")
    if not os.path.exists(DIR1):
        print("Summary file not found")

def print_summary_details():
    """
    This function will
    print summary details
    on console.
    """
    cmd1 = DIR1
    cmd2 = DIR
    out1 = open(cmd1, 'r')
    datas1 = out1.read()

    with open(DIR1) as f:
        contents = f.read()
        occurences1 = sum(1 for _ in re.finditer(r"\bHEALTHY\b" , contents))
    occurences2 = datas1.count("UNHEALTHY")
    if 'WARNING' in datas1:
        occurences3 = 1
    else:
        occurences3 = 0
    print("Health Check Status :")
    print("\033[92mHEALTHY : \033[00m{}".format(occurences1))
    print("\033[91mUNHEALTHY : \033[00m{}".format(occurences2))
    print("\033[38;5;202mWARNINGS : \033[00m{}".format(occurences3))
    print('\n')
    if occurences2 == 0 and occurences3 == 0:
        print("Health Check Summary :")
        print("MWS Server is Healthy")
        print("Summary file path: {}".format(cmd1))
        print('\n')
        exit_codes(4,"------------------Successfully Completed MWS Health Check-------------------")
    elif occurences2 != 0 or occurences3 != 0:
        print("Health Check Summary :")
        print("Summary file path: {}".format(cmd1))
        os.system('cat {}'.format(cmd2))
    print('\n')
    report_time()

def report_time():
    """
    This function will
    fetch last time
    report was taken.
    """
    f = datetime.datetime.now()
    dtp = f.strftime("%d-%m-%Y %H:%M:%S")
    print("Report last taken on :{} \n ".format(dtp))
    a = '/var/tmp/.report_time'
    if not os.path.exists(a):
        os.system("touch {}".format(a))
    with open(a , 'w') as f:
        f.writelines(dtp)

def remove_summary_file():
    """
    This function will
    remove the summary
    file.
    """
    my_file1 = DATA
    my_file2 = DIR
    my_file3 = '/var/tmp/mws_health'
    my_file4 = DIR1
    if os.path.exists(my_file1):
        os.remove(my_file1)
    if os.path.exists(my_file2):
        os.remove(my_file2)
    if os.path.exists(my_file3):
        os.remove(my_file3)
    if os.path.exists(my_file4):
        os.remove(my_file4)

def remove_files():
    """
    This function will
    remove the residue
    files.
    """
    res_path1 = '/opt/ericsson/mwshealthcheck/bin/load.txt'
    res_path2 = '/opt/ericsson/mwshealthcheck/bin/tmp.txt'
    res_path3 = '/root/tmp.txt'
    res_path4 = '/root/load.txt'

    if os.path.exists(res_path1):
        os.remove(res_path1)
    if os.path.exists(res_path2):
        os.remove(res_path2)
    if os.path.exists(res_path3):
        os.remove(res_path3)
    if os.path.exists(res_path4):
        os.remove(res_path4)



def main():
    """
    The main function to wrap all functions
    Param: None
    return: None
    """
    exit_codes(4, "-------------------Starting MWS Health Check--------------------")
    print('\n')
    print("Please wait ...")
    print('\n')
    remove_summary_file()
    wrapper_test()
    formatted_logs_us()
    formatted_logs_hs()
    common_file()
    print_summary_details()
    remove_files()
    log_deletion()

if __name__ == "__main__":
    main()

