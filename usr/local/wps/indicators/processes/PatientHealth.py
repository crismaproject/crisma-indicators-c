"""
Peter Kutschera, 2013-09-11
Time-stamp: "2015-03-16 12:43:49 peter"

The server gets an ICMM worldstate URL and calculates an indicator

Execution example (Change service part and identifier):
http://crisma.ait.ac.at/indicators/pywps.cgi?service=WPS&request=Execute&version=1.0.0&identifier=PatientHealth&datainputs=ICMMworldstateURL=http://crisma.cismet.de/pilotC/icmm_api/CRISMA.worldstates/2

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
            identifier="PatientHealth", #the same as the file name
            version = "1.0",
            title="Patients health status summary",
            abstract="""Number of patients with health categorized in 3 groups.

indicator;PatientHealth;Patients health status summary;Number of patients with health categorized in 3 groups (up to 30, up to 70, better than 70);histogram

""")

    def calculateIndicator(self):
        # Define values to be used if indicator can not be calculated (e.g. missing input data)
        self.result = {}
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


        # patients and their life state
        numberOfPatients = {'sum' : 0, 'green' : 0, 'yellow': 0, 'red' : 0}
        requiredLifePropertyValue = {'green': 70, 'yellow': 30} # below yellow: 'red'

        params = {
            'wsid' : self.OOIworldstate.id, 
            'etpid' : OOI.patientLifePropertyId
            }
        jsonData = OOI.getJson ("{0}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 

        self.status.set("Got input data data", 21)
        self.status.set("Calculate indicator value", 30)

        for ep in jsonData:
            if ep["entityId"] in IDsToSkip:
                continue
            # Needs to be int (0..100). If not this is an error. Just silently skip to get an result anyway!
            if ep["entityTypeProperty"]['entityTypePropertyType'] != 1: 
                logging.error ("Patient life property is not of type 1 (integer)!")
                continue 
            # The entityTypePropertyType might be a lie
            try:
                life = float (ep["entityPropertyValue"].replace (",", "."))
                numberOfPatients['sum'] += 1
                if life > requiredLifePropertyValue['green']:
                    numberOfPatients['green'] += 1
                elif life > requiredLifePropertyValue['yellow']:
                    numberOfPatients['yellow'] += 1
                else:
                    numberOfPatients['red'] += 1
            except:
                logging.error (ep["entityPropertyValue"], " is not an integer!")
                # ignore problem !?!?
                pass
        
        self.status.set("Calculated PatientHealth: {0}".format (numberOfPatients), 40)
        
        # create indicator value structure
        self.result = {
          'indicator' : {
            'id': self.identifier,
            'name': self.title,
            'description': "Number of patients with health categorized in 3 groups",
            "worldstateDescription": self.worldstateDescription,
            'worldstates': [self.OOIworldstate.id],
            'type': "histogram",
            'data': [
                {
                    "key": "red",
                    "value": numberOfPatients['red'],
                    "desc" : "life status up to 30",
                    "cssClass": "indicator-lifeIndicator-red"
                    },
                {
                    "key" : "yellow",
                    "value" : numberOfPatients['yellow'],
                    "desc" : "life status between 30 and 70",
                    "cssClass": "indicator-lifeIndicator-yellow"
                    },
                {
                    'key': "green",
                    "value" : numberOfPatients['green'],
                    'desc' : "live status better than 70",
                    "cssClass": "indicator-lifeIndicator-green"
                    }
                ]
#            },
# No KPI for this indicator
#          'kpi': {
#                "casualties": {
#                    "displayName": "Casualties",
#                    "iconResource": "flower_16.png",
#                    self.identifier: {
#                        "displayName": self.title,
#                        "iconResource": "flower_dead_16.png",
#                        "value": numberOfPatients['dead'],
#                        "unit": "People"
#                        }
#                    } 
                }
          }
        return
