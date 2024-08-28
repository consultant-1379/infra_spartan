################################################################
#
# This is ERICstorconfig Product Spec File
#
###############################################################
%define CXP CXP9042467

###############################################################
Summary:    ERIC sanconfig  package
Name:       ERICstorconfig
Version:  R10B
Release: 03
Group:      Ericsson/ENIQ_STATS
Packager:   XGIRRED
BuildRoot:  %{_builddir}/%{name}_%{CXP}-%{version}%{release}
License: Ericsson AB @2018
#################################################################

%define _rpmfilename %{name}-%{version}%{release}.rpm

%description
This the ERICstorconfig RPM package

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
install -d -m 755 %{buildroot}/opt/ericsson/san/
install -d -m 755 %{buildroot}/opt/ericsson/san/bin/
install -d -m 755 %{buildroot}/opt/ericsson/san/etc/
install -d -m 755 %{buildroot}/opt/ericsson/san/lib/

cd %{_sourcedir}/src/bin/
cp * %{buildroot}/opt/ericsson/san/bin

cd %{_sourcedir}/src/etc/
cp .san %{buildroot}/opt/ericsson/san/etc

cd %{_sourcedir}/src/lib/
cp * %{buildroot}/opt/ericsson/san/lib

%files
%defattr(755,root,root)
##### bin files list
/opt/ericsson/san/bin/StorageConfiguration.py
/opt/ericsson/san/bin/StorageExpansion.py

###### lib files list
/opt/ericsson/san/lib/BlockConfiguration.py
/opt/ericsson/san/lib/FileConfiguration.py
/opt/ericsson/san/lib/PoolExpansion.py
/opt/ericsson/san/lib/LunCreation.py
/opt/ericsson/san/lib/LunAddition.py
/opt/ericsson/san/lib/StoragePostExpansion.py
/opt/ericsson/san/lib/ExpansionInputPrecheck.py
/opt/ericsson/san/lib/NasExpansion.py
%exclude /opt/ericsson/san/lib/FileConfiguration.pyc
%exclude /opt/ericsson/san/lib/FileConfiguration.pyo
%exclude /opt/ericsson/san/lib/BlockConfiguration.pyc
%exclude /opt/ericsson/san/lib/BlockConfiguration.pyo
%exclude /opt/ericsson/san/lib/PoolExpansion.pyc
%exclude /opt/ericsson/san/lib/PoolExpansion.pyo
%exclude /opt/ericsson/san/lib/LunCreation.pyc
%exclude /opt/ericsson/san/lib/LunCreation.pyo
%exclude /opt/ericsson/san/lib/LunAddition.pyc
%exclude /opt/ericsson/san/lib/LunAddition.pyo
%exclude /opt/ericsson/san/lib/ExpansionInputPrecheck.pyc
%exclude /opt/ericsson/san/lib/ExpansionInputPrecheck.pyo
%exclude /opt/ericsson/san/lib/StoragePostExpansion.pyc
%exclude /opt/ericsson/san/lib/StoragePostExpansion.pyo
%exclude /opt/ericsson/san/lib/NasExpansion.pyc
%exclude /opt/ericsson/san/lib/NasExpansion.pyo

##### etc files list
%exclude /opt/ericsson/san/etc/.san
%changelog
* Fri Aug 31 2018 XGIRRED
- Intial RPM Build

