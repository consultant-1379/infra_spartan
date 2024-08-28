################################################################
#
# This is ERICstmnas Product Spec File
#
################################################################
%define CXP CXP9036744

###############################################################
Summary:    ERIC Storage NAS package
Name:       ERICstmnas
Version:  R1C
Release: 01
Group:      Ericsson/ENIQ_STATS
Packager:   XGIRRED
BuildRoot:  %{_builddir}/%{name}_%{CXP}-%{version}%{release}
License:    Ericsson AB @2018
################################################################

%define _rpmfilename %{name}-%{version}%{release}.rpm

%description
This the ERICstmnas RPM package

%prep
rm -rf %{buildroot}
# extract the tar file containing all the sources, to the build directory.
cd %{_sourcedir}
ls -lrt %{_sourcedir}/ERIC*
/bin/tar -xvf %{_sourcedir}/ERIC*.tar
ls -lrt %{_sourcedir}



#%build
#echo "Building the project..."

%install
#rm -rf %{buildroot}
install -d -m 755 %{buildroot}/ericsson/storage/plugins/filestore/etc
install -d -m 755 %{buildroot}/ericsson/storage/plugins/filestore/lib

cd %{_sourcedir}/src/plugins/filestore/etc
cp nasplugin.conf_template %{buildroot}/ericsson/storage/plugins/filestore/etc
cd %{_sourcedir}/src/plugins/filestore/lib
cp nasplugin %{buildroot}/ericsson/storage/plugins/filestore/lib

%post
cd /ericsson/storage/plugins/
ln -s filestore nas


%files
%defattr(755,root,root)
##### /ericsson/storage/etc files list
/ericsson/storage/plugins/filestore/etc/nasplugin.conf_template

###### /ericsson/etc files list
/ericsson/storage/plugins/filestore/lib/nasplugin

%changelog
* Mon Sep 03 2018 XGIRRED 
- Intial RPM Build

