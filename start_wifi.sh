#!/usr/bin/env bash
eval $(sed -e '1,/\[wifi\]/d' -e 's/ *= */=/g' server.ini)
echo "Setup WIFI"
echo "with SSID: $ssid"
echo "password: $password"
echo "(only need to do this once or on SSID change)"

cat <<EOF > /etc/wpa_supplicant/wpa_supplicant.conf
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=DE
network={
 ssid="$ssid"
 psk="$password"
}
EOF
