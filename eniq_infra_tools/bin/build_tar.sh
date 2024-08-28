#!bin/bash
set -e
usage ()
{
        echo ""
        echo  "Usage: $cmd [-thx] -r Rstate -m Module
        er -S sms_signum" 1>&2
        echo ""
        printf "  -r Rstate of Module"
        printf "  -m Module name"
        echo ""
        exit 1
}


while getopts r:m: opt;do
        case $opt in
            r) Rstate=$OPTARG
               ;;
            m) Module=$OPTARG
               ;;
        esac
done
shift `expr $OPTIND - 1`
[ "$Rstate" != "" ] || usage
[ "${Module}" != "" ] || usage

chmod 777 eniq_infra_tools/bin/build_rpm
if [ "$Module" == "storage" ]
then
        perl eniq_infra_tools/bin/build_rpm -r $Rstate -m ERICstmapi		
	perl eniq_infra_tools/bin/build_rpm -r $Rstate -m ERICstmnas
        perl eniq_infra_tools/bin/build_rpm -r $Rstate -m ERICstorapi
#	perl eniq_infra_tools/bin/build_rpm -r $Rstate -m ERICmigration
	        mkdir rpm_files
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
		mkdir -p /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
		cp -r storage_$Rstate.tar.gz /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
				
elif [ "$Module" == "omtools" ]
then
		perl eniq_infra_tools/bin/build_rpm -r $Rstate -m ERICkickstart
		mkdir rpm_files
		cp -r eniq_infra_delivery/ERICkickstart/RPMS/ERICkickstart-$Rstate.rpm rpm_files/
		cd om_linux/omtools
		sed -i "s/Rev/$Rstate/g" cxp_info
		cd eric_kickstart
		rm -rf *.rpm
		cp -r ../../../eniq_infra_delivery/ERICkickstart/RPMS/ERICkickstart-$Rstate.rpm .
		tar -cvf omtools_$Rstate.tar ../../omtools
		gzip omtools_$Rstate.tar
		mkdir -p /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
		cp -r omtools_$Rstate.tar.gz /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files

elif [ "$Module" == "sanconfig" ]
then
		perl eniq_infra_tools/bin/build_rpm -r $Rstate -m ERICstorconfig
		mkdir rpm_files
		cp -r eniq_infra_delivery/ERICstorconfig/RPMS/ERICstorconfig-$Rstate.rpm rpm_files/
		cd om_linux/sanconfig
		rm -rf *.rpm
		sed -i "s/Rev/$Rstate/g" cxp_info
		cp -r ../../eniq_infra_delivery/ERICstorconfig/RPMS/ERICstorconfig-$Rstate.rpm .
		tar -cvf sanconfig_$Rstate.tar ../sanconfig
		gzip sanconfig_$Rstate.tar
		mkdir -p /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
		cp -r sanconfig_$Rstate.tar.gz /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
		
elif [ "$Module" == "security" ]	
then
		perl eniq_infra_tools/bin/build_rpm -r $Rstate -m ERICnodehardening
		mkdir rpm_files
		cp -r eniq_infra_delivery/ERICnodehardening/RPMS/ERICnodehardening-$Rstate.rpm rpm_files/
		cd om_linux/security
		rm -rf *.rpm
		sed -i "s/Rev/$Rstate/g" cxp_info
		cp -r ../../eniq_infra_delivery/ERICnodehardening/RPMS/ERICnodehardening-$Rstate.rpm .
		tar -cvf security_$Rstate.tar ../security
		gzip security_$Rstate.tar
		mkdir -p /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
		cp -r security_$Rstate.tar.gz /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files

elif [ "$Module" == "bootstrap" ]
then
		cd om_linux/bootstrap
		sed -i "s/Rev/$Rstate/g" cxp_info
		tar -cvf bootstrap_$Rstate.tar ../bootstrap
		gzip bootstrap_$Rstate.tar
		mkdir -p /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
		cp -r bootstrap_$Rstate.tar.gz /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
		
elif [ "$Module" == "EMC" ]
then
		cd om_linux/EMC
		sed -i "s/Rev/$Rstate/g" cxp_info
		#createrepo /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/om_linux/EMC/x86_64
#		createrepo /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/om_linux/EMC/
		tar -cvf EMC_$Rstate.tar ../EMC
		gzip EMC_$Rstate.tar
		mkdir -p /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
		cp -r EMC_$Rstate.tar.gz /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files

elif [ "$Module" == "HWcomm" ]
then
		cd om_linux/HWcomm
		sed -i "s/Rev/$Rstate/g" cxp_info
		#createrepo /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/om_linux/HWcomm
		tar -cvf HWcomm_$Rstate.tar ../HWcomm
		gzip HWcomm_$Rstate.tar
		mkdir -p /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
		cp -r HWcomm_$Rstate.tar.gz /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
		
elif [ "$Module" == "patch" ]
then
		cd om_linux/patch
		sed -i "s/Rev/$Rstate/g" cxp_info
		tar -cvf patch_$Rstate.tar ../patch
		gzip patch_$Rstate.tar
		mkdir -p /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
		cp -r patch_$Rstate.tar.gz /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files

elif [ "$Module" == "blade" ]
then
                cd om_linux/blade
                sed -i "s/Rev/$Rstate/g" cxp_info

                #createrepo /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/om_linux/blade
                tar -cvf blade_$Rstate.tar ../blade
                gzip blade_$Rstate.tar
                mkdir -p /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
                cp -r blade_$Rstate.tar.gz /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files


elif [ "$Module" == "sanconfig" ]
then
                perl eniq_infra_tools/bin/build_rpm -r $Rstate -m ERICstorconfig
		mkdir rpm_files
		cp -r eniq_infra_delivery/ERICstorconfig/RPMS/ERICstorconfig-$Rstate.rpm rpm_files/
		cd om_linux/sanconfig
		rm -rf *.rpm
		sed -i "s/Rev/$Rstate/g" cxp_info
		cp -r ../../eniq_infra_delivery/ERICstorconfig/RPMS/ERICstorconfig-$Rstate.rpm .
		tar -cvf sanconfig_$Rstate.tar ../sanconfig
		gzip sanconfig_$Rstate.tar
		mkdir -p /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
		cp -r sanconfig_$Rstate.tar.gz /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files

elif [ "$Module" == "mwshealthcheck" ]
then
                perl eniq_infra_tools/bin/build_rpm -r $Rstate -m ERICmwshealthcheck
                mkdir rpm_files
                cp -r eniq_infra_delivery/ERICmwshealthcheck/RPMS/ERICmwshealthcheck-$Rstate.rpm rpm_files/
                cd om_linux/mwshealthcheck
                rm -rf *.rpm
                sed -i "s/Rev/$Rstate/g" cxp_info
                cp -r ../../eniq_infra_delivery/ERICmwshealthcheck/RPMS/ERICmwshealthcheck-$Rstate.rpm .
                tar -cvf mwshealthcheck_$Rstate.tar ../mwshealthcheck
                gzip mwshealthcheck_$Rstate.tar
                mkdir -p /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
                cp -r mwshealthcheck_$Rstate.tar.gz /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files

elif [ "$Module" == "vaupgrade" ]
then
                cd om_linux/vaupgrade
                sed -i "s/Rev/$Rstate/g" cxp_info
                #createrepo /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/om_linux/vaupgrade
                tar -cvf vaupgrade_$Rstate.tar ../vaupgrade
                gzip vaupgrade_$Rstate.tar
                mkdir -p /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files
                cp -r vaupgrade_$Rstate.tar.gz /home/lciadm100/jenkins/workspace/INFRA_KGB_Build/tar_files

else
		echo "Invalid Module Name Provided....!!!!!!!!!!!!!"
		false

fi	
