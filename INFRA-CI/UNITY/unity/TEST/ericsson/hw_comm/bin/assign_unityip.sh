#!/bin/bash
AWK=/usr/bin/awk
BASENAME=/usr/bin/basename
CAT=/usr/bin/cat
CP=/usr/bin/cp
ECHO=/usr/bin/echo
EGREP=/usr/bin/egrep
#EGREP=/usr/xpg4/bin/egrep
GREP=/usr/bin/grep
GGREP=/usr/bin/ggrep
HEAD=/usr/bin/head
IPADM=/usr/sbin/ipadm
#IPCALC=/bin/ipcalc
LOGDIR=/var/log/Unity.$$
LOG=${LOGDIR}/initialise_log.txt
MKDIR=/usr/bin/mkdir
MV=/usr/bin/mv
#PIDOF=/sbin/pidof
PING=/usr/sbin/ping
PRINTF=/usr/bin/printf
PS=/usr/bin/ps
SED=/usr/bin/sed
SVCADM=/usr/sbin/svcadm
TCPDUMP=/usr/sbin/tcpdump
TIMEOUT=/usr/bin/timeout
TEE=/usr/bin/tee
TR=/usr/bin/tr
UEMCLI="/usr/bin/uemcli -noheader"
#RHELVERSION="6"
SOLARISVERSION="11.3"
U_DEFAULT_PW="Password123#"
# Files
dhcpd_conf=/etc/inet/dhcpd4.conf
#dhcpd_file=/etc/sysconfig/dhcpd
tcpdump_out=${LOGDIR}/tcpdump_out
unityip_out=${LOGDIR}/unityip_out

info_and_log(){
    $ECHO  "INFO: $1" | $TEE -a $LOG 2>&1
}
warn_and_log(){
    $ECHO  "WARNING: $1" | $TEE -a $LOG 2>&1
}
exitwitherror(){
    $ECHO  "$($PRINTF '=%.0s' {1..108})\nERROR: $1. \nERROR: Please fix any issues and re-run the script or run with '-h' option for usage information.\n$($PRINTF '=%.0s' {1..108})" | $TEE -a $LOG 2>&            1
    info_and_log "Exiting script. Please see logfile $LOG"
    exit 1
}
cmd_logonly(){
    $1>>$LOG 2>&1
}

usage() {
$CAT << EOF
    ------------------
    USAGE INFORMATION
    ------------------

    Description: Assign an IP to Unity from the Management Server using DHCP

    Command Examples:
          # $0 -f <input_file>
          # $0 -h
          # $0 -H


    Command Arguments:
          -f <input_file>   Mandatory file passed into the script
          -h|-H             Display this usage information


    Input File:
          For ENM, <input_file>  =>  ENM SED
          Fill in the following mandatory parameters:
                Parameter           Example
                ----------------------------------
                san_spaIP           10.10.10.10
                san_serial          CKM01234567890
                storage_subnet      10.10.10.0/23
                LMS_IP_storage      10.10.10.11


          For ENIQ, <input_file>  =>  /var/tmp/eniq_hw_template
          Fill in these mandatory parameters:
                Parameter           Example
                ----------------------------------
                san_ip              10.10.10.10
                san_serial          CKM01234567890
                storage_subnet      10.10.10.0/23
                MS_IP_storage       10.10.10.11


EOF
exit 0
}

validate_ip(){
    # Validate that the value given is in a valid IPv4 format
    ip=$1
    type=$2
    info_and_log "Verifying $type IP address $ip"
    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        OIFS=$IFS
        IFS='.'
        iparray=($ip)
        IFS=$OIFS
        [[ ${iparray[0]} -le 255 && ${iparray[1]} -le 255 && ${iparray[2]} -le 255 && ${iparray[3]} -le 255 ]]
        [ $? -eq 0 ] && info_and_log "$ip is a valid IP address" || exitwitherror "$ip is not a valid IP address"
    else
        exitwitherror "$ip is not a valid IP address"
    fi
}
validate_serial(){
    # Validate that this is an EMC serial
    serial=$1
    info_and_log "Verifying Unity Serial $serial"
    s=$($ECHO $serial | $SED 's/CKM//')
    [ ${#s} -eq 11 ] && [[ "$s" =~ ^[0-9]+$ ]] && info_and_log "$serial is a valid serial" || exitwitherror "$serial is not a valid EMC serial number"
}
validate_storage_subnet(){
    # Validate that the storage subnet value is as expected
    sub=$1
    info_and_log "Verifying storage subnet $sub"
    if [[ $sub =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/[0-9]{1,2}$ ]]; then
        info_and_log "$sub has the correct format."
    else
        exitwitherror "$sub does not have the correct format"
    fi
}
validate_mac(){
    mac=$1
    info_and_log "Verifying Unity MAC Address $mac"
    if [[ "$mac" =~ ^[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}$ ]]; then
        info_and_log "$mac is a valid MAC address"
    else
        exitwitherror "$mac is not a valid MAC address"
    fi
}
process_inputfile(){
   # Take in and verify Unity File
   $EGREP -se "san_ip|san_spaIP" $UNITY_FILE  || exitwitherror "The parameter for the SAN IP is missing from $UNITY_FILE"
   unity_ip=$($EGREP -e "san_ip|san_spaIP" $UNITY_FILE | $AWK -F= '{print $2}' | $TR -d '\r')
   [ -z "$unity_ip" ] && exitwitherror "The value for the SAN IP is missing from $UNITY_FILE"
   validate_ip $unity_ip "Unity"
   info_and_log "Verifying that the Unity IP is not in use"
   $PING -c 1 -t 1 $unity_ip >/dev/null 2>&1 && exitwitherror "$unity_ip is already in use" || info_and_log "$unity_ip is not pingable"

   $GREP -qw san_serial $UNITY_FILE || exitwitherror "The parameter san_serial is missing from $UNITY_FILE"
   unity_serial=$($GREP -w san_serial $UNITY_FILE | $AWK -F= '{print $2}' | $TR -d '\r')
   [ -z "$unity_serial" ] && exitwitherror "The value for san_serial is missing from $UNITY_FILE"
   validate_serial $unity_serial

   $GREP -qw storage_subnet $UNITY_FILE || exitwitherror "The parameter storage_subnet is missing from $UNITY_FILE"
   storage_subnet=$($GREP storage_subnet $UNITY_FILE | $AWK -F= '{print $2}' | $TR -d '\r')
   [ -z "$storage_subnet" ] && exitwitherror "The value for storage_subnet is missing from $UNITY_FILE"
   validate_storage_subnet $storage_subnet
   storage_subnet_ip=$($ECHO $storage_subnet | $SED "s/\/.*//")
   #storage_netmask=$($IPCALC -m $storage_subnet | $SED 's/.*=//')
   storage_subnet_ip=$($ECHO $storage_subnet | $SED "s/\/.*//")
   subnet_value=`$ECHO $storage_subnet | $AWK -F'/' '{print $2}'`

case $subnet_value in
        1) net_ip=128.0.0.0
                ;;
        2) net_ip=192.0.0.0
                ;;
        3) net_ip=224.0.0.0
                ;;
        4) net_ip=240.0.0.0
                ;;
        5) net_ip=248.0.0.0
                ;;
        6) net_ip=252.0.0.0
                ;;
        7) net_ip=254.0.0.0
                ;;
        8) net_ip=255.0.0.0
                ;;
        9) net_ip=255.128.0.0
                ;;
        10) net_ip=255.192.0.0
                ;;
        11) net_ip=255.224.0.0
                ;;
        12) net_ip=255.240.0.0
                ;;
        13) net_ip=255.248.0.0
                ;;
        14) net_ip=255.252.0.0
                ;;
        15) net_ip=255.254.0.0
                ;;
        16) net_ip=255.255.0.0
                ;;
        17) net_ip=255.255.128.0
                ;;
        18) net_ip=255.255.192.0
                ;;
        19) net_ip=255.255.224.0
                ;;
        20) net_ip=255.255.240.0
                ;;
        21) net_ip=255.255.248.0
                ;;
        22) net_ip=255.255.252.0
                ;;
        23) net_ip=255.255.254.0
                ;;
        24) net_ip=255.255.255.0
                ;;
        25) net_ip=255.255.255.128
                ;;
        26) net_ip=255.255.255.192
                ;;
        27) net_ip=255.255.255.224
                ;;
        28) net_ip=255.255.255.240
                ;;
        29) net_ip=255.255.255.248
                ;;
        30) net_ip=255.255.255.252
                ;;
        31) net_ip=255.255.255.254
                ;;
        32) net_ip=255.255.255.255
                ;;
        *) RESULT=1
                exitwitherror "$subnet_value is not a valid subnet"
                ;;
esac

   storage_netmask=$net_ip
   info_and_log "$storage_subnet is made up of IP $storage_subnet_ip and netmask $storage_netmask"
   validate_ip $storage_subnet_ip "Subnet"
   validate_ip $storage_netmask "Netmask"

   $EGREP -se "LMS_IP_storage|MS_IP_storage" $UNITY_FILE || exitwitherror "The parameter for the MS storage IP is missing from $UNITY_FILE"
   lms_ip_storage=$($EGREP -e "LMS_IP_storage|MS_IP_storage" $UNITY_FILE | $AWK -F= '{print $2}' | $TR -d '\r')
   [ -z "$lms_ip_storage" ] && exitwitherror "The value for the MS storage IP is missing from $UNITY_FILE"
   validate_ip $lms_ip_storage "Storage"
   info_and_log "Verifying that the Storage IP $lms_ip_storage is plumbed here"
   $IPADM show-addr  | $GREP -q $lms_ip_storage && {
                                                 lms_dev_storage=$($IPADM show-addr | $GREP $lms_ip_storage | $AWK -F'/' '{print $1}')
                                                 info_and_log "$lms_ip_storage is plumbed on interface $lms_dev_storage"
                                               } || exitwitherror "The IP Address supplied(${lms_ip_storage}) does not appear to be plumbed on the MS"
}
verify_uemcli(){
   # Verify uemcli is installed and set security verification level to low 
   info_and_log "Verifying that uemcli is installed and setting security verification level to low"
   [ -f /opt/emc/uemcli-*/bin/uemcli.sh ] && info_and_log "Uemcli is installed" || exitwitherror "Uemcli is not installed"
   cmd_logonly "/opt/emc/uemcli-*/bin/uemcli.sh --securityLevel low" && info_and_log "Uemcli verification level is low" || exitwitherror "Failed to set Uemcli verification level"
}
run_tcpdump(){
   # Get Serial and MAC of Unity from tcpdump
   info_and_log "Checking for DHCP traffic on the storage interface[${lms_dev_storage}]. Please wait."
   for i in {1..3}; do
      info_and_log "Checking all DHCP requests over a 60 second period (Attempt ${i})..."
      $TIMEOUT 60 $TCPDUMP -ni $lms_dev_storage -c 33 port 67 or port 68 -n -v > $tcpdump_out 2>&1
      $GREP -q "Hostname Option.*CKM" $tcpdump_out && break || warn_and_log "No incoming DHCP request from the Unity array."
   done
   $GREP -q "Hostname Option.*CKM" $tcpdump_out || exitwitherror "No Unity array detected. Verify that Unity has power and is on this storage VLAN"
   u_serial=$($GREP "Hostname Option.*CKM" $tcpdump_out | $HEAD -n 1 | $AWK '{print $NF}' | $SED 's/"//g')
   u_mac=$($EGREP "Client-Ethernet-Address|Hostname Option.*CKM" $tcpdump_out | $GGREP -B1 "Hostname Option.*${u_serial}" | $HEAD -n 1 | $AWK '/Client-Ethernet-Address/ {print $NF}')
   info_and_log "Unity found with serial $u_serial and MAC $u_mac"
   validate_serial $u_serial
   validate_mac $u_mac

   # Check the serial from tcpdump against the serial in the input file
   [ "$u_serial" = "$unity_serial" ] && info_and_log "Unity serial matches the expected serial(${unity_serial})" || exitwitherror "Unity serial from tcpdump (${u_serial}) does not match the serial in input file(${unity_serial})"
}
backup_dhcp(){
   # Backup DHCP files
   info_and_log "Backing up DHCP files."
   [ -f $dhcpd_conf ] && $CP -f $dhcpd_conf ${dhcpd_conf}.preUnity
}
modify_dhcp(){
   # Modify DHCP Files
   info_and_log "Modifying DHCP files."
   $CAT << EOF > $dhcpd_conf
subnet $storage_subnet_ip netmask $storage_netmask {
     option routers             $lms_ip_storage;
     option subnet-mask         $storage_netmask;
     default-lease-time         1800;
     max-lease-time             1800;
}
host unity {
     hardware ethernet $u_mac;
     fixed-address $unity_ip;
}
EOF
   info_and_log "The file ${dhcpd_conf} has been modified as follows:"
   $CAT $dhcpd_conf | $TEE -a $LOG
   restart_dhcp "Please check the values in the input file"
}
restart_dhcp(){
   failmsg=$1
   info_and_log "Restarting the DHCP service..."
   cmd_logonly "$SVCADM restart /network/dhcp/server:ipv4" || exitwitherror "Failed to restart DHCPD service. ${failmsg}"
}
uemcli_assignip(){
   info_and_log "Waiting for Unity to be assigned an IP..."
   for i in {1..6}; do
      sleep 30
      info_and_log "Running: $UEMCLI -d $unity_ip -u admin -p <password> /net/if/mgmt show -detail"
      $UEMCLI -d $unity_ip -u admin -p $U_DEFAULT_PW /net/if/mgmt show -detail > $unityip_out 2>&1
      $GREP -q "MAC address" $unityip_out && break || warn_and_log "No IP assigned to the Unity array. Retrying..."
   done
   $GREP -q "MAC address" $unityip_out || {
                                            revert_dhcp
                                            exitwitherror "Failed to assign an IP to the Unity array"
                                          }
   info_and_log "The following IP is assigned to the Unity array:"
   $CAT $unityip_out | $TEE -a $LOG 2>&1
}
revert_dhcp(){
   info_and_log "Reverting DHCP file changes..."
   $CP -f ${dhcpd_conf}.preUnity $dhcpd_conf
   restart_dhcp "Please verify the file ${dhcpd_conf}.preUnity has been restored"
}


# Main #
[ $# -eq 0 ] || [ $# -gt 2 ] && usage
case $1 in
   -f|-h|-H) : ;;
   *) $ECHO  "\n    ERROR: Incorrect script usage.\n" ; usage ;;
esac
while getopts ":f:hH" opt; do
   case $opt in
      f) UNITY_FILE=$OPTARG ; [ -f $UNITY_FILE ] || {
                                                      $ECHO  "\n    ERROR: $UNITY_FILE is not a valid file.\n"
                                                      usage
                                                    } ;;
      h) usage ;;
      H) usage ;;
      \?) $ECHO  "\n    ERROR: Unknown option: \"-$OPTARG\"\n" ; usage ;;
      :) $ECHO  "\n    ERROR: Missing argument for \"-$OPTARG\"\n" ; usage ;;
   esac
done

$MKDIR -p $LOGDIR
info_and_log "Logging to ${LOG}"
info_and_log "Running with ARGS:[$*]"
$PS -ef | grep init > /dev/null
[ $? -eq 0 ] && SOLARISVERSION="11.3"


# Steps
process_inputfile

verify_uemcli

run_tcpdump

backup_dhcp

modify_dhcp

uemcli_assignip

revert_dhcp

info_and_log "Finished. Please see logfile $LOG"
