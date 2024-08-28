package vnx;

use strict;
use warnings;

use Data::Dumper;
use File::Basename;
use Socket;
use FileHandle;
use IPC::Open2;

use StorageApi;

our @ISA = qw(StorageApi);

our $AGENT_CONFIG_FILE = "/etc/Unisphere/agent.config";
our $AGENT_ID_FILE = "/agentID.txt";
our $HOST_ID_FILE = "/etc/log/HostIdFile.txt";

our $AGENT = "/etc/init.d/hostagent";
our $NAVISECCLI = "/opt/Navisphere/bin/naviseccli";
our $storage_grp_pass;
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

# Collect the following information
#  HostAgent IP Address, IP address on the NIC used to connect to the SAN
#  Foreach SAN
#   SAN Name
#   User ID and Password
#   SP IP Addresses
#   StorageGroup
#
# Once this has been done, configure the agent.config file, agentID.txt file
# and remove the HostID.txt file
#
# Now we restart the agent and for each SAN, connect this host to the
# storage group
#
sub configure($) {
    my ($this,$configFile) = @_;

    if ( $main::DEBUG > 3 ) { print "vnx::configure\n"; }

    if ( defined $configFile ) {
        $this->parseConfigFile($configFile);
    } else {
        $this->{'cfg'}->{'agentip'} = ask("Enter Host Agent IP Address");
        my $clariionName;
        do {
            $clariionName = ask("Enter  EMC SAN Name [return to exit]");
            if ( $clariionName !~ /^$/ ) {
                $this->getClariionConfiguration($clariionName);
            }
        } while ( $clariionName !~ /^$/ );
    }

    my $hostname = `hostname`;
    chop($hostname);
    $this->{'cfg'}->{'agenthostname'} = $hostname;

    $this->saveConfiguration();
    $this->initialize();

    $this->updateAgentConfig();

    $this->configureSecFile();

    #
    # Restart the agent
    #
    print "INFO: Restarting Agent\n";
    system("$AGENT stop");
    system("$AGENT start");


    foreach my $clariion ( keys %{$this->{'cfg'}->{'clariion'}} ) {
        my $r_clariionCfg = $this->{'cfg'}->{'clariion'}->{$clariion};
        # Test connectivity
        print "INFO: Registering with $clariion\n";
        my $baseCmd = $this->baseCommand($clariion,undef);
        my $cmd = $baseCmd . " server -register -host " . $this->{'cfg'}->{'agentip'};
        $this->execCmdWithInput($cmd,"2\n");

        # Connect host to the specified storage group
        print "INFO: Connecting to storage group $r_clariionCfg->{'sg'} on $clariion\n";
        $cmd = $baseCmd . sprintf(" storagegroup -connecthost -host %s -gname %s -o",
                                  $this->{'cfg'}->{'agenthostname'},
                                  $r_clariionCfg->{'sg'});
        $this->execCmd($cmd);

        # Setup
        #  Enable LUN Z (-arraycommpath 1)
        #  Enable ALUA   (-failovermode 4)
        print "INFO: Configure host parameters for storage group $r_clariionCfg->{'sg'} on $clariion\n";
        $cmd = $baseCmd . sprintf(" storagegroup -sethost -host %s -gname %s -arraycommpath 1 -failovermode 4 -o",
                                  $this->{'cfg'}->{'agenthostname'},
                                  $r_clariionCfg->{'sg'});
        $this->execCmd($cmd);

        # Log the actual ACP setting after the Disable.
        print "INFO: Extracting the actual ACP setting after the Disable\n";
        $cmd = $baseCmd . sprintf(" arraycommpath");
        $this->execCmd($cmd);
    }
}


# Foreach SAN
#  use server -volmap to get the list of devices and the assoicated WWN.
#  Then use getlun -uid -name -type and use the UID match to the to the WWN,
#  The returned lunid is in the format
#   clariion_name@LUN
#
sub listLUNs() {
    my ($this) = @_;
    if ( $main::DEBUG > 3 ) { print "vnx::listLUNs\n"; }

    $this->initialize();

    my @luns = ();

    foreach my $clariion ( keys %{$this->{'cfg'}->{'clariion'}} ) {
        my $baseCmd = $this->baseCommand($clariion,undef);

        # Force a refresh
        my $cmd = $baseCmd . sprintf(" server -update -host %s -rescanDevices -o",
                                  $this->{'cfg'}->{'agentip'});
        $this->execCmd($cmd);


        # Get the volmap
        $cmd = $baseCmd . " server -volmap -host " . $this->{'cfg'}->{'agentip'};
        my @output = $this->execCmd($cmd);


        my $device = undef;
        my %wwnToDeviceMap = ();
        foreach my $line ( @output ) {
            if ( $line =~ /Device Id:\s+(\S+)/ ) {
                $device = $1;
            } elsif ( $line =~ /^LOGICAL UNIT WWN:\s+(\S+)/ ) {
                my $wwn = $1;
                if ( defined $device ) {
                    $wwnToDeviceMap{$wwn} = $device;
                }
            } elsif ( $line =~ /^$/ ) {
                $device = undef;
            }
        }
        if ( $main::DEBUG > 5 ) { print Dumper("vnx::listLUNs wwnToDeviceMap: ", \%wwnToDeviceMap); }

        $cmd = $baseCmd . " getlun -uid -name -type";
        @output = $this->execCmd($cmd);

        my @clariionLUNs = ();

        # Parse getlun printout
        my $r_currLUN = undef;
        foreach my $line ( @output ) {
            if ( $line =~ /^LOGICAL UNIT NUMBER (\d+)/ ) {
                my $number = $1;
                if ( $main::DEBUG > 7 ) { print "vnx::listLUNs matched LUN $number\n"; }
                $r_currLUN = {
                    'number' => $number
                };
            } elsif ( $line =~ /^UID:\s+(\S+)/ ) {
                $r_currLUN->{'uid'} = $1;
            } elsif ( $line =~ /^Name\s+(.*)/ ) {
                $r_currLUN->{'name'} = $1;
            } elsif ( $line =~ /^RAID Type:\s+(.*)/ ) {
                $r_currLUN->{'type'} = $1;
            } elsif ( $line =~ /^$/ ) {
                if ( $main::DEBUG > 7 ) { print Dumper("vnx::listLUNs blank line r_currLUN", $r_currLUN); }

                if ( defined $r_currLUN && exists $r_currLUN->{'uid'} &&
                     exists $r_currLUN->{'type'} && exists $r_currLUN->{'name'} ) {
                    push @clariionLUNs, $r_currLUN;
                }
                $r_currLUN = undef;
            }
        }

        foreach $r_currLUN ( @clariionLUNs ) {
            if ( exists $wwnToDeviceMap{$r_currLUN->{'uid'}} ) {
                        my $r_LUN = {
                        'device' => $wwnToDeviceMap{$r_currLUN->{'uid'}},
                        'lunid'     => $clariion . "@" . $r_currLUN->{'number'},
                        'desc'   => $r_currLUN->{'type'} . " " . $r_currLUN->{'name'} . " on " . $clariion
                        };
                        push @luns, $r_LUN;
                        delete $wwnToDeviceMap{$r_currLUN->{'uid'}} ;
             }
        }
    }
    return \@luns;
}


# Extract the LUNs for each SAN.
# Foreach specified SAN
#  Use snapview -listsessions -sessionstate -tlunumber to get the list of snapshots
#  Foreach session
#   Foreach LUN in the Target LUN list
#    If the target LUN is in the list of specified LUNs, add session to list of
#    snapshots for that LUN
#    The returned snapid is in the format clarrion_name@LUN@sessionname
#
sub listSnapshots ($) {
    my ($this,$r_lunIdArray) = @_;
    if ( $main::DEBUG > 3 ) { print "vnx::listSnapshots: " . join(" ", @{$r_lunIdArray}) . "\n"; }

    $this->initialize();
    my @snapshots = ();
     my $r_lunsByClariion = $this->parseLUNids($r_lunIdArray);
    #if condition to separate ALL and with lunid
    foreach my $clariion ( keys %{$r_lunsByClariion} ) {
        my $r_specifiedLUNlist = $r_lunsByClariion->{$clariion};
        my %specifiedLUNs = ();
        foreach my $specifiedLUN ( @{$r_specifiedLUNlist} ) {
            $specifiedLUNs{$specifiedLUN} = 1;
        }

        my $cmd = $this->baseCommand($clariion,undef);
        $cmd .= " snapview -listsessions -sessionstate -tlunumber";
        my @output = $this->execCmd($cmd);
        my $r_sessions = $this->parseListSessions(\@output);

        foreach my $r_session ( @{$r_sessions} ) {
            foreach my $session_lun ( @{$r_session->{'lunlist'}} ) {
                my $state = $StorageApi::OKAY;
                if ( $r_session->{'state'} eq "Normal" ) {
                    $state = $StorageApi::OKAY;
                } elsif ( $r_session->{'state'} eq "Rolling Back" ) {
                    $state = $StorageApi::ROLLING_BACK;
                } else {
                    $state = $StorageApi::FAILED;
                }
                if ( exists $specifiedLUNs{$session_lun} ) {
                    my $r_snapshot = {
                        'lunid'  => $clariion . "@" . $session_lun,
                        'snapid' => $clariion .  "@" . $session_lun . "@" .
                            $r_session->{'name'},
                            'state'  => $state
                    };
                    push @snapshots, $r_snapshot;
                }
            }
        }
     return \@snapshots;
   }
}

#
# Extract the LUNs for each SAN.
# Foreach specified SAN
#  Use snapview -startsession "tag" -consistent -lun [LUNs]
#  If this fails then abort, no cleanup as we don't know what has happened
#
sub createSnapshot($$) {
    my ($this,$r_lunIdArray,$tag) = @_;
    if ( $main::DEBUG > 3 ) { print "clariion::createSnapshot: tag=$tag luns=" . join(" ", @{$r_lunIdArray}) . "\n"; }

    $this->initialize();

    my $r_lunsByClariion = $this->parseLUNids($r_lunIdArray);

    my @results = ();
    foreach my $clariion ( keys %{$r_lunsByClariion} ) {
        my $cmd = $this->baseCommand($clariion,undef);
        $cmd .= " snapview -startsession \"$tag\" -consistent -lun " .
            join(" ", @{$r_lunsByClariion->{$clariion}});
        my @output = $this->execCmd($cmd);
        foreach my $lun ( @{$r_lunsByClariion->{$clariion}} ) {
            my $r_snapshot = {
                'lunid' => $clariion . "@" . $lun,
                'snapid' => $clariion . "@" . $lun . "@" . $tag
            };
            push @results, $r_snapshot;
        }
    }

    return \@results;
}

#
# Parse the Ids and make sure they all belong to the same session
# Foreach specified clariion
#  Use snapview -stopsession sessionname -o
#
sub deleteSnapshot($$) {
    my ($this,$r_snapIdArray) = @_;
    if ( $main::DEBUG > 3 ) { print "clariion::deleteSnapshot: snapids=" . join(" ", @{$r_snapIdArray}) . "\n"; }

    $this->initialize();

    my @clariionList = ();
    my $theSessionName = $this->validateSnapIds($r_snapIdArray,\@clariionList);
    foreach my $clariion ( @clariionList ) {
        my $cmd = $this->baseCommand($clariion,undef);
        $cmd .= " snapview -stopsession $theSessionName -o";
        $this->execCmd($cmd);
    }
}

#
# Parse the Ids and make sure they all belong to the same session
# Foreach specified clariion
#  Use snapview -startrollback sessionname -o
#
sub rollbackSnapshot($) {
    my ($this,$r_snapIdArray) = @_;

    if ( $main::DEBUG > 3 ) { print "clariion::deleteSnapshot: snapids=" . join(" ", @{$r_snapIdArray}) . "\n"; }

    $this->initialize();

    my @clariionList = ();
    my $theSessionName = $this->validateSnapIds($r_snapIdArray,\@clariionList);
    foreach my $clariion ( @clariionList ) {
        my $cmd = $this->baseCommand($clariion,undef);
        $cmd .= " snapview -startrollback $theSessionName -rate high -o";
        $this->execCmd($cmd);
    }
                     }


##########################################################################
#
# Private methods
#
##########################################################################

sub baseCommand($$) {
    my ($this,$clariion,$sp) = @_;

    my $r_clariionCfg = $this->{'cfg'}->{'clariion'}->{$clariion};
    my $spIP;
    if ( defined $sp ) {
        $spIP = $r_clariionCfg->{$sp};
    } else {
        $spIP = $r_clariionCfg->{'spa'};
    }

    my $secFile = getRootDir() . "/cred";
    my $cmd = $this->{'cfg'}->{'naviseccli'} . " " .
        "-secfilepath $secFile " .
        "-Address " . $spIP;

    return $cmd;
}

sub configureSecFile() {
    my ($this) = @_;

    my $secFile = getRootDir() . "/cred";
    foreach my $clariion ( keys %{$this->{'cfg'}->{'clariion'}} ) {
        my $r_clariionCfg = $this->{'cfg'}->{'clariion'}->{$clariion};
        foreach my $sp ( $r_clariionCfg->{'spa'}, $r_clariionCfg->{'spb'} ) {
            my $cmd = sprintf("%s -Address %s -AddUserSecurity -user %s -password %s -scope 0 -secfilepath %s",
                              $this->{'cfg'}->{'naviseccli'}, $sp,
                              $r_clariionCfg->{'user'}, $storage_grp_pass, #$r_clariionCfg->{'pass'},
                              $secFile);
            $this->execCmd($cmd);
        }
    }
}

sub execCmdWithInput($$) {
    my ($this,$cmd,$input) = @_;

    if ( $main::DEBUG > 0 ) { print "clariion::execCmdWithInput cmd = $cmd, input= $input\n"; }

    $this->log("exec start: $cmd");
    my $pid = open2( \*FROM_CMD, \*TO_CMD, $cmd );
    if ( ! $pid ) {
        my $error = $!;
        print "ERROR: Failed to execute $cmd, $error\n";
        $this->log("exec failed: $error");
        exit 1;
    }

    print TO_CMD $input;
    close TO_CMD;

    my @output = <FROM_CMD>;
    $this->log("exec printout:\n" . join("", @output));

    my $closeResult = close FROM_CMD;
    my $exitCode = $?;
    $this->log("exec exit: $exitCode");
    if ( ! $closeResult ) {
        print "ERROR: Failed to complete $cmd, exit code $exitCode\n";
        print @output;
        exit 1;
    }

    if ( $main::DEBUG > 8 ) { print Dumper("clariion::execCmd output",\@output); }

    return @output;
}

sub execCmd($) {
    my ($this,$cmd) = @_;

    if ( $cmd =~ /-password/ ){
    	$this->log("exec start: Establishing Passwordless connection from ENIQ to SAN");
    }
    else {
        $this->log("exec start: $cmd");
    }
    if ( $main::DEBUG > 0 ) { print "clariion::execCmd cmd = $cmd\n"; }
    my $pid = open CMD_PIPE, "$cmd 2>&1 |";
    if ( ! $pid ) {
        my $error = $!;
        print "ERROR: Failed to execute $cmd, $error\n";
        $this->log("exec failed: $error");
        exit 1;
    }

    my @output = <CMD_PIPE>;
    $this->log("exec printout:\n" . join("", @output));

    my $closeResult = close CMD_PIPE;
    my $exitCode = $?;
    $this->log("exec exit: $exitCode");
    if ( ! $closeResult ) {
        print "ERROR: Failed to complete $cmd, exit code $exitCode\n";
        print @output;
        exit 1;
    }

    if ( $main::DEBUG > 8 ) { print Dumper("clariion::execCmd output",\@output); }

    return @output;

}

sub getClariionConfiguration($) {
    my ($this,$clariionName) = @_;

    if ( $main::DEBUG > 4 ) { print "clariion::getClariionConfiguration: $clariionName\n"; }

    my $userName = ask("Enter userid");
    my $password = ask("Enter password");
    my $spA      = ask("Enter SP A IP Address");
    my $spB      = ask("Enter SP B IP Address");
    my $storGrp  = ask("Enter Storage Group Name");
    #Hiding password
    $storage_grp_pass = $password; 
    my $clariionCfg = {
        'user' => $userName,
     #   'pass' => $password,
        'spa'  => $spA,
        'spb'  => $spB,
        'sg'   => $storGrp
    };

    $this->{'cfg'}->{'clariion'}->{$clariionName} = $clariionCfg;
}

sub initialize() {
    my ($this) = @_;

    if ( $main::DEBUG > 5 ) { print "clariion::initialize\n"; }

    if ( ! exists $this->{'cfg'} ) {
        my $configFile = getRootDir() . "/etc/clariion.conf";
        if ( ! -r $configFile ) {
            print "ERROR: Configuration file not found, $configFile";
            exit 1;
        }
        $this->loadConfiguration();
    }

    if ( ! exists $this->{'cfg'}->{'naviseccli'} ) {
        if ( -r $NAVISECCLI ) {
            $this->{'cfg'}->{'naviseccli'} = $NAVISECCLI;
        } else {
            print "ERROR: Cannot find $NAVISECCLI";
            exit 1;
        }
    }

    if ( ! exists $this->{'cfg'}->{'logfile'} ) {
        $this->{'cfg'}->{'logfile'} = getRootDir() . "/cmd.log";
    }
}

sub loadConfiguration() {
    my ($this) = shift;

    if ( $main::DEBUG > 4 ) { print "clariion::loadConfiguration\n"; }

    my $configFile = getRootDir() . "/etc/clariion.conf";
    if ( ! ( open CONFIG, "$configFile" ) ) {
        print "ERROR: Failed to open configuration file $configFile, $@\n";
        exit 1;
    }
    my @cfgLines = <CONFIG>;
    close CONFIG;

    my $cfgStr = join('',@cfgLines);
    if ( $main::DEBUG > 7 ) { print "clariion::loadConfiguration cfgStr\n" . $cfgStr; }
    my $VAR1;
    eval($cfgStr);
    if ( $@ ) {
        print "ERROR: Failed to load clariion configuration, $@\n";
        exit 1;
    }

    $this->{'cfg'} = $VAR1;
}

sub log($) {
    my ($this,$msg) = @_;

    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) =
        localtime(time());

    if ( ! open LOG, ">>" . $this->{'cfg'}->{'logfile'} ) {
        print "ERROR: Failed to open " . $this->{'cfg'}->{'logfile'} . ", $!\n";
        exit 1;
    }
    my $logLine = sprintf("%04d-%02d-%02d:%02d:%02d:%02d %s\n",
                          $year + 1900, $mon + 1, $mday,
                          $hour, $min, $sec,
                          $msg);
    if ( ! print LOG $logLine ) {
        print "ERROR: Failed to write to  " . $this->{'cfg'}->{'logfile'} . ", $!\n";
        exit 1;
    }
    close LOG;
}

sub parseConfigFile($) {
    my ($this,$configFile) = @_;

    if ( $main::DEBUG > 4 ) { print "clariion::parseConfigFile: $configFile\n"; }

    if ( ! ( open CONFIG, $configFile ) ) {
        print "ERROR: Failed to open config file $configFile, $!\n";
        exit 1;
    }
    my @lines = <CONFIG>;
    close CONFIG;

    for my $line ( @lines ) {
        if ( $line !~ /^$/ && $line !~ /^#/ ) {
             chop $line;
             if ( $line =~ /^agentip=([\d\.]+)/ ) {
                 $this->{'cfg'}->{'agentip'} = $1;
             } elsif ( $line =~ /^vnx=([^:]+):([^:]+):([^:]+):([^:]+):([^:]+):([^:]+)$/ ) {
                 my ($clariionName,$userName,$password,$spA,$spB,$storGrp) = ($1,$2,$3,$4,$5,$6);
		 #hidning password 
		 $storage_grp_pass = $password;
                 my $clariionCfg = {
                     'user' => $userName,
#                     'pass' => $password,
                     'spa'  => $spA,
                     'spb'  => $spB,
                     'sg'   => $storGrp
                 };
                 $this->{'cfg'}->{'clariion'}->{$clariionName} = $clariionCfg;
             } else {
                 print "ERROR: Invalid line in config file $line";
                 exit 1;
             }
            }
    }
}

sub parseListSessions($) {
    my ($this,$r_output) = @_;

    my @sessions = ();

    my $r_session;
    foreach my $line ( @{$r_output} ) {
        if ( $line =~ /^Name of the session:\s+ (.*)/ ) {
            my $name = $1;
            if ( $main::DEBUG > 7 ) { print "clariion::parseListSessions matched session $name\n"; }
            $r_session = {
                'name' => $name
            };
        } elsif ( defined $r_session && $line =~ /^Session state:\s+(\S+)/ ) {
            $r_session->{'state'} = $1;
        } elsif ( defined $r_session && $line =~ /^List of Target LUN Number:\s+(.*)/ ) {
            my @lunList = split (", ", $1);
            $r_session->{'lunlist'} = \@lunList;
        } elsif ( defined $r_session && $line =~ /^$/ ) {
            if ( $main::DEBUG > 7 ) { print Dumper("clariion::parseListSessions blank line r_session", $r_session); }

            if ( exists $r_session->{'state'} && exists $r_session->{'lunlist'} ) {
                push @sessions, $r_session;
            } else {
                print "ERROR: Failed to parse listsessions output";
                exit 1;
            }

            $r_session = undef;
        }
    }

    return \@sessions;
}

sub parseLUNids($) {
    my ($this,$r_lunIdArray) = @_;
    if ( $main::DEBUG > 4 ) { print "clariion::parseLUNids: " . join(" ", @{$r_lunIdArray}) . "\n"; }

    my %lunsByClariion = ();
    foreach my $lunID ( @{$r_lunIdArray} ) {
        #Added regex for vnx@ALL
        my ($clariion,$lun) = $lunID =~ /^([^@]+)@(\d+)$/;
        if ( ! $clariion ) {
            print "ERROR: Invalid format for id $lunID\n";
            exit 1;
        }

        if ( ! exists $this->{'cfg'}->{'clariion'}->{$clariion} ) {
            print "ERROR: Unknown EMC SAN $clariion in id $lunID\n";
            exit 1;
        }

        if ( ! exists $lunsByClariion{$clariion} ) {
            $lunsByClariion{$clariion} = [];
        }
        push @{$lunsByClariion{$clariion}}, $lun;
    }

    return \%lunsByClariion;
}

sub saveConfiguration() {
    my ($this) = @_;

    # my @cfgLines = ();
    # foreach my $key ( sort keys %{$this->{'cfg'}} ) {
    #   if ( $key eq 'clariion' ) {
    #       my @clariionNames = sort keys %{$this->{'cfg'}->{'clariion'}};
    #       push @cfgLines, sprintf "%clariion=%s\n", join(",", @clariionNames);
    #       foreach my $clariionName ( @clariionNames ) {
    #           my $r_cfg = $this->{'cfg'}->{'clariion'}->{$clariionName};
    #           foreach my $clarParam ( keys %{$r_cfg} ) {
    #               push @cfgLines, sprintf "%s.%s=%s", $clariionName, $clarParam, $r_cfg->{$clarParam};
    #           }
    #       }
    #   }
    # }
    my $cfgStr = Dumper($this->{'cfg'});

    my $configFile = getRootDir() . "/etc/clariion.conf";
    if ( ! ( open CONFIG, ">$configFile" ) ) {
        print "ERROR: Failed to open configuration file $configFile, $@\n";
        exit 1;
    }
    if ( ! ( print CONFIG $cfgStr ) ) {
        print "ERROR: Failed to write configuration file $configFile, $@\n";
        exit 1;
    }
    close CONFIG;
}

sub updateAgentConfig() {
    my ($this) = @_;

    if ( ! open CONFIG, $AGENT_CONFIG_FILE ) {
        print "ERROR: Failed to open $AGENT_CONFIG_FILE, $!\n";
        exit 1;
    }

    my @configLines = <CONFIG>;
    close CONFIG;

    my %spIP = ();
    foreach my $clariion ( keys %{$this->{'cfg'}->{'clariion'}} ) {
        $spIP{$this->{'cfg'}->{'clariion'}->{$clariion}->{'spa'}} = $clariion . " SP A";
        $spIP{$this->{'cfg'}->{'clariion'}->{$clariion}->{'spb'}} = $clariion . " SP B";
    }

    foreach my $line ( @configLines ) {
        if ( $line =~ /^user\s+system@([\d\.]+)/ ) {
            my $ip = $1;
            delete $spIP{$ip};
        }
    }

    my @missingSP = keys %spIP;
    if ( $#missingSP != -1 ) {
        #
        # Backup old config
        #
        if ( ! open CONFIG_BAK, ">$AGENT_CONFIG_FILE" . ".bak" ) {
            print "ERROR: Cannot backup $AGENT_CONFIG_FILE, $!\n";
            exit 1;
        }
        print CONFIG_BAK @configLines;
        close CONFIG_BAK;

        #
        # Write new config
        #
        if ( ! open CONFIG, ">$AGENT_CONFIG_FILE" ) {
            print "ERROR: Cannot open $AGENT_CONFIG_FILE for writing, $!\n";
            exit 1;
        }
        print CONFIG @configLines;
        # Append the missing SPs
        foreach my $sp ( @missingSP ) {
            printf CONFIG "# %s\n", $spIP{$sp};
            printf CONFIG "user system@%s\n", $sp;
        }
        close CONFIG;
    }

    # my $hostname = `hostname`;
    # chop $hostname;
    # my $packed_ip = gethostbyname($hostname);
    # if ( ! defined $packed_ip ) {
    #   print "ERROR: Failed to resolve hostname $hostname, $!\n";
    #   exit 1;
    # }
    # my $hostip = inet_ntoa($packed_ip);

    #
    # Configure the agent to bind to the correct NIC
    #
    if ( ! open ID, ">$AGENT_ID_FILE" ) {
        print "ERROR: Cannot open $AGENT_ID_FILE, $!\n";
        exit 1;
    }
    print ID $this->{'cfg'}->{'agenthostname'} . "\n";
    print ID $this->{'cfg'}->{'agentip'} . "\n";
    close ID;

    if ( -r $HOST_ID_FILE ) {
        if ( ! unlink($HOST_ID_FILE) ) {
            print "ERROR: Cannot remove $HOST_ID_FILE, $!\n";
            exit 1;
        }
    }
}

sub validateSnapIds($$) {
    my ($this,$r_snapIdArray,$r_clariionList) =@_;

    if ( $main::DEBUG > 4 ) { print "clariion::validateSnapIds: " . join(" ", @{$r_snapIdArray}) . "\n"; }

    my %specifiedClariions = ();
    my $theSessionName = undef;
    foreach my $snapId ( @{$r_snapIdArray} ) {
        my ($clariion,$lun,$sessionName) = $snapId =~ /^([^@]+)@([^@]+)@([^@]+)$/;
        if ( ! defined $clariion ) {
            print "ERROR: Invalid snapid $snapId\n";
            exit 1;
        }
        if ( ! exists $this->{'cfg'}->{'clariion'}->{$clariion} ) {
            print "ERROR: Invalid snapid $snapId, unknown EMC SAN $clariion\n";
            exit 1;
        }

        if ( defined $theSessionName ) {
            if ( $theSessionName ne $sessionName ) {
                print "ERROR: Inconsistent snapid $snapId, session name differents from $theSessionName\n";
                exit 1;
            }
        } else {
            $theSessionName = $sessionName;
        }
        $specifiedClariions{$clariion}++;
    }

    foreach my $clariion ( keys %specifiedClariions ) {
        push @{$r_clariionList}, $clariion;
    }

    return $theSessionName;
}

#
# Helper methods
#
sub ask($) {
    my $prompt = @_;
    print @_, " : ";
    my $answer = <STDIN>;
    chop $answer;

    return $answer;
}

sub getRootDir() {
    my $scriptName = $0;
    my $scriptDir = dirname($scriptName);
    my $rootDir = dirname($scriptDir);

    return $rootDir . "/plugins/vnx";
}

1;

