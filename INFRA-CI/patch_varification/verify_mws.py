#!/usr/bin/python
""" This script to check the server reachable/mws configured or not """
import subprocess
import re
import os
import socket

class Verify_MWS:
    """ This class to verify the mws """
    def __init__(self):
        pass

    def verify_ip(self,ip):
        """This function validate the IP"""
        ipv = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
        
        return bool(ipv) and all(map(lambda n: 0 <= int(n) <= 255, ipv.groups()))
    def ip_input(self):
        """ This function is to ip input """
        while True:
            self.IP_Addr = raw_input("Enter the IP address to check MWS configured or not ")
            if self.verify_ip(self.IP_Addr):
                break 
            elif self.verify_ip(self.IP_Addr) == False:
                self.IP_Addr = socket.gethostbyname(self.IP_Addr)
                break
            else:
                print "You have given wrong input,please verify and provide the valid input"
                 


    def verify_mws(self):
        """ This function to verify the mws """
        v_mws = os.path.exists("/net/"+self.IP_Addr+"/JUMP")
        ping_output = subprocess.check_output("nslookup {}".format(self.IP_Addr), shell=True)
        ping_output1 = subprocess.check_output("echo $?", shell=True)
        if ping_output1:
            print("The Server is Reachable")
        else:
            print("The Server is not Reachable")
        
        if v_mws:
            print("MWS configured")
        else:
            print("MWS not configured")



if __name__ == "__main__":
    vrfy = Verify_MWS()
    vrfy.ip_input()
    vrfy.verify_mws()
