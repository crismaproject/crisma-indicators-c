"""
Peter Kutschera, 2013-09-11
Time-stamp: "2014-03-21 13:27:23 peter"
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
from xml.sax.saxutils import escape
import time

class Process(WPSProcess):
    def __init__(self):
        # init process
        WPSProcess.__init__(
            self,
            identifier="lifeIndicator", #the same as the file name
            version = "1.0",
            title="Some indicator of the given world state",
            storeSupported = "false",
            statusSupported = "false",
            abstract="Fetch needed WorldState data and calculate an indicator",
            grassLocation =False)
        self.WorldState = self.addLiteralInput (identifier = "WorldStateId",
                                                type = type(""), # default: integer
                                                title = "One particular WorldState")
        self.Answer=self.addLiteralOutput(identifier = "indicator",
                                          type = type (""),
                                          title = "URL to access indicator")
        self.value=self.addLiteralOutput(identifier = "value",
                                          type = type (""),
                                          title = "indicator value")

                                           
    def execute(self):
        # some constants, see OOI-WSR docu
        patientTypeId = 10         #is this sufficient or might there be subclasses?
        patientLifePropertyId = 42
        indicatorEntityId = 101
        indicatorPropertyId = 60
        baseUrl = 'http://crisma-ooi.ait.ac.at/api/EntityProperty'

        self.status.set("baseUrl = {}".format (baseUrl), 1)

        worldStateId = self.WorldState.getValue();
        self.status.set("Check WorldState {} status".format (worldStateId), 10)

        params = {
            'wsid' :  worldStateId, 
            'etpid' : indicatorPropertyId
            }
        headers = {'content-type': 'application/json'}
        indicatorProperties = requests.get(baseUrl, params=params, headers=headers) 

        print >> stderr, indicatorProperties

        
        if indicatorProperties.status_code != 200:
            return "Error accessing WorldState with id {}: {}".format (worldStateId, response.raise_for_status())

        # count already existing results
        existingResults = 0;
        existingResult = None
        for ep in indicatorProperties.json():
            # print "{}: {}".format (indicatorProperties, ep)
            existingResults +=1
        if existingResults > 1:
            return "There are already {} results! This should not be the case!".format (existingResults)
        if existingResults == 1:
            existingResult = indicatorProperties.json()[0]['entityPropertyId']
            # Select what you want:
            # ## option 1: This is an error
            #return "There is already a result!"
            # ## option 2: not an error, just use existing result
            #resultUrl = "{}/{}".format (baseUrl, existingResult)
            #self.Answer.setValue(escape (resultUrl))
            #return
            # ## option 3: not an error, recalculate and replace
            pass


        self.status.set("Start collecting input data for WorldState = {}".format (worldStateId), 10)

        # patients and their life state
        numberOfPatients = {'sum' : 0, 'green' : 0, 'yellow': 0, 'red' : 0, 'dead' : 0}
        requiredLifePropertyValue = {'green': 85, 'yellow': 50, 'red' : 10} # below 'red': 'dead'


        params = {
            'wsid' :  worldStateId, 
            'etpid' : patientLifePropertyId
            }
        entityProperties = requests.get(baseUrl, params=params) 

        self.status.set("Got WorldState data", 50)

        for ep in entityProperties.json():
            # Needs to be int (0..100). If not this is an error. Just silently skip to get an result anyway!
            if ep["entityTypeProperty"]['entityTypePropertyType'] != 1: 
                print >> stderr, "Patient life property is not of type 1 (integer)!"
                continue 
            # The entityTypePropertyType might be a lie
            try:
                life = int (ep["entityPropertyValue"])
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
                print >> stderr, ep["entityPropertyValue"], " is not an integer!"
                # ignore problem !?!?
                pass
        
        self.status.set("Calculated indicator for WorldState with id {}: {}".format (worldStateId, json.dumps (numberOfPatients)), 90)

        # create indicator value structure
        indicatorData = {
            'id': "lifeIndicator",
            'name': "health status summary",
            'description': "Life status categoized and summed up per category",
            'worldstates': [worldStateId],
            'type': "histogram",
            'data': [
                {
                    "key": "dead",
                    "value": numberOfPatients['dead'],
                    "desc": "life status below 10",
                    "color": "#000000"
                    },
                {
                    "key": "red",
                    "value": numberOfPatients['red'],
                    "desc" : "life status 10..50",
                    "color" : "#ff0000"
                    },
                {
                    "key" : "yellow",
                    "value" : numberOfPatients['yellow'],
                    "desc" : "life status 50..85",
                    "color" : "yellow"
                    },
                {
                    'key': "green",
                    "value" : numberOfPatients['green'],
                    'desc' : "live status 85 or better",
                    "color" : "#00FF00"
                    }
                ]
            }

        self.value.setValue (json.dumps (indicatorData))

        # write result to OOI-WSR
        indicatorValue = json.dumps (indicatorData)
        #indicatorValue = json.dumps (numberOfPatients)

        indicatorProperty = {
            "entityId" : indicatorEntityId,
            "entityTypePropertyId": indicatorPropertyId,
            "entityPropertyValue": indicatorValue,
            "worldStateId": worldStateId,
            }
        print >> stderr, json.dumps (indicatorProperty)

        if existingResults == 1:
            indicatorProperty["entityPropertyId"] = existingResult
            print >> stderr, "put to {}/{}".format (baseUrl, existingResult)
            result = requests.put ("{}/{}".format (baseUrl, existingResult), data=json.dumps (indicatorProperty), headers={'content-type': 'application/json'})
            if result.status_code != 200:
                return "Unable to PUT result at {}/{}: {}".format (baseUrl, existingResult, result.status_code)
            resultUrl = "{}/{}".format (baseUrl, existingResult)
        else:
            print >> stderr, "post to{}".format (baseUrl)
            result = requests.post (baseUrl, data=json.dumps (indicatorProperty), headers={'content-type': 'application/json'})
            if result.status_code != 201:
                return "Unable to POST result at {}: {}".format (baseUrl, result.status_code)
            newResult = result.json()[u'entityPropertyId']
            resultUrl = "{}/{}".format (baseUrl, newResult)

        self.status.set("Saved indicator for WorldState with id {}: {}".format (worldStateId, result.status_code), 99)
        self.Answer.setValue(escape (resultUrl))


        return

