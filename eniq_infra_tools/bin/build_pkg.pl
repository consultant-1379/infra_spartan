#!/usr/bin/perl

#-----------------------------------------------------------
# COPYRIGHT Ericsson Radio Systems  AB 2016
#
# The copyright to the computer program(s) herein is the
# property of ERICSSON RADIO SYSTEMS AB, Sweden. The
# programs may be usedand/or copied only with the written
# permission from ERICSSON RADIO SYSTEMS AB or in accordance
# with the terms and conditions stipulated in the agreement
# contract under which the program(s)have been supplied.
#-----------------------------------------------------------
#-----------------------------------------------------------
#
#   PRODUCT      : Delivery Management
#   RESP         : zmudshu
#   DATE         : 22/11/2018
#   Description  : This script is use to build and package rpm's.           
#   REV          : A1
# --------------------------------------------------------------
#
#

use strict;
use warnings;
use Getopt::Long;
use File::Copy;
no warnings 'uninitialized';



my $help;
my $PRINTER;
my $ERROR;
my $LINE_NUMBER;
my $Base_Path = "/vobs/oss_sck";
my $Base_Del_Path = $Base_Path."/eniq_infra_delivery";
my $Base_Src_Path = $Base_Path."/eniq_infra_src";
my $RPMBUILD = $Base_Path."/eniq_infra_tools/bin";
my $pkg_details = $Base_Path."/eniq_infra_tools/etc/pkg_details.txt";
my $info_cxp = $Base_Path."/eniq_infra_tools/etc/info_cxp.txt";
my $tempdir = $Base_Path."/eniq_infra_delivery/temp";
my $tempd = $Base_Path."/eniq_infra_delivery/temp";
my $RState;
my $Module;
my $Version;
my $Release;
my $CLEARTOOL = "/usr/atria/bin/cleartool";
my $identifier;
my $prodnum;

###########################################################
# Funtion Name : printer
# Purpose      : To print values passed.
# Return Value : NA
###########################################################
sub printer
{
    $PRINTER = $_[0] ;
    print "------------<   $PRINTER    >------------\n";
    return 0
}


###########################################################
#  Function Name:  error
#  Function Desc:  Show a uniform modern error message
#  Return:         1
###########################################################
sub error
{
    $ERROR = $_[0] ;
    $LINE_NUMBER=$_[1] ;

    print "------------------------------------------------------------------------------\n";
    print "  ERROR!             $ERROR \n";
    print "  Line Number:       $LINE_NUMBER \n";
    print "------------------------------------------------------------------------------\n";

    exit 1;

}


###########################################################
# Funtion Name : Usage
# Purpose      : To print usage when no parameter/worng parameter are passed.
# Return Value : NA
###########################################################
sub usage
{
        print "Unknown option: @_\n" if ( @_ );
        print "usage: build_pkg.pl [-r RState] [-m Module/Component] [-help|-?]\n";
        exit;
}


###########################################################
# Funtion Name : PARAMETERS
# Purpose      : To check right parameters are being passed to the script.
# Return Value : Fail and print Usage if wrong parameters are passed.
###########################################################
sub PARAMETERS
{
        usage() if ( @ARGV < 1 or ! GetOptions('help|?' => \$help, 'rstate|r=s' => \$RState, 'module|m=s' => \$Module,) or defined $help );


        if (`grep $Module $pkg_details` ne "")
        {
            printer("Module getting Built is $Module ");

        }
        else{
            printer("Incorrect module. Please check the name of the module. \n");
            exit;
        }
        if ($RState =~ /^R[0-9][A-Z][0-9]*/)
        {
            printer("$RState is used to build the $Module");
        }
        else{
            printer("Incorrect RState. Please check the RState. \n");
            exit;
        }

} 


###########################################################
# Funtion Name : RPM_BUILD
# Purpose      : To Build RPM
# Return Value : Failure if the rpm build fails.
###########################################################
sub RPM_BUILD
{
    $tempdir = $tempdir."/$Module/";
    if(${tempdir})
    {
        `rm -rf ${tempdir}`;
    }

    `mkdir -p "${tempdir}"`;
    open(pkg_detail, $pkg_details);
    my @pkg = <pkg_detail>;
    close(pkg_detail);

    foreach (@pkg){
        my @detail = split('::', $_);
        my $pkgname = $detail[0];
        if($pkgname eq $Module){
            shift @detail;
            if(${Module} ne "storage"){
                    system("cp -r ${Base_Src_Path}/${Module}/* ${tempdir}");
            }
            foreach(@detail[0 .. $#detail - 1]){
                my $mod = $_;
                my $rp = ${mod}."-".${RState}.".rpm";
                system("./build_rpm -r ${RState} -m ${mod}");
                if(${mod} eq "ERICkickstart"){
                    #if( -d "${tempdir}/eric_kickstart"){}
                    `rm -rf ${tempdir}/eric_kickstart/*`;
                    system("cp ${Base_Del_Path}/${mod}/RPMS/${rp} ${tempdir}/eric_kickstart/");
                }
                else{
                system("cp ${Base_Del_Path}/${mod}/RPMS/${rp} ${tempdir}");
                }
                #print($rp."  ");
            }
            
        }
    }
}


###########################################################
# Funtion Name : Create_cxpinfo
# Purpose      : To Create cxp_info file
# Return Value : Failure if the creation fails.
###########################################################
sub Create_cxpinfo
{
    
    open(INFOR, $info_cxp);
    my @infocx = <INFOR>;
    close(INFOR);
    
    foreach(@infocx[1 .. $#infocx]){
        my @inf = split(':::', $_);
        my $pckg = $inf[0];
        if($pckg eq ${Module}){
            my $filename = 'cxp_info';
            open(my $fh, '>', $filename) or die "Could not open file '$filename' $!";
                print $fh "PKGINST=${inf[0]} \nNAME=${inf[1]} \nARCH=${inf[2]} \nVERSION=${RState} \nPRODNUM=${inf[3]}";
            close $fh;
        }
    }
    system("cp ${RPMBUILD}/cxp_info ${tempdir}");
    `rm -rf ${RPMBUILD}/cxp_info`;
    
}


###########################################################
# Funtion Name : TAR_PKG
# Purpose      : To tar the package
# Return Value : Failure if tar fails.
###########################################################
sub TAR_PKG
{       chdir($tempd) or die "Unable to Switch to dir $!, $tempd \n";
        `/bin/chmod 755 -R ${Module}`;
        `/bin/tar -cvf ${Module}_${RState}.tar ${Module}/`;
}

sub create_label
{
    my $CXP_INFO_FILE = "${tempdir}/cxp_info" ;
    my @CXP_INFO;
    my $LINE;
    

        open ( CXP_INFO_FILE, "$CXP_INFO_FILE" ) or error ( "unable to open to $CXP_INFO_FILE", __LINE__ );
        chomp ( @CXP_INFO=( <CXP_INFO_FILE> ) );
        close ( CXP_INFO_FILE );

        # Parse Through File to get CXP Number
        foreach ( @CXP_INFO )
        {
                $LINE=$_;
                if  ( /^PRODNUM=/ )
                {
                        ($identifier,$prodnum) = split(/=/,$LINE);
                }
        }
        my $label_to_create="${prodnum}_${RState}";
        
        my $new_lb_exist = `$CLEARTOOL desc -s lbtype:$label_to_create 2>/dev/null`;
        chomp $new_lb_exist;


        #check if label exists within clearcase
        if($new_lb_exist eq $label_to_create){
                print "\nThis label ($label_to_create) already exists\n";
                print "Please build using a new label\n";
                exit 1;
        }
        else{
                print "\nThis label ($label_to_create) doesn't exist\n";
                print "\nCreating new Label type ($label_to_create) in Clearcase... \n";
                `$CLEARTOOL mklbtype -c "Automated label for build" $label_to_create`;
        }
}

## MAIN
{
    PARAMETERS();
    RPM_BUILD();
    Create_cxpinfo();
    create_label();
    TAR_PKG();
}
