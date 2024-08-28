#!/usr/bin/bash
#
# ######################################################################
# #   COPYRIGHT Ericsson AB 2018                                       #
# #                                                                    #
# #   The copyright to the computer program(s) herein is               #
# #   the property of Ericsson Microwave Systems AB, Sweden.           #
# #   The program(s) may be used and/or copied only with               #
# #   the written permission from Ericsson Microwave Systems           #
# #   AB or in accordance with the terms and conditions                #
# #   stipulated in the agreement/contract under which                 #
# #   the program(s) have been supplied.                               #
# ********************************************************************
# Product : Storage Manager NAS API, CXP  903 6743
# Name    : nascli
# Written : Niklas Nordlund
# Modified: zchesiv (Modified for linux porting)
# ********************************************************************
#
# ######################################################################
#
#------ History -----------------------------------------------------------
# Rev   Date            Prepared        Description
#
# -     120314          REENIND         This version
#
#------ Purpose -----------------------------------------------------------
#
#  Name       : setup_ssh_FileStore.sh
#
#  Description: This script will setup PASSWD-free SSH login between
#    the executing host (OSS-RC/ENIQ) and Symantec NAS FileStore.
#  - It will not scratch current ssh-files, but rather cleanout old
#    entries and add new ones, preserving setup to other hosts.
#  - It requires 'expect' on the running server.
#  - Setup is made for local user 'storadm'.
#  - Setup is made for remote user 'master', using user 'support'.
#
#  Arguments  : -
#  Output     : Screen and logfile: setup_ssh_FileStore_<date>.log
#  ReturnVal  : -
#  Limitation : -
#  Environment: -
#
#--------------------------------------------------------------------------

sh /ericsson/storage/etc/decrypt.sh
source /ericsson/storage/etc/sourcefile


#-------------------------< Generic Functions >---------------------------

#----------------------
#   h e a d e r _ 1
#----------------------
# $1 = Text to be printed centered
header_1()
{
   typeset c2

   set_cols
   let c2=cols/2-1
   [ $c2 -gt 36 ] && c2=36

   echo -e "\007"
   echo "$*" | $AWK -v c2=$c2 '{n1=length($0);n2=c2-n1/2-n1%2;n3=c2-n1/2;for(n=1;n<n2;n++)printf("-");printf("< %s >",$0);for(n=1;n<n3;n++)printf("-");printf("\n\n")}'
}

#----------------------
#   h e a d e r _ 2
#----------------------
# $* = Text to be printed
header_2()
{
   echo -e "===> $*"
}

#----------------------
#   h e a d e r _ 3
#----------------------
# $* = Text to be printed
header_3()
{
   echo -e "-> $*"
}
#----------------------
#   s e t _ c o l s
#----------------------
# Sets: cols
# Used to adjust the menues to the terminal window.
set_cols()
{
   cols=$(stty 2>/dev/null| sed -n -e 's/.*columns = \([0-9]*\);.*/\1/p')
   [ "$cols" = "0" -o "$cols" = "" ] && cols=74
   let cols=cols-$(expr $cols % 2)
}

#------------------------------------
#   c h e c k _ p i n g _ h o s t
#------------------------------------
# $1 = Host to ping
check_ping_host()
{
   typeset host=$1

   /usr/bin/ping -c 2 $host >/dev/null

   if [ $? -eq 1 ]; then
      echo -e "\007 ERROR: Ping towards $host did not succeed. Exiting..."
      return 1
   fi
   return 0
}

#------------
#   a s k
#------------
# Asks the user for an answer.
# Sets the variable ANS.
# Uses SILENT
#
# Purpose: To be able to have also the typed input in the log file,
# this procedure has to be used, instead of "read".
#
# $1 = Prompt
# $2 = Default answer (optional)
ask()
{
   typeset defstr=""

   [ "$2" != "" ] && defstr=" [$2]"
   while :; do
      echo "${1}${defstr}: "
      if [ "$SILENT" = "y" -a "$2" != "" ]; then
         ANS="$2"
         echo $ANS
         break
      fi
      if [ ! -t 0 ]; then
         if [ "$2" != "" ]; then
            ANS="$2"
            echo $ANS
            break
         else
            echo -e "No connection to terminal. Exiting!"
            exit 1
         fi
      fi
      read ANS
      [ "$ANS" = "" ] && ANS="$2"
      [ "$ANS" != "" ] && break
   done
}

#--------------------
#   a s k _ n u m
#--------------------
# Asks the user for a number.
# Sets the variable ANS.
# $1 = Prompt
# $2 = Default answer (option)
ask_num()
{
   while :; do
      ask "$1" "$2"
      [ "$(echo $ANS|egrep '^[0-9]*$')" != "" ] && break
      echo -e "\007   Please enter only numbers!"
   done
}

#------------------
#   a s k _ y n
#------------------
# Asks the user for either yes or no.
# Sets the variable YESNO to 'y' or 'n'.
# Uses SILENT
#
# $1 = Prompt
# $2 = Default answer (y/n) (option)
ask_yn()
{
   defstr=""
   [ "$2" != "" ] && defstr=" [$2]"
   while :; do
      echo "$1 (y/n)?${defstr} "
      if [ "$SILENT" = "y" -a "$2" != "" ]; then
         YESNO="$2"
         echo $YESNO
         break
      fi
      if [ ! -t 0 ]; then
         if [ "$2" != "" ]; then
            YESNO="$2"
            echo $YESNO
            break
         else
            echo -e "No connection to terminal. Exiting!"
            exit 1
         fi
      fi
      read YESNO
      [ "$YESNO" = "" ] && YESNO="$2"
      case "$YESNO" in
         [yY]|[yY][eE][sS]) YESNO=y ; break ;;
         [nN]|[nN][oO]) YESNO=n ; break ;;
      esac
   done
}

#--------------------------
#   a s k _ p a s s w d
#--------------------------
# $1 = Hostname
# $2 = User
# Sets: PASSWD
ask_passwd()
{
   typeset stty_orig PASSWD2 host=$1 user=$2

   while :; do
      echo -e "  Enter $user PASSWD for $host: "
      stty_orig=$(stty -g)
      stty -echo
      read -r PASSWD
      stty $stty_orig
      echo -e "  Re-enter $user PASSWD: "
      stty_orig=$(stty -g)
      stty -echo
      read -r PASSWD2
      stty $stty_orig

      [ "$PASSWD" = "$PASSWD2" ] && break
      ask_yn "    Passwords entered do not match, would you like to re-try" y
      [ "$YESNO" = "n" ] && echo -e "Script will now exit..." && exit 1
   done
   PASSWD="$(escapepasswd "$PASSWD")"
   echo
   return 0
}

#----------------
#   escapepasswd
#----------------
# Adds escape character to special character.
# $1 = password

escapepasswd()
{
passwd="$1"
regex="[a-zA-Z0-9]"
newpass=''
        for ((i=0;i<${#passwd};i++)); do
           mychar="${passwd:$i:1}"
        for ((j=0; j<${#passwd};j++)); do
             if [[ "$mychar" == $regex ]] ; then
                mychar="${mychar}"
             else
                mychar="\\${mychar}"
             fi
                break
        done
        newpass="${newpass}${mychar}"
        done
echo "$newpass"
}

#----------------
#   p _ s e d
#----------------
# Edits a file with 'sed' commands.
# $1 = filename
# $2 = 'sed' command(s)
p_sed()
{
   typeset efile=$1
   shift
   echo "sed $* $efile" >>$OUT
   sed "$*" $efile >$TMP_FILE
   [ $? -eq 0 ] && cp $TMP_FILE $efile
}

#----------------------------------------------------------
# Functions to operate on LISTS.
# A list is just a string of words. "item1 item2 ..."
# I.e. it is not the ksh lists: set -A array item1 item2 ...
#----------------------------------------------------------

#------------------------------
#   l i s t _ s e c t i o n
#------------------------------
# Returns items found in both lists, on stdout.
# $1 = Name of first list
# $2 = Name of second list
# (A snitt B)
list_section()
{
   eval echo \$$1 | tr -s ' ' '\n' | sort >/tmp/a1.$$
   eval echo \$$2 | tr -s ' ' '\n' | sort >/tmp/b1.$$
   comm -12 /tmp/a1.$$ /tmp/b1.$$ | sort | egrep -v '^$'
   rm /tmp/a1.$$ /tmp/b1.$$
}
# Examples:
# commonInterest=`list_section myHobby yourHobby`

#--------------------------
#   l i s t _ m i n u s
#--------------------------
# Returns items in A, not found in B.
# $1 = Name of first list
# $2 = Name of second list
# (A - B)
list_minus()
{
   eval echo \$$1 | tr -s ' ' '\n' | sort >/tmp/a1.$$
   eval echo \$$2 | tr -s ' ' '\n' | sort >/tmp/b1.$$
   comm -23 /tmp/a1.$$ /tmp/b1.$$ | sort | egrep -v '^$'
   rm /tmp/a1.$$ /tmp/b1.$$
}
# Examples:
# restList=`list_minus toDoList doneList`

#--------------------------
#   l i s t _ u n i o n
#--------------------------
# Return items in both lists, not duplicated.
# $1 = Name of first list
# $2 = Name of second list
list_union()
{
   eval echo \$$1 | tr -s ' ' '\n' | sort >/tmp/a1.$$
   eval echo \$$2 | tr -s ' ' '\n' | sort >/tmp/b1.$$
   (comm -23 /tmp/a1.$$ /tmp/b1.$$ | sort | egrep -v '^$'
   cat /tmp/b1.$$ )| sort
   rm /tmp/a1.$$ /tmp/b1.$$
}

#------------------------------
#   l i s t _ p r o c e s s
#------------------------------
# Returns the list, where all items have been "processed":
# $1 = In-List
# $2 = Command, for sed-substitute (sxxxg) e.g. '/bad/good/'
list_process()
{
   eval aList=\$$1
   echo $aList | tr -s ' ' '\n' | sed -e 's'"$2"'g'
}
# Add $SUFFIX to all element:
# dbList=`list_process dbList "/\([^ ]*\)/\1$SUFFIX/"`
# Remove $SUFFIX from all element:
# dbList=`list_process dbList "/$SUFFIX//"`

#------------------------
#   l i s t _ u n i q
#------------------------
# Returns items sorted and unique.
# $1 = In-List
list_uniq()
{
   eval echo \$$1 | tr -s ' ' '\n' | sort -u
}

#--------------------
#   l i s t _ n r
#--------------------
# Counts the number of items in the list.
# $1 = Name of list to be counted
list_nr()
{
   echo $(eval echo \$$1 | wc -w)
}

#------------------------
#   l i s t _ i t e m
#------------------------
# Returns on stdout the item in the list selected by Index.
# $1 = Name of list
# $2 = Index (1-n)
list_item()
{
   eval echo \$$1 | tr -s ' ' '\n' | $AWK -v a=$2 'NR==a{print $1;exit}'
}

#--------------------------
#   l i s t _ i n d e x
#--------------------------
# Returns on stdout the index of Item in the list. (1-n, 0=not found)
# $1 = Name of list
# $2 = Item
list_index()
{
   eval echo \$$1 | tr -s ' ' '\n' | $AWK -v a=$2 'BEGIN{i=0}$1==a{i=NR;exit}END{print i}'
}

#--------------------
#   b a i l o u t
#--------------------
# $* = (optional) Error text
bailout()
{
   echo -e "\007*** ERROR encountered!"
   [ "$*" != "" ] && echo "$*"
   echo -e "Check log file: $OUT \n"
   tail $OUT
   echo "*** Exiting..."
   exit 1
}

#------------------
#   s e t _ p w
#------------------
set_pw()
{
   typeset USER=$1 PW=$2

   echo -e "-> Set default PW for $USER"
   $EXPECT <<EOF
spawn /usr/bin/passwd -r files $USER
expect -re "assword:"
send "$PW\r"
expect -re "assword:"
send "$PW\r"
expect eof
EOF
   [ $? -ne 0 ] && bailout "Problems setting default PW for user $USER!"
   return 0
}


#---------------------------< Local Functions >----------------------------

#------------------
#   e x p a n d
#------------------
# $1 = Connection str <user>:<password>@<host>:<port><dir>
# $2 = Prefix (optional)
expand()
{

   eval ${2}_USER=$(echo "$1"|sed  's/^\([a-zA-Z]*\):\(.*\):\(.*\)$/\1/')
   eval ${2}_PORT=$(echo "$1"|sed  's/^\([a-zA-Z]*\):\(.*\):\(.*\)$/\3/'|cut -d/ -f1)
   eval ${2}_DIR=$(echo "$1"|sed  's/^\([a-zA-Z]*\):\(.*\):\(.*\)$/\3/'|sed -n 's#[^/]*\(/.*\)#\1#p')
   if [[ "$1" =~ ([0-9]{1,3}\.){3}[0-9]{1,3} ]]; then
        eval ${2}_HOST=$(echo "$1"|sed  's/^\([a-zA-Z]*\):\(.*\):\(.*\)$/\2/' |sed  's/.*@\([0-9].*[0-9]\)$/\1/')
   else
        eval ${2}_HOST=$(echo "$1"|sed 's/^\([a-zA-Z]*\):\(.*\):\(.*\)$/\2/'|sed 's/.*@\([a-zA-Z]*$\)/\1/')
   fi
   if [[ "$1" =~ ([0-9]{1,3}\.){3}[0-9]{1,3} ]];then
        if [[ "${2}" =~ ([A_B]) ]];then
                if [[ "${2}" == "A" ]];then
                        A_PW="$(echo "$1"|sed  's/^\([a-zA-Z]*\):\(.*\):\(.*\)$/\2/'  | sed  's/@\([0-9]\{1,3\}.\)\{3\}[0-9]\{1,3\}$//')"
                else
                        B_PW="$(echo "$1"|sed  's/^\([a-zA-Z]*\):\(.*\):\(.*\)$/\2/'  | sed  's/@\([0-9]\{1,3\}.\)\{3\}[0-9]\{1,3\}$//')"
                fi
        else
                        _PW="$(echo "$1"|sed  's/^\([a-zA-Z]*\):\(.*\):\(.*\)$/\2/'  | sed  's/@\([0-9]\{1,3\}.\)\{3\}[0-9]\{1,3\}$//')"
        fi
   else
        if [[ "${2}" =~ ([A_B]) ]];then
                if [[ "${2}" == "A" ]];then
                        A_PW=$(echo "$1"|sed  's/^\([a-zA-Z]*\):\(.*\):\(.*\)$/\2/' | sed 's/@[a-zA-Z]*$//')
                else
                        B_PW=$(echo "$1"|sed  's/^\([a-zA-Z]*\):\(.*\):\(.*\)$/\2/' | sed 's/@[a-zA-Z]*$//')
                fi
        else
                _PW=$(echo "$1"|sed  's/^\([a-zA-Z]*\):\(.*\):\(.*\)$/\2/' | sed 's/@[a-zA-Z]*$//')
        fi
   fi

}

#--------------------------
#   e x p e c t _ r s a
#--------------------------
# $1 = Connection str <user>:<password>@<host>:<port><dir>
# EXPECT code for setting up rsa keys on given host.
expect_rsa()
{
   header_2 "expect_rsa $*\n"|sed 's/:[^:@/]*@/:x@/g' >>$OUT
   expand $1

   $EXPECT <<EOF >>$OUT 2>&1
set timeout 60
spawn $SSH -p $_PORT $_USER@$_HOST
expect {
"Are you sure you want to continue connecting (yes/no)?" {send "YES\r";exp_continue}
"assword:" {send "$_PW\r";exp_continue}
-re {> $|# $|[$] $} {send "\r"}
timeout {send_user "\nTIMEOUT!\n"; exit 9}
}
expect -re {> $|# $|[$] $}
send "/usr/bin/ssh-keygen -t rsa\r"
expect "Enter file in which to save the key"
send "$_DIR/.ssh/id_rsa\r"
expect "Enter passphrase (empty for no passphrase):"
send "\r"
expect "Enter same passphrase again:"
send "\r"
expect -re {> $|# $|[$] $}
send "exit\r"
expect eof
EOF
}

#----------------------------------------------------------------
#   e x p e c t _ a d d _ B _ t o _ A _ k n o w n _ h o s t s
#----------------------------------------------------------------
# To add host B to A:known_hosts
# EXPECT code for ssh to B from A
# $1 = Connection str to A <user>:<password>@<host>:<port><dir>
# $2 = Connection str to B <user>:<password>@<host>:<port><dir>
expect_add_B_to_A_known_hosts()
{
   typeset exitStr=exit
   header_2 "expect_add_B_to_A_known_hosts $*\n"|sed 's/:[^:@/]*@/:x@/g' >>$OUT
   #expand $1 A
   expand $1 A
   expand $2 B

   [ "$B_USER" = "master" ] && exitStr=logout

   $EXPECT <<EOF >>$OUT 2>&1
set timeout 60
spawn $SSH -p $A_PORT $A_USER@$A_HOST
expect {
"Are you sure you want to continue connecting (yes/no)?" {send "YES\r";exp_continue}
"assword:" {send "$A_PW\r";exp_continue}
#"assword:" {send "$A_PW\r";exp_continue}
-re {> $|# $|[$] $} {send "\r"}
timeout {send_user "\nTIMEOUT!\n"; exit 9}
}
#expand $2 B
expect -re {> $|# $|[$] $}
send "ssh -p $B_PORT $B_USER@$B_HOST\r"
expect {
"Are you sure you want to continue connecting (yes/no)" {send "YES\r";exp_continue}
"assword:" {send "$B_PW\r";exp_continue}
#"assword:" {send "$B_PW\r";exp_continue}
-re {> $|# $|[$] $} {send "\r"}
timeout {send_user "\nTIMEOUT!\n"; exit 9}
}
expect -re {> $|# $|[$] $} {send "$exitStr\r"}
expect -re {> $|# $|[$] $} {send "exit\r"}
expect eof
EOF
}

#----------------------------------
#   e x p e c t _ s s h _ c m d
#----------------------------------
# $1 = Connection str <user>:<password>@<host>:<port>[<dir>]
# $2-n = command to launch
expect_ssh_cmd()
{
   typeset cmd exitStr=exit
   header_2 "expect_ssh_cmd $*\n"|sed 's/:[^:@/]*@/:x@/g' >>$OUT
   expand $1
   shift
   cmd=$*

   [ "$_USER" = "master" ] && exitStr=logout

   $EXPECT <<EOF >>$OUT 2>&1
set timeout 60
spawn $SSH -p $_PORT $_USER@$_HOST
expect {
"Are you sure you want to continue connecting (yes/no)?" {send "YES\r";exp_continue}
"assword:" {send "$_PW\r";exp_continue}
-re {> $|# $|[$] $} {send "\r"}
timeout {send_user "\nTIMEOUT!\n"; exit 9}
}
expect -re {> $|# $|[$] $}
send "$cmd\r"
expect -re {> $|# $|[$] $}
send "$exitStr\r"
expect eof
EOF
}

#------------------------------------
#   e x p e c t _ s f t p _ c m d
#------------------------------------
# $1 = Connection str <user>:<password>@<host>:<port>[<dir>]
# $2-n = command, like "put local-file remote-file"
#                    "get remote-file local-file"
expect_sftp_cmd()
{
   typeset cmd
   header_2 "expect_sftp_cmd $*\n"|sed 's/:[^:@/]*@/:x@/g' >>$OUT
   expand $1
   shift
   cmd=$*

   $EXPECT <<EOF >>$OUT 2>&1
set timeout 60
spawn $SFTP -o Port=$_PORT $_USER@$_HOST
expect {
"Are you sure you want to continue connecting (yes/no)?" {send "YES\r";exp_continue}
"assword:" {send "$_PW\r";exp_continue}
"sftp>" {send "\r"}
timeout {send_user "\nTIMEOUT!\n"; exit 9}
}
expect "sftp>"
send "$cmd\r"
expect "sftp>" {send "quit\r"}
expect eof
EOF
}

#------------------------------------------------------------
#   e x p e c t _ s s h _ t e s t _ f r o m _ A _ t o _ B
#------------------------------------------------------------
# EXPECT code to TEST password free ssh login from A to B.
# If not entering directly, it will fail with return code != 0
# $1 = Connection str to A <user>:<password>@<host>:<port><dir>
# $2 = Connection str to B <user>:<password>@<host>:<port><dir>
expect_ssh_test_from_A_to_B()
{
   typeset exitStr=exit
   header_2 "expect_ssh_test_from_A_to_B $*\n"|sed 's/:[^:@/]*@/:x@/g' >>$OUT
   expand $1 A
   expand $2 B

   [ "$B_USER" = "master" ] && exitStr=logout

   $EXPECT <<EOF >>$OUT 2>&1
set timeout 60
spawn $SSH -p $A_PORT $A_USER@$A_HOST
expect {
"Are you sure you want to continue connecting (yes/no)?" {send "YES\r";exp_continue}
"assword:" {send "$A_PW\r";exp_continue}
-re {> $|# $|[$] $} {send "\r"}
timeout {send_user "\nTIMEOUT!\n"; exit 9}
}
expect -re {> $|# $|[$] $}
send "$SSH -p $B_PORT -o StrictHostKeyChecking=no $B_USER@$B_HOST\r"
expect {
"Are you sure you want to continue connecting (yes/no)?" {send "NO\r";send_user "LoGiNfAiLeD!\n";exit 1}
"assword:" {send "DUMMY\r";send_user "LoGiNfAiLeD\n";exit 1}
-re {> $|# $|[$] $} {send "\r"}
timeout {send_user "\nTIMEOUT!\n"; exit 9}
}
expect -re {> $|# $|[$] $} {send_user "LoGiNoK\n";send "$exitStr\r"}
expect -re {> $|# $|[$] $} {send "exit\r"}
expect eof
EOF
}


#------------------------------< Procedures >------------------------------

#--------------------------
#   i n p u t _ d a t a
#--------------------------
## $1 = Input file (optional)
input_data()
{
   typeset inFile=$1
   header_1 Input Data

   VARS="L_HOST L_PORT L_USER_A L_PW_A R_HOST R_PORT R_USER_M R_PW_M R_USER_S R_PW_S"
   unset $VARS

   if [ "$inFile" != "" ] && [ -f $inFile ]; then
      . $inFile
      L_HOST=${L_HOST:-$($GETENT hosts  $(hostname)|$AWK '{print $1;exit}')}
   fi

   header_2 NFS Client Data
   if [ "$L_HOST" = "" ]; then

      while :; do
         ask "    Enter OSS/ENIQ (NFS client) IP/name" $($GETENT hosts  $(hostname)|$AWK '{print $1;exit}')
         L_HOST=$ANS
         check_ping_host $L_HOST && break
      done
   fi
   L_PORT=${L_PORT:-22}

   if [ "$L_USER_A" = "" ]; then
      ask "    Enter Admin user" storadm
      L_USER_A=$ANS
   fi

   if [ "$L_PW_A" = "set" ]; then
      # This option only works if executing on the same host
      L_PW_A=$SAPASSWD
      set_pw $L_USER_A $L_PW_A
   elif [ "$L_PW_A" = "" ]; then
      ask_passwd $L_HOST $L_USER_A
      L_PW_A=$PASSWD
   fi

   L_CONN_A="$L_USER_A:$L_PW_A@$L_HOST:$L_PORT"





   L_TMPDIR=/tmp/locssh


   header_2 FileStore Data

   if [ "$R_HOST" = "" ]; then
      while :; do
         ask "    Enter FileStore server IP/name" nasconsole
         R_HOST=$ANS
         check_ping_host $R_HOST && break
      done
   fi
   R_PORT=${R_PORT:-22}

   if [ "$R_USER_M" = "" ]; then
      ask "    Enter FileStore user" master
      R_USER_M=$ANS
   fi

   if [ "$R_PW_M" = "" ]; then
      ask_passwd $R_HOST $R_USER_M
      R_PW_M=$PASSWD
   else
      R_PW_M="$(escapepasswd "$R_PW_M")"
   fi

   R_CONN_M="$R_USER_M:$R_PW_M@$R_HOST:$R_PORT"


   if [ "$R_USER_S" = "" ]; then
      ask "    Enter FileStore Support user" support
      R_USER_S=$ANS
   fi

   if [ "$R_PW_S" = "" ]; then
      ask_passwd $R_HOST $R_USER_S
      R_PW_S=$PASSWD
   else
      R_PW_S="$(escapepasswd "$R_PW_S")"
   fi

   R_TMPDIR=/tmp/remssh

   if [ "$SSH_SETUP_FILE" != "" ]; then
      >$SSH_SETUP_FILE
      for var in $VARS
      do
         eval echo "$var='\"'\$$var'\"'" >>$SSH_SETUP_FILE
      done
   fi
}

#--------------------------------------------
#   p r e p a r e _ r e m o t e _ h o s t
#--------------------------------------------
prepare_remote_host()
{
   header_1 "Prepare Host"

   header_2 "Prepare for host $R_HOST"

   echo "    Clean out $R_HOST and $L_HOST from my root's known_hosts"
   cd $($AWK -F: '$1=="root"{print $6}' /etc/passwd)
   if [ -f .ssh/known_hosts ]; then
      p_sed .ssh/known_hosts "/[,]*${R_HOST}[, ]/d"
      p_sed .ssh/known_hosts "/[,]*$(getent hosts $R_HOST|$AWK '{print $1;exit}')[, ]/d"
      p_sed .ssh/known_hosts "/[,]*${L_HOST}[, ]/d"
      p_sed .ssh/known_hosts "/[,]*$(getent hosts $L_HOST|$AWK '{print $1;exit}')[, ]/d"
   fi

}

#------------------------------------------
#   g e t _ p h y s i c a l _ h o s t s
#------------------------------------------
get_physical_hosts()
{
   typeset host1 ipList ip host hostList found
   header_2 "Get All Hosts in $R_HOST cluster"

   # Add at least 'nasconsole'
   R_HOST_LIST=$R_HOST

   R_CONN_M="$R_USER_M:$R_PW_M@$R_HOST:$R_PORT"

   echo "    Connecting to $R_HOST as $R_USER_M to get all nodes..."
   expect_ssh_cmd $R_CONN_M "cluster show" || bailout
   hostList=$($AWK '/^[^a-zA-Z0-9_-]/{a=0}a==1{print $1}/^----/{a=1}/^================/{a=1}/^=========/{a=1}' $OUT)


   echo "    Connecting to $R_HOST as $R_USER_M to get all IP:s..."
   expect_ssh_cmd $R_CONN_M "network ip addr show" || bailout

   host1=$($AWK '/Con IP/{print $4;exit}' $OUT)
   if [ "$host1" != "" ]; then  # Just a safety check
      for host in $(list_minus hostList host1)
      do
         echo "    Getting IP for node $host"
         ipList=$($AWK -v h=$host '$4==h{print $1}' $OUT)
         found=n
         for ip in $ipList
         do
            echo "        Pinging $ip"
            ping -c 2 $ip >/dev/null 2>&1
            if [ $? -eq 0 ]; then
               echo "        OK: node $host is accessible via $ip"
               R_HOST_LIST="$R_HOST_LIST $ip"
               found=y
               break
            fi
         done
         [ "$found" = "n" ] && echo "        NOK: node $host is not responding"
      done
   fi

   if [ $(list_nr hostList) -ne $(list_nr R_HOST_LIST) -o $(list_nr R_HOST_LIST) -eq 1 ]; then
echo -e "***********************************************************************"
echo -e "*                                                                     *"
echo -e "*                        One Node!                                    *"
echo -e "*                                                                     *"
echo -e "***********************************************************************"
      #banner "One Node!"
      echo -e "  Could not extract info to find all SFS nodes"
      echo "    $(list_nr R_HOST_LIST) node(s) will be setup"
      echo "    Re-run this script when the all nodes in SFS cluster is up"
   fi
   return 0
}

#------------------------------------------------
#   s e t u p _ a d m i n _ u s e r _ k e y s
#------------------------------------------------
setup_admin_user_keys()
{
   header_1 "Local keys for Admin user $L_USER_A"

   header_2 "Check/Generate RSA keys for $L_USER_A@$L_HOST"

   [ -d $L_TMPDIR ] && $RM -rf $L_TMPDIR
   mkdir $L_TMPDIR || bailout

   echo "    Fetching $L_USER_A/.ssh files from $L_HOST..."
   expect_ssh_cmd $L_CONN_A "rm /tmp/pwd.out;cd;pwd >/tmp/pwd.out" || bailout
   expect_sftp_cmd $L_CONN_A get /tmp/pwd.out $L_TMPDIR/pwd.out || bailout
   expect_ssh_cmd $L_CONN_A "rm /tmp/pwd.out" || bailout
   L_DIR=$(echo $(cat $L_TMPDIR/pwd.out|strings))
   L_CONN_A="${L_CONN_A}$L_DIR"

   expect_ssh_cmd $L_CONN_A "rm /tmp/hostname.out;hostname >/tmp/hostname.out" || bailout
   expect_sftp_cmd $L_CONN_A get /tmp/hostname.out $L_TMPDIR/hostname.out || bailout
   expect_ssh_cmd $L_CONN_A "rm /tmp/hostname.out" || bailout
   L_HOSTNAME=""
   [ -f $L_TMPDIR/hostname.out ] && L_HOSTNAME=$(cat $L_TMPDIR/hostname.out)
   if [ "$L_HOSTNAME" = "" ]; then
      [ "$(echo $L_HOST|egrep '^[0-9]')" = "" ] && L_HOSTNAME=$L_HOST
      ask " Enter real HOSTNAME for $L_HOST" $L_HOSTNAME
      L_HOSTNAME=$ANS
   fi

   expect_sftp_cmd $L_CONN_A get $L_DIR/.ssh/known_hosts $L_TMPDIR/known_hosts || bailout

   if [ -f $L_TMPDIR/known_hosts ]; then
      sum $L_TMPDIR/known_hosts >/tmp/sum.1
      for R_HOST in $R_HOST_LIST
      do
         p_sed $L_TMPDIR/known_hosts "/[,]*${R_HOST}[, ]/d"
      done
      sum $L_TMPDIR/known_hosts >/tmp/sum.2
      if [ "$(diff /tmp/sum.1 /tmp/sum.2)" != "" ]; then
         expect_sftp_cmd $L_CONN_A put $L_TMPDIR/known_hosts $L_DIR/.ssh/known_hosts || bailout
      fi
   fi

   expect_sftp_cmd $L_CONN_A get $L_DIR/.ssh/id_rsa.pub $L_TMPDIR/id_rsa.pub || bailout

   if [ ! -f $L_TMPDIR/id_rsa.pub ]; then
      echo "    No id_rsa.pub: Removing old dir $L_DIR/.ssh"
      expect_ssh_cmd $L_CONN_A "rm -rf $L_DIR/.ssh;mkdir $L_DIR/.ssh" || bailout

      echo "    Generating new RSA key on $L_HOST for $L_USER_A"
      expect_rsa $L_CONN_A || bailout
      expect_sftp_cmd $L_CONN_A get $L_DIR/.ssh/id_rsa.pub $L_TMPDIR/id_rsa.pub || bailout
   else
      echo "    Using old keys"
   fi
}


#----------------------------------------------------
#   s e t u p _ a d m i n _ u s e r _ r e m o t e
#----------------------------------------------------
setup_admin_user_remote()
{
   header_1 "Setup for $L_USER_A to $R_USER_M@$R_HOST"

   header_2 "Authorized_keys for $R_USER_M@$R_HOST"

   [ -d $R_TMPDIR ] && $RM -rf $R_TMPDIR
   mkdir $R_TMPDIR || bailout

   # Hardcode dir for user 'master'
   R_DIR="/root"
   R_CONN_S="$R_USER_S:$R_PW_S@$R_HOST:$R_PORT$R_DIR"

   echo "    Fetching remote authorized_keys"
   expect_sftp_cmd $R_CONN_S get $R_DIR/.ssh/authorized_keys $R_TMPDIR/authorized_keys || bailout

#   $TOUCH $R_TMPDIR/authorized_keys
   [ ! -f $R_TMPDIR/authorized_keys ] && bailout
   if [ "$(egrep "$L_USER_A@${L_HOSTNAME}\$" $R_TMPDIR/authorized_keys 2>/dev/null)" != "" ]; then
      echo "    Removing old entry"
      p_sed $R_TMPDIR/authorized_keys "/$L_USER_A@${L_HOSTNAME}\$/d"
   fi
   echo "    Adding $L_USER_A@${L_HOSTNAME} id_rsa.pub"
   $CAT $L_TMPDIR/id_rsa.pub >> $R_TMPDIR/authorized_keys

   echo "    Sending back"
   expect_sftp_cmd $R_CONN_S put $R_TMPDIR/authorized_keys $R_DIR/.ssh/authorized_keys || bailout

   expect_sfs_version $R_CONN_M
   stat=$?
   ver=$(awk '/^ACCESS/{print $2;exit}' $OUT|sed 's/^\([0-9]*[.][0-9]*\).*/\1/')
   [[ -z $ver ]] && ver=$(awk '/ENTERPRISE EDITION.*Installed/{print $1;exit}' $OUT|sed 's/^\([0-9]*[.][0-9]*\).*/\1/')


   if [[ $ver < "7.4" ]]; then
           header_2 "Known_hosts for $L_USER_A@$L_HOST"

           echo "    Adding $R_USER_M@$R_HOST"
           expect_add_B_to_A_known_hosts $L_CONN_A $R_CONN_M || bailout


           header_2 "Testing NO PASSWD SSH connection"

           header_3 "From $L_USER_A@$L_HOST to $R_USER_M@$R_HOST"
           expect_ssh_test_from_A_to_B $L_CONN_A $R_CONN_M || bailout

           [ "$(grep LoGiNfAiLeD $OUT)" != "" ] && bailout
           echo "<- OK"
   fi
   return 0


}


### TEMPORARY ###
# Until storam doesn't need to login as support
#------------------------------------------------------
#   s e t u p _ a d m i n _ u s e r _ s u p p o r t
#------------------------------------------------------
setup_admin_user_support()
{
   header_1 "Setup for $L_USER_A to $R_USER_S@$R_HOST"

   header_2 "Authorized_keys for $R_USER_S@$R_HOST"

   [ -d $R_TMPDIR ] && $RM -rf $R_TMPDIR
   mkdir $R_TMPDIR || bailout

   # Hardcode dir for user 'support'
   R_DIR="/home/support"
   R_CONN_S="$R_USER_S:$R_PW_S@$R_HOST:$R_PORT$R_DIR"

   echo "    Checking directory $R_DIR/.ssh"
   expect_ssh_cmd $R_CONN_S "mkdir -p $R_DIR/.ssh;chmod 700 $R_DIR/.ssh" || bailout

   echo "    Fetching remote authorized_keys"
   expect_sftp_cmd $R_CONN_S get $R_DIR/.ssh/authorized_keys $R_TMPDIR/authorized_keys || bailout

   $TOUCH $R_TMPDIR/authorized_keys
   if [ "$(egrep "$L_USER_A@${L_HOSTNAME}\$" $R_TMPDIR/authorized_keys 2>/dev/null)" != "" ]; then
      echo "    Removing old entry"
      p_sed $R_TMPDIR/authorized_keys "/$L_USER_A@${L_HOSTNAME}\$/d"
   fi
   echo "    Adding $L_USER_A@${L_HOSTNAME} id_rsa.pub"
   $CAT $L_TMPDIR/id_rsa.pub >> $R_TMPDIR/authorized_keys

   echo "    Sending back"
   expect_sftp_cmd $R_CONN_S put $R_TMPDIR/authorized_keys $R_DIR/.ssh/authorized_keys || bailout


   header_2 "Testing NO PASSWD SSH connection"

   header_3 "From $L_USER_A@$L_HOST to $R_USER_S@$R_HOST"
   expect_ssh_test_from_A_to_B $L_CONN_A $R_CONN_S || bailout

   [ "$(grep LoGiNfAiLeD $OUT)" != "" ] && bailout
   echo "<- OK"

   return 0
}


#----------------------------------------
#   c h e c k _ s f s _ v e r s i o n
#----------------------------------------
#check_sfs_version()
#{
#   typeset ver file=$SCRIPT_HOME/plugins/filestore/etc/nasplugin.conf
#   header_1 "Check SFS Version"


#   [ ! -f $file ] && cp ${file}_template $file
#   chown storadm $file

 #  expect_ssh_cmd $R_CONN_M "upgrade show"
  # stat=$?
#   ver=$($AWK '/ENTERPRISE EDITION.*Installed/{print $1;exit}' $OUT|sed 's/^\([0-9]*[.][0-9]*\).*/\1/')
   #ver=$(awk '/^ACCESS/{print $2;exit}' $OUT|sed 's/^\([0-9]*[.][0-9]*\).*/\1/')
#   [[ -z $ver ]] && ver=$(awk '/ENTERPRISE EDITION.*Installed/{print $1;exit}' $OUT|sed 's/^\([0-9]*[.][0-9]*\).*/\1/')


#   if [ $stat -eq 0 -a "$ver" != "" ]; then
 #     header_3 "Setting SFS_VERSION=$ver in $file"
  #    if [ "$(grep SFS_VERSION= $file)" != "" ]; then
   #      p_sed $file "s/SFS_VERSION=.*/SFS_VERSION=$ver/"
    #  else
     #    echo "SFS_VERSION=$ver" >>$file
      #fi
#   else
 #     echo -e "ERROR: Could not extract SFS version!"
  #    echo "Update SFS_VERSION in $file manually."
   #   return 1
 #  fi
  # return 0
#}

check_sfs_version()
{
   typeset ver file=$SCRIPT_HOME/plugins/filestore/etc/nasplugin.conf
   header_1 "Check SFS Version"


   [ ! -f $file ] && cp ${file}_template $file
   chown storadm $file

   expect_sfs_version $R_CONN_M
   stat=$?
   ver=$(awk '/^ACCESS/{print $2;exit}' $OUT|sed 's/^\([0-9]*[.][0-9]*\).*/\1/')
   [[ -z $ver ]] && ver=$(awk '/ENTERPRISE EDITION.*Installed/{print $1;exit}' $OUT|sed 's/^\([0-9]*[.][0-9]*\).*/\1/')

   if [ $stat -eq 0 -a "$ver" != "" ]; then
      header_3 "Setting SFS_VERSION=$ver in $file"
      if [ "$(grep SFS_VERSION= $file)" != "" ]; then
         p_sed $file "s/SFS_VERSION=.*/SFS_VERSION=$ver/"
      else
         echo "SFS_VERSION=$ver" >>$file
      fi
   else
      echo "\nERROR: Could not extract SFS version!"
      echo "Update SFS_VERSION in $file manually."
      return 1
   fi
   return 0
}

#--------------------------------------
#   e x p e c t _ s f s _ v e r s i o n
#--------------------------------------
# $1 = Connection str <user>:<password>@<host>:<port>[<dir>]
expect_sfs_version()
{

   typeset cmd exitStr=exit
   header_2 "expect_ssh_cmd $*\n"|sed 's/:[^:@/]*@/:x@/g' >>$OUT
   expand $1

   [ "$_USER" = "master" ] && exitStr=logout

   $EXPECT <<EOF >>$OUT 2>&1

set timeout 60
spawn $SSH -p $_PORT $_USER@$_HOST

expect {
   "Are you sure you want to continue connecting (yes/no)?" {send "yes\r";exp_continue}
   "assword:" {send "$_PW\r";exp_continue}
   -re {> $|# $|[$] $} {send "\r"}
   timeout {send_user "\nTIMEOUT!\n"; exit 9}
}

expect -re {> $|# $|[$] $}

# SFS MP1P3 has "upgrade show" command
# InfoScale Access has "upgrade version" command
# Send a tab after "upgrade" to discover options as could be either MP1P3 or InfoScale Access
send "upgrade \t"

expect {
   -re "\[ ]+version\[ ]*" {send "version\r"; exp_continue}
   -re "\[ ]+show\[ ]*" {send "show\r"; exp_continue}
   -re {> $|# $|[$] $} {send "$exitStr\r"}
   -ex "--More--" {send "\r"; exp_continue;}
   timeout {send_user "\nTIMEOUT!\n"; exit 9}
}

expect eof
EOF
}
#---------------------------------< Main >---------------------------------

umask 022
set -a

DATE=/usr/bin/date
LS=/usr/xpg4/bin/ls
GREP=/usr/xpg4/bin/grep
CAT=/usr/bin/cat
SED=/usr/bin/sed
AWK=/usr/bin/awk
READ=/usr/bin/read
RM=/usr/bin/rm
ECHO=/usr/bin/echo
TOUCH=/usr/bin/touch
SSH=/usr/bin/ssh
SFTP=/usr/bin/sftp
GETENT=/usr/bin/getent
WHOAMI=/usr/ucb/whoami
EXPECT=/usr/bin/expect

echo -e "### Setup PW-free SSH for Symantec FileStore"

SCRIPT_NAME=$(basename $0)
cd $(dirname $0)
SCRIPT_HOME=$(dirname $(/usr/bin/pwd))
TMP_FILE=/tmp/setup_ssh_FileStore.$$
INST_TIME=$($DATE "+%Y%m%d.%H:%M:%S")
OUT=setup_ssh_FileStore_${INST_TIME}.log
[ -d $SCRIPT_HOME/log ] && OUT=$SCRIPT_HOME/log/$OUT
$ECHO "### Log file: $OUT"
>$OUT
link=$(dirname $OUT)/setup_ssh_FileStore.log
[ -h $link -o -f $link ] && rm $link
ln -s $OUT $link


input_data $*

prepare_remote_host
get_physical_hosts

setup_admin_user_keys

for R_HOST in $R_HOST_LIST
do
   prepare_remote_host
   setup_admin_user_remote
   setup_admin_user_support
done




$RM -rf $L_TMPDIR
$RM -rf $R_TMPDIR

check_sfs_version

header_1 Done

exit 0
