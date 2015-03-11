#!/usr/bin/env python

""" 
Register this server as listener at the orion eventBroker
"""

"""
    Copyright (C) 2014  AIT / Austrian Institute of Technology
    http://www.ait.ac.at
 
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as
    published by the Free Software Foundation, either version 2 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
 
    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see http://www.gnu.org/licenses/gpl-2.0.html
"""

import os, sys
import json
import io
import requests
import string
import time
import logging

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',level=logging.DEBUG)

# The PubSub service-endpoint
#orion="http://{}:{}/".format (os.environ['ORION_PORT_1026_TCP_ADDR'], os.environ['ORION_PORT_1026_TCP_PORT'])
orion=os.environ['ORION_ENDPOINT']

# The listener (this script!) endpoint
listener="http://{}/cgi-bin/OrionListener.py".format (os.environ['MYIP'])

# the last registration id
subscriptionIdFile = "/var/www/subscription.json"


# try to read last subscriptionId from file
# do this every minute: 
#  If there is a subscriptionId try to update subscription for another 5 minutes
#  else subscribe for 5 minutes


def readSubscriptionIdFromFile():
    """try to read last subscriptionId from file"""
    if (os.path.exists (subscriptionIdFile)):
        with io.open(subscriptionIdFile) as f:
            subscription = json.load(f)
        if ('subscribeResponse' in subscription):
            subscriptionId = subscription['subscribeResponse']['subscriptionId']
    else:
        subscriptionId = None
    logging.info ("readSubscriptionIdFromFile: %s", subscriptionId)
    return subscriptionId;

def subscribe():
    """subscribe for 5 minutes"""
    data = {
        "entities": [
            {
                "type": "CRISMA.worldstates",
                "isPattern": "true",
                "id": ".*"
                }
            ],
        "reference": listener,
        "duration": "PT5M",
        "notifyConditions": [
            {
                "type": "ONCHANGE",
                "condValues": [
                    "dataslot_OOI-worldstate-ref"
                    ]
                }
            ]
        }
    params = {}
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    try :
        response = requests.post("{}/NGSI10/subscribeContext".format (orion), data=json.dumps (data), params=params, headers=headers) 
        subscription = response.json() if callable (response.json) else response.json
        if ("subscribeError" in subscription):
            subscriptionId = None
        else:
            subscriptionId = subscription['subscribeResponse']['subscriptionId']
        with io.open (subscriptionIdFile, "w") as f:
            f.write (response.text)
    except Exception, e:
        logging.warning ("subscribe: %s", e)
        subscriptionId = None
    logging.info ("subscribe: %s", subscriptionId)
    return subscriptionId;

def updateSubscription(subscriptionId):
    """Try to update subscription for another 5 minutes
    
    On failure subscriptionId will be None afterwards
    """
    data = {
        "subscriptionId": subscriptionId,
        "duration": "PT5M",
        }
    params = {}
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    try:
        response = requests.post("{}/NGSI10/updateContextSubscription".format (orion), data=json.dumps (data), params=params, headers=headers) 
        subscription = response.json() if callable (response.json) else response.json
        if ("subscribeError" in subscription):
            subscriptionId = None
        else:
            subscriptionId = subscription['subscribeResponse']['subscriptionId']
        with io.open (subscriptionIdFile, "w") as f:
            f.write (response.text)
    except Exception, e:
        logging.warning ("subscribe: %s", e)
        subscriptionId = None
    logging.info ("updateSubscription: %s", subscriptionId)
    return subscriptionId;

if __name__ == '__main__':
    logging.info ("registerAtOrion2.py started, orion = %s", orion)
    subscriptionId = readSubscriptionIdFromFile()
    while True:
        if (subscriptionId != None):
            subscriptionId = updateSubscription(subscriptionId)
        if (subscriptionId == None):
            subscriptionId = subscribe()
        if (subscriptionId == None):
            logging.info ("Waiting for subscription...")
            time.sleep (3)
        else:
            logging.info ("Subscribed! Waiting to update later...")
            time.sleep (60)

