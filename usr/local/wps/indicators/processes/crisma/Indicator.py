"""
Peter Kutschera, 2014-11-27
Time-stamp: "2015-03-13 11:32:10 peter"

This is a base class for indcators holding all common code
Includes basic handling of ICMM and OOI-WSR.
Input datya is taken from ICMM and OOI
Indicators and KPI are stored in ICMM
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

class Indicator(WPSProcess):

    def __init__(self, identifier, version, title, abstract, hasOOI = True):
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
        self.indicatorRef=self.addLiteralOutput(identifier = "ICMMindicatorValueURL",
                                                type = type (""),
                                                title = "URL to access indicator value from ICMM")
        self.kpiRef=self.addLiteralOutput(identifier = "ICMMkpiValueURL",
                                          type = type (""),
                                          title = "URL to access indicator value from ICMM")
        self.indicator=self.addLiteralOutput(identifier = "indicator",
                                             type = type (""),
                                             title = "indicator value")
        self.kpi=self.addLiteralOutput(identifier = "kpi",
                                       type = type (""),
                                       title = "kpi value")
        # for ICMM and OOI
        self.doUpdate = 1              # 1: recalculate existing indicator; 0: use existing value
        self.ICMMworldstate = None     # Access-object for ICMM WorldState
        self.worldstateDescription = None  # description of WorldState: ICMMname, ICMMdescription, ICMMworldstateURL, OOIworldstateURL
        self.hasOOI = hasOOI           # Provide access to OOI
        self.OOIworldstate = None      # Access-object for OOI-WSR WorldState

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
        # KPI
        kpiData = {
           "casualties": {
             "displayName": "Casualties",
             "iconResource": "flower_16.png",
             "noOfDead": {
                "displayName": "Number of dead",
                "iconResource": "flower_dead_16.png",
                "value": 257,
                "unit": "People"
             }, ...
           }, ...
        }
        return {indicator: indicatorData, kpi: kpiData}
    """
                 
    def toMinutes (self, timedelta):
        """Workaroud for missing total_seconds() in Python < 2.7"""
        if hasattr(timedelta, 'total_seconds'):
            duration = timedelta.total_seconds()
        else: 
            duration = (timedelta.microseconds + (timedelta.seconds +  timedelta.days * 24 * 3600) * 10**6) / 10**6
        duration = duration / 60 
        return duration

                          
    def execute(self):
 
        self.status.set("Check ICMM WorldState status", 1)

        # http://crisma.cismet.de/icmm_api/CRISMA.worldstates/1
        ICMMworldstateURL = self.ICMMworldstateURL.getValue()
        logging.info ("ICMMworldstateURL = {0}".format (ICMMworldstateURL))
        if (ICMMworldstateURL is None):
            return "invalid ICMM URL: {0}".format (ICMMworldstateURL)

        # ICMM-URL -> Endpoint, id, ...
        self.ICMMworldstate = ICMM.ICMMAccess (ICMMworldstateURL)
        logging.info ("ICMMworldstate = {0}".format (self.ICMMworldstate))
        if (self.ICMMworldstate.endpoint is None):
            return "invalid ICMM ref: {0}".format (self.ICMMworldstate)
        
        self.worldstateDescription = ICMM.getNameDescription (self.ICMMworldstate.id, baseUrl=self.ICMMworldstate.endpoint)
        self.worldstateDescription["ICMMworldstateURL"] = ICMMworldstateURL

        # Not used / available in PilotEv1
        if (self.hasOOI):
            OOIworldstateURL = ICMM.getOOIRef (self.ICMMworldstate.id, 'OOI-worldstate-ref', baseUrl=self.ICMMworldstate.endpoint)
            logging.info ("OOIworldstateURL = {0}".format (OOIworldstateURL))
            if (OOIworldstateURL is None):
                return "invalid OOI URL: {0}".format (OOIworldstateURL)
            self.worldstateDescription["OOIworldstateURL"] = OOIworldstateURL
        
            # OOI-URL -> Endpoint, id, ...
            self.OOIworldstate = OOI.OOIAccess(OOIworldstateURL)
            logging.info ("OOIWorldState = {0}".format (self.OOIworldstate))
            if (self.OOIworldstate.endpoint is None):
                return "invalid OOI ref: {0}".format (self.OOIworldstate)

        self.status.set("Check if indicator value already exists", 10)

        indicatorURL = ICMM.getIndicatorURL (self.ICMMworldstate.id, self.identifier, baseUrl=self.ICMMworldstate.endpoint)
        logging.info ("old indicatorURL = {0}".format (indicatorURL))
        if (indicatorURL is not None):
            logging.info ("Indicator value already exists at: {0}".format (indicatorURL))

        if ((self.doUpdate == 1) or (indicatorURL is None)):
            try:
                data = self.calculateIndicator ()

                if 'indicator' in data:
                    logging.info ("indicatorData: {0}".format (json.dumps (data['indicator'])))
                    self.indicator.setValue (json.dumps (data['indicator']))
                    if isinstance(data['indicator'], list):
                        for x in data['indicator']:
                            ICMMindicatorValueURL = ICMM.addIndicatorValToICMM (self.ICMMworldstate.id, x['id'], x['name'], x, self.ICMMworldstate.endpoint)
                            # only the last value will be used, sorry
                            self.indicatorRef.setValue(escape (ICMMindicatorValueURL))
                    if isinstance(data['indicator'], dict):
                        ICMMindicatorValueURL = ICMM.addIndicatorValToICMM (self.ICMMworldstate.id, self.identifier, self.title, data['indicator'], self.ICMMworldstate.endpoint)
                        self.indicatorRef.setValue(escape (ICMMindicatorValueURL))

                if 'kpi' in data:
                    logging.info ("kpiData: {0}".format (json.dumps (data['kpi'])))
                    self.kpi.setValue (json.dumps (data['kpi']))
                    ICMMkpiValueURL = ICMM.addKpiValToICMM (self.ICMMworldstate.id, self.identifier, self.title, data['kpi'], self.ICMMworldstate.endpoint)
                    self.kpiRef.setValue(escape (ICMMkpiValueURL))

            except Exception, e:
                logging.exception ("calculateIndicator: {0}".format (str(e.args)))
                return ("calculateIndicator: {0}".format (str(e.args)))
        return

