#!/usr/bin/python
""" Script to get all the JIRA tickt details"""
from jira import JIRA
import getpass
from jira.exceptions import JIRAError
import subprocess
import time
import sys
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')

class GetJiraDetails():
    """ Class to get all the JIRA tickt details"""
    def __init__(self):
	    """ To get a connection to JIRA server """
            self.jira = ""
	    self.options = {
            'server': 'https://jira-oss.seli.wh.rnd.internal.ericsson.com'
            }
            self.sprint = self.getuserinput("sprint")
            self.getConnectionToJira()

    def getuserinput(self, sprint):
        """Get the input from user"""
        inputuser = raw_input("Enter the {} name\n".format(sprint))
        return(inputuser)      
    def getConnectionToJira(self):
        """ get connection"""
	self.passwd = getpass.getpass()
        try:
            self.jira = JIRA(options=self.options, basic_auth=('xkumvig', self.passwd))
        except JIRAError as e:
            if e.status_code == 401:
                print "Login to JIRA failed. Check your username and password"
				
    def exe_curl_cmd(self, jstr, tik):
        """ Curl command execution for particular ticket"""
        cmd = 'curl  -X POST -u \"xkumvig:{}\" \"https://fem156-eiffel004.lmera.ericsson.se:8443/jenkins/view/INFRA_TEAM_JOBS/job/INFRA_test1/buildWithParameters?token=a7a57eb30f7d8fb2ef34334a9a93cf45&{}\"'.format(self.passwd, jstr)
        subprocess.call(cmd, shell=True)
        print "Sending mail  through jenkins for the Ticket {}".format(tik)
        time.sleep(10)

    def sendMailfromJenkin(self, jira_d):
        """ Setting params for jenkins build job"""
        for i in jira_d.keys():
            jkin_param = "ID={}&email={}&name={}&sum={}&".format(i,
                                                                 jira_d[i]['email'],
                                                                 jira_d[i]['name'].replace(' ', "%20"),
                                                                 jira_d[i]['sum'].replace(' ', "%20"))
            jkin_param = jkin_param+"upd={}&fid={}&itype={}".format(jira_d[i]['upd'],
                                                                    jira_d[i]['fid'],
                                                                    jira_d[i]['itype'].replace(' ', '%20'))
            jkin_param = jkin_param+"&msg={}&sts={}&sub={}".format(jira_d[i]['msg'],
                                                            jira_d[i]['sts'],
                                                            jira_d[i]['sub'])
            self.exe_curl_cmd(jkin_param, i)
    def getAlltickets(self):
        """ getting all ticket deatils """
        try:
            issues_in_project = self.jira.search_issues('project = EQEV AND status = "In Progress" \
                                                        AND resolution = Unresolved \
                                                        AND sprint = {} \
                                                        AND component = INFRA-SPARTAN \
                                                        AND component not in (PowerRangers,\
                                                            Solitaire,\
                                                            "Indian Ocean",\
                                                            BO_TigerTeam_Design,\
                                                            NetAn, "Team 8",\
                                                            "ENIQ Stats RV")\
                                                        AND updated< -24h order by updated DESC'.format(self.sprint))
        except:
            print "Given sprint is invalid as per JIRA server and please check"
            exit(1)
        sub = "Reminder: name, please provide update for ID JIRA"
        self.getSignleTicketDetails(issues_in_project, "In-Progress", "", sub)

    def getAllOpentickets(self):
        """Getting All poen ticekts"""
        try:
            issues_in_project = self.jira.search_issues('project = EQEV \
	                                                AND status = Open \
                                                        AND sprint = {} \
                                                        AND resolution = Unresolved \
                                                        AND component = INFRA-SPARTAN \
                                                        AND component not in (PowerRangers,\
                                                            Solitaire,\
                                                            "Indian Ocean",\
                                                            BO_TigerTeam_Design,\
                                                            NetAn, "Team 8",\
                                                            "ENIQ Stats RV")'.format(self.sprint))
        except:
            print "Given sprint is invalid as per JIRA server and please check"
            exit(1)
        msg = "Kindly move it to In-Progress and add all required sub-tasks".replace(' ',"%20")
        sub = "name, please move ID JIRA to In-Progress"
        self.getSignleTicketDetails(issues_in_project, "Open", msg, sub)

    def getSignleTicketDetails(self, issues_in_project, sts, msg, sub):
        jira_list=[str(i) for i in issues_in_project]
#        jira_list=['EQEV-64939']
        jira_dict={}
        for item in jira_list:
            jira_dict[item] = {}
            issue = self.jira.issue(item)
            try:
		jira_dict[item]['email'] = issue.fields.assignee.emailAddress
                jira_dict[item]['name'] = issue.fields.assignee.displayName
            except:
                del jira_dict[item]
                continue 
            jira_dict[item]['sum'] = issue.fields.summary
            jira_dict[item]['upd'] = issue.fields.updated
            jira_dict[item]['fid'] = str(issue.fields.customfield_10701[0]).split(',')[3].split('=')[1]
            jira_dict[item]['itype'] = issue.fields.issuetype.name
	    jira_dict[item]['sts'] = sts
	    jira_dict[item]['msg'] = msg
            jira_dict[item]['sub'] = sub.replace("name", 
                                                 "{}").replace("ID",
                                                 "{} ").format(jira_dict[item]['name'],
                                                 item+" "+issue.fields.issuetype.name).replace(' ', "%20") 
        self.sendMailfromJenkin(jira_dict)	
if __name__ == '__main__':
    JIRA_call = GetJiraDetails()
    JIRA_call.getAllOpentickets()
    JIRA_call.getAlltickets()
