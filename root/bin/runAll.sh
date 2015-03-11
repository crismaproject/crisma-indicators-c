#!/bin/bash
#
# Run all needed for contextBroker

# logging output from wps:
[ -e /var/www/wps/ ] || mkdir /var/www/wps/
chown www-data:www-data /var/www/wps/

MYIP=$(grep ${HOSTNAME} /etc/hosts | awk '{print $1}'); export MYIP

if [ "xORION_ENDPOINT" == "x" ]
then
    ORION_ENDPOINT="http://${ORION_PORT_1026_TCP_ADDR}:${ORION_PORT_1026_TCP_PORT}"
    export ORION_ENDPOINT
fi

# save some settings for later use
env | grep ORION | sed -e's/=/="/' -e's/$/"/' > e.py
echo MYIP=\"$(grep ${HOSTNAME} /etc/hosts | awk '{print $1}')\" >> e.py

## give orion service some time to come up
#while ! curl -s "${ORION_ENDPOINT}/version" | grep -q version; do echo waiting for orion..; sleep 3; done
## Register at the orion context broker
#/root/bin/registerAtOrion.py --subscribe >> /var/log/orion.log

# Register at the orion context broker; This includes retrys.
/root/bin/registerAtOrion2.py > /var/www/orion.log 2>&1 &

/usr/sbin/apache2ctl -D FOREGROUND


