#!/usr/bin/env bash
ethip=$(ip addr show dev eth0 | grep 'inet ' | awk '{print $2}' | tr -d ' ')
ssid=$(/sbin/iwconfig 2>/dev/null  | grep -i ssid | sed -e 's/.*SSID://')
wlanip=$(ip addr show dev wlan0 | grep 'inet ' | awk '{print $2}' | tr -d ' ')

echo "eth ip: $ethip"
echo "wlan ssid: $ssid"
echo "wlan ip: $wlanip"

#echo Printers available:
#lpstat -e
# full:
#lp stat -t

# setup wifi
# https://desertbot.io/blog/headless-raspberry-pi-4-ssh-wifi-SETUP