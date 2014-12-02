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


# The PubSub service-endpoint
orion="http://{}:{}/".format (os.environ['ORION_PORT_1026_TCP_ADDR'], os.environ['ORION_PORT_1026_TCP_PORT'])

# The listener (this script!) endpoint
listener="http://{}/cgi-bin/OrionListener.py".format (os.environ['MYIP'])

# the last registration id
subscriptionIdFile = "/tmp/subscription.json"

# if invoked as command: register as PubSub listener
# Production use: set duration to 2 years (P2Y) instead of 5 minutes (PT5M) for short-term testing

# is there a subscription id from the last subscription stored? If so unsubscribe!
if (os.path.exists (subscriptionIdFile)):
    # unsubscribe
    with io.open(subscriptionIdFile) as f:
        subscription = json.load(f)
        print "unsubscribe: "
        if ('subscribeResponse' in subscription):
            data = {
                'subscriptionId' : subscription['subscribeResponse']['subscriptionId']
                }
            params = {}
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            response = requests.post("{}/NGSI10/unsubscribeContext".format (orion), data=json.dumps (data), params=params, headers=headers) 
            # unsubscription = response.json() if callable (response.json) else response.json
            print response.text
    os.remove (subscriptionIdFile)
if (sys.argv[1] == "--subscribe"):
    print "subscribe: "
    # condValues was ["time"], but that is not ceccassary.
    data = {
            "entities": [
                {
                    "type": "CRISMA.worldstates",
                    "isPattern": "true",
                    "id": ".*"
                    }
                ],
            "reference": listener,
            "duration": "P2Y",
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
    response = requests.post("{}/NGSI10/subscribeContext".format (orion), data=json.dumps (data), params=params, headers=headers) 
    # subscription = response.json() if callable (response.json) else response.json
    with io.open (subscriptionIdFile, "w") as f:
        f.write (response.text)
    print response.text
    

