#!/bin/sh

#Reading Command Line Args
val=$1
pkgVersion=$2
echo "\n#################################################"
echo "Make sure that the latest source code is correct"
echo "#################################################"

if [[ -z $val ]] && [[ -z ${pkgVersion} ]]; then
	echo "ERROR" "Wrong command Line Args\n"
	echo "USAGE:" "solaris_pkgbuild.sh 1 <pkg version>\n"
	exit 1
fi
#variable assigning

SOL_DIR=/tmp/INFRA_CI_BUILD_Kickstart_SOL_Pkg/
DEST=${SOL_DIR}DESTINATION
PKGDIR=${SOL_DIR}PKGDIRECTORY
#SOLSORCE=${SOL_DIR}/SOLARIS
GIT=${SOL_DIR}SOURCECODE/
PROTO=${SOL_DIR}/SOURCECODE/kickstart.proto

#Creating and Deleting the Required Dir's
mkdir -p $DEST
mkdir -p $PKGDIR

if [ ! -d $GIT/kickstart ]; then
	echo "ERRO:  Issue in ${GIT}"
	exit 1
fi


#Actual building process 
COMP="ERICkickstart-sol"
echo "Package Name" $COMP

PKG="${COMP}-${pkgVersion}"
echo "Package version" $PKG

echo "Package build starting....."

pkgmk -o -d $DEST -r $GIT -f $GIT/kickstart.proto || error "Package build failed."

pkgtrans -s $DEST $PKGDIR/$PKG.pkg all 1>/dev/null 2>&1

#Checking whether package Build is successful
if [ -f $PKGDIR/$PKG.pkg ]; then
	echo "INFR: Packaging complete - package located in $PKGDIR/$PKG.pkg"
	echo "NOTE: Unwanted packages should be removed from the path manually for space saving"
fi

#Clean up started
rm -fr $DEST
rm -fr $GIT/*
exit 0
