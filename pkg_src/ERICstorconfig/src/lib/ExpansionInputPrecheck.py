#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This Script will handle inputs for storage expansion and post expansion
and also manage the prechecks.
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
import subprocess,re,sys,os,getpass,optparse,time,logging,signal,paramiko,base64
CONFIG = {'E':["29", 21, 7,33], 'F':["43", 33, 9,47], 'G':["62", 50, 16,71]}
CONFIG_E = {'Co':["24", 21, 1], 'En':["1", 0, 0], 'R1':["27", 21, 4], 'R2':["25", 21, 2]}
CONFIG_F = {'Co':["36", 33, 1], 'En':["1", 0, 0], 'R1':["41", 33, 6], 'R2':["37", 33, 2]}
CONFIG_G = {'Co':["53", 50, 1], 'En':["1", 0, 0], 'R1':["63", 50, 11], 'R2':["56", 50, 4]}
TMP_FILE ,FILE_PATH,LOG_DIRE= '/var/tmp/input_file2.txt','/opt/ericsson/san/etc/','/var/ericsson/log/storage/'
LOG_NAME = os.path.basename(__file__).replace('.py', '_')+time.strftime("%m_%d_%Y-%H_%M_%S")+'.log'
MSG2="issue with the CLI/CMD execution and above are the actual ERROR"
HST_FILE,IP1,CON= '/var/tmp/input_file3.txt',"\nEnter the required inputs again.\n",'/var/tmp/con'
HOST="uemcli -d {} -noHeader /remote/host/hlu -host {} show -filter LUN"
CMD,IP="uemcli -d {} -noHeader /stor/config/dg show -filter","\nIs the above provided input correct <yes/no/quit>: "
CMD1="ID,Drive type,Vendor size,Number of drives,Unconfigured drives"
MSG,RE="Existing Configuration not suitable for Storage Expansion",r'^\s*(?:[0-9]{1,3}\.){3}[0-9]{1,3}\s*$'
STAGE,JOB,PATH1,PATH2='/var/tmp/stg','/var/tmp/job.txt','/opt/emc/uemcli/bin/','/opt/dellemc/uemcli/bin/'
IP2,IP_AD="Entered input is not valid. Enter input among <yes/no/quit>","Invalid IP Address Entered, try again\n"
CMD5,DR="uemcli -d {} -noHeader /stor/config/pool show -filter","ID,Number of drives"

class input_precheck(object):
    """
    This class will handle the inputs required for Storage expansion and post expansion
    and perfore prechecks for expansion.
    """
    def __init__(self):
        """
        Init for variable initialization
        """
        self.logger = logging.getLogger()
        self.logging_configs()
        self.colors={'RED' : '\033[91m', 'END' : '\033[00m','GREEN' : '\033[92m', 'YELLOW' : '\033[93m'}
        self.ip,self.lunconfig_type,self.config_type,self.pool_id,self.pool_name ="","","","",""
        self.host_id1,self.host_id2,self.host_id3,self.host_id4,self.uout="","","","",""
        self.host_name,self.main_lun,self.temp_lun,self.sysmain_lun,self.ext4_lun= [],[],[],[],[]
        self.main_name,self.temp_name,self.required_drives,self.uname,self.password="","","","",""
        self.data,self.eng,self.co,self.r1,self.r2,self.hst,self.hst_id=[],[],[],[],[],[],[]
        self.ext_id,self.p_name,self.p_id,self.usname,self.psword,self.cord_ip=[],[],[],"","",""
        self.code1,self.code2,self.code3,self.a,self.usd_dr,self.err ='','','','','',''
        self.con1, self.con2, self.con3 , self.path, self.usd_dr1 = '', '', '', '', ''
    def logging_configs(self):
        """
        Creates the custom logger for logs
        It creates 2 different log handler
        """
        if not os.path.exists(LOG_DIRE):
            os.makedirs(LOG_DIRE)
        s_handlers,f_handlers = logging.StreamHandler(),logging.FileHandler(LOG_DIRE+LOG_NAME)
        s_handlers.setLevel(logging.ERROR)
        f_handlers.setLevel(logging.WARNING)
        s_formats = logging.Formatter('%(message)s')
        f_formats = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s_handlers.setFormatter(s_formats)
        f_handlers.setFormatter(f_formats)
        self.logger.addHandler(s_handlers)
        self.logger.addHandler(f_handlers)
    def log_file_scrn(self, msg1, log_dec=0):
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
        color,msg = self.colors,"Please find the script execution logs  ---> "
        hash_print = '------------------------------------------------------------------------------'
        self.log_file_scrn(color['YELLOW']+hash_print+color['END'])
        self.log_file_scrn(color['YELLOW']+msg+LOG_DIRE+LOG_NAME+color['END'])
        self.log_file_scrn(color['YELLOW']+hash_print+color['END'])
    def verify_uemcli(self):
        """
        This function verifies whether uemcli is installed or not
        return --> none
        args --> none
        self.path--->uemclipath
        PATH1-->old uemcli path
        PATH2--->new uemcli path
        this function will handle roboust enough to
        check for ols and new uemcli paths
        """
        msg="uemcli is not installed\n Please install and try again"
        try:
            val="find {} -type f -name setlevel.sh".format(PATH2)
            value = val.split(' ')
            file1 = subprocess.check_output(value)
            if file1:
                self.path = PATH2
                self.log_file_scrn("uemcli is installed\n",1)
        except Exception:
            try:
                val = "find {} -type f -name setlevel.sh".format(PATH1)
                value = val.split(' ')
                file2 = subprocess.check_output(value)
                if file2:
                    self.path = PATH1
                    self.log_file_scrn("uemcli is installed\n",1)
                    sys.stdout.flush()
                else:
                    self.log_file_scrn("="*50),self.exit_codes(1, msg)
            except Exception:
                self.log_file_scrn("="*50),self.exit_codes(1, msg)
    def exit_codes(self, code13, msg):
        """
        Script Exit function
        param: code --> Exit code of the script and changing type of the message
               msg --> Actual message to print on the screen
        return: None
        colors -- >to print colors
        """
        colors = self.colors
        if code13 == 1 or code13 == 3:
            self.log_file_scrn(colors['RED']+"[ERROR] "+colors['END']+": "+msg)
            self.print_logging_detail(),sys.exit(code13)
        elif code13 == 2:
            self.log_file_scrn(colors['YELLOW']+"[WARN] "+colors['END']+ ":"+msg)
        elif code13 == 4:
            self.log_file_scrn("["+time.strftime("%m-%d-%Y-%H:%M:%S")+"] "
                               + colors['GREEN'] + "[INFO] " + colors['END'] + ": " + msg)
        else:
            self.log_file_scrn(colors['GREEN']+"[INFO] "+colors['END']+": "+msg)
    def fn2(self):
        """function calls"""
        self.input_ip(1),self.input_f(0,1),self.fn(),self.lun_user()
    def exception_stmnts(self):
        """ function for exception statements """
        self.log_file_scrn("-"*75),self.log_file_scrn(self.err),self.log_file_scrn("-"*75),self.exit_codes(1,MSG2)
    def lu_ck(self):
        """
        Checking for Host wise LUNs
        """
        x=len(self.data)
        a1=(x == int(CONFIG_E['Co'][0])) or (x == int(CONFIG_F['Co'][0]))
        b=(x == int(CONFIG_E['R1'][0])) or (x == int(CONFIG_F['R1'][0]))
        c=(x == int(CONFIG_E['R2'][0])) or (x == int(CONFIG_F['R2'][0]))
        if (a1 or (x== int(CONFIG_G['Co'][0]))) and (self.main_lun[0] in self.data):
            self.co.append(self.hst[self.a])
            self.co.append(self.hst_id[self.a])
        elif (b or (x== int(CONFIG_G['R1'][0]))) and (self.main_lun[0] in self.data):
            self.r1.append(self.hst[self.a])
            self.r1.append(self.hst_id[self.a])
        elif (c or (x== int(CONFIG_G['R2'][0]))) and (self.main_lun[0] in self.data):
            self.r2.append(self.hst[self.a])
            self.r2.append(self.hst_id[self.a])
        self.chek_lns()
    def chek_lns(self):
        """
        Luns check
        """
        if len(self.data) == 1:
            if self.data[0] in self.ext4_lun:
                self.eng.append(self.hst[self.a])
                self.eng.append(self.hst_id[self.a])
            elif len(self.eng)>2:
                self.exit_codes(1,"The Existing Configuration is not standard Configuration, Check and try again.")
    def input_ip(self, num1):
        """
        Function to check the server reachability
        function will validate server ip provided by user
        Args: num1 -> int
        return: None
        """
        while True:
            self.ip = raw_input("Enter the UnityXT IP Address: ")
            if not re.search(RE, self.ip):
                self.exit_codes(2, IP_AD)
            else:
                break
        try:
            code1 = subprocess.call(["ping", self.ip, "-c", "2"], stdout=subprocess.PIPE)
            if code1==True:
                sys.stdout.write("Server unreachable\nTry again\n")
                sys.stdout.flush()
                if num1 == 3:
                    self.log_file_scrn("="*50),self.exit_codes(1, "\nServer Unreachable\nExiting the script")
                self.input_ip(num1+1)
        except Exception as self.err:
            self.exception_stmnts()
    def input_f(self, flag=0, num1=1):
        """
        This function takes the required input from the user
        uname --> user name
        password --> password from user
        this function will save user to system
        Args: num -> int
        return: None
        """
        if flag == 0:
            try:
                cmd="uemcli -d {} -noHeader /sys/general show -filter".format(self.ip).split(' ')
                cmd.append("System name")
                subprocess.check_output(cmd)
            except subprocess.CalledProcessError:
                flag=flag+1
                self.input_f(flag,1)
        else:
            self.uname = raw_input("Enter Username: ")
            self.password = getpass.getpass("Enter Password: ")
            try:
                cmd4="uemcli -d {} -u {} -p {} -noHeader /sys/general show -filter"
                cmd2=cmd4.format(self.ip, self.uname, self.password).split(' ')
                cmd2.append("System name")
                cm="{}setlevel.sh l".format(self.path)
                cmd5=cm.split(' ')
                subprocess.call(cmd5, stdout=subprocess.PIPE)
                subprocess.check_output(cmd2)
                cmd = "uemcli -d {} -u {} -p {} -saveUser".format(self.ip, self.uname, self.password).split(' ')
                subprocess.call(cmd, stdout=subprocess.PIPE)
            except subprocess.CalledProcessError:
                self.exit_codes(2, "Username or Password incorrect. Please try again...\n\n")
                if num1 == 4:
                    self.exit_codes(1, "Exceeded attempts to retry!\nExiting...")
                self.input_f(1,num1+1)
        with open(TMP_FILE, 'w') as f:
            f.write(str(self.ip))
            f.write("\n")
    def fn(self):
        """
        This function will call are required function to take inputs from user
        1.Unity Check
        2.Pool check
        3.Lun check
        4.disk space check
        """
        self.unity_check()
        self.pool_check(),self.lun_check(),self.lun_config(),self.check_diskspace()
    def unity_check(self):
        """
        This function will allow script to execute only on Unity XT server
        Model -- > Unity Model
        """
        try:
            cmd1="uemcli -d {} -noHeader /sys/general show -filter Model".format(self.ip).split(' ')
            unity_id1= subprocess.check_output(cmd1)
            unity_id1 =unity_id1.split(":")
            unity_id1.pop(0)
            new_unity_id ={k.split('=')[0].strip() :k.split('=')[1].strip() for k in unity_id1}
            if new_unity_id["Model"] != 'Unity 480F':
                os.remove(TMP_FILE)
                self.log_file_scrn("="*50)
                self.exit_codes(1, "Requested Configuration can be performed only on Unity XT ")
        except Exception as self.err:
            self.exception_stmnts()
    def pool_check(self):
        """
        This function will check for existing pool id and name
        return -->none
        args --> none
        self.p_name --> available pool names
        self.p_id --> available pool ids
        """
        try:
            self.p_name,self.p_id=[],[]
            cmd1="uemcli -noHeader -d {} /stor/config/pool show -filter Name,ID"
            cmd=cmd1.format(self.ip).split(' ')
            pool= subprocess.check_output(cmd).split()
            for i in range(0,len(pool)):
                if pool[i]=="Name":
                    self.p_name.append(pool[i+2])
                if pool[i]=="ID":
                    self.p_id.append(pool[i+2])
            self.pool_chk()
        except Exception as self.err:
            self.exception_stmnts()
    def pool_chk(self):
        """
        This function will check for existing pool id and name
        return -->none
        args --> none
        pool_name --> existing pool name
        pool_id --> existing pool id
        """
        if len(self.p_id) == 1:
            self.pool_name,self.pool_id=self.p_name[0],self.p_id[0]
        elif len(self.p_id) > 1:
            print("The available pools are:")
            for i in range(0,(len(self.p_id))):
                print(self.p_name[i])
            name=raw_input("Enter the pool name to select the pool: ")
            for i in range(0,len(self.p_id)):
                if str(self.p_name[i]) == str(name):
                    self.pool_name,self.pool_id=self.p_name[i],self.p_id[i]
            if self.pool_name not in self.p_name:
                print("Entered wrong pool name. Try Again."),self.pool_check()
        with open(TMP_FILE, 'a') as f:
            ln=[self.pool_id,"\n",self.pool_name,"\n"]
            f.writelines(ln)
    def disk_validation(self):
        """
        This function will do required drives calculation
        """
        try:
            ud_dr,req_dr = '',''
            cmd14 = CMD5
            cmd24 = cmd14.format(self.ip).split(' ')
            cmd24.append(DR)
            val3 = subprocess.check_output(cmd24).split()
            for i in range(0, len(val3)):
                if str(val3[i]) == str(self.pool_id):
                    ud_dr = val3[i + 5]
            if int(ud_dr) >= int(CONFIG[self.lunconfig_type][0]):
                req_dr = 0
            else:
                req_dr = int(CONFIG[self.lunconfig_type][0]) - int(ud_dr)
            return req_dr,ud_dr
        except Exception as self.err:
            self.exception_stmnts()
    def lun_check(self):
        """
        This function will check existing configuration type by number of LUNs and pool size and drives used
        size --> luns size
        lun --> lun id
        args --> none
        return --> none
        lun types --> mainDb,TempDB,sysmain,ext4
        """
        try:
            cmd1="uemcli -d {} -noHeader /stor/prov/luns/lun show -filter"
            cmd=cmd1.format(self.ip).split(' ')
            cmd.append("ID,Size,Storage pool ID")
            out = subprocess.check_output(cmd).split()
            self.main_lun,self.temp_lun,self.sysmain_lun,self.ext4_lun,self.ext_id,lun,size=[],[],[],[],[],[],[]
            size2=[]
            for i in range(0,len(out)):
                if out[i]==self.pool_id:
                    lun.append(out[i-9])
                    size2.append(out[i-6])
                    size.append(out[i-5])
            for i in range(0,len(lun)):
                if size2[i]=='1319413953536' or size[i] == '(1.2T)':
                    self.main_lun.append(lun[i])
                elif size2[i]=='569083166720' or size[i] == '(530.0G)':
                    self.temp_lun.append(lun[i])
                elif size2[i]=='644245094400' or size[i] == '(600.0G)':
                    self.sysmain_lun.append(lun[i])
                elif size2[i]=='429496729600' or size2[i]=='214748364800' or \
                        (size[i] == '(400.0G)') or (size[i] == '(200.0G)'):
                    self.ext4_lun.append(lun[i])
            if len(self.main_lun)<21:
                self.exit_codes(1,"Pool is not as per Standard config.check and try again")
            self.host_names(),self.lun_chk()
        except Exception as self.err:
            self.exception_stmnts()
    def host_names(self):
        """
        This function will do host selection by displaying available hosts to user
        return -->none
        args -->none
        host_id -->  host ids
        host_name --> host names
        hosts --> coordinator,engine,reader1,reader2
        HST_FILE --> to save host details
        """
        try:
            self.hst,self.hst_id,self.eng,self.co,self.r1,self.r2=[],[],[],[],[],[]
            cmd='uemcli -d {} /remote/host show -filter Name,ID'.format(self.ip).split(' ')
            host = subprocess.check_output(cmd).split()
            for i in range(0,(len(host))):
                if host[i] == 'Name':
                    self.hst.append(host[i+2])
                if host[i] == 'ID':
                    self.hst_id.append(host[i+2])
            if len(self.hst_id) >=4:
                with open(HST_FILE, 'w'):
                    """No actions"""
                    pass
                self.hst_1()
                if len(self.co)==0 or len(self.eng)==0 or len(self.r1)==0 or len(self.r2)==0:
                    self.exit_codes(1,"The Existing Configuration is not standard Configuration, Check and try again.")
                with open(HST_FILE, 'a') as f:
                    l1 = [self.co[0], "\n", self.co[1], "\n", self.eng[0], "\n", self.eng[1], "\n"]
                    l2 = [self.r1[0], "\n", self.r1[1], "\n", self.r2[0], "\n", self.r2[1], "\n"]
                    f.writelines(l1)
                    f.writelines(l2)
            else:
                self.exit_codes(1,"Existing Configuration is not suitable for Expansion")
        except Exception as self.err:
            self.exception_stmnts()
    def hst_1(self):
        """
        host check
        """
        try:
            for self.a in range(0,len(self.hst_id)):
                cmd=HOST.format(self.ip,self.hst_id[self.a]).split(' ')
                out4=subprocess.check_output(cmd).split()
                self.data=[]
                for i in range(0,len(out4)):
                    if out4[i]=="LUN":
                        self.data.append(out4[i+2])
                self.lu_ck()
        except Exception as self.err:
            self.exception_stmnts()
    def lun_chk(self):
        """
        This function will check the type of configuration existing on deployment
        return --> none
        args --> none
        main_lun --> maindb luns
        temp_lun -->tempdb luns
        sysmain_lun --> sysmain luns
        ext4_lun --> ext4 luns
        u --> used drives
        """
        try:
            cmd1=CMD5
            cmd=cmd1.format(self.ip).split(' ')
            cmd.append(DR)
            out = subprocess.check_output(cmd).split()
            for i in range(0,len(out)):
                if str(out[i]) == str(self.pool_id):
                    self.usd_dr=out[i+5]
            b,c=int(CONFIG['F'][0]),int(CONFIG['G'][0])
            if not ((int(self.usd_dr)==int(CONFIG['E'][0])) or (int(self.usd_dr)==b) or (int(self.usd_dr)==c)):
                self.exit_codes(1,MSG)
            if (len(self.sysmain_lun)==1) and (len(self.ext4_lun)==4):
                self.lun_ck()
            else:
                self.exit_codes(1,MSG)
            with open(TMP_FILE, 'a') as f:
                f.write(str(self.config_type))
                f.write("\n")
        except Exception as self.err:
            self.exception_stmnts()
    def lun_ck(self):
        """this function will do lun check"""
        self.con1,self.con2,self.con3='','',''
        total=len(self.main_lun)+len(self.temp_lun)+len(self.sysmain_lun)+len(self.ext4_lun)
        self.con1=(len(self.temp_lun)==int(CONFIG['E'][2])) and (total==int(CONFIG['E'][3]))
        self.con2=(len(self.temp_lun)==int(CONFIG['F'][2])) and (total==int(CONFIG['F'][3]))
        self.con3=(len(self.temp_lun)==int(CONFIG['G'][2])) and (total==int(CONFIG['G'][3]))
        self.lun_ck2()
    def lun_ck2(self):
        """this function will do lun check"""
        if (len(self.main_lun)==int(CONFIG['E'][1])) and self.con1:
            self.config_type = "E"
            print("\nExisting Configuration Type is E\nSupported Configurations to Expand are F and G")
        elif (len(self.main_lun)==int(CONFIG['F'][1])) and self.con2:
            self.config_type = "F"
            print("\nExisting Configuration Type is F\nSupported Configuration to Expand is G")
        elif (len(self.main_lun)==int(CONFIG['G'][1])) and self.con3:
            self.config_type = "G"
            print("\nExisting Configuration Type is G")
            self.exit_codes(1,"Existing Configuration is already higher Configuration")
        else:
            self.exit_codes(1,"Existing Configuration not suitable for Expansion")
            self.exit_codes(1,MSG)
    def lun_config(self):
        """
        This function will take configuration type to expand LUNs from user
        lunconfig_types -->  target configuration type
        conf_types --> supported config types
        """
        msg = "Entered Configuration Type is incorrect!!!. Enter Configuration Type again..."
        if self.config_type == 'E':
            self.lunconfig_type = raw_input("Enter the Configuration type to Expand(F/G): ")
            conf_types = ['F','G']
            if self.lunconfig_type in conf_types:
                with open(TMP_FILE, 'a') as f:
                    f.write(str(self.lunconfig_type))
                    f.write("\n")
                with open("/var/tmp/target_conf.txt",'w') as f1:
                    f1.write(str(self.lunconfig_type))
            else:
                self.log_file_scrn("="*50),self.exit_codes(2,msg),self.lun_config()
        if self.config_type == 'F':
            self.lunconfig_type = raw_input("Enter the Configuration type to Expand(G): ")
            conf_types=['G']
            if self.lunconfig_type in conf_types:
                with open(TMP_FILE, 'a') as f:
                    f.write(str(self.lunconfig_type))
                    f.write("\n")
                with open("/var/tmp/target_conf.txt",'w') as f1:
                    f1.write(str(self.lunconfig_type))
            else:
                self.log_file_scrn("="*50),self.exit_codes(2,msg),self.lun_config()
    def check_diskspace(self):
        """This function will check for the disk space available for pool expansion
        return none
        args -->none
        check for required disks for expansion and compares with available unconfigured drives
        validates disk type
        exits the script if numbr of required drives are not sufficient"""
        try:
            cmd='uemcli -d {} -noHeader /stor/config/profile show'.format(self.ip).split(' ')
            chk_pro=subprocess.check_output(cmd)
            chk_pro=[k for k in chk_pro.split('\n')if len(k)>4]
            po,co,x,bo=[],[],[],[]
            for i in chk_pro:
                k=i.translate(None, ' \n\t\r')
                po.append(k)
            sas_positon=po.index("Description=SASFlashRAID5(12+1)")
            for i in range(sas_positon-2,sas_positon+5):
                z=po[i]
                co.append(z)
            for i in range(0,1):
                su=co[i]
                su=su[2:]
                co[0]=su
            new_chk_pro={k.split('=')[0].strip() :k.split('=')[1].strip() for k in co}
            drive_type_pro = (new_chk_pro['Drivetype'])
            cmd=CMD.format(self.ip).split(' ')
            cmd.append(CMD1)
            chk_disksp=subprocess.check_output(cmd).split('\n')
            chk_disksp.pop()
            chk_disksp = [k+'\n' for k in chk_disksp]
            for i in chk_disksp:
                m=i.translate(None,' \n\t\r')
                x.append(m)
            for i in range(0,len(x)-1):
                bo.append(x[i])
            for i in range(0,1):
                x1=bo[i]
                x1=x1[2:]
                bo[0]=x1
            chk_disksp={k.split("=")[0].strip() : k.split("=")[1].strip() for k in bo}
            dri_type='SASFlash'
            if dri_type != drive_type_pro:
                self.exit_codes(1,'Invalid Drive type')
            self.log_file_scrn('SAS-Flash Validation Done', 1)
            n=int(chk_disksp['Unconfigureddrives'])
            self.required_drives=(int(CONFIG[self.lunconfig_type][0]))-(int(CONFIG[self.config_type][0]))
            if n < self.required_drives:
                self.exit_codes(1, "Disk Space not sufficient for Storage Expansion.")
            with open(TMP_FILE, 'a') as f:
                f.write(str(self.required_drives))
                f.write("\n")
        except (OSError, subprocess.CalledProcessError) as self.err:
            self.exception_stmnts()
    def exception_stmnts(self):
        """ function for exception statements """
        self.log_file_scrn("-"*75),self.log_file_scrn(self.err),self.log_file_scrn("-"*75),self.exit_codes(1,MSG2)
    def lun_user(self):
        """
        This function will collect lun name from user
        HST_FILE-->host files
        """
        self.main_name=raw_input("Enter Prefix of MainDB name<ex-->MainDB>: ")
        self.temp_name=raw_input("Enter Prefix of TempDB name<ex-->TempDB>: ")
        with open(HST_FILE, 'r') as f:
            out=f.readlines()
            for i in range(1,len(out),2):
                with open(TMP_FILE, 'a') as f:
                    line=out[i].split('\n')[0].strip()
                    f.write(str(line))
                    f.write("\n")
        with open(TMP_FILE, 'a') as f:
            l=[self.main_name,"\n",self.temp_name,"\n"]
            f.writelines(l)
def main():
    '''
    this is the main function
    '''
    obj =input_precheck()
    obj.verify_uemcli()
    obj.fn2()

if __name__ == "__main__":
    main()

