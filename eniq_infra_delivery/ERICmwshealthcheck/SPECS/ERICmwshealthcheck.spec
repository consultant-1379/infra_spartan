################################################################
#
# This is ERICmwshealthcheck Product Spec File
#
###############################################################
%define CXP CXP9042747

###############################################################
Summary:    ERIC mwshealthcheck  package
Name:       ERICmwshealthcheck
Version: R8A
Release: 05
Group:      Ericsson/ENIQ_STATS
Packager:   ZAHAHIM
BuildRoot:  %{_builddir}/%{name}_%{CXP}-%{version}%{release}
License: Ericsson AB @2018
#################################################################

%define _rpmfilename %{name}-%{version}%{release}.rpm

%description
This the ERICmwshealthcheck RPM package

%prep
rm -rf %{buildroot}
# extract the tar file containing all the sources, to the build directory.
cd %{_sourcedir}
ls -lrt %{_sourcedir}/ERIC*
/bin/tar -xvf %{_sourcedir}/ERIC*.tar

%install
install -d -m 755 %{buildroot}/opt/ericsson/mwshealthcheck/
install -d -m 755 %{buildroot}/opt/ericsson/mwshealthcheck/bin/
install -d -m 755 %{buildroot}/opt/ericsson/mwshealthcheck/lib/

cd %{_sourcedir}/src/bin/
cp * %{buildroot}/opt/ericsson/mwshealthcheck/bin

cd %{_sourcedir}/src/lib/
cp * %{buildroot}/opt/ericsson/mwshealthcheck/lib

%files
%defattr(755,root,root)
##### bin files list
/opt/ericsson/mwshealthcheck/bin/mws_health_check.py
/opt/ericsson/mwshealthcheck/bin/mws_health_check_summary.py

###### lib files list
/opt/ericsson/mwshealthcheck/lib/mws_check_grub_cfg.py
/opt/ericsson/mwshealthcheck/lib/mws_disk_usage.py
/opt/ericsson/mwshealthcheck/lib/mws_package_repo.py
/opt/ericsson/mwshealthcheck/lib/mws_swap_details.py
/opt/ericsson/mwshealthcheck/lib/mws_verify_networking.py
/opt/ericsson/mwshealthcheck/lib/mws_check_kernel_index.py
/opt/ericsson/mwshealthcheck/lib/mws_inode_usage.py
/opt/ericsson/mwshealthcheck/lib/mws_verify_boot_modes.py
/opt/ericsson/mwshealthcheck/lib/mws_verify_volumes.py
/opt/ericsson/mwshealthcheck/lib/mws_check_services.py
/opt/ericsson/mwshealthcheck/lib/mws_load_average.py
/opt/ericsson/mwshealthcheck/lib/mws_processor_utilization.py
/opt/ericsson/mwshealthcheck/lib/mws_verify_firewall.py
/opt/ericsson/mwshealthcheck/lib/mws_check_time_sync.py
/opt/ericsson/mwshealthcheck/lib/mws_memory_utilization.py
/opt/ericsson/mwshealthcheck/lib/mws_reboot_status.py
/opt/ericsson/mwshealthcheck/lib/mws_verify_hw.py
/opt/ericsson/mwshealthcheck/lib/mws_cpu_utilization.py
/opt/ericsson/mwshealthcheck/lib/mws_nfs_details.py
/opt/ericsson/mwshealthcheck/lib/mws_shutdown_status.py
/opt/ericsson/mwshealthcheck/lib/mws_verify_kernel.py
%exclude /opt/ericsson/mwshealthcheck/lib/mws_check_grub_cfg.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_check_kernel_index.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_check_services.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_check_time_sync.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_cpu_utilization.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_disk_usage.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_inode_usage.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_load_average.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_memory_utilization.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_nfs_details.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_package_repo.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_processor_utilization.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_reboot_status.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_shutdown_status.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_swap_details.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_verify_boot_modes.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_verify_firewall.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_verify_hw.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_verify_kernel.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_verify_networking.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_verify_volumes.pyo
%exclude /opt/ericsson/mwshealthcheck/lib/mws_check_grub_cfg.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_check_kernel_index.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_check_services.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_check_time_sync.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_cpu_utilization.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_disk_usage.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_inode_usage.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_load_average.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_memory_utilization.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_nfs_details.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_package_repo.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_processor_utilization.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_reboot_status.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_shutdown_status.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_swap_details.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_verify_boot_modes.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_verify_firewall.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_verify_hw.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_verify_kernel.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_verify_networking.pyc
%exclude /opt/ericsson/mwshealthcheck/lib/mws_verify_volumes.pyc

%dir %attr(755,root,root) /opt/ericsson/mwshealthcheck

%post -p /bin/sh

################################################################################
# Set up cron job for the script                                               #
################################################################################
echo "# Generate MWS Health Check Report after reboot" > /etc/cron.d/mwshealthcheck
echo "@reboot    root /usr/bin/sleep 5 ; /usr/bin/python /opt/ericsson/mwshealthcheck/bin/mws_health_check.py" >> /etc/cron.d/mwshealthcheck
echo "# Generate MWS Health Check Report on daily basis at 00:30" >> /etc/cron.d/mwshealthcheck
echo "30 0 * * * root /usr/bin/python /opt/ericsson/mwshealthcheck/bin/mws_health_check.py" >> /etc/cron.d/mwshealthcheck
################################################################################
# Set up profile the script                                                    #
################################################################################
cd /etc
# Backup the current profile
check_profile=$(grep -w "/usr/bin/python /opt/ericsson/mwshealthcheck/bin/mws_health_check_summary.py" /etc/profile)
profile_status=$?
if [ "$profile_status" -ne 0 ]
then
   cp profile profile_mwshealthcheck_PREBKP
   echo "/usr/bin/python /opt/ericsson/mwshealthcheck/bin/mws_health_check_summary.py" >> profile
fi

%postun

case "$1" in
        0) # This is a package remove

        # remove mwshealthcheck,bin and lib folders
                rm -rf /opt/ericsson/mwshealthcheck
        # remove mwshealthcheck cron job
                rm -rf /etc/cron.d/mwshealthcheck
        # remove mwshealthcheck line from /etc/profile
                cp /etc/profile /etc/profile_mwschealthcheck_POSTBKP
                sed -i '/\/usr\/bin\/python \/opt\/ericsson\/mwshealthcheck\/bin\/mws_health_check_summary.py/d' /etc/profile
        ;;

        1) # This is a package upgrade
                # do nothing
        ;;
esac

%changelog
* Thu Sep 01 2022 ZAHAHIM
- Intial RPM Build
