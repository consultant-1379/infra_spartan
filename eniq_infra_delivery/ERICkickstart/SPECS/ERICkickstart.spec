################################################################
#
# This is ERICkickstart Product Spec File
#
###############################################################
%define CXP CXP9036859

###############################################################
Summary:    ERIC Kickstart package
Name:       ERICkickstart
Version:  R1D
Release: 02
Group:      Ericsson/ENIQ_STATS
Packager:   XGIRRED
BuildRoot:  %{_builddir}/%{name}_%{CXP}-%{version}%{release}
License: Ericsson AB @2018
#################################################################

%define _rpmfilename %{name}-%{version}%{release}.rpm

%description
This the ERICkickstart RPM package

%prep
rm -rf %{buildroot}
# extract the tar file containing all the sources, to the build directory.
cd %{_sourcedir}
ls -lrt %{_sourcedir}/ERIC*
/bin/tar -xvf %{_sourcedir}/ERIC*.tar

#%build
#echo "Building the project..."

%install
#rm -rf %{buildroot}
install -d -m 755 %{buildroot}/ericsson/kickstart/bin
install -d -m 755 %{buildroot}/ericsson/kickstart/etc
install -d -m 755 %{buildroot}/ericsson/kickstart/linux/RHEL/install_profiles
install -d -m 755 %{buildroot}/ericsson/kickstart/template/media_config_template
install -d -m 755 %{buildroot}/ericsson/kickstart/release/x86_64/media_identity/REDHAT
install -d -m 755 %{buildroot}/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT
install -d -m 755 %{buildroot}/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT
install -d -m 755 %{buildroot}/ericsson/kickstart/lib
install -d -m 755 %{buildroot}/ericsson/kickstart/patch
install -d -m 755 %{buildroot}/ericsson/kickstart/patch/RHEL

cd %{_sourcedir}/src/bin/
cp * %{buildroot}/ericsson/kickstart/bin

cd %{_sourcedir}/src/etc/
cp * %{buildroot}/ericsson/kickstart/etc

cd %{_sourcedir}/src/lib/
cp * %{buildroot}/ericsson/kickstart/lib

cd %{_sourcedir}/src/linux/RHEL
cp linux_client_config_template %{buildroot}/ericsson/kickstart/linux/RHEL

cd %{_sourcedir}/src/linux/RHEL/install_profiles
cp linux.cfg.template %{buildroot}/ericsson/kickstart/linux/RHEL/install_profiles
cp linux_bmr.cfg.template %{buildroot}/ericsson/kickstart/linux/RHEL/install_profiles

cd %{_sourcedir}/src/template/
cp ericks_config_template %{buildroot}/ericsson/kickstart/template
cp patchks_config_template %{buildroot}/ericsson/kickstart/template
cp upgrade_patchks_config_template %{buildroot}/ericsson/kickstart/template

cd %{_sourcedir}/src/template/media_config_template
cp * %{buildroot}/ericsson/kickstart/template/media_config_template

cd %{_sourcedir}/src/release/x86_64/media_identity/REDHAT
cp * %{buildroot}/ericsson/kickstart/release/x86_64/media_identity/REDHAT

cd %{_sourcedir}/src/release/x86_64/install_patch_media_identity/REDHAT
cp * %{buildroot}/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT

cd %{_sourcedir}/src/release/x86_64/upgrade_patch_media_identity/REDHAT
cp * %{buildroot}/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT

cd %{_sourcedir}/src/patch/
cp -r * %{buildroot}/ericsson/kickstart/patch/
cp -r * %{buildroot}/ericsson/kickstart/patch/RHEL


%files
%defattr(755,root,root)
##### bin files list
/ericsson/kickstart/bin/manage_linux_dhcp.bsh
/ericsson/kickstart/bin/manage_linux_dhcp_clients.bsh
/ericsson/kickstart/bin/manage_linux_kickstart.bsh
/ericsson/kickstart/bin/manage_nfs_media.bsh
/ericsson/kickstart/bin/rpm2cpio_new
/ericsson/kickstart/bin/setup_feature_path.bsh
/ericsson/kickstart/bin/manage_upg_patch_kickstart.bsh
/ericsson/kickstart/bin/manage_install_patch_kickstart.bsh
/ericsson/kickstart/bin/cxp_info
/ericsson/kickstart/bin/manage_mws_services.py

###### etc files list
/ericsson/kickstart/etc/ericks_config
/ericsson/kickstart/etc/upgrade_patchks_config
/ericsson/kickstart/etc/patchks_config

###### lib files list
/ericsson/kickstart/lib/common_ericks_functions.lib
/ericsson/kickstart/lib/port_ping.pl

###### linux/RHEL files list
/ericsson/kickstart/linux/RHEL/linux_client_config_template
/ericsson/kickstart/linux/RHEL/install_profiles/linux.cfg.template
/ericsson/kickstart/linux/RHEL/install_profiles/linux_bmr.cfg.template

###### release files list
/ericsson/kickstart/release/x86_64/media_identity/REDHAT/7.6-4
/ericsson/kickstart/release/x86_64/media_identity/REDHAT/7.7-10
/ericsson/kickstart/release/x86_64/media_identity/REDHAT/7.9-3
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/1.0.5
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/1.0.7
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/1.0.9
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/1.0.10
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/1.0.11
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/1.0.12
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/1.0.13
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/1.0.14
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/1.0.15
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/1.0.16
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/2.0.1
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/2.0.2
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/2.0.3
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/2.0.4
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/2.0.5
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/2.0.7
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/2.0.8
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.1
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.2
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.3
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.4
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.5
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.6
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.7
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.8
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.9
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.10
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.11
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.12
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.13
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.14
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.15
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.16
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.17
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.18
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.19
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.20
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.21
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.22
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.23
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.24
/ericsson/kickstart/release/x86_64/install_patch_media_identity/REDHAT/3.0.25
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/1.0.5
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/1.0.7
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/1.0.9
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/1.0.10
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/1.0.11
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/1.0.12
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/1.0.13
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/1.0.14
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/1.0.15
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/1.0.16
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/2.0.1
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/2.0.2
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/2.0.3
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/2.0.4
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/2.0.5
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/2.0.7
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/2.0.8
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.1
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.2
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.3
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.4
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.5
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.6
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.7
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.8
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.9
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.10
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.11
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.12
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.13
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.14
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.15
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.16
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.17
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.18
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.19
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.20
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.21
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.22
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.23
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.24
/ericsson/kickstart/release/x86_64/upgrade_patch_media_identity/REDHAT/3.0.25

########## template files list
/ericsson/kickstart/template/ericks_config_template
/ericsson/kickstart/template/patchks_config_template
/ericsson/kickstart/template/upgrade_patchks_config_template
/ericsson/kickstart/template/media_config_template/eniq_stats_template
/ericsson/kickstart/template/media_config_template/om_linux_template
/ericsson/kickstart/template/media_config_template/ombs_linux_template
/ericsson/kickstart/template/media_config_template/rhelonly_template


########## patch files list
/ericsson/kickstart/patch/
/ericsson/kickstart/patch/RHEL

%changelog
* Fri Aug 31 2018 XGIRRED
- Intial RPM Build

