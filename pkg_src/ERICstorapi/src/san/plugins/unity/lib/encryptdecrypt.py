#!/usr/bin/python
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
# Name      : encryptdecrypt.py
# Purpose   : The script provides encryption and decryption mechanism 
#             to protect system sensitive data. This is primarily 
#             introduced to protect the SAN data
# ********************************************************************

import os
import argparse
import subprocess
import sys
import logging
import time
from os import path


class EncryptDecrypt:
    """ This class is to encryption and decryption """
    def __init__(self):
        """ init function to intialize the variable """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument("--encrypt", help="Encrypt the given password")
            parser.add_argument("--decrypt", help="Decrypt the given password",
                                action="store_true", default=False)
            self.args = parser.parse_args()
            if len(sys.argv) == 1:
                parser.print_help()
                sys.exit(0)
        except (Exception, KeyboardInterrupt, EOFError) as e:
            self.create_log()
            logging.error(e)
            print("Error: proper usage: encrypt.py [--encrypt]][--decrypt]")

    def create_log(self):
        timestr = time.strftime("%Y%m%d-%H%M%S")
        self.fname = path.basename(__file__).strip('.py')+ "_"+ timestr + '.log'
        format_str = '%(levelname)s: %(asctime)s: %(message)s'
        os.system("mkdir -p /var/ericsson/log/storage/")
        logging.basicConfig(level=logging.DEBUG, filename="/var/ericsson"
                                                          "/log/storage/%s"\
                                                           %self.fname, format=format_str)

    def Encryption_Decryption(self):
        """ OpenSSL utility is utilized for encrypting and decrypting the input string """

        try:
            r_path = "/ericsson/storage/san/plugins/unity/etc/"
            if self.args.encrypt:
                subprocess.check_output("openssl genrsa -out {}.rsa_key.dat 2048  2>&1 >> /dev/null"
                                        .format(r_path), shell=True)
                subprocess.check_output(" echo '{}' | openssl rsautl -encrypt -inkey "
                                        "{p}.rsa_key.dat -out {p}.ddc.conf"
                                        .format(self.args.encrypt, p=r_path), shell=True)
            if self.args.decrypt:
                dcrypt_data = subprocess.check_output("openssl rsautl -decrypt -inkey "
                                                      "{p}.rsa_key.dat -in "
                                                      "{p}.ddc.conf ".format(p=r_path), shell=True)
                print dcrypt_data.strip()
        except (Exception, KeyboardInterrupt, EOFError) as e:
            self.create_log()
            logging.error(e)
            print "usage: encrypt.py [--encrypt][--decrypt]"


if __name__ == '__main__':
    if os.geteuid() != 0:
        print "Error: required root permission to execute this :"+ os.path.abspath(__file__)
        sys.exit(1)
    encrypt_decrypt = EncryptDecrypt()
    encrypt_decrypt.Encryption_Decryption()
