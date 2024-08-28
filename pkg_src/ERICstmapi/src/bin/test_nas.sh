#!/usr/bin/bash
HOME_PATH=/ericsson/storage
BIN_PATH=$HOME_PATH/bin
STORAGE_INI=/ericsson/config/storage.ini
[ ! -f $STORAGE_INI -a -d /eniq ] && STORAGE_INI=/eniq/installation/config/storage.ini
SYS_ID=$(awk -F= '$1=="SYS_ID"{print $2;exit}' $STORAGE_INI)
[ "$SYS_ID" = "" ] && SYS_ID=testid
mnt=/tmp/testmnt
[ ! -d $mnt ] && mkdir $mnt

printf "\nName of test FS: "
read testfs

printf "\nCreate (y/n): "
read ans
if [ "$ans" = "y" ]; then
   $BIN_PATH/nascli create_fs - 1g - ${testfs}
   $BIN_PATH/nascli create_share - rw,no_root_squash ${testfs}
   if [ "$($BIN_PATH/nascli list_cache -)" = "" ]; then
      echo "### Creating snapshot-cache (should normally exist if DMR/SCT have been used) ###\n"
      touch $HOME_PATH/etc/test-cache
      $BIN_PATH/nascli create_cache - 5g - -
   fi
   $BIN_PATH/nascli create_snapshot - optim - snap1 ${testfs}
   $BIN_PATH/nascli create_share - rw,no_root_squash ${testfs}/snap1
   printf "\n$SYS_ID/${testfs}/snap1 uses KB: "
   $BIN_PATH/nascli list_snapshots usage $SYS_ID/${testfs}/snap1
   share=$($BIN_PATH/nascli get_share - ${testfs})
   if [ "$share" != "" ]; then
      umount $mnt 2>/dev/null
      mount -t nfs nas1:$share $mnt
      if [ $? -eq 0 ]; then
         dd if=/dev/zero of=$mnt/100m-file bs=1024K count=100 2>/dev/null
      fi
      printf "\n$SYS_ID/${testfs}/snap1 uses KB: "
      $BIN_PATH/nascli list_snapshots usage $SYS_ID/${testfs}/snap1
   fi
   $BIN_PATH/nascli create_snapshot - optim - snap2 ${testfs}
   $BIN_PATH/nascli add_client - 111.111.111.111 rw,no_root_squash ${testfs}/snap2
   $BIN_PATH/nascli rollback_snapshot - snap2 ${testfs}
   $BIN_PATH/nascli refresh_snapshot - snap2 ${testfs}
fi

printf "\nDelete (y/n): "
read ans
if [ "$ans" = "y" ]; then
   umount $mnt 2>/dev/null
   $BIN_PATH/nascli delete_fs - ${testfs}
   if [ "$($BIN_PATH/nascli le -)" != "" -a -f $HOME_PATH/etc/test-cache ]; then
      $BIN_PATH/nascli delete_cache - -
      [ $? -eq 0 ] && rm $HOME_PATH/etc/test-cache
   fi
fi
