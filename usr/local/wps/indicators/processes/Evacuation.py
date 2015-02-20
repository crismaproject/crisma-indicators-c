"""
Peter Kutschera, 2013-09-11
Time-stamp: "2015-02-20 11:49:45 peter"

The server gets an ICMM worldstate URL and calculates an indicator

Execution example (Change service part):
http://crisma.ait.ac.at/indicators/pywps.cgi?service=WPS&request=Execute&version=1.0.0&identifier=Evacuation&datainputs=ICMMworldstateURL=http://crisma.cismet.de/pilotC/icmm_api/CRISMA.worldstates/2

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
            identifier="Evacuation", #the same as the file name
            version = "1.0",
            title="Evacuation time",
            abstract="""Evacuation start and end.

indicator;Evacuation;Evacuation time;Evacuation start and end;timeintervals
indicator;TimeToEvacuation;Time to Evacuation;Minutes from start till evacuation is ordered;number
indicator;LastPatientEvacuated;Last Patient Evacuated;Minutes from start till last patient is evacuated;number
kpi;Evacuation;Evacuation completed;Minutes from start till last patient is evacuated;number

""")

    def getTimeFromICMMws (self, wsid):
        params = {
            'level' :  1,
            'fields' : "simulatedTime",
            'omitNullValues' : 'true',
            'deduplicate' : 'true'
            }
        headers = {'content-type': 'application/json'}
        response = requests.get("{0}/{1}.{2}/{3}".format (self.ICMMworldstate.endpoint, self.ICMMworldstate.domain, "worldstates", wsid), params=params, headers=headers) 
        if response.status_code != 200:
            raise Exception ( "Error accessing ICMM at {0}: {1}".format (response.url, response.status_code))
        # Depending on the requests-version json might be an field instead of on method
        jsonData = response.json() if callable (response.json) else response.json

        ts = jsonData['simulatedTime']
        if (len(ts) == 16):
            ts = ts + ":00.0Z"
        return dateutil.parser.parse (ts)

    def calculateIndicator(self):
        self.status.set("Start collecting input data", 20)
        # find base WorldState from ICMM
        parents = ICMM.getParentWorldstates (self.ICMMworldstate.id, baseCategory="Baseline", baseUrl=self.ICMMworldstate.endpoint)
        if (parents is None):
            raise Exception ("Base ICMM WorldState not found for actual ICMM WorldState = {0}".format (self.ICMMworldstate))

        basewsid = parents[0]

        logging.info ("get start time from ws {0}".format (basewsid))
        t0 = self.getTimeFromICMMws (basewsid)
        t1 = None
        t2 = None
        t3 = self.getTimeFromICMMws (self.ICMMworldstate.id)


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

            # find out which vehicles are not part of the game
            IDsToSkip = []
            for ep in jsonData:
                try:
                    if (OOI.vehicleAvailabilityPropertyId == ep["entityTypePropertyId"]) and (-1 == float (ep["entityPropertyValue"].replace (",", "."))):
                        IDsToSkip.append (ep["entityId"])
                except Exception, e:
                    logging.error ("problem {1} with EntityProperty {0}".format (json.dumps (ep), e))
            logging.info ("IDsToSkip = {0]", IDsToSkip)

            # look for evacuation start (at least 1 vehicle with "evacuate" command)
            if t1 == None:
                logging.info ("look for evacuation start (at least 1 vehicle with 'evacuate' command)")
                for ep in jsonData:
                    if (OOI.vehicleResourceCommandId != ep["entityTypePropertyId"]):
                        continue
                    if ep["entityId"] in IDsToSkip:
                        continue
                    if ('entityPropertyValue' in ep) and (ep['entityPropertyValue'] != ""):
                        try :
                            logging.info ("VehicleResourceCommand: {0}".format (ep['entityPropertyValue']))
                            command = json.loads (ep['entityPropertyValue'])
                            if 'Command-Type' in command:
                                if command['Command-Type'].lower() == 'evacuate':
                                    # hurray!
                                    t1 = self.getTimeFromICMMws (wsid)
                                    break;
                        except:
                            raise Exception ("Problem understanding the command '{0}' (OOI wsid={1}, entityId={2})".format (ep['entityPropertyValue'], ooiWorldstate.id, ep["entityId"]))

            # look for evacuation end (All patients with Treatment-State == evacuated)
            if (t1 != None) and (t2 == None):
                logging.info ("look for evacuation end (All patients with Treatment-State == 'evacuated')")
                notEvacuated = 0
                for ep in jsonData:
                    if (OOI.patientTreatmentStatePropertyId != ep["entityTypePropertyId"]):
                        continue
                    if ep["entityId"] in IDsToSkip:
                        continue
                    # Needs to be a string. If not this is an error. Just silently skip to get an result anyway!
                    if ep["entityTypeProperty"]['entityTypePropertyType'] != 2: 
                        logging.error ("Property is not of type 2 (String)!")
                        continue 
                    if (ep["entityPropertyValue"] == None) | (ep["entityPropertyValue"].lower() != 'evacuated'):
                        notEvacuated += 1
                    
                logging.info ("Patients still to evacuate: {0}".format (notEvacuated))
                if notEvacuated == 0:
                    t2 = self.getTimeFromICMMws (wsid)
                    break;

        self.status.set("Calculated 'Evacuation' indicator: Start Excercise: {0}, start evacuation: {1}, end evacuation {2}, end exercise (so far): {0}".format (
                t0.isoformat(), 
                "not yet" if t1 == None else t1.isoformat(), 
                "not yet" if t2 == None else t2.isoformat(), 
                t3.isoformat()), 90)

        # create indicator value structure
        result = {}
        intervals = []
        indicators = []
        if t1 == None:
            # evacuation not even started
            intervals = []
        else:
            # evacuation started
            indicators.append ({
                    'id': "TimeToEvacuation",
                    'name': "Time to Evacuation",
                    'description': "Minutes from start till evacuation is ordered",
                    "worldstateDescription": self.worldstateDescription,
                    'worldstates': parents,
                    'type': "number",
                    'data': (t1 - t0).total_seconds() / 60
                    })
            if t2 == None:
                # evacuation still running
                intervals = [
                    {
                        "startTime": t1.isoformat(),
                        "endTime": t3.isoformat()
                        }
                    ]
            else:
                # evacuation completed
                intervals = [
                    {
                        "startTime": t1.isoformat(),
                        "endTime": t2.isoformat()
                        }
                    ]
                indicators.append ({
                        'id': "LastPatientEvacuated",
                        'name': "Last Patient Evacuated",
                        'description': "Minutes from start till last patient is evacuated",
                        "worldstateDescription": self.worldstateDescription,
                        'worldstates': parents,
                        'type': "number",
                        'data': (t2 - t0).total_seconds() / 60
                        })
                result['kpi'] = {
                    "delay": {
                        "displayName": "Evacuation completed",
                        "iconResource": "flower_16.png",
                        self.identifier: {
                            "displayName": self.title,
                            "iconResource": "flower_dead_16.png",
                            "value": (t2 - t0).total_seconds() / 60,
                            "unit": "Minutes"
                            }
                        } 
                    }

        indicators.insert(0, {
                'id': self.identifier,
                'name': self.title,
                'description': "Evacuation start and end",
                "worldstateDescription": self.worldstateDescription,
                'worldstates': parents,
                "type":"timeintervals",
                "data": {
                    "intervals": intervals,
                    "color": "#00cc00",
                    "linewidth": 2
                    }
                })

        result['indicator'] = indicators;
        return result

