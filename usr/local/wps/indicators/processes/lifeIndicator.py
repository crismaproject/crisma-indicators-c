"""
Peter Kutschera, 2013-09-11
Time-stamp: "2014-05-07 14:26:09 peter"

The server gets an ICMM worldstate URL and calculates an indicator

Execution example (Change service part and identifier):
http://crisma.ait.ac.at/indicators/pywps.cgi?service=WPS&request=Execute&version=1.0.0&identifier=deathsIndicator&datainputs=ICMMworldstateURL=http://crisma.cismet.de/pilotC/icmm_api/CRISMA.worldstates/2

Creation of a new indicator:
1. Copy this file
2. Update identifier - need to match file name
3. Update title
4. Update abstract
5. Update self.indicatorPropertyId; The value need to be define in OOI-WSR beforehand!
6. Replace the code inside of calculateIndicator()
7. Copy the file into the processes directory
8. Update __init__.py in the processes directory
9. Add indicator to list of indicators on the testpage (../../web/libs/wpsControllers.js)


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

import ICMMtools as ICMM
import OOItools as OOI

class Process(WPSProcess):
    def __init__(self):
        # init process
        WPSProcess.__init__(
            self,
            identifier="lifeIndicator", #the same as the file name
            version = "1.0",
            title="Patients health status summary",
            storeSupported = "false",
            statusSupported = "false",
            abstract="Number of patients with health categorized in 4 groups",
            grassLocation = False)
        self.ICMMworldstateURL = self.addLiteralInput (identifier = "ICMMworldstateURL",
                                                type = type(""),
                                                title = "ICMM WorldState id")
        self.ooi=self.addLiteralOutput(identifier = "OOIindicatorURL",
                                          type = type (""),
                                          title = "URL to access indicator from OOI")
        self.icmmRef=self.addLiteralOutput(identifier = "ICMMindicatorRefURL",
                                          type = type (""),
                                          title = "URL to access indicator reference from ICMM")
        self.icmmVal=self.addLiteralOutput(identifier = "ICMMindicatorValueURL",
                                          type = type (""),
                                          title = "URL to access indicator value from ICMM")
        self.value=self.addLiteralOutput(identifier = "value",
                                         type = type (""),
                                         title = "indicator value")
        # for ICMM and OOI
        self.indicatorPropertyId = 60  # lifeIndicator
        self.doUpdate = 1              # 1: recalculate existing indicator; 0: use existing value
        self.ICMMworldstate = None     # Access-object for ICMM WorldState
        self.OOIworldstate = None      # Access-object for OOI WorldState
        self.worldstateDescription = None  # description of WorldState: ICMMname, ICMMdescription, ICMMworldstateURL, OOIworldstateURL

    def calculateIndicator(self):
        # calculate indicator value
        self.status.set("Start collecting input data", 20)

        # patients and their life state
        numberOfPatients = {'sum' : 0, 'green' : 0, 'yellow': 0, 'red' : 0, 'dead' : 0}
        requiredLifePropertyValue = {'green': 85, 'yellow': 50, 'red' : 10} # below 'red': 'dead'

        params = {
            'wsid' : self.OOIworldstate.id, 
            'etpid' : OOI.patientLifePropertyId
            }
        jsonData = OOI.getJson ("{}/EntityProperty".format (self.OOIworldstate.endpoint), params=params) 

        self.status.set("Got input data data", 21)
        self.status.set("Calculate indicator value", 30)

        for ep in jsonData:
            # Needs to be int (0..100). If not this is an error. Just silently skip to get an result anyway!
            if ep["entityTypeProperty"]['entityTypePropertyType'] != 1: 
                logging.error ("Patient life property is not of type 1 (integer)!")
                continue 
            # The entityTypePropertyType might be a lie
            try:
                life = float (ep["entityPropertyValue"].replace (",", "."))
                numberOfPatients['sum'] += 1
                if life >= requiredLifePropertyValue['green']:
                    numberOfPatients['green'] += 1
                elif life >= requiredLifePropertyValue['yellow']:
                    numberOfPatients['yellow'] += 1
                elif life >= requiredLifePropertyValue['red']:
                    numberOfPatients['red'] += 1
                else:
                    numberOfPatients['dead'] += 1
            except:
                logging.error (ep["entityPropertyValue"], " is not an integer!")
                # ignore problem !?!?
                pass
        
        self.status.set("Calculated deathsIndicator: {}".format (numberOfPatients), 40)
        
        # create indicator value structure
        indicatorData = {
            'id': "lifeIndicator",
            'name': "health status summary",
            'description': "Life status categoized and summed up per category",
            "worldstateDescription": self.worldstateDescription,
            'worldstates': [self.OOIworldstate.id],
            'type': "histogram",
            'data': [
                {
                    "key": "dead",
                    "value": numberOfPatients['dead'],
                    "desc": "life status below 10",
                    "cssClass": "indicator-lifeIndicator-black"
                    },
                {
                    "key": "red",
                    "value": numberOfPatients['red'],
                    "desc" : "life status 10..50",
                    "cssClass": "indicator-lifeIndicator-red"
                    },
                {
                    "key" : "yellow",
                    "value" : numberOfPatients['yellow'],
                    "desc" : "life status 50..85",
                    "cssClass": "indicator-lifeIndicator-yellow"
                    },
                {
                    'key': "green",
                    "value" : numberOfPatients['green'],
                    'desc' : "live status 85 or better",
                    "cssClass": "indicator-lifeIndicator-green"
                    }
                ]
            }
        return indicatorData

##############################
#                            #
# Nothing to configure below #
#                            #
##############################
                                           
    def execute(self):
 
        self.status.set("Check ICMM and OOI WorldState status", 1)

        # http://crisma.cismet.de/icmm_api/CRISMA.worldstates/1
        ICMMworldstateURL = self.ICMMworldstateURL.getValue()
        logging.info ("ICMMworldstateURL = {}".format (ICMMworldstateURL))
        if (ICMMworldstateURL is None):
            return "invalid ICMM URL: {}".format (ICMMworldstateURL)

        # ICMM-URL -> Endpoint, id, ...
        self.ICMMworldstate = ICMM.ICMMAccess (ICMMworldstateURL)
        logging.info ("ICMMworldstate = {}".format (self.ICMMworldstate))
        if (self.ICMMworldstate.endpoint is None):
            return "invalid ICMM ref: {}".format (self.ICMMworldstate)
        
        self.worldstateDescription = ICMM.getNameDescription (self.ICMMworldstate.id, baseUrl=self.ICMMworldstate.endpoint)
        self.worldstateDescription["ICMMworldstateURL"] = ICMMworldstateURL

        OOIworldstateURL = ICMM.getOOIRef (self.ICMMworldstate.id, 'OOI-worldstate-ref', baseUrl=self.ICMMworldstate.endpoint)
        logging.info ("OOIworldstateURL = {}".format (OOIworldstateURL))
        if (OOIworldstateURL is None):
            return "invalid OOI URL: {}".format (OOIworldstateURL)
        self.worldstateDescription["OOIworldstateURL"] = OOIworldstateURL
        
        # OOI-URL -> Endpoint, id, ...
        self.OOIworldstate = OOI.OOIAccess(OOIworldstateURL)
        logging.info ("OOIWorldState = {}".format (self.OOIworldstate))
        if (self.OOIworldstate.endpoint is None):
            return "invalid OOI ref: {}".format (self.OOIworldstate)

        self.status.set("Check if indicator value already exists", 10)

        logging.info ("self.indicatorPropertyId = {}".format (self.indicatorPropertyId))

        indicatorURL = OOI.getIndicatorRef (self.OOIworldstate.id, self.indicatorPropertyId, self.OOIworldstate.endpoint) # None or URI of already existing indicator value
        logging.info ("old indicatorURL = {}".format (indicatorURL))
        if (indicatorURL is not None):
            logging.info ("Indicator value already exists: {}".format (indicatorURL))

        if ((self.doUpdate == 1) or (indicatorURL is None)):
            try:
                indicatorData = self.calculateIndicator ()
            except Exception, e:
                logging.error ("calculateIndicator: {}".format (str(e.args)))
                return ("calculateIndicator: {}".format (str(e.args)))
            logging.info ("indicatorData: {}".format (json.dumps (indicatorData)))
            self.value.setValue (json.dumps (indicatorData))

            ICMMindicatorValueURL = ICMM.addIndicatorValToICMM (self.ICMMworldstate.id, self.identifier, self.title, indicatorData, self.ICMMworldstate.endpoint)
            self.icmmVal.setValue(escape (ICMMindicatorValueURL))

            indicatorURL = OOI.storeIndicatorValue (self.OOIworldstate.id, self.indicatorPropertyId, indicatorData, indicatorURL, self.OOIworldstate.endpoint)

        self.status.set("Store indicator reference in ICMM", 90)

        ICMMindicatorURL = ICMM.addIndicatorRefToICMM (self.ICMMworldstate.id, self.identifier, self.title, indicatorURL, self.ICMMworldstate.endpoint)
            
        self.ooi.setValue(escape (indicatorURL))
        self.icmmRef.setValue(escape (ICMMindicatorURL))
        return

