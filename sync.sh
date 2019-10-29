#!/usr/bin/env bash
EXCLUDEFLAGS="
--exclude server.ini
--exclude .monitor_last_printed_file.txt
--exclude .print_counter.txt
--exclude *.pyc
--exclude dynamic_data
"
[ $# -le 0 ] && echo "$0 <ip>" && exit 1
#IP=192.168.4.1
IP=$1
set -x
rsync -avz $EXCLUDEFLAGS -e ssh ./ pi@${IP}:/home/pi/shrine/
set +x
