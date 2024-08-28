package unity;

#
# This package implements the blkcli plugin for Dell EMC Unity arrays
#
# It requires the uemcli program to be already installed (part of  UnisphereCLI-Linux)
# It does NOT require the Unisphere Agent
#
use strict;
use warnings;

use Data::Dumper;
use File::Basename;
use Socket;
use FileHandle;
use IPC::Open2;

use StorageApi;

our @ISA = qw(StorageApi);

our $UEMCLI = "/usr/bin/uemcli";
our $RESCAN_SCSI_BUS = "/usr/bin/rescan-scsi-bus.sh";
our $MULTIPATH = "/usr/sbin/multipath";

our $FC_HOST_DIR = "/sys/class/fc_host";
our $ENDECRYPT_SCRIPT = '/ericsson/storage/san/plugins/unity/lib/encryptdecrypt.py';
##########################################################################
#
# API Methods
#
##########################################################################

sub new() {
    my $class = shift;
    my $this = {};
    bless($this,$class);
    return $this;
}

#
# This method performs the following tasks
# - Save the configuration (without the password) to file
# - Save the user credentials to the Unisphere CLI "secure lockbox"
# - Register the host with the array
# - Register the hosts HBAs as initiators for this host with the array
# - Connect the LUNs specified in the configuration to this host
# - Rescan the SCSI bus for the LUN ids we created when connecting the LUNs
#
# The $configFile attribute is mandatory. The file pointed to by $configFile should
# contain a single line with the following format
#
# unity=<user_name>:<password>:<IP Address>:<LUN IDs>:<CG ID>
#
# where
#  user_name, password and IP Address are the login details for the Unity array
#    Note: The user_name and password must not contain a ":" character
#  LUN IDs a comma separated list of CLI IDs for the LUNs to be connected to this host
#  CG ID is the CLI ID of the consistency group of the LUNs that are to part of the snapshot
#    The LUNs to be snapped must have already been added to this consistency group
#
# Note: This method assumes a "green field" state, i.e. that this host is not currently registered
#       with the array.
# Note: All other API methods can only be called after the successful completion of the configure method
#
sub configure($) {
    my ($this,$configFile) = @_;

    if ( $main::DEBUG > 3 ) { print "unity::configure\n" }

    if ( defined $configFile ) {
		$this->parseConfigFile($configFile);                
    }
    else {
	my $clariionName;
        do {
            $clariionName = ask("Enter yes to add unity host [return to exit]");
            if ( $clariionName !~ /^$/ ) {
                $this->getClariionConfiguration($clariionName);
            }
        } while ( $clariionName !~ /^$/ );
    }   

    #
    # Save the configuration (without the password) to file
    #
    $this->saveConfiguration();

    $this->initialize();

    #
    # Save the user credentials to the Unisphere CLI "secure lockbox"
    #
    $this->saveUserCreds();

    #
    # Register the host with the array
    # Register the hosts HBAs as initiators for this host with the array
    #
    my $hostId = $this->registerHostAndHBAs();


    #
    # Connect the LUNs specified in the configuration to this host
    #
    my $r_hlusForThisHost = $this->connectLUNs($hostId);

    #
    # Rescan the SCSI bus for the LUN ids we created when connecting the LUNs
    #
    # Now that the LUNs have been added, force rescan to find the new devices
    print "INFO: Performing scan for LUNs\n";
    my $rescanCmd = $RESCAN_SCSI_BUS . " -r -f --luns=" . join(",", @{$r_hlusForThisHost});
    $this->execCmd($rescanCmd);

    return 0;
}


#
# This method performs the following tasks
# - Use multipath to get the list of multi path devices we can see and the associated WWN
# - Use uemcli /stor/prov/luns/lun show to list all LUNs and find the LUNs with whose
#       WWN matches the WWN we got from multipath
#
sub listLUNs() {
    my ($this) = @_;
    if ( $main::DEBUG > 3 ) { print "unity::listLUNs\n"; }

    $this->initialize();

    # Make hash of WWN to multipath device
    my @output = $this->execCmd($MULTIPATH . " -l");
    my %wwnToDeviceMap = ();
    foreach my $line ( @output ) {
        if ( $line =~ /^(mpath[a-z]+)\s+\(([0-9a-f]+)\)/ ) {
            my ($device,$wwn) = ($1,$2);
            # Strip the leading character of the wwn
            # https://access.redhat.com/articles/17054#NR5
            $wwn =~ s/^.//;
            $wwnToDeviceMap{formatName($wwn)} = $device;
        }
    }
    if ( $main::DEBUG > 5 ) { print Dumper("unity::listLUNs wwnToDeviceMap: ", \%wwnToDeviceMap); }

    # Get the LUNs on the array and find the ones where we have a
    # multipath device with a matching WWN
    my $cmd = $this->baseCommand() . " -sslPolicy store /stor/prov/luns/lun show -output csv -detail";
    @output = $this->execCmd($cmd);
    my $header = shift @output;
    my $r_fieldIndex = parseHeader($header);
    my @luns = ();
    foreach my $line ( @output ) {
        my $r_fields = splitAndStrip($line);
        my $wwn = $r_fields->[$r_fieldIndex->{"WWN"}];
        my $device = $wwnToDeviceMap{$wwn};
        if ( defined $device ) {
            push @luns, {
                'device' => $device,
                'lunid'  => $r_fields->[$r_fieldIndex->{"ID"}],
                'desc'   => $r_fields->[$r_fieldIndex->{"Name"}]
            };
        }
    }
    return \@luns;
}

#
# This method performs the following tasks
# - Use uemcli /prot/snap -source <CG ID> show to get the ID of any
#     snapshot sessions on the configured consistency group
# - For each snapshot session
#      For each LUN in r_lunIdArray
#          add a result containing the lunid,snapshot session state and session id
#
sub listSnapshots ($) {
    my ($this,$r_lunIdArray) = @_;
    if ( $main::DEBUG > 3 ) { print "unity::listSnapshots: " . join(" ", @{$r_lunIdArray}) . "\n"; }

    $this->initialize();
    my @snapshots = ();

    # Get the list of snapshot sessions on the consistency group
    my $cmd = sprintf(
        "%s -sslPolicy store /prot/snap -source %s show -output csv",
        $this->baseCommand(),
        $this->{'cfg'}->{'unity'}->{'csgrpid'}
    );
    my @output = $this->execCmd($cmd);

    my $header = shift @output;
    my $r_fieldIndex = parseHeader($header);
    my @snaps = ();
    foreach my $line ( @output ) {
        $line =~ s/([^"])(,)/$1/g;
        my $r_fields = splitAndStrip($line);
        my $state = $r_fields->[$r_fieldIndex->{'State'}];
        my $mappedState = $StorageApi::FAILED;
        if ( $state eq "Ready" ) {
            $state = $StorageApi::OKAY;
        }

        push @snaps, {
            'id' => $r_fields->[$r_fieldIndex->{'ID'}],
            'name' => $r_fields->[$r_fieldIndex->{'Name'}],
            'state' => $state,
            'members' => $r_fields->[$r_fieldIndex->{'Members'}]
        };
    }

    foreach my $r_snap ( @snaps ) {
        my @spl = split(' ', "$r_snap->{'members'}");
        my %params = map { $_ => 1 } @spl;
        foreach my $lunid ( @{$r_lunIdArray} ) {
            #Condition for args check for -ids with csgrpid
            if ("$this->{'cfg'}->{'unity'}->{'csgrpid'}" =~ "$lunid" ||  exists($params{"$lunid"})) {
                my $r_snapshot = {
                   'lunid'  => $lunid,
                   'snapid' => $r_snap->{'id'} . '@' . $r_snap->{'name'},
                   'state'  => $r_snap->{'state'}
               };
               push @snapshots, $r_snapshot;
           }
           else {
                print "FAILED: $lunid is not part of Consitency Group $this->{'cfg'}->{'unity'}->{'csgrpid'}\n";
                exit 1;
            }
        }
    }
    return \@snapshots;
}


#
# This method performs the following tasks
# - Use uemcli /prot/snap create to create a snapshot of the
#    configured consistency group
#  - For each LUN in r_lunIdArray
#          add a result containing the lunid,snapshot id
#
sub createSnapshot($$) {
    my ($this,$r_lunIdArray,$tag) = @_;
    if ( $main::DEBUG > 3 ) {
        print "unity::createSnapshot: tag=$tag luns=" . join(" ", @{$r_lunIdArray}) . "\n";
    }

    $this->initialize();

    my $cmd = sprintf(
        "%s -sslPolicy store /prot/snap create -name \"%s\" -source %s",
        $this->baseCommand(),
        $tag,
        $this->{'cfg'}->{'unity'}->{'csgrpid'}
    );
    my @output = $this->execCmd($cmd);
    my $id = undef;
    foreach my $line ( @output ) {
        if ( $line =~ /^ID = (\S+)/ ) {
            $id = $1;
        }
    }
    if ( ! defined $id ) {
        print "ERROR: Could not get ID from printout\n";
        exit 1;
    }

    my @results = ();
    foreach my $lunid ( @{$r_lunIdArray} ) {
        my $r_snapshot = {
            'lunid' => $lunid,
            'snapid' => $id . '@' . $tag
        };
        push @results, $r_snapshot;
    }


    return \@results;
}

#
# This method performs the following tasks
# - Parse the Ids and make sure they all belong to the same session
# - Use uemcli /prot/snap -id <id> delete to delete the snapshot
#
sub deleteSnapshot($$) {
    my ($this,$r_snapIdArray) = @_;
    if ( $main::DEBUG > 3 ) {
        print "unity::deleteSnapshot: snapids=" . join(" ", @{$r_snapIdArray}) . "\n";
    }

    $this->initialize();

    my $snapID = $this->validateSnapIds($r_snapIdArray);

    my $cmd = sprintf(
        "%s -sslPolicy store /prot/snap -id %d detach",
        $this->baseCommand(),
        $snapID
    );
    $this->execCmd($cmd);

   $cmd = sprintf(
        "%s -sslPolicy store /prot/snap -id %d delete",
        $this->baseCommand(),
        $snapID
    );
    $this->execCmd($cmd);

}

#
# This method performs the following tasks
# - Parse the Ids and make sure they all belong to the same session
# - Use uemcli  /prot/snap -id <id> restore to rollback the snapshot
#   Note: On Unity, when you rollback a snapshot, Unity automatically
#         creates another "backup" snapshot
# - Use uemcli /prot/snap -id <id> delete to delete the backup snapshot
#
sub rollbackSnapshot($) {
    my ($this,$r_snapIdArray) = @_;

    if ( $main::DEBUG > 3 ) {
        print "unity::deleteSnapshot: snapids=" . join(" ", @{$r_snapIdArray}) . "\n";
    }

    $this->initialize();

    my $snapID = $this->validateSnapIds($r_snapIdArray);

    # Rollback the snapshot
    # This command generates the following prompt
    #
    # WARNING, Data corruption can occur if hosts are connected to the storage resource during a snapshot restore operation.
    # EMC strongly recommends that you disconnect (unmount) all connected hosts before proceeding with a snapshot restore operation.  The system automatically  creates a restore point snapshot on the storage resource before beginning a snapshot restore operation in case of unintentional data corruption.
    # Are you sure that you want to restore the snapshot?
    # yes / no / y / n:
    #
    # So we have to send a yes
    my $cmd = sprintf(
        "%s /prot/snap -id %d restore -backupName backup_%d",
        $this->baseCommand(),
        $snapID,
        $snapID
    );
    my @output = $this->execCmdWithInput($cmd,"yes");

    # Delete the auto-created backup snapshot
    my $backupID = undef;
    foreach my $line ( @output ) {
        if ( $line =~ /ID = (\d+)/ ) {
            $backupID = $1;
        }
    }
    if ( ! defined $backupID ) {
        print "ERROR: Could not get ID of backup snapshot from printout\n";
        exit 1;
    }

    $cmd = sprintf(
        "%s /prot/snap -id %d delete",
        $this->baseCommand(),
        $backupID
    );
    $this->execCmd($cmd);
}


##########################################################################
#
# Private methods
#
##########################################################################

sub baseCommand($) {
    my ($this) = @_;

    my $r_unityCfg = $this->{'cfg'}->{'unity'};
    my $cmd = $UEMCLI . " -noHeader -d " . $r_unityCfg->{'sp'};

    return $cmd;
}

sub saveUserCreds() {
    my ($this) = @_;
    my $r_unityCfg = $this->{'cfg'}->{'unity'};
    #Added If condition to check user input
    if ( ! exists $r_unityCfg->{'user'} ) {
	print "ERROR: Nothing to add/configure\n";
	exit 1
    }
    my $cmd = sprintf("%s -d %s -silent -user %s -p %s -saveUser",
                      $UEMCLI,
                      $r_unityCfg->{'sp'},
                      $r_unityCfg->{'user'},
                      $r_unityCfg->{'pass'}
                  );
    $this->execCmd($cmd);
}

sub execCmd($) {
    my ($this,$cmd) = @_;
    if ( $cmd =~ /--encrypt/ ){
        $this->log("exec start: Encrypting the password");
    }
    elsif ( $cmd =~ /-p/ ){
	$this->log("exec start: Establishing Passwordless connection from ENIQ to SAN");
    }
    else {
        $this->log("exec start: $cmd");
    }
    if ( $main::DEBUG > 0 ) { print "unity::execCmd cmd = $cmd\n"; }

    #$this->log("exec start: $cmd");
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

    if ( $main::DEBUG > 8 ) { print Dumper("unity::execCmd output",\@output); }

    return @output;
}


sub execCmdWithInput($$) {
    my ($this,$cmd,$input) = @_;

    if ( $main::DEBUG > 0 ) { print "unity::execCmdWithInput cmd = $cmd, input= $input\n"; }

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

    if ( $main::DEBUG > 8 ) { print Dumper("unity::execCmd output",\@output); }

    return @output;
}


sub initialize() {
    my ($this) = @_;

    if ( $main::DEBUG > 5 ) { print "unity::initialize\n"; }

    if ( ! exists $this->{'cfg'} ) {
        $this->loadConfiguration();
    }

    if ( ! exists $this->{'cfg'}->{'logfile'} ) {
        $this->{'cfg'}->{'logfile'} = getRootDir() . "/cmd.log";
    }
}

sub loadConfiguration() {
    my ($this) = shift;

    if ( $main::DEBUG > 4 ) { print "unity::loadConfiguration\n"; }

    my $configFile = getRootDir() . "/etc/unity.conf";
    if ( ! -r $configFile ) {
        print "ERROR: Configuration file not found, $configFile";
        exit 1;
    }
    if ( ! ( open CONFIG, "$configFile" ) ) {
        print "ERROR: Failed to open configuration file $configFile, $@\n";
        exit 1;
    }
    my @cfgLines = <CONFIG>;
    close CONFIG;

    my $cfgStr = join('',@cfgLines);
    if ( $main::DEBUG > 7 ) {
        print "unity::loadConfiguration cfgStr\n" . $cfgStr;
    }
    my $VAR1;
    eval($cfgStr);
    if ( $@ ) {
        print "ERROR: Failed to load unity configuration, $@\n";
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

    # Make sure we don't log the password
    $logLine =~ s/-p ".*"$/-p PASSWORD/;

    if ( ! print LOG $logLine ) {
        print "ERROR: Failed to write to  " . $this->{'cfg'}->{'logfile'} . ", $!\n";
        exit 1;
    }
    close LOG;
}

sub parseConfigFile($) {
    my ($this,$configFile) = @_;

    if ( $main::DEBUG > 4 ) { print "unity::parseConfigFile: $configFile\n"; }

    if ( ! ( open CONFIG, $configFile ) ) {
        print "ERROR: Failed to open config file $configFile, $!\n";
        exit 1;
    }
    my @lines = <CONFIG>;
    close CONFIG;

    for my $line ( @lines ) {
        if ( $line !~ /^$/ && $line !~ /^#/ ) {
            chop $line;
            if ( $line =~ /^unity=([^:]+):([^:]+):([^:]+):([^:]+):(\S+)$/ ) {
                my ($userName,$password,$sp,$lunIds,$csgrpid) = ($1,$2,$3,$4,$5);
                my $unityCfg = {
                    'user' => $userName,
                    'pass' => $password,
                    'sp'  => $sp,
                    'lunids'   => $lunIds,
                    'csgrpid' => $csgrpid
                };
                $this->{'cfg'}->{'unity'} = $unityCfg;
            } else {
                print "ERROR: Invalid line in config file $line";
                exit 1;
            }
        }
    }
}
sub enDecrypt($$) {
    my ($this, $passString) = @_;
    my $cmd = $ENDECRYPT_SCRIPT . ' --encrypt ' . "$passString";
    if ( $main::DEBUG > 4 ) { print "unity::enDecrypt: Password\n"; }
    #check script is exist or not
    if ( ! ( -e $ENDECRYPT_SCRIPT ) ) {
	print "ERROR: Encryption Script not found\n";
        exit 1;	
    }
    if ( ! exists $this->{'cfg'}->{'logfile'} ) {
        $this->{'cfg'}->{'logfile'} = getRootDir() . "/cmd.log";
    }
    $this->execCmd($cmd);
    print "successfully encrypted the password\n";
}
sub saveConfiguration() {
    my ($this) = @_;

    # Copy the config
    my $VAR1 = undef;
    eval(Dumper($this->{'cfg'}));
    delete $VAR1->{'unity'}->{'pass'};

    my $cfgStr = Dumper($VAR1);

    my $configFile = getRootDir() . "/etc/unity.conf";    
    my $passvar = $this->{'cfg'}->{'unity'}->{'pass'};
    if ( ! ( open CONFIG, ">$configFile" ) ) {
        print "ERROR: Failed to open configuration file $configFile, $@\n";
        exit 1;
    }
    if ( ! ( print CONFIG $cfgStr ) ) {
        print "ERROR: Failed to write configuration file $configFile, $@\n";
        exit 1;
    }
    close CONFIG;  
    $this->enDecrypt($passvar)
}

sub validateSnapIds($$) {
    my ($this,$r_snapIdArray) =@_;

    if ( $main::DEBUG > 4 ) {
        print "unity::validateSnapIds: " . join(" ", @{$r_snapIdArray}) . "\n";
    }

    my $id = undef;
    foreach my $blkCliId ( @{$r_snapIdArray} ) {
        my ($thisId) = $blkCliId =~ /^(\d+)@/;
        if ( ! defined $thisId ) {
            print "ERROR: Invalid snapid $blkCliId\n";
            exit 1;
        }
        if ( defined $id ) {
            if ( $id ne $thisId ) {
                print "ERROR: Inconsistent snapid $blkCliId, snap id different from $id\n";
                exit 1;
            }
        } else {
            $id = $thisId;
        }
    }

    return $id;
}

sub registerHostAndHBAs($) {
    my ($this) = @_;

    my $r_unityCfg = $this->{'cfg'}->{'unity'};

    #
    # Register the host with the array
    #
    my $hostname = `hostname`;
    chop($hostname);
    print "INFO: Registering host with Unity\n";
    my $baseCmd = $this->baseCommand();
    my $cmd = $baseCmd . " -sslPolicy store /remote/host create -name $hostname -type host";
    my @output = $this->execCmd($cmd);
    my $hostId = undef;
    foreach my $line ( @output ) {
        if ( $line =~ /^ID = (Host_\d+)/ ) {
            $hostId = $1;
        }
    }
    if ( ! defined $hostId ) {
        print "ERROR: Host ID not found in command response\n";
        exit 1;
    }

    #
    # Register the hosts HBAs as initiators for this host with the array
    #
    my $r_wwns = getHbaWWN();
    if ( $#{$r_wwns} == -1 ) {
        print "ERROR: No HBA found\n";
        exit 1;
    }

    # Get the list of HBA WWNs that the Unity can "see"
    @output = $this->execCmd($baseCmd . " /remote/initiator -unregistered show -output csv");
    my $header = shift @output;
    my $r_fieldIndex = parseHeader($header);
    my %initiatorIdByWWN = ();
    foreach my $line ( @output ) {
        my $r_fields = splitAndStrip($line);
        if ( $main::DEBUG > 5 ) { print Dumper("unity::registerHostAndHBAs HostInitiator fields", \$r_fields); }

        # We only want unregistered initiators
        if ( $r_fields->[$r_fieldIndex->{'Host'}] eq "" ) {
            $initiatorIdByWWN{$r_fields->[$r_fieldIndex->{'UID'}]} =
                $r_fields->[$r_fieldIndex->{'ID'}];
        }
    }
    if ( $main::DEBUG > 3 ) { print Dumper("unity::registerHostAndHBAs initiatorIdByWWN", \%initiatorIdByWWN); }

    # Now iterate through the HBAs and find the matching HostInitiator in the Unity and
    # register it as belonging to our Host_ID
    my $wwnsRegistered = 0;
    foreach my $wwn ( @{$r_wwns} ) {
        my $hostInitiatorId = $initiatorIdByWWN{$wwn};
        if ( defined $hostInitiatorId ) {
            # Connect host to the specified storage group
            print "INFO: Registering initiator for $wwn\n";
            $cmd = $baseCmd . " /remote/initiator -id $hostInitiatorId set -host $hostId";
            $this->execCmd($cmd);

            $wwnsRegistered++;
        } else {
            print "WARN: HBA with WWN $wwn is not logged into Unity\n";
        }
    }

    if ( $wwnsRegistered == 0 ) {
        print "ERROR: Found 0 HBAs for this host logged in to Unity\n";
        exit 1;
    }

    return $hostId;
}

sub connectLUNs($$) {
    my ($this,$hostId) = @_;

    my $r_unityCfg = $this->{'cfg'}->{'unity'};

    my @lunIds = split(",", $r_unityCfg->{'lunids'} );
    if ( $#lunIds == -1 ) {
        print "ERROR: 0 LUN ids provided\n";
        exit 1;
    }

    my $baseCmd = $this->baseCommand();
    my $hlu = 0;
    my @hlusForThisHost = ();
    foreach my $lunid ( @lunIds ) {
        # First we have to get any existing HLUs (for other hosts) for this LUN
        my $cmd = sprintf(
            "%s /remote/host/hlu -lun %s show -output csv",
            $baseCmd,
            $lunid
            );
        my @output = $this->execCmd($cmd);
        my @hostIds = ();
        my @hlusForThisLUN = ();
        my $header = shift @output;
        my $r_fieldIndex = parseHeader($header);
        foreach my $line ( @output ) {
            my $r_fields = splitAndStrip($line);
            push @hostIds, $r_fields->[$r_fieldIndex->{"Host"}];
            push @hlusForThisLUN, $r_fields->[$r_fieldIndex->{"LUN ID"}];
        }

        $hlu++;
        # Add the host/hlu for this host
        push @hostIds, $hostId;
        push @hlusForThisLUN, $hlu;

        print "INFO: Adding LUN $lunid to host with HLU $hlu\n";
        $cmd = sprintf(
            "%s -silent /stor/prov/luns/lun -id %s set -lunHosts %s -hlus %s",
            $baseCmd,
            $lunid,
            join(",", @hostIds),
            join(",", @hlusForThisLUN)
            );
        $this->execCmd($cmd);
        push @hlusForThisHost, $hlu;
    }

    return \@hlusForThisHost;
}
#
# Helper methods
#
sub getRootDir() {
    my $scriptName = $0;
    my $scriptDir = dirname($scriptName);
    my $rootDir = dirname($scriptDir);

    return $rootDir . "/plugins/unity";
}

sub ask($) {
    my $prompt = @_;
    print @_, " : ";
    my $answer = <STDIN>;
    chop $answer;

    return $answer;
}
sub formatName($) {
    my ($name) = @_;

    $name =~ s/^0x//;
    my @array_wwn = unpack ("(a2)*", uc($name));
    $name = join (":", @array_wwn);

    return $name;
}

sub splitAndStrip($) {
    my ($line) = @_;

    if ( $main::DEBUG > 6 ) { print "unity::splitAndStrip line=$line"; }

    chop($line);
    my @results = ();
    foreach my $field ( split(",", $line) ) {
        my ($result) = $field =~ /^"(.*)"$/;
        push @results, $result;
    }

    if ( $main::DEBUG > 6 ) { print Dumper("unity::splitAndStrip results", \@results); }
    return \@results;
}

sub parseHeader($) {
    my ($line) = @_;

    my $r_columns = splitAndStrip($line);
    my %columnMap = ();
    for ( my $index = 0; $index <= $#{$r_columns}; $index++ ) {
        $columnMap{$r_columns->[$index]} = $index;
    }

    if ( $main::DEBUG > 6 ) { print Dumper("unity::parseHeader columnMap", \%columnMap); }
    return \%columnMap;
}

sub getHbaWWN() {
    opendir(my $dh, $FC_HOST_DIR) || die "Can't $FC_HOST_DIR";
    my @host_dirs = grep { /^host/ } readdir($dh);
    closedir $dh;

    my @wwns = ();
    foreach my $host ( @host_dirs ) {
        my $nodeNameFile = $FC_HOST_DIR . "/" . $host . "/node_name";
        open (my $node_h, $nodeNameFile) or die "Cannot open $nodeNameFile";
        my $nodeName = <$node_h>;
        close $node_h;
        chop($nodeName);

        my $portNameFile = $FC_HOST_DIR . "/" . $host . "/port_name";
        open (my $port_h, $portNameFile) or die "Cannot open $portNameFile";
        my $portName = <$port_h>;
        chop($portName);
        close $port_h;

        my $wwn = formatName($nodeName) . ":" . formatName($portName);
        if ( $main::DEBUG > 4 ) { print "unity::getHbaWWN host=$host www=$wwn\n"; }
        push @wwns, $wwn;
    }

    return \@wwns;
}

sub getClariionConfiguration($) {
    my ($this,$clariionName) = @_;
    
    if ( $main::DEBUG > 4 ) { print "clariion::getClariionConfiguration: $clariionName\n"; }
    
    my $userName = ask("Enter userid");
    my $password = ask("Enter password");
    my $sp     = ask("Enter SP IP Address");
    my $lunIds   = ask("Enter lunIds Id separated by commo's (Ex: sv_1,sv_2)");
    my $csgrpid  = ask("Enter csgrpid Group ID");
    if ( ! $csgrpid =~ m/res_\d+/)
    {
	print "ERROR: CS Group ID format is wrong";
	exit 1; 
    } 
    my $clariionCfg = {
        'user' => $userName,
        'pass' => $password,
        'sp'  => $sp,
        'lunids'  => $lunIds,
        'csgrpid'   => $csgrpid
    };    
    $this->{'cfg'}->{'unity'} = $clariionCfg;
}

1;
