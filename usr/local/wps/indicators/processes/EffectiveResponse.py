"""
Peter Kutschera, 2013-09-11
Update to create KPI also, 2014-11-27
Time-stamp: "2015-03-13 11:23:04 peter"

The server gets an ICMM worldstate URL and calculates an indicator and an KPI from OOI-data

Execution example (Change service part):
http://crisma.ait.ac.at/indicators/pywps.cgi?service=WPS&request=Execute&version=1.0.0&identifier=EffectiveResponse&datainputs=ICMMworldstateURL=http://crisma.cismet.de/pilotC/icmm_api/CRISMA.worldstates/2

Creation of a new indicator:
1. Copy this file
2. Update identifier - need to match file name
3. Update title
4. Update abstract
5. Replace the code inside of calculateIndicator()
6. Copy the file into the processes directory
7. Update __init__.py in the processes directory


This programm needs an recent requests library:
pip install requests --upgrade
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


from pywps.Process import WPSProcess                                
from sys import stderr
import json
import requests
import urllib
from xml.sax.saxutils import escape
import time
import logging

from crisma.Indicator import Indicator
import crisma.ICMMtools as ICMM
import crisma.OOItools as OOI

class Process(Indicator):
    def __init__(self):
        # init process
        Indicator.__init__(
            self,
            identifier="EffectiveResponse", #the same as the file name
            version = "1.0",
            title="Effective Response",
            abstract="""Percent of patients already treated.

indicator;EffectiveResponse;Effective Response;Percent of patients already treated;number
indicator;IneffectiveResponse;Inffective Response;Percent of patients not already treated;number
kpi;EffectiveResponse;Effective Response;Percent of patients already treated;number
kpi;IneffectiveResponse;Inffective Response;Percent of patients not already treated;number


""")


    def calculateIndicator(self):
        # calculate indicator value
        self.status.set("Start collecting input data", 20)

        # find out which pationts are part of the game
        IDsToSkip = []
        logging.info("Request list of patient IDs to be taken into account from base OOI WorldState = {0}".format (self.OOIworldstate.id))
        params = {
            'wsid' :  self.OOIworldstate.id, 
            'etpid' : OOI.patientExposedPropertyId
            }
        jsonBaseData = OOI.getJson ("{0}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 
        for ep in jsonBaseData:
            if ep["entityPropertyValue"].lower() == "false":
                IDsToSkip.append (ep["entityId"])


        # overall number of properties
        totalCount = 0
        # matching properties
        number = 0;

        params = {
            'wsid' : self.OOIworldstate.id, 
            'etpid' : OOI.patientTreatmentStatePropertyId
            }
        jsonData = OOI.getJson ("{0}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 

        self.status.set("Got input data data", 21)
        logging.info ("worldstate data: {0}".format (json.dumps (jsonData)))
        self.status.set("Calculate indicator value", 30)

        for ep in jsonData:
            if ep["entityId"] in IDsToSkip:
                continue
            totalCount += 1
            # Needs to be a string. If not this is an error. Just silently skip to get an result anyway!
            if ep["entityTypeProperty"]['entityTypePropertyType'] != 2: 
                logging.error ("Property is not of type 2 (String)!")
                continue 
            # The entityTypePropertyType might be a lie
            try:
                if 'None' == ep["entityPropertyValue"]:
                    number += 1;
            except:
                logging.error ("Property is not a number: '{0}'".format (ep["entityPropertyValue"]))
                # ignore problem !?!?
                pass
        
        self.status.set("Calculated number: {0}; out of totalCount: {1}".format (number, totalCount), 40)
        
        if totalCount > 0:
            number = 100 * number / totalCount

        # create indicator value structure
        result = {
         'indicator': [
                {
                    'id': self.identifier,
                    'name': self.title,
                    'description': "Percent of patients already treated",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "number",
                    'data': number,
                    'totalCount': totalCount
                    },
                {
                    'id': "IneffectiveResponse",
                    'name': "Ineffective response",
                    'description': "Percent of patients not already treated",
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates":[self.ICMMworldstate.id],
                    'type': "number",
                    'data': 100 - number,
                    'totalCount': totalCount
                    }
                ],
         'kpi': {
           "Resources": {
             "displayName": self.title,
             "iconResource": "flower_16.png",
             self.identifier: {
                "displayName": self.title,
                "iconResource": "flower_dead_16.png",
                "value": number,
                "unit": "%"
             },
             "IneffectiveResponse": {
                "displayName": "Ineffective response",
                "iconResource": "flower_dead_16.png",
                "value": 100 - number,
                "unit": "%"
             }
           }
         }
        }
        return result
