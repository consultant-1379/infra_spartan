#!/bin/bash
./nascli create_fs - - - 
./nascli create_share - -
./nascli create_cache - - -
./nascli create_snapshot - - - snap1 -
./nascli add_client - $(hostname) ro,no_root_squash home/snap1
#./nascli refresh_snapshot - snap1 -
#./nascli rollback_snapshot - snap1 -
#./nascli delete_fs -
