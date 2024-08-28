#!bin/bash
set -e
usage ()
{
        echo ""
        echo  "Usage: $cmd [-thx] -r Rstate -m Module -p source-code-path
        er -S sms_signum" 1>&2
        echo ""
        printf "  -r Rstate of Module"
        printf "  -m Module name"
        printf "  -p Source path"
        echo ""
        exit 1
}


while getopts r:m:p: opt;do
        case $opt in
            r) Rstate=$OPTARG
               ;;
            m) Module=$OPTARG
               ;;
            p) Spath=$OPTARG
               ;;
        esac
done
shift `expr $OPTIND - 1`
[ "$Rstate" != "" ] || usage
[ "${Module}" != "" ] || usage
[ "${Spath}" != "" ] || usage

chmod 777 eniq_infra_tools/bin/build_INFRA_CI_rpm
if [ "$Module" == "storage" ]
then
        perl eniq_infra_tools/bin/build_INFRA_CI_rpm -r $Rstate -m ERICstmapi -p $Spath	
	perl eniq_infra_tools/bin/build_INFRA_CI_rpm -r $Rstate -m ERICstmnas -p $Spath
        perl eniq_infra_tools/bin/build_INFRA_CI_rpm -r $Rstate -m ERICstorapi -p $Spath
#	perl eniq_infra_tools/bin/build_INFRA_CI_rpm -r $Rstate -m ERICmigration -p $Spath
	        mkdir -p rpm_files
		cp -r eniq_infra_delivery/ERICstmapi/RPMS/ERICstmapi-$Rstate.rpm rpm_files/
		cp -r eniq_infra_delivery/ERICstmnas/RPMS/ERICstmnas-$Rstate.rpm rpm_files/
		cp -r eniq_infra_delivery/ERICstorapi/RPMS/ERICstorapi-$Rstate.rpm rpm_files/
#                cp -r eniq_infra_delivery/ERICmigration/RPMS/ERICmigration-$Rstate.rpm rpm_files/		
		cd om_linux/storage
		rm -rf *.rpm
		cp -r ../../eniq_infra_delivery/ERICstmapi/RPMS/ERICstmapi-$Rstate.rpm .
		cp -r ../../eniq_infra_delivery/ERICstmnas/RPMS/ERICstmnas-$Rstate.rpm .
		cp -r ../../eniq_infra_delivery/ERICstorapi/RPMS/ERICstorapi-$Rstate.rpm .
#		cp -r ../../eniq_infra_delivery/ERICmigration/RPMS/ERICmigration-$Rstate.rpm .
		sed -i "s/Rev/$Rstate/g" cxp_info ; 
		tar -cvf storage_$Rstate.tar ../storage
		gzip storage_$Rstate.tar
		mkdir -p "$Spath/tar_files"
		cp -r storage_$Rstate.tar.gz "$Spath/tar_files"
				
elif [ "$Module" == "omtools" ]
then
		perl eniq_infra_tools/bin/build_INFRA_CI_rpm -r $Rstate -m ERICkickstart -p $Spath
		mkdir -p rpm_files
		cp -r eniq_infra_delivery/ERICkickstart/RPMS/ERICkickstart-$Rstate.rpm rpm_files/
		cd om_linux/omtools
		sed -i "s/Rev/$Rstate/g" cxp_info
		cd eric_kickstart
		rm -rf *.rpm
		cp -r ../../../eniq_infra_delivery/ERICkickstart/RPMS/ERICkickstart-$Rstate.rpm .
		tar -cvf omtools_$Rstate.tar ../../omtools
		gzip omtools_$Rstate.tar
		mkdir -p "$Spath/tar_files"
		cp -r omtools_$Rstate.tar.gz "$Spath/tar_files"
		
elif [ "$Module" == "security" ]	
then
		perl eniq_infra_tools/bin/build_INFRA_CI_rpm -r $Rstate -m ERICnodehardening -p $Spath
		mkdir -p rpm_files
		cp -r eniq_infra_delivery/ERICnodehardening/RPMS/ERICnodehardening-$Rstate.rpm rpm_files/
		cd om_linux/security
		rm -rf *.rpm
		sed -i "s/Rev/$Rstate/g" cxp_info
		cp -r ../../eniq_infra_delivery/ERICnodehardening/RPMS/ERICnodehardening-$Rstate.rpm .
		tar -cvf security_$Rstate.tar ../security
		gzip security_$Rstate.tar
		mkdir -p "$Spath/tar_files"
		cp -r security_$Rstate.tar.gz "$Spath/tar_files"

elif [ "$Module" == "bootstrap" ]
then
		cd om_linux/bootstrap
		sed -i "s/Rev/$Rstate/g" cxp_info
		tar -cvf bootstrap_$Rstate.tar ../bootstrap
		gzip bootstrap_$Rstate.tar
		mkdir -p "$Spath/tar_files"
		cp -r bootstrap_$Rstate.tar.gz "$Spath/tar_files"
		
elif [ "$Module" == "EMC" ]
then
		cd om_linux/EMC
		sed -i "s/Rev/$Rstate/g" cxp_info
		#createrepo "$Spath"./om_linux/EMC/x86_64
		createrepo "$Spath"./om_linux/EMC
		tar -cvf EMC_$Rstate.tar ../EMC
		gzip EMC_$Rstate.tar
		mkdir -p "$Spath/tar_files"
		cp -r EMC_$Rstate.tar.gz "$Spath/tar_files"

elif [ "$Module" == "HWcomm" ]
then
		cd om_linux/HWcomm
		sed -i "s/Rev/$Rstate/g" cxp_info
		#createrepo "$Spath"./om_linux/HWcomm
		tar -cvf HWcomm_$Rstate.tar ../HWcomm
		gzip HWcomm_$Rstate.tar
		mkdir -p "$Spath/tar_files"
		cp -r HWcomm_$Rstate.tar.gz "$Spath/tar_files"
		
elif [ "$Module" == "patch" ]
then
		cd om_linux/patch
		sed -i "s/Rev/$Rstate/g" cxp_info
		tar -cvf patch_$Rstate.tar ../patch
		gzip patch_$Rstate.tar
		mkdir -p "$Spath/tar_files"
		cp -r patch_$Rstate.tar.gz "$Spath/tar_files"

elif [ "$Module" == "blade" ]
then
                cd om_linux/blade
                sed -i "s/Rev/$Rstate/g" cxp_info
                #createrepo /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/om_linux/blade
                tar -cvf blade_$Rstate.tar ../blade
                gzip blade_$Rstate.tar
		mkdir -p "$Spath/tar_files"
                #mkdir -p /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
                #cp -r blade_$Rstate.tar.gz /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
                cp -r blade_$Rstate.tar.gz "$Spath/tar_files" 
		
else
		echo "Invalid Module Name Provided....!!!!!!!!!!!!!"
		false

fi	
