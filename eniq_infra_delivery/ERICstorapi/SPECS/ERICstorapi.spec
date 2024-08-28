#################################################################
#
# This is ERICstorapi Products Spec File
#
#################################################################

%define CXP CXP9036908

###############################################################
Summary:    ERIC Storage Api package
Name:       ERICstorapi
Version:  R1C
Release: 01
Group:      Ericsson/ENIQ_STATS
Packager:   XKEERBV
BuildRoot:  %{_builddir}/%{name}_%{CXP}-%{version}%{release}
License: Ericsson AB @2018
##################################################################

%define _rpmfilename %{name}-%{version}%{release}.rpm


%description
This the ERICstorapi RPM package

%prep
rm -rf %{buildroot}
# extract the tar file containing all the sources, to the build directory.
cd %{_sourcedir}
ls -lrt %{_sourcedir}/ERIC*
/bin/tar -xvf %{_sourcedir}/ERIC*.tar

#%build
#echo "Building the project..."

%install
rm -rf %{buildroot}
install -d -m 755 %{buildroot}/ericsson/storage/
install -d -m 755 %{buildroot}/ericsson/storage/san
install -d -m 755 %{buildroot}/ericsson/storage/san/bin
install -d -m 755 %{buildroot}/ericsson/storage/san/etc
install -d -m 755 %{buildroot}/ericsson/storage/san/lib
install -d -m 755 %{buildroot}/ericsson/storage/san/plugins
install -d -m 755 %{buildroot}/ericsson/storage/san/plugins/local
install -d -m 755 %{buildroot}/ericsson/storage/san/plugins/local/lib
install -d -m 755 %{buildroot}/ericsson/storage/san/plugins/vnx
install -d -m 755 %{buildroot}/ericsson/storage/san/plugins/vnx/cred
install -d -m 755 %{buildroot}/ericsson/storage/san/plugins/vnx/etc
install -d -m 755 %{buildroot}/ericsson/storage/san/plugins/vnx/lib
install -d -m 755 %{buildroot}/ericsson/storage/san/plugins/unity
install -d -m 755 %{buildroot}/ericsson/storage/san/plugins/unity/etc
install -d -m 755 %{buildroot}/ericsson/storage/san/plugins/unity/lib

cd %{_sourcedir}/src/san/
cp -r * %{buildroot}/ericsson/storage/san/
exit 0

%files
%defattr(755,root,root)


##### /ericsson/bin files list
/ericsson/storage/san/bin/blkcli
/ericsson/storage/san/bin/resetPasswordforSAN.py
/ericsson/storage/san/bin/vnx_unitypwdupdate.py
#### /ericsson/storage/etc
/ericsson/storage/san/etc


###### /ericsson/lib files list
/ericsson/storage/san/lib/StorageApi.pm


###### /ericsson/plugins files list
/ericsson/storage/san/plugins/local/lib/local.pm


###### /ericsson//plugins/vnx/lib files list
/ericsson/storage/san/plugins/vnx/etc
/ericsson/storage/san/plugins/vnx/cred
/ericsson/storage/san/plugins/vnx/lib/vnx.pm

###### /ericsson//plugins/unity/lib files list
/ericsson/storage/san/plugins/unity/etc
/ericsson/storage/san/plugins/unity/lib/unity.pm
/ericsson/storage/san/plugins/unity/lib/encryptdecrypt.py

%changelog
* Wed Mar 17 2020 ZBHTMNJ
- Intial RPM Build

