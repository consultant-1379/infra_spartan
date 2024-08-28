#!/bin/bash

# Red Hat Linux Patch Script

# ********************************************************************
# Ericsson Radio Systems AB                                     SCRIPT
# ********************************************************************
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
# Name    : rollback_script.sh
# Date    : 31/03/2019
# Revision: A
# Purpose : This script is to rollback the LVM snapshot and Kernel to
#           previous version if required.
#
#
# Version Information:
#       Version Who             Date            Comment
#       0.1     zsmrsmr         31/03/2019      Initial draft
#
#
# ********************************************************************

##'Mount_root_fs' function will verify the /boot /boot/efi /var, /home, /tmp, /var/log & /var/tmp mounte point moints and mount the same.

Mount_root_fs()
{

echo "Checking system mount points status"
mount_points=(/boot/efi /boot /var /home /tmp /var/tmp /var/log)

for i in "${mount_points[@]}"
do
echo $i
mountpoint -q $i
if [[ $? == 0 ]]
then
        echo "$i already mounted"
else

if [ ! -d /sys/firmware/efi ]; then
        if [ $i == "/boot" ] ; then
                 echo "$i is not mounted"
                 echo " "
                 echo "mounting of $i"
                 mount /dev/sda1 $i
         elif [ $i != "/boot/efi" ]; then
                if [[ "$i" == "/home" ]] || [[ "$i" == "/tmp" ]] || [[ "$i" == "/var/tmp" ]] || [[ "$i" == "/var/log" ]] ; then
                  	echo "/n "
		else
                  	echo "$i is not mounted" 
                  	echo " "
                  	echo "mounting of $i"
                  	mount $i
                fi
         else
                 echo "Already mounted"
         fi
else

        if [ $i == "/boot/efi" ] ; then
                 echo "$i is not mounted"
                 echo " "
                 echo "mounting of $i"
                 mount /dev/sda1 $i
        elif [ $i == "/boot" ]; then
                 echo "$i is not mounted"
                 echo " "
                 echo "mounting of $i"
                 mount /dev/sda2 $i
        else
                 echo "$i is not mounted"
                 echo " "
                 echo "mounting $i"
                 mount $i
        fi

fi
fi
done

}

##'lvm_rollback' function will merge the LVM snapshot to old release or configuration.

lvm_rollback() {
echo "---Snapshot_rollback---"

        ROOTSNAP_VG=`lvs | grep -iw rootsnap | awk '{print $2}'`

        VARSNAP_VG=`lvs | grep -iw varsnap | awk '{print $2}'`

        if [ -d /sys/firmware/efi ]; then

                HOMESNAP_VG=`lvs | grep -iw homesnap | awk '{print $2}'`

                VARTMPSNAP_VG=`lvs | grep -iw vartmpsnap | awk '{print $2}'`

                VARLOGSNAP_VG=`lvs | grep -iw varlogsnap | awk '{print $2}'`

        else

		 echo " \n "
	fi


        lvconvert --merge $ROOTSNAP_VG/rootsnap

                                sleep 3

        lvconvert --merge $VARSNAP_VG/varsnap

                                sleep 3

        if [ -d /sys/firmware/efi ]; then

                lvconvert --merge $HOMESNAP_VG/homesnap

                                sleep 3

                lvconvert --merge $VARTMPSNAP_VG/vartmpsnap

                                sleep 3

                lvconvert --merge $VARLOGSNAP_VG/varlogsnap

                                sleep 3

        else

		echo " \n "
        fi


}

#Function to replace /boot with old kernel files.

boot_replace()
{
  if [ ! -d /sys/firmware/efi ]; then
               rm -rf /boot/{*,.vm*}
               cp -r /var/tmp/.bkp_boot/. /boot
               sleep 3
      grub2-mkconfig -o /boot/grub2/grub.cfg > /var/grub_build_rollback 2>&1
  else
    cd /boot; rm -rf `ls -a| grep -v '^efi$'` > /var/grub_build_rollback 2>&1
    cp -r /var/tmp/.bkp_boot/. /boot
    sleep 3
      grub2-mkconfig -o /boot/efi/EFI/redhat/grub.cfg  >> /var/grub_build_rollback 2>&1
  fi               
 
}


Mount_root_fs
lvm_rollback
boot_replace
echo "Rollback is done"
