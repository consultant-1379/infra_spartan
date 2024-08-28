#!/usr/bin/perl -w
#

use strict;
use IO::Socket;

#
#  Command line arguments
#
my $host = defined $ARGV[0] ? $ARGV[0] : "";
usage() if $host =~ /^(-h|--help|)$/;
my $port = defined $ARGV[1] ? $ARGV[1] : 22;    # default port

#
#  Try to connect
#
my $remote = IO::Socket::INET->new(
    Proto    => "tcp",
    PeerAddr => $host,
    PeerPort => $port,
    Timeout  => 2,
);

#
#  Print response
#
if ($remote) {
    print "$host is alive\n";
    close $remote;
    exit 0;
}
else {
    print "$host failed\n";
    exit 1;
}

# usage - print usage message and exit
#
sub usage {
    print STDERR "USAGE: portping [-h] | hostname [port]\n";
    print STDERR "   eg, portping mars      # try port 22 (ssh) on mars\n";
    print STDERR "       portping mars 21   # try port 21 on mars\n";
    exit 1;
}

