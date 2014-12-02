#!/usr/bin/env python

""" 
 receive events from orion Pub/Sup (JSON POST requests)
 Calculate indicator values using WPS
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

# list of indicators to calculate for each new worldstate
indicators = [
    'lifeIndicator', 
    'deathsIndicator',
    'seriouslyDeterioratedIndicator',
    'improvedIndicator'
    ]

# WPS service
wps = "http://localhost:80/cgi-bin/pywps.cgi?service=WPS&request=Execute&version=1.0.0&identifier={}&datainputs=ICMMworldstateURL={}"

print "Content-Type: text/plain"    # HTML is following
print                               # blank line, end of headers
print "<!-- The OrionBroker Listener says: Thanks for your message -->"


# os.getenv("QUERY_STRING")

data = sys.stdin.read()

print >>sys.stderr, "\n\n"
print >>sys.stderr, data 
print >>sys.stderr, "\n\n"


# since subscription was done using json the notification is also formatted as json

notification = json.loads (data)

elems = notification["contextResponses"]

for elem in elems:
    for attr in elem["contextElement"]["attributes"]:
        if attr["name"].startswith ("worldstate"):
            value = attr["value"]
            # print >>sys.stderr, "value1={} ({})".format (value, type (value))
            if (isinstance (value, str)):
                value = json.loads (value)
                # print >>sys.stderr, "value2={}".format (value)
            if (isinstance (value, unicode)):
                value = json.loads (value)
                # print >>sys.stderr, "value3={}".format (value)
            wsURL = value["URI"]
            for indicator in indicators:
                print >>sys.stderr, "Start indicator {} for {}".format (indicator, wsURL)
                response = requests.get(wps.format (indicator, wsURL))
                print >>sys.stderr, response.text
            

exit (0)

"""
exampleNotification = {
    "subscriptionId" : "5357b2b3000000dea5adf59d",
    "originator" : "localhost",
    "contextResponses" : [
        {
            "contextElement" : {
                "type" : "CRISMA.worldstates",
                "isPattern" : "false",
                "id" : "1_2",
                "attributes" : [
                    {
                        "name" : "time",
                        "type" : "",
                        "value" : "1398256494"
                        },
                    {
                        "name" : "worldstate_Baseline",
                        "type" : "Test baseline",
                        "value" : "{\"operation\":\"updated\",\"time\":1398256494,\"URI\":\"http://crisma.cismet.de/pilotC/icmm_api/CRISMA.worldstates/2\"}"
                        },
                    {
                        "name" : "dataslot_OOI-worldstate-ref",
                        "type" : "Test baseline",
                        "value" : {
                            "operation":"created",
                            "time":1398256492,
                            "URI":"http://crisma.cismet.de/pilotC/icmm_api/CRISMA.dataitems/3"
                            }
                        }
                    ]
                },
            "statusCode" : {
                "code" : "200",
                "reasonPhrase" : "OK"
                }
            }
        ]
    }
"""
