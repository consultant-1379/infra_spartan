#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Script for Storage Expansion
pre_checks:
a:unity IP accessibility check
b:uemcli check
c:unity check
d:user name and password validation
e:pool validation
f:host validation
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
HST_FILE,IP1= '/var/tmp/input_file3.txt',"\nEnter the required inputs again.\n"
HOST="uemcli -d {} -noHeader /remote/host/hlu -host {} show -filter LUN"
CMD,IP="uemcli -d {} -noHeader /stor/config/dg show -filter","\nIs the above provided input correct <yes/no/quit>: "
CMD1="ID,Drive type,Vendor size,Number of drives,Unconfigured drives"
MSG,RE="Existing Configuration not suitable for Storage Expansion",r'^\s*(?:[0-9]{1,3}\.){3}[0-9]{1,3}\s*$'
STAGE,JOB,PATH1,PATH2='/var/tmp/stg','/var/tmp/job.txt','/opt/emc/uemcli/bin/','/opt/dellemc/uemcli/bin/'
IP2,IP_AD="Entered input is not valid. Enter input among <yes/no/quit>","Invalid IP Address Entered, try again\n"
CMD5,DR="uemcli -d {} -noHeader /stor/config/pool show -filter","ID,Number of drives"
class storage_config(object):
    """
    this class will do the input validation
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
        self.co,self.r1,self.r2,self.hst,self.hst_id=[],[],[],[],[]
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
        s1_handlers,f1_handlers = logging.StreamHandler(),logging.FileHandler(LOG_DIRE+LOG_NAME)
        s1_handlers.setLevel(logging.ERROR)
        f1_handlers.setLevel(logging.WARNING)
        s_formats = logging.Formatter('%(message)s')
        f_formats = logging.Formatter('%(asctime)s - %(message)s', datefmt='%d-%b-%y-%H:%M:%S')
        s1_handlers.setFormatter(s_formats)
        f1_handlers.setFormatter(f_formats)
        self.logger.addHandler(s1_handlers)
        self.logger.addHandler(f1_handlers)
    def log_file_scrn(self, msg111, log_dec=0):
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
            self.logger.error(msg111)
        else:
            self.logger.warning(msg111)
    def print_logging_detail(self):
        """
        Prints logging details with log file for exit,
        completion and start of the script
        colors --> colors print for logs
        return --> none
        """
        color,msg12 = self.colors,"Please find the script execution logs  ---> "
        hash_printt = '------------------------------------------------------------------------------'
        self.log_file_scrn(color['YELLOW']+hash_printt+color['END'])
        self.log_file_scrn(color['YELLOW']+msg12+LOG_DIRE+LOG_NAME+color['END'])
        self.log_file_scrn(color['YELLOW']+hash_printt+color['END'])
    def exit_codes(self, code13, msg21):
        """
        Script Exit function
        param: code --> Exit code of the script and changing type of the message
               msg21 --> Actual message to print on the screen
        return: None
        colors -- >to print colors
        """
        colors = self.colors
        if code13 == 1:
            self.log_file_scrn(colors['RED']+"[ERROR] "+colors['END']+": "+msg21)
            self.print_logging_detail(),rm_file(),sys.exit(code13)
        elif code13 == 2:
            self.log_file_scrn(colors['YELLOW']+"[WARN] "+colors['END']+ ":"+msg21)
        elif code13 == 3:
            self.log_file_scrn(colors['RED']+"[ERROR] "+colors['END']+": "+msg21)
            self.print_logging_detail(),sys.exit(code13)
        elif code13 == 4:
            self.log_file_scrn("["+time.strftime("%m-%d-%Y-%H:%M:%S")+"] "
                               + colors['GREEN'] + "[INFO] " + colors['END'] + ": " + msg21)
        else:
            self.log_file_scrn(colors['GREEN']+"[INFO] "+colors['END']+": "+msg21)
    def input_ip2(self, num12):
        """
        Function to check the server reachability
        function will validate server ip provided by user
        Args: num1 -> int
        return: None
        """
        while True:
            self.cord_ip = raw_input("Enter the Coordinator IP Address: ")
            if not re.search(RE, self.cord_ip):
                self.exit_codes(2, IP_AD)
            else:
                break
        try:
            code11 = subprocess.call(["ping", self.cord_ip, "-c", "2"], stdout=subprocess.PIPE)
            if code11 == True:
                sys.stdout.write("Coordinator Server unreachable\nTry again\n")
                sys.stdout.flush()
                if num12 == 3:
                    self.log_file_scrn("="*50),self.exit_codes(1,"\nCoordinator Server Unreachable\nExiting the script")
                self.input_ip2(num12+1)
            else:
                with open(TMP_FILE, 'w') as f:
                    f.write(str(self.cord_ip))
                    f.write("\n")
        except subprocess.CalledProcessError as self.err:
            self.exception_stmnts()
    def input_ff(self):
        """
        This function takes the required input from the user
        uname --> user name
        password --> password from user
        this function will save user to system
        Args: num -> int
        return: None
        """
        try:
            self.usname = raw_input("Enter the Coordinator username: ")
            self.psword = getpass.getpass("Enter the Coordinator password: ")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.cord_ip, username=self.usname, password=self.psword)
            client.close()
            with open(TMP_FILE, 'a') as f:
                password = base64.b64encode(self.psword)
                l=[str(self.usname),"\n",password,"\n"]
                f.writelines(l)
        except paramiko.ssh_exception.AuthenticationException:
            print("Entered inputs are wrong. Try again.")
            self.input_ff()
    def unity_ip(self):
        """
        This function will collect the unity ip
        of the server from unity.conf file
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.cord_ip, 22, self.usname, self.psword)
            stdin, stdout, stderr = ssh.exec_command("cat /ericsson/storage/san/plugins/unity/etc/unity.conf")
            out1 = stdout.read().split("\n")
            for i in range(0, len(out1)):
                if 'sp' in out1[i]:
                    data = out1[i].split("=>")
                    unity_ip_is = data[1].strip(",")
                    ip1 = unity_ip_is.strip()
                    self.ip = ip1.strip("'")
                    with open(TMP_FILE,"a") as f:
                        f.write(str(self.ip))
                        f.write("\n")
        except Exception as self.err:
            self.exception_stmnts()

    def pool_ex(self):
        """This function will validate pool expansion required or not"""
        try:
            with open(TMP_FILE, 'r') as f:
                out = f.readlines()
                self.pool_id = out[1].split('\n')[0].strip()
                self.pool_name = out[2].split('\n')[0].strip()
                self.ip = out[0].split('\n')[0].strip()
                self.config_type = out[3].split('\n')[0].strip()
                self.lunconfig_type = out[4].split('\n')[0].strip()
            cmd1 = CMD5
            cmd = cmd1.format(self.ip).split(' ')
            cmd.append(DR)
            out = subprocess.check_output(cmd).split()
            for i in range(0, len(out)):
                if str(out[i]) == str(self.pool_id):
                    self.usd_dr1 = out[i + 5]
            if int(self.usd_dr1)==int(CONFIG[self.lunconfig_type][0]):
                return 1
            else:
                return 0
        except Exception as self.err:
            self.exception_stmnts()
    def stor_expand(self):
        """This function will do file configuration
        File configuration script will be called based on provided inputs
        self.code12 --> to take the status of file script execution
        pool expansion, LUN creation and Addition scripts call"""
        stage=stagelist_w()
        try:
            if not os.path.exists(TMP_FILE):
                print("Input File not found")
                sys.exit(1)
            self.exit_codes(4,"Starting Storage Expansion...")
            cmd="python /opt/ericsson/san/lib/PoolExpansion.py".split(' ')
            cmd1="python /opt/ericsson/san/lib/LunCreation.py".split(' ')
            cmd2="python /opt/ericsson/san/lib/LunAddition.py".split(' ')
            if stage == 1:
                out3=self.pool_ex()
                if out3==1:
                    self.exit_codes(0,"Dynamic Pool Expansion Not required")
                    self.code1=0
                else:
                    self.code1=subprocess.call(cmd)
                if self.code1==0:
                    stage = stage+1
                    with open(STAGE,'w') as f:
                        f.write(str(stage))
                else:
                    sys.exit(1)
            self.stage2_3(stage,cmd1,cmd2)
        except Exception as self.err:
            self.exception_stmnts()
    def stage2_3(self,stage,cmd1,cmd2):
        '''
        this function will call stage 2 and 3
        :return:
        '''
        try:
            if stage == 2:
                self.code2 = subprocess.call(cmd1)
                if self.code2 == 0:
                    stage = stage + 1
                    with open(STAGE, 'w') as f:
                        f.write(str(stage))
                else:
                    sys.exit(1)
            if stage == 3:
                self.code3 = subprocess.call(cmd2)
                if self.code3 == 0:
                    self.exit_codes(4, "----------Storage Expansion Completed Successfully-----------")
                else:
                    sys.exit(1)
        except Exception as self.err:
            self.exception_stmnts()
    def post_config(self):
        """
        This function will do the block configuration
        Block configuration script will be called based on provided inputs
        self.code1 --> to take the status of block script execution
        return --> none
        """
        try:
            if not os.path.exists(TMP_FILE):
                self.fn3()
            self.exit_codes(4,"Starting Post Expansion...")
            cmd = "python /opt/ericsson/san/lib/StoragePostExpansion.py ".split(' ')
            self.code1 = subprocess.call(cmd)
            if self.code1 == 0:
                self.exit_codes(4, "----------Storage Post Expansion Completed Successfully-----------"), rm_file()
            else:
                self.exit_codes(3, "Issue while in performing post Expansion. Check and try again")
        except Exception as self.err:
            self.exception_stmnts()
    def exception_stmnts(self):
        """ function for exception statements """
        self.log_file_scrn("-"*75),self.log_file_scrn(self.err),self.log_file_scrn("-"*75),self.exit_codes(1,MSG2)
    def fn3(self):
        """function calls for post expansion"""
        print("Enter required inputs for Post Expansion.")
        self.input_ip2(1),self.input_ff(),self.unity_ip()
        self.unity_check(),self.pool_check(),self.lun_check(),self.input_f3()
    def fn_call(self):
        """" Function calls"""
        self.log_file_scrn("=" * 70),self.print_logging_detail()
def rm_file():
    """
    To remove temporary files
    post completion of operation files will be removed
    """
    if os.path.exists(TMP_FILE):
        os.remove(TMP_FILE)
    if os.path.exists(STAGE):
        os.remove(STAGE)
    if os.path.exists(JOB):
        os.remove(JOB)
    if os.path.exists('/var/tmp/cor.txt'):
        os.remove('/var/tmp/cor.txt')
    if os.path.exists('/var/tmp/r1.txt'):
        os.remove('/var/tmp/r1.txt')
    if os.path.exists('/var/tmp/r2.txt'):
        os.remove('/var/tmp/r2.txt')
    if os.path.exists(HST_FILE):
        os.remove(HST_FILE)
    if os.path.exists('/var/tmp/tp1.txt'):
        os.remove('/var/tmp/tp1.txt')
    if os.path.exists('/var/tmp/tp2.txt'):
        os.remove('/var/tmp/tp2.txt')
def stagelist_w():
    """
    Checks and returns which stage we are currently present at in case of failure
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
def help_fn():
    """
    Help function to guid user with available actions
    """
    print("Usage: StorageExpansion.py <--action>\n\nValid actions are:\n")
    print("--expand          Performs Storage Expansion \n--input      Performs precheck and collects required input")
    print("--postconfig      performs Post Storage Expansion\n\n--help            Show this help message and exit\n")
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
    Return: None
    """
    if os.getuid() != 0:
        print("ERROR: Only Root can execute the script..."),sys.exit(1)
def rm():
    """remove files"""
    if os.path.exists(TMP_FILE):
        os.remove(TMP_FILE)
    if os.path.exists(HST_FILE):
        os.remove(HST_FILE)
def main():
    """
    This is main function to call desired function calls for performing requirement
    performs configuration as per user request
    provides rerun in case of improper inputs provided by user
    sys.arg-->CLI args along with script
    """
    check_userid(),signal.signal(signal.SIGINT, handler)
    wrap,msg5=storage_config(),"Invalid Request!. check and try again."
    if len(sys.argv)==2:
        IP_USR=str(sys.argv[1])
    else:
        wrap.log_file_scrn("="*70),wrap.exit_codes(2,msg5),wrap.log_file_scrn("="*70),help_fn(),sys.exit(1)
    if not os.path.exists('/opt/ericsson/san/etc'):
        os.mkdir('/opt/ericsson/san/etc')
    if IP_USR=='--expand':
        wrap.log_file_scrn("="*70),wrap.exit_codes(4,"This Script will perform Storage Expansion")
        wrap.fn_call(),wrap.stor_expand()
    elif IP_USR == '--input':
        val='python /opt/ericsson/san/lib/ExpansionInputPrecheck.py'
        a=os.system(val)
        if a!=0:
            sys.exit(1)
        else:
            sys.exit(0)
    elif IP_USR == '--nasexpansion':
        wrap.log_file_scrn("=" * 70), wrap.exit_codes(4, "This Script will perform NAS Pool Expansion")
        wrap.log_file_scrn("=" * 70)
        cmd_ne = 'python /opt/ericsson/san/lib/NasExpansion.py'.split()
        ret_code1 = subprocess.call(cmd_ne)
        if ret_code1 == 0:
            sys.exit(0)
        else:
            sys.exit(1)
    elif IP_USR == '--postconfig':
        wrap.log_file_scrn("="*70),wrap.exit_codes(4,"This Script will perform Post Expansion")
        wrap.fn_call(),wrap.post_config()
    elif IP_USR in ['--help','-h']:
        help_fn()
    else:
        wrap.log_file_scrn("="*70),wrap.exit_codes(2,msg5),wrap.log_file_scrn("="*70),help_fn(),sys.exit(1)
if __name__ == "__main__":
    main()

