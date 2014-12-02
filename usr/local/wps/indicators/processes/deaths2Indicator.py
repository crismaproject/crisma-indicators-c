"""
Peter Kutschera, 2013-09-11
Time-stamp: "2014-05-19 14:16:03 peter"

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

import Indicator
import ICMMtools as ICMM
import OOItools as OOI

class Process(Indicator):
    def __init__(self):
        # init process
        Indicator.__init__(
            self,
            identifier="deathsIndicator", #the same as the file name
            version = "1.0",
            title="Number of fatalities",
            abstract="Number of patients with health less than 20")

    def calculateIndicator(self):
        # calculate indicator value
        self.status.set("Start collecting input data", 20)
        self.status.set("Calculated deathsIndicator: {}".format (numberOfDeaths), 40)
        
        # create indicator value structure
        indicatorData = {
            'id': "deathsIndicator",
            'name': "Deaths",
            'description': "Number of patients with life status less then 20",
            "worldstateDescription": self.worldstateDescription,
            'worldstates': [self.OOIworldstate.id],
            'type': "number",
            'data': numberOfDeaths
            }
        return indicatorData


