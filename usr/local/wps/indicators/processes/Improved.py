"""
Peter Kutschera, 2013-09-11
Time-stamp: "2015-02-18 15:14:49 peter"

The server gets an ICMM worldstate URL and calculates an indicator

Execution example (Change service part):
http://crisma.ait.ac.at/indicators/pywps.cgi?service=WPS&request=Execute&version=1.0.0&identifier=Improved&datainputs=ICMMworldstateURL=http://crisma.cismet.de/pilotC/icmm_api/CRISMA.worldstates/2

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

from Indicator import Indicator
import ICMMtools as ICMM
import OOItools as OOI

class Process(Indicator):
    def __init__(self):
        # init process
        Indicator.__init__(
            self,
            identifier="Improved", #the same as the file name
            version = "1.0",
            title="Improved patients",
            abstract="Number of patients with actual health better or equal as at the beginning")

    def calculateIndicator(self):
        self.status.set("Start collecting input data", 20)
        # find base WorldState from ICMM
        baseICMMworldstateId = ICMM.getBaseWorldstate (self.ICMMworldstate.id, baseCategory="Baseline", baseUrl=self.ICMMworldstate.endpoint)
        if (baseICMMworldstateId is None):
            raise Exception ("Base ICMM WorldState not found for actual ICMM WorldState = {}".format (self.ICMMworldstate))

        baseOOIworldstateURL = ICMM.getOOIRef (baseICMMworldstateId, 'OOI-worldstate-ref', baseUrl=self.ICMMworldstate.endpoint)
        logging.info ("baseOOIworldstateURL = {}".format (baseOOIworldstateURL))
        if (baseOOIworldstateURL is None):
            raise Exception ("invalid OOI URL: {}".format (baseOOIworldstateURL))
        
        # OOI-URL -> Endpoint, id, ...
        baseOOIworldstate = OOI.OOIAccess(baseOOIworldstateURL)
        logging.info ("baseOOIWorldState = {}".format (baseOOIworldstate))
        if (baseOOIworldstate.endpoint is None):
            raise Exception ("invalid OOI ref: {}".format (baseOOIworldstate))

        self.status.set("Base WorldState: {}".format (baseOOIworldstateURL), 21)

        # now:
        #  self.OOIworldstate: Actual worldstate I want to calculate the indicator for
        #  baseOOIworldstate:  Worldstate at the beginning of the experiment / training


        # find out which pationts are part of the game
        IDsToSkip = []
        logging.info("Request list of patient IDs to be taken into account from base OOI WorldState = {}".format (baseOOIworldstate.id))
        params = {
            'wsid' :  baseOOIworldstate.id, 
            'etpid' : OOI.patientExposedPropertyId
            }
        jsonBaseData = OOI.getJson ("{}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 
        for ep in jsonBaseData:
            if ep["entityPropertyValue"].lower() == "false":
                IDsToSkip.append (ep["entityId"])



        # calculate indicator value
        # patients and their life state
        numberOfImproved = 0;
        numberOfDeteriorated = 0;
        totalCount = 0

        # base data:
        logging.info("Request input data for base OOI WorldState = {}".format (baseOOIworldstate.id))
        params = {
            'wsid' :  baseOOIworldstate.id, 
            'etpid' : OOI.patientLifePropertyId
            }
        jsonBaseData = OOI.getJson ("{}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 
        # actual data:
        params = {
            'wsid' : self.OOIworldstate.id, 
            'etpid' : OOI.patientLifePropertyId
            }
        jsonData = OOI.getJson ("{}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 

        self.status.set("Calculate indicator value", 30)
        patients = {}

        for ep in jsonBaseData:
            if ep["entityId"] in IDsToSkip:
                continue
            # Needs to be int (0..100). If not this is an error. Just silently skip to get an result anyway!
            if ep["entityTypeProperty"]['entityTypePropertyType'] != 1: 
                # print >> stderr, "Patient life property is not of type 1 (integer)!"
                continue 
            # The entityTypePropertyType might be a lie
            try:
                life = float (ep["entityPropertyValue"].replace (",", "."))
                patients[ep["entityId"]] = life
            except:
                # print >> stderr, ep["entityPropertyValue"], " is not an integer!"
                # ignore problem !?!?
                pass
        for ep in jsonData:
            if ep["entityId"] in IDsToSkip:
                continue
            totalCount += 1
            # Needs to be int (0..100). If not this is an error. Just silently skip to get an result anyway!
            if ep["entityTypeProperty"]['entityTypePropertyType'] != 1: 
                # print >> stderr, "Patient life property is not of type 1 (integer)!"
                continue 
            # The entityTypePropertyType might be a lie
            try:
                life = float (ep["entityPropertyValue"].replace (",", "."))
                if life >= patients[ep["entityId"]]:
                    numberOfImproved += 1
                if life < patients[ep["entityId"]] - 50:
                    numberOfDeteriorated += 1
            except:
                # print >> stderr, ep["entityPropertyValue"], " is not an integer!"
                # ignore problem !?!?
                pass

        self.status.set("Calculated improvedIndicator for ICMM WorldState with id {}: {} out of {}".format (self.ICMMworldstate.id, numberOfImproved, len (patients)), 90)

        # create indicator value structure
        result = {
         'indicator': [
                {
                    'id': self.identifier,
                    'name': self.title,
                    'description': self.abstract,
                    "worldstateDescription": self.worldstateDescription,
                    'worldstates': [baseOOIworldstate.id, self.OOIworldstate.id],
                    'totalCount': totalCount,
                    'type': "number",
                    'data': numberOfImproved
                    },
                {
                    'id': "SeriouslyDeteriorated",
                    'name': "Seriously deteriorated patients",
                    'description': "Number of patients with (actual health) less than (health at the beginning - 50)",
                    "worldstateDescription": self.worldstateDescription,
                    'worldstates': [baseOOIworldstate.id, self.OOIworldstate.id],
                    'totalCount': totalCount,
                    'type': "number",
                    'data': numberOfDeteriorated
                    }
                ],
          'kpi': {
                "casualties": {
                    "displayName": "Casualties",
                    "iconResource": "flower_16.png",
                    self.identifier: {
                        "displayName": self.title,
                        "iconResource": "flower_dead_16.png",
                        "value": numberOfImproved,
                        "unit": "People"
                        },
                    "SeriouslyDeteriorated": {
                        "displayName": "Seriously deteriorated patients",
                        "iconResource": "flower_dead_16.png",
                        "value": numberOfDeteriorated,
                        "unit": "People"
                        }
                    } 
                }
         }
        return result
