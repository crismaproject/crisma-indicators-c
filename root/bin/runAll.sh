#!/bin/bash
#
# Run all needed for contextBroker


MYIP=$(grep ${HOSTNAME} /etc/hosts | awk '{print $1}'); export MYIP

# save some settings for later use
env | grep ORION | sed -e's/=/="/' -e's/$/"/' > e.py
echo MYIP=\"$(grep ${HOSTNAME} /etc/hosts | awk '{print $1}')\" >> e.py


# Register at the orion context broker
/root/bin/registerAtOrion.py --subscribe >> /var/log/orion.log

/usr/sbin/apache2ctl -D FOREGROUND


