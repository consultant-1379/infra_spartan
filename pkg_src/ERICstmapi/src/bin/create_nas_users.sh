#!/bin/bash
# ********************************************************************
# Ericsson Radio Systems AB                                     SCRIPT
# ********************************************************************
#
#
# (c) Ericsson Radio Systems AB 2018 - All rights reserved.
#
# The copyright to the computer program(s) herein is the property
# of Ericsson Radio Systems AB, Sweden. The programs may be used
# and/or copied only with the written permission from Ericsson Radio
# Systems AB or in accordance with the terms and conditions stipulated
# in the agreement/contract under which the program(s) have been
# supplied.
#
# ********************************************************************
# Product : Storage Manager NAS API, CXP  903 6743
# Name    : nascli
# Written : Niklas Nordlund
# Modified: xkeerbv (Modified for linux porting)
# ********************************************************************
#
# Usage: create_nas_user.sh
# 2010-05-04 First version reenind
# 2017-05-23 Last update
#
# This script will create the user 'storadm'.
# Both with password '*******'.
# Home directory: <path>/storage/home/<user>
#

#---------------------------< Command Section >----------------------------

set -a
EXPECT=/usr/bin/expect
GROUPADD=/usr/sbin/groupadd
GROUPDEL=/usr/sbin/groupdel
USERADD=/usr/sbin/useradd
USERDEL=/usr/sbin/userdel
PASSWD=/usr/bin/passwd
CHMOD=/usr/bin/chmod
CHGRP=/usr/bin/chgrp
GETENT=/usr/bin/getent
ECHO=/usr/bin/echo
LS=/usr/bin/ls
DATE=/usr/bin/date
SED=/usr/bin/sed
MV=/usr/bin/mv
GREP=/usr/bin/grep
AWK=/usr/bin/awk


sh /ericsson/storage/etc/decrypt.sh
source /ericsson/storage/etc/sourcefile

#------------------------------< Procedures >------------------------------

#------------------
#   s e t _ p w
#------------------
# $1 = User
# $2 = Password
set_pw()
{
   local user=$1 PW=$2

   $ECHO -e "-> Set default PW for $user"
   $EXPECT <<EOF
spawn $PASSWD $user
expect -re "password:"
send "$PW\r"
expect -re "password:"
send "$PW\r"
expect eof
EOF
   [ $? -ne 0 ] && $ECHO "ERROR: Problems setting default PW for user $user!" && return 1
   return 0
}

#----------------------------
#   c r e a t e _ u s e r
#----------------------------
# $1 = User
# $2 = UID
# $3 = Group
# $4-n = Comment text
create_user()
{
   local user=$1 uid=$2 group=$3 comment stat
   shift 3
   comment="$*"
   $ECHO -e "-> Create user: $user ${uid}:${group}"

   if [ "$($GETENT passwd|$AWK -F: -v u=$user '$1==u{print $1;exit}')" != "" ]; then
      $ECHO "WARNING: User $user exists! Will remove first."
      $USERDEL $user
      [ -d $HOME/$user ] && rm -rf $HOME/$user
   fi
   if [ "$($GETENT passwd|$AWK -F: -v id=$uid '$3==id{print $1;exit}')" != "" ]; then
      $ECHO "    $uid occupied. \c"
      uid=$($GETENT passwd|$AWK -F: '$3>300&&$3<500{print $3}'|sort -n|$AWK 'BEGIN{i=500}$1>i{exit}{i=$1+1}END{print i}')
      $ECHO "New ID: $uid"
  fi
   $USERADD -u $uid  -g $group -d $HOME/$user -s /bin/bash -c "$comment" -m $user
   if [ $? -ne 0 ]; then
      $ECHO "ERROR: Problems creating user $user!"
      exit 1
   fi
   $CHMOD 750 $HOME/$user
   if [ $? -ne 0 ]; then
      $ECHO "ERROR: Problem changing home directory permissions for user $user!"
      exit 1
   fi
   return 0
}

#------------------------------
#   c r e a t e _ g r o u p
#------------------------------
# $1 = Group
# $2 = GID
create_group()
{
   local group=$1 gid=$2
   $ECHO -e "-> Create group: $group $gid"

   if [ "$($GETENT group|$AWK -F: -v g=$group '$1==g{print $1;exit}')" != "" ]; then
      $ECHO "WARNING: Group $group exists! Will remove first."
      $GROUPDEL $group || return 1
   fi
   if [ "$($GETENT group|$AWK -F: -v id=$gid '$3==id{print $1;exit}')" != "" ]; then
      $ECHO "    $gid occupied. \c"
      gid=$($GETENT group|$AWK -F: '$3>200&&$3<400{print $3}'|sort -n|$AWK 'BEGIN{i=400}$1>i{exit}{i=$1+1}END{print i}')
      $ECHO "New ID: $gid"
   fi
   $GROUPADD -g $gid $group
   if [ $? -ne 0 ]; then
      $ECHO "ERROR: Problems creating group $group!"
      exit 1
   fi
   return 0
}

#---------------------------------< MAIN >---------------------------------

SCRIPT_NAME=$(basename $0)
cd $(dirname $0)
SCRIPT_HOME=$(dirname $(/usr/bin/pwd))
HOME=$SCRIPT_HOME/home
[ ! -d $HOME ] && mkdir -p $HOME
INST_TIME=$($DATE "+%Y%m%d.%H:%M:%S")
OUT=create_nas_users_${INST_TIME}.log
[ -d $SCRIPT_HOME/log ] && OUT=$SCRIPT_HOME/log/$OUT
$ECHO "### Log file: $OUT"
>$OUT
link=$(dirname $OUT)/create_nas_users.log
[ -h $link -o -f $link ] && rm $link
ln -s $OUT $link

main()
{
create_group storage 206 || exit 1

$CHMOD 775 $SCRIPT_HOME $SCRIPT_HOME/etc $SCRIPT_HOME/plugins/nas/etc
   if [ $? -ne 0 ]; then
      $ECHO "ERROR: Problem changing permissions for $SCRIPT_HOME or it's sub-directories"
      exit 1
   fi

$CHGRP storage $SCRIPT_HOME $SCRIPT_HOME/etc $SCRIPT_HOME/plugins/nas/etc
   if [ $? -ne 0 ]; then
      $ECHO "ERROR: Problem changing ownership for $SCRIPT_HOME or it's sub-directories"
      exit 1
   fi

create_user storadm 309 storage Storage Manager Admin || exit 1

## checking if password history file exists and removing respective entries for NAS users if any
$LS /etc/security/opasswd &&  hist=`$GREP -w "storadm" /etc/security/opasswd`
if [ $? -eq 0 ] &&  [ -n "$hist" ] ; then
   $SED -e '/storadm/d' /etc/security/opasswd >/tmp/opasswd.tmp
   $CHMOD 600 /etc/security/opasswd && $MV /tmp/opasswd.tmp /etc/security/opasswd
   [ $? -eq 0 ] && $CHMOD 400 /etc/security/opasswd
   if [ $? -ne 0 ]; then
      $ECHO "ERROR: Problem in deleting password history for NAS users"
      exit 1
   fi
fi

set_pw storadm $SAPASSWD || exit 1

$ECHO -e "-----< SCRIPT TERMINATED SUCCESSFULLY >------"
}

main 2>&1 | tee -a $OUT

