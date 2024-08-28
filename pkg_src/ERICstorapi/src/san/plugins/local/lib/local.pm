package local;

use strict;
use warnings;

use Data::Dumper;
use File::Basename;
use Socket;
use FileHandle;
use IPC::Open2;

use StorageApi;

our @ISA = qw(StorageApi);

our $GET_DISK_LIST = "/eniq/installation/core_install/bin/get_disk_list.sh";

##########################################################################
#
# API Methods
#
##########################################################################

sub new() {
    my $class = shift;
    my $this = {
    };
    bless($this,$class);
    return $this;
}

sub configure($) {
    my ($this,$configFile) = @_;

    if ( $main::DEBUG > 3 ) { print "local::configure\n"; }
}

sub listLUNs() {
    my ($this) = @_;
    if ( $main::DEBUG > 3 ) { print "local::listLUNs\n"; }
    my $cmd = $GET_DISK_LIST . ' -r -f -d "@"';
    my @output = $this->execCmd($cmd);

    my %disks = ();
    foreach my $line ( @output ) {
        chop $line;
        my @fields = split( /@/, $line );
        $disks{$fields[0]} = $fields[3]." " . $fields[4] . " " . $fields[2];
    }

    my @luns = ();
    @output = $this->execCmd("/usr/bin/lsscsi -i -s");
     my $currDisk = "";

    foreach my $line ( @output ) {
        if ( $main::DEBUG > 9 ) { print "local::listLUNs  lsscsi  line $line"; }
        if ( $line =~ /\/dev\/(\S+)\s+([0-9a-z]+)\s+/) {
            $currDisk=$1;
            my $devid = $2;
            if ( exists $disks{$currDisk} ) {
                my $r_LUN = {
                    'device' => $currDisk,
                    'desc'   => $disks{$currDisk},
                    'lunid'  => $devid
                };
                push @luns, $r_LUN;
            }
        }
    }

    return \@luns;
}

sub listSnapshots ($) {
    my ($this,$r_lunIdArray) = @_;
    if ( $main::DEBUG > 3 ) { print "local::listSnapshots: " . join(" ", @{$r_lunIdArray}) . "\n"; }
    print "ERROR: snapshots not supported by this plugin\n";
    exit 1;
}

sub createSnapshot($$) {
    my ($this,$r_lunIdArray,$tag) = @_;
    if ( $main::DEBUG > 3 ) { print "local::createSnapshot: tag=$tag luns=" . join(" ", @{$r_lunIdArray}) . "\n"; }
    print "ERROR: snapshots not supported by this plugin\n";
    exit 1;
}

sub deleteSnapshot($$) {
    my ($this,$r_snapIdArray) = @_;
    if ( $main::DEBUG > 3 ) { print "local::deleteSnapshot: snapids=" . join(" ", @{$r_snapIdArray}) . "\n"; }
    print "ERROR: snapshots not supported by this plugin\n";
    exit 1;
}

sub rollbackSnapshot($) {
    my ($this,$r_snapIdArray) = @_;
    if ( $main::DEBUG > 3 ) { print "local::deleteSnapshot: snapids=" . join(" ", @{$r_snapIdArray}) . "\n"; }
    print "ERROR: snapshots not supported by this plugin\n";
    exit 1;
}
##########################################################################
#
# Private methods
#
##########################################################################

sub execCmd($) {
    my ($this,$cmd) = @_;

    if ( $main::DEBUG > 0 ) { print "local::execCmd cmd = $cmd\n"; }

    my $pid = open CMD_PIPE, "$cmd 2>&1 |";
    if ( ! $pid ) {
        my $error = $!;
        print "ERROR: Failed to execute $cmd, $error\n";
        exit 1;
    }

    my @output = <CMD_PIPE>;
    if ( $main::DEBUG > 0 ) { print "local::execCmd output\n@output\n"; }
    my $closeResult = close CMD_PIPE;
    if ( $main::DEBUG > 0 ) { print "local::execCmd exit code=$closeResult\n"; }
    my $exitCode = $?;
    if ( ! $closeResult ) {
        print "ERROR: Failed to complete $cmd, exit code $exitCode\n";
        print @output;
        exit 1;
    }

    if ( $main::DEBUG > 8 ) { print Dumper("local::execCmd output",\@output); }

    return @output;

}
