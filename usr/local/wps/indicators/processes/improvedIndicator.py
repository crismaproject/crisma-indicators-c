"""
Peter Kutschera, 2013-09-11
Time-stamp: "2014-05-07 14:25:49 peter"

The server gets an ICMM worldstate URL and calculates an indicator

Execution example (Change service part):
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
            identifier="improvedIndicator", #the same as the file name
            version = "1.0",
            title="Improved patients",
            storeSupported = "false",
            statusSupported = "false",
            abstract="Number of patients with actual health better or equal as at the beginning",
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
        self.indicatorPropertyId = 63  # improvedIndicator
        self.doUpdate = 1              # 1: recalculate existing indicator; 0: use existing value
        self.ICMMworldstate = None     # Access-object for ICMM WorldState
        self.OOIworldstate = None      # Access-object for OOI WorldState
        self.worldstateDescription = None  # description of WorldState: ICMMname, ICMMdescription, ICMMworldstateURL, OOIworldstateURL

    def calculateIndicator(self):
        self.status.set("Start collecting input data", 20)
        # find base WorldState from ICMM
        baseICMMworldstateId = ICMM.getBaseWorldstate (self.ICMMworldstate.id, baseCategory="Baseline", baseUrl=self.ICMMworldstate.endpoint)
        if (baseICMMworldstateId is None):
            return "Base ICMM WorldState not found for actual ICMM WorldState = {}".format (self.ICMMworldstate)

        baseOOIworldstateURL = ICMM.getOOIRef (baseICMMworldstateId, 'OOI-worldstate-ref', baseUrl=self.ICMMworldstate.endpoint)
        logging.info ("baseOOIworldstateURL = {}".format (baseOOIworldstateURL))
        if (baseOOIworldstateURL is None):
            return "invalid OOI URL: {}".format (baseOOIworldstateURL)
        
        # OOI-URL -> Endpoint, id, ...
        baseOOIworldstate = OOI.OOIAccess(baseOOIworldstateURL)
        logging.info ("baseOOIWorldState = {}".format (baseOOIworldstate))
        if (baseOOIworldstate.endpoint is None):
            return "invalid OOI ref: {}".format (baseOOIworldstate)

        self.status.set("Base WorldState: {}".format (baseOOIworldstateURL), 21)

        # now:
        #  self.OOIworldstate: Actual worldstate I want to calculate the indicator for
        #  baseOOIworldstate:  Worldstate at the beginning of the experiment / training

        # calculate indicator value
        # patients and their life state
        numberOfImproved = 0;

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
            # Needs to be int (0..100). If not this is an error. Just silently skip to get an result anyway!
            if ep["entityTypeProperty"]['entityTypePropertyType'] != 1: 
                # print >> stderr, "Patient life property is not of type 1 (integer)!"
                continue 
            # The entityTypePropertyType might be a lie
            try:
                life = float (ep["entityPropertyValue"].replace (",", "."))
                if life >= patients[ep["entityId"]]:
                    numberOfImproved += 1
            except:
                # print >> stderr, ep["entityPropertyValue"], " is not an integer!"
                # ignore problem !?!?
                pass

        self.status.set("Calculated improvedIndicator for ICMM WorldState with id {}: {} out of {}".format (self.ICMMworldstate.id, numberOfImproved, len (patients)), 90)

        # create indicator value structure
        indicatorData = {
            'id': "improvedIndicator",
            'name': "improved",
            'description': "Number of patients with actual life status better or equal then base life status",
            "worldstateDescription": self.worldstateDescription,
            'worldstates': [baseOOIworldstate.id, self.OOIworldstate.id],
            'type': "number",
            'data': numberOfImproved
            }

        self.value.setValue (json.dumps (indicatorData))

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

