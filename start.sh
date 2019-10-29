#!/usr/bin/env bash
echo "## Initialize shrine code ##"

SH_SOURCE=${BASH_SOURCE:-$_}

BASE="$(dirname $(readlink -f $SH_SOURCE))"
cd $BASE

if [[ $- != *i* ]]; then
    # not interactive mode, so running from init script
    # pipe log 
    # limit log to 10000 lines:
    tail -10000 ${BASE}/shrine.log > .concat
    mv .concat ${BASE}/shrine.log
    exec > >(tee -a -i ${BASE}/shrine.log)
    echo -e "\n#\n#\n# start $(date)\n#\n#"
fi

if grep -qi raspbian /etc/issue; then
    echo "## On Raspberry Pi"
    echo "## wifi init"
    ./start_wifi.sh 2>&1
fi
echo "## printer init"
./start_printer.sh 2>&1

# 10 seconds we hope is enough to connect to wifi and get ip address
# run in background so that web server can remain in thread
eval $(grep "printer_name" server.ini | sed -e 's/ *= */=/g')
(
sleep 10
echo "## status"
./status.sh 2>&1
if lpstat -p | grep -q enabled; then 
    echo "print status"
    (./status.sh; echo -e "\n\n") | lp -d "${printer_name}" -o raw "-"
    # if test -e /dev/serial0 ; then
    #     stty -F /dev/serial0 19200
    #     ./status.sh > /dev/serial0
    # elif test -e /dev/ttyAMA0
    #     stty -F /dev/serial0 19200
    #     ./status.sh > /dev/serial0
    # else
        
fi
) &

echo "## start web server"
#cd web && sudo -u pi python3 server.py
# run as root so we get port 80
python3 server.py 2>&1
