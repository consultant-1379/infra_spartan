#!/bin/sh

echo "\n"
echo "Make sure that the latest source code is available in the below given paths"
echo "\n" 
echo "Build solaris pacakge for ... \n"
echo  "press 1 for kickstart_sol || sourcecodepath :/var/tmp/sol/TEST/\n"
echo  "press 2 for Unityinit || sourcecodepath :/var/tmp/unity/TEST/\n"
read val

if [ $val == "1" ]; then

  DEST=/var/tmp/sol/SOL_PKG_BUILD/DESTINATION
  PKGDIR=/var/tmp/sol/PKGDIRECTORY
  SOLSORCE=/var/tmp/sol/SOL_PKG_BUILD/SOLARIS
  GIT=/var/tmp/sol/SOURCECODE/
  PARENT=/var/tmp/sol/SOL_PKG_BUILD
  REPO=/var/tmp/sol/TEST/
  PKGINFO=/var/tmp/sol/pkginfo
  PROTO=/var/tmp/sol/kickstart.proto

 echo "Enter the Rstate:"
# read Rstate
 
 if [ ! -d "$GIT" ]; then
   mkdir $GIT
   mkdir  $GIT/kickstart 
   cp -r $REPO/. $GIT/kickstart/ || error "An issue while copying the source code from GIT Repository to local. Package build will be failed."
   cp $PKGINFO $GIT || error"pkginfo is not copied" 
   cp $PROTO $GIT || error "An issue while copying the prototype  file from GIT Repository to local. Package build will be failed."
 fi



 if [ ! -d "$PARENT" ]; then
   mkdir $PARENT
 fi


 if [ -d "$SOLSORCE" ]; then
   rm -r $SOLSORCE

 fi

 if [ ! -d "$SOLSORCE" ]; then
   mkdir $SOLSORCE
   mkdir $SOLSORCE/kickstart 
   cp -r $GIT/kickstart/ $SOLSORCE/ 
   cp $GIT/pkginfo $SOLSORCE
   cp $GIT/kickstart.proto $SOLSORCE

 fi

 COMP=`grep "PKG=" ./sol/SOL_PKG_BUILD/SOLARIS/pkginfo | cut -c5-`
 echo $COMP
 PKG="$COMP-"`grep "VERSION=" ./sol/SOL_PKG_BUILD/SOLARIS/pkginfo | cut -c9-`
 echo $PKG
 if [ ! -d "$DEST" ]; then
   mkdir $DEST 
 fi

 if [ ! -d "$PKGDIR" ]; then
   mkdir $PKGDIR
 fi

 echo "Package build starting....."

 pkgmk -o -d $DEST -r $SOLSORCE -f $SOLSORCE/kickstart.proto || error "Package build failed."

 pkgtrans -s $DEST $PKGDIR/$PKG.pkg all 1>/dev/null 2>&1

 if [ -f $PKGDIR/$PKG.pkg ]; then 
   echo "Packaging complete - package located in $PKGDIR/$PKG.pkg \nunwanted packages should be removed from the path manually for space saving"
 fi

 rm -r $DEST
 rm -r $SOLSORCE
 rm -r $GIT
 rm -r $PARENT


elif [ $val == "2" ]; then

  DEST=/var/tmp/unity/SOL_PKG_BUILD/DESTINATION
  PKGDIR=/var/tmp/unity/PKGDIRECTORY
  SOLSORCE=/var/tmp/unity/SOL_PKG_BUILD/SOLARIS
  GIT=/var/tmp/unity/SOURCECODE/
  PARENT=/var/tmp/unity/SOL_PKG_BUILD
  REPO=/var/tmp/unity/TEST/
  PKGINFO=/var/tmp/unity/pkginfo
  PROTO=/var/tmp/unity/unity.proto


 if [ ! -d "$GIT" ]; then
   mkdir $GIT
   mkdir  $GIT/kickstart
   cp -r $REPO/. $GIT/opt/ || error "An issue while copying the source code from GIT Repository to local. Package build will be failed."
   cp $PKGINFO $GIT
   cp $PROTO $GIT || error "An issue while copying the prototype  file from GIT Repository to local. Package build will be failed."
 fi


 if [ ! -d "$PARENT" ]; then
   mkdir $PARENT
 fi


 if [ -d "$SOLSORCE" ]; then
   rm -r $SOLSORCE

 fi

 if [ ! -d "$SOLSORCE" ]; then
   mkdir $SOLSORCE
   mkdir $SOLSORCE/opt
   cp -r $GIT/opt/ $SOLSORCE/
   cp $GIT/pkginfo $SOLSORCE
   cp $GIT/unity.proto $SOLSORCE

 fi

 COMP=`grep "PKG=" /var/tmp/unity/SOL_PKG_BUILD/SOLARIS/pkginfo | cut -c5-`
 echo $COMP
 PKG="$COMP-"`grep "VERSION=" /var/tmp/unity/SOL_PKG_BUILD/SOLARIS/pkginfo | cut -c9-`
 echo $PKG
 if [ ! -d "$DEST" ]; then
   mkdir $DEST
 fi

 if [ ! -d "$PKGDIR" ]; then
   mkdir $PKGDIR
 fi

 echo "Package build starting....."

 pkgmk -o -d $DEST -r $SOLSORCE -f $SOLSORCE/unity.proto || error "Package build failed."

 pkgtrans -s $DEST $PKGDIR/$PKG.pkg all 1>/dev/null 2>&1

 if [ -f $PKGDIR/$PKG.pkg ]; then
   echo "Packaging complete - package located in $PKGDIR/$PKG.pkg \nunwanted packages should be removed from the path manually for space saving"
 fi

 rm -r $DEST
 rm -r $SOLSORCE
 rm -r $GIT
 rm -r $PARENT

else

  echo "There is not buildscript for available" 

fi
