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
# Name      : mws_health_check_summary.py
# Purpose   : The script wil perform mws health check automatically
# ********************************************************************

import os
import re

dir1 = "/var/tmp/mws_health_check_summary"
dir2 = "/var/tmp/mws_health_check_failure_summary"

if not os.path.exists(dir1) or not os.path.exists(dir2):
    print("")

else:
    file1 = open(dir1, 'r')
    data1 = file1.read()
    with open(dir1) as f:
        contents = f.read()
        occurences1 = sum(1 for _ in re.finditer(r"\bHEALTHY\b" , contents))
        occurences2 = data1.count("UNHEALTHY")
    if 'WARNING' in data1:
        occurences3 = 1
    else:
        occurences3 = 0
    print('\n')
    print('*****************************************')
    print('         System Health Status            ')
    print('*****************************************')
    print("Health Check Status :")
    print("\033[92mHEALTHY : \033[00m{}".format(occurences1))
    print("\033[91mUNHEALTHY : \033[00m{}".format(occurences2))
    print("\033[38;5;202mWARNINGS: \033[00m{}".format(occurences3))
    if occurences2 == 0 and occurences3 == 0:
        print("Health Check Summary :")
        print("MWS Server is Healthy ")
        print("Summary file path : {}".format(dir1))
    elif occurences2 != 0 or occurences3 != 0:
        print("Health Check Summary :")
        print("Summary file path: {}".format(dir1))
        os.system('cat {}'.format(dir2))
    print('\n')
    with open('/var/tmp/.report_time' , 'r') as f:
        val = f.read()
    print("Report last taken on {}".format(val))
    print('\n')

