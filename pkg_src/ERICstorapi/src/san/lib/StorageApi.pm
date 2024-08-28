package StorageApi;

our $OKAY   = "OKAY";
our $FAILED = "FAILED";
our $ROLLING_BACK = "ROLLING_BACK";

sub new() {
    die "ERROR: The new method has not been implemented";
}

sub configure($) {
    my ($this,$configFile) = @_;
    die "ERROR: The configure method has not been implemented";
}

#
# List the snapshots available for the specified LUNs
#
# Parameters:
#  None
#
# Return:
#  An array of hashes which each hash contains the following fields
#   device => CTD device corresponding to the LUN
#   lunid  => Identifier of the LUN,  This will be taken as input to
#             the other methods in the API
#   desc   => Free text description of the LUN, content of this is specific
#             to the API Implementation
#
sub listLUNs() {
    die "ERROR: The listLUNs method has not been implemented";
}

#
# List the snapshots available for the specified LUNs
#
# Parameters:
#  r_lunIdArray: Array of IDs the LUNs for which to list snapshots, the IDs
#                must match what is returned by listLUNs
#
# Return:
#  An array of hashes where each hash contains the following fields
#   lunid  => Identifier of the LUN
#   snapid => Identifier of the Snapshot of the LUN, content of this is specific
#             to the API Implementation.
#   state   => $StorageApi::OKAY, $StorageApi::FAILED $StorageApi::ROLLING_BACK
#
sub listSnapshots($) {
    my ($this,$r_lunIdArray) = @_;
    die "ERROR: The listSnapshots method has not been implemented";
}

#
# Creates a snapshot for each of the specified LUNs
#
# Parameters:
#  r_lunIdArray: Array of IDs the LUNs for which to list snapshots, the IDs
#                must match what is returned by listLUNs
#  tag: User label for the snapshot. The API Implementation MAY use this when
#       creating it's snap shots
# Return:
#  An array of hashes where each hash contains the following fields
#   lunid  => Identifier of the LUN
#   snapid => Identifier of the Snapshot of the LUN, content of this is specific
#             to the API Implementation.
#
sub createSnapshot($) {
    my ($this,$r_lunIdArray,$tag) = @_;
    die "ERROR: The createSnapshot method has not been implemented";
}

#
# Deletes the specified a LUN snapshots
#
# Parameters:
#  r_snapIdArray: Array of IDs the LUN snapshots.
#                 Note: This should all belong to the same snapshot "set", i.e.
#                 they should have all been created in the same createSnapshot
#                 call
#
# Return:
#  None
#
sub deleteSnapshot($) {
    my ($this,$r_snapIdArray) = @_;
    die "ERROR: The deleteSnapshot method has not been implemented";
}

#
# Revert the content of the specified a LUN snapshots
#
# Implementation should return when the host "sees" the contents of the
# snapshot via the LUN
#
# Parameters:
#  r_snapIdArray: Array of IDs the LUN snapshots.
#                 Note: This should all belong to the same snapshot "set", i.e.
#                 they should have all been created in the same createSnapshot
#                 call
# Return:
#  None
#
sub rollbackSnapshot($) {
    my ($this,$r_snapIdArray) = @_;
    die "ERROR: The rollbackSnapshot method has not been implemented";
}

1;

