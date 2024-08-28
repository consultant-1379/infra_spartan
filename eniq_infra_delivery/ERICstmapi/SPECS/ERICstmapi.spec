###############################################################
#
# This is ERICstmapi Products Spec File
#
################################################################

%define CXP CXP9036743

###############################################################
Summary:    ERIC Storage Api package
Name:       ERICstmapi
Version:  R1C
Release: 01
Group:      Ericsson/ENIQ_STATS
Packager:   XGIRRED
BuildRoot:  %{_builddir}/%{name}_%{CXP}-%{version}%{release}
License: Ericsson AB @2018
#################################################################

%define _rpmfilename %{name}-%{version}%{release}.rpm


%description
This the ERICstmapi RPM package

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
install -d -m 755 %{buildroot}/ericsson/storage/bin
install -d -m 755 %{buildroot}/ericsson/storage/etc
cd %{_sourcedir}/src/bin/
cp create_my_fs.sh setup_ssh_FileStore.sh create_nas_users.sh test_nas.sh storobs_removal.py nascli %{buildroot}/ericsson/storage/bin
cd %{_sourcedir}/src/etc/
cp README_HELP nascli.conf_template ssh_input_file storage.ini_template sourcefile decrypt.sh %{buildroot}/ericsson/storage/etc

%files
%defattr(755,root,root)
###### /ericsson/bin files list
/ericsson/storage/bin/nascli
/ericsson/storage/bin/test_nas.sh
/ericsson/storage/bin/create_nas_users.sh
/ericsson/storage/bin/setup_ssh_FileStore.sh
/ericsson/storage/bin/create_my_fs.sh

%defattr(744,root,root)
/ericsson/storage/bin/storobs_removal.py

###### /ericsson/etc files list
/ericsson/storage/etc/README_HELP
/ericsson/storage/etc/nascli.conf_template
/ericsson/storage/etc/storage.ini_template

%defattr(700,root,root)
/ericsson/storage/etc/sourcefile
/ericsson/storage/etc/decrypt.sh
/ericsson/storage/etc/ssh_input_file


%changelog
* Fri Aug 31 2018 XGIRRED 
- Intial RPM Build
