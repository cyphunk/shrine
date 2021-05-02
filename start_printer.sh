#!/usr/bin/env bash
eval $(grep "printer_name" server.ini | sed -e 's/ *= */=/g')
eval $(grep "printer_serial_baud" server.ini | sed -e 's/ *= */=/g')
test "${printer_serial_baud}" = "" -a printer_serial_baud=19200

echo "SETUP '${printer_name}'"
if test -e /usr/share/cups/model/zjiang/ZJ-58.ppd; then
    echo "Assuming adafruit ZJ-80 driver (raspberrypi?)"
    DRIVER=/usr/share/cups/model/zjiang/ZJ-58.ppd
elif test -e /usr/share/cups/model/zjiang/zj80.ppd; then
    echo "Assuming klirichek zj80 driver (PC?)"
    DRIVER=/usr/share/cups/model/zjiang/zj80.ppd
fi

if grep -qi raspbian /etc/issue; then
    true
else
    systemctl start org.cups.cupsd.service \
    || systemctl start cups
fi

USBURI=$(/usr/lib/cups/backend/usb 2>/dev/null | awk '{print $2}')
if test "$USBURI" = ""; then
    # RPi4 /dev/serial0, RPi3 /dev/ttyAMA0
    test -e /dev/serial0 \
    && URI="serial:/dev/serial0?baud=${printer_serial_baud}" \
    || URI="serial:/dev/ttyAMA0?baud=${printer_serial_baud}"
    echo "Assume serial (non usb) URI: $URI"
else
    URI="$USBURI"
    echo "Found USB URI: $URI"
fi

set -x
/usr/sbin/lpadmin -p "${printer_name}" -E -v $URI -P $DRIVER
set +x

# clear queue if it exists
lpstat -o
cancel -a

#echo "sending status test"
#echo "." | lp -d ${printer_name}

#echo "Printer options"
#lpoptions -d PRINTER -l
# PageSize/Media Size: *X48MMY64MM X48MMY210MM X48MMY297MM X48MMY3276MM
# FeedDist/Feed distance after print: 0feed3mm 1feed6mm 2feed9mm 3feed12mm *4feed15mm 5feed18mm 6feed21mm 7feed24mm 8feed27mm 9feed30mm 10feed33mm 11feed36mm 12feed39mm 13feed42mm 14feed45mm
# BlankSpace/Blank space at page's end: 0Print *1NoPrint
# CashDrawer1Setting/Cash Drawer 1: *0NotCashDrawer1 1NotCashDrawer1BeforePrinting 2NotCashDrawer1BeforePrinting
# CashDrawer2Setting/Cash Drawer 2: *0NotCashDrawer2 1NotCashDrawer2BeforePrinting 2NotCashDrawer2BeforePrinting

# Change global options
# lpoptions -d PRINTER -o FeedDist=0feed3mm
