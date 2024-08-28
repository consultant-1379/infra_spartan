import pexpect
from read_csv import read_csv_file

DATABSE_FILE = '/var/tmp/database_file/hardware.csv'
class mws_profile_add():
    """
	class to add profile in given mws server
    """
    def __init__(self, mws_server, client_server):
        self.mws_server = mws_server
        self.client_server = client_server
    def add_profile(self):
       """
		Function to add client profile to mws
       """
       hwdetails = self.get_basic_details(self.client_server)
       mws_child = pexpect.spawn('ssh -o StrictHostKeyChecking=no {}@{}'.format(hwdetails['Login_User']), self.mws_server)
       
    def get_basic_details(self, client_server):
       """
		Get the Basic details from the database file
       """
       read_file = read_csv_file('hwfile')
       hwdetail  = read_file.check_read_file()
       hwdetail = hwdetail[client_server]
       return hwdetail 

