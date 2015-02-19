"""
Peter Kutschera, 2013-09-11
Time-stamp: "2015-02-19 14:00:35 peter"

The server gets an ICMM worldstate URL and calculates an indicator

Execution example (Change service part):
http://crisma.ait.ac.at/indicators/pywps.cgi?service=WPS&request=Execute&version=1.0.0&identifier=UnusedResources&datainputs=ICMMworldstateURL=http://crisma.cismet.de/pilotC/icmm_api/CRISMA.worldstates/2

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
import datetime
import dateutil.parser


from Indicator import Indicator
import ICMMtools as ICMM
import OOItools as OOI

class Process(Indicator):
    def __init__(self):
        # init process
        Indicator.__init__(
            self,
            identifier="UnusedResources", #the same as the file name
            version = "1.0",
            title="Number of resources not used",
            abstract="Number of available resources that was not uned yet")

    def calculateIndicator(self):
        self.status.set("Start collecting input data", 20)
        # find base WorldState from ICMM
        parents = ICMM.getParentWorldstates (self.ICMMworldstate.id, baseCategory="Baseline", baseUrl=self.ICMMworldstate.endpoint)
        if (parents is None):
            raise Exception ("Base ICMM WorldState not found for actual ICMM WorldState = {0}".format (self.ICMMworldstate))

        # resources: id -> [unavailable | unused | used]
        resources = {}


        for wsid in parents:
            logging.info ("get ws {0}".format (wsid))
            ooiWorldstateURL = ICMM.getOOIRef (wsid, 'OOI-worldstate-ref', baseUrl=self.ICMMworldstate.endpoint)
            logging.info ("  ooiWorldstateURL = {0}".format (ooiWorldstateURL))
            if (ooiWorldstateURL is None):
                return "invalid OOI URL: {0}".format (ooiWorldstateURL)
            # OOI-URL -> Endpoint, id, ...
            ooiWorldstate = OOI.OOIAccess(ooiWorldstateURL)
            # logging.info ("ooiWorldState = {0}".format (ooiWorldstate))
            if (ooiWorldstate.endpoint is None):
                return "invalid OOI ref: {0}".format (ooiWorldstate)
        

            logging.info("Request input data for OOI WorldState = {0}".format (ooiWorldstate.id))
            params = {
                'wsid' :  ooiWorldstate.id 
                }
            jsonData = OOI.getJson ("{0}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 

            # this now contaions ALL EntityPropertyIds !

            for ep in jsonData:
                if (OOI.vehicleAvailabilityPropertyId == ep["entityTypePropertyId"]):
                    # find out which vehicles exists and wich if them are available
                    if ep["entityId"] not in resources:
                        try:
                            if (-1 == float (ep["entityPropertyValue"].replace (",", "."))):
                                resources[ep["entityId"]] = "unavailable"
                            else:
                                resources[ep["entityId"]] = "unused"
                        except Exception, e:
                            logging.error ("problem {1} with EntityProperty {0}".format (json.dumps (ep), e))
                    continue

                if (OOI.vehicleDisplayStatePropertyId == ep["entityTypePropertyId"]):
                    # looking for resources actually in use
                    state = ep['entityPropertyValue']
                    logging.info ("  resource {0}: {1}".format (ep["entityId"], state))
                    if (state != None) and (state != "") and (state.lower() != "idle"):
                        resources[ep["entityId"]] = "used"
                    continue

            logging.info ("Resources so far: {0}".format (len (resources)))

        noUnavailable = 0
        noUnused = 0
        noUsed = 0

        for resource in resources:
            if resources[resource] == "unavailable":
                noUnavailable += 1
            if resources[resource] == "unused":
                noUnused += 1
            if resources[resource] == "used":
                noUsed += 1


        self.status.set("Calculated 'UnusedResources' indicator: Unavailable: {0}, Unused: {1}, Used: {2}".format (noUnavailable, noUnused, noUsed))

        # create indicator value structure
        result = {
         'indicator': [
                {
                    'id': self.identifier,
                    'name': self.title,
                    'description': self.abstract,
                    "worldstateDescription": self.worldstateDescription,
                    "worldstates": parents,
                    'type': "number",
                    'data': noUnused,
                    'totalCount': noUnused + noUsed
                    }
                ],
         'kpi': {
           "Resources": {
             "displayName": self.title,
             "iconResource": "flower_16.png",
             self.identifier: {
                "displayName": self.title,
                "iconResource": "flower_dead_16.png",
                "value": noUnused,
                "unit": "Resources"
             }
           }
         }
        }
        return result

