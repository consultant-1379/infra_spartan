#!/usr/bin/bash

LOGFILE=logfile4_cleartext.$(date +%F_%R)
exec 2> /tmp/log.txt

if [ ! -d /ericsson/security/bin/ ]; then

  if [ ! -f /ericsson/storage/etc/sourcefile ]; then

    gpg /ericsson/storage/etc/sourcefile.gpg

      if [ -f /ericsson/storage/etc/sourcefile ]; then

        echo $(date -u) : "decryption done" >> /ericsson/storage/etc/$LOGFILE

      fi
  fi
else

  if [ -d /root/.gnupg/ ]; then
   
    if [ -f /root/.gnupg/trustdb.gpg ]; then
  
      if [ ! -f /ericsson/storage/etc/sourcefile ]; then
  
        gpg /ericsson/storage/etc/sourcefile.gpg

        if [ -f /ericsson/storage/etc/sourcefile ]; then
          
          echo $(date -u) : "decryption done" >> /ericsson/storage/etc/$LOGFILE
        else
      
          echo -e  "Decryption did not happend due to some reason, check the conf-files, logs for more details.\n"
          echo $(date -u) : "decryption not happend, check the keys are available(/root/.gnupg/), /ericsson/storage/etc/sourcefile.gpg exists" >> /ericsson/storage/etc/$LOGFILE

        fi
      fi
    else
      
      echo -e " No keys are available to decrypt/GPG key been removed. Check and restore the backed up keys to proceed decryption\n"  
      echo $(date -u) : "gpg keys are removed/not available" >> /ericsson/storage/etc/$LOGFILE 
    fi
  else
   
    echo -e "GPG key directory is not available to decrypt, Check and restore the backed up directory to proceed decryption\n"i
    echo $(date -u) : "gpg key directory is removed/not available" >> /ericsson/storage/etc/$LOGFILE

  fi
fi
rm -rf /tmp/logfile.txt

