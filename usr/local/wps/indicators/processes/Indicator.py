"""
Peter Kutschera, 2013-09-11
Time-stamp: "2014-05-21 11:28:50 peter"

This is a base class for inicators holding all common code
Includes basic handling of ICMM.
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

class Indicator(WPSProcess):

    def __init__(self, identifier, version, title, abstract):
        # init process
        WPSProcess.__init__(
            self,
            identifier=identifier,
            version = version,
            title=title,
            storeSupported = "false",
            statusSupported = "false",
            abstract=abstract,
            grassLocation = False)
        self.ICMMworldstateURL = self.addLiteralInput (identifier = "ICMMworldstateURL",
                                                type = type(""),
                                                title = "ICMM WorldState id")
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
        self.doUpdate = 1              # 1: recalculate existing indicator; 0: use existing value
        self.ICMMworldstate = None     # Access-object for ICMM WorldState
        self.worldstateDescription = None  # description of WorldState: ICMMname, ICMMdescription, ICMMworldstateURL, OOIworldstateURL

    """
    def calculateIndicator(self):
        # create indicator value structure
        indicatorData = {
            'id': "newIndicator",
            'name': "Newbies",
            'description': "Some Number",
            "worldstateDescription": self.worldstateDescription,
            'type': "number",
            'data': 42
            }
        return indicatorData
    """
                                           
    def execute(self):
 
        self.status.set("Check ICMM WorldState status", 1)

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

        self.status.set("Check if indicator value already exists", 10)

        indicatorURL = ICMM.getIndicatorURL (self.ICMMworldstate.id, self.identifier, baseUrl=self.ICMMworldstate.endpoint)
        logging.info ("old indicatorURL = {}".format (indicatorURL))
        if (indicatorURL is not None):
            logging.info ("Indicator value already exists at: {}".format (indicatorURL))

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

        return

