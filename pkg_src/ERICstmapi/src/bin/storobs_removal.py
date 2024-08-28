#!/usr/bin/python

"""
Currently 'storobs' user doesn't have any scope in ENIQ server.
Hence as per security we are removing unnecessary user from ENIQ server.
Author: ZAHAHIM.
"""
import sys
import subprocess

TEMP1 = "/etc/passwd"
TEMP2 = "/ericsson/storage/etc/ssh_input_file"

string1 = 'storobs'

def userdel():
	"""This function removes the storobs user from ENIQ server."""
        # opening the file and reading it's content
        with open(TEMP1, "r") as f1:
                readfile1 = f1.read()
        with open(TEMP2, "r") as f2:
                readfile2 = f2.read()

        # checking condition for string found or not
        if string1 in readfile1 and string1 not in readfile2:
		# Delete the storobs user
		# from ENIQ if the string is found
		# This scenario runs only for ENIQ Upgrade
                call = subprocess.call("userdel -r {}".format(string1),shell=True)
		if call==0:
                	print("User deleted successfully")

        else:
                print(" No Action required!")
                sys.exit(1)

userdel()
