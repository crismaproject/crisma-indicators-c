"""
Peter Kutschera, 2014-02-10
Time-stamp: "2014-02-10 14:56:03 peter"

The server gets an world state id and calculates an indicator
../wps.py?request=Execute
&service=WPS
&version=1.0.0
&identifier=improvedIndicator
&datainputs=WorldStateId=21

Needs an recent requests library:
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
from xml.sax.saxutils import escape
import time

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
        self.WorldState = self.addLiteralInput (identifier = "WorldStateId",
                                                # type = type(""), # default: integer
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
        indicatorPropertyId = 63
        baseUrl = 'http://crisma-ooi.ait.ac.at/api/EntityProperty'
        worldStateUrl = 'http://crisma-ooi.ait.ac.at/api/WorldState'
        headers = {'content-type': 'application/json'}

        worldStateId = self.WorldState.getValue();
        self.status.set("Actual WorldState: {}".format (worldStateId), 10)

        # get list of WorldStates to find base WorldState
        worldStateList = requests.get (worldStateUrl);
        if worldStateList.status_code != 200:
            return "Error accessing WorldState list: {}".format (response.raise_for_status())

        baseWorldStateId = findBaseId (worldStateId, worldStateList.json())
        
        if baseWorldStateId is None:
            return "Base WorldState not found for actual WorldState = {}".format (worldStateId)

        self.status.set("Base WorldState: {}".format (baseWorldStateId), 15)

        params = {
            'wsid' :  worldStateId, 
            'etpid' : indicatorPropertyId
            }
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



        # patients and their life state
        numberOfImproved = 0;

        # base data:
        self.status.set("Request input data for WorldState = {}".format (baseWorldStateId), 20)
        params = {
            'wsid' :  baseWorldStateId, 
            'etpid' : patientLifePropertyId
            }
        baseEntityProperties = requests.get(baseUrl, params=params) 

        # actual data
        self.status.set("Request input data for WorldState = {}".format (worldStateId), 21)
        params = {
            'wsid' :  worldStateId, 
            'etpid' : patientLifePropertyId
            }
        entityProperties = requests.get(baseUrl, params=params) 

        self.status.set("Got WorldState data", 22)

        patients = {}

        for ep in baseEntityProperties.json():
            # Needs to be int (0..100). If not this is an error. Just silently skip to get an result anyway!
            if ep["entityTypeProperty"]['entityTypePropertyType'] != 1: 
                # print >> stderr, "Patient life property is not of type 1 (integer)!"
                continue 
            # The entityTypePropertyType might be a lie
            try:
                life = int (ep["entityPropertyValue"])
                patients[ep["entityId"]] = life
            except:
                # print >> stderr, ep["entityPropertyValue"], " is not an integer!"
                # ignore problem !?!?
                pass
        for ep in entityProperties.json():
            # Needs to be int (0..100). If not this is an error. Just silently skip to get an result anyway!
            if ep["entityTypeProperty"]['entityTypePropertyType'] != 1: 
                # print >> stderr, "Patient life property is not of type 1 (integer)!"
                continue 
            # The entityTypePropertyType might be a lie
            try:
                life = int (ep["entityPropertyValue"])
                if life >= patients[ep["entityId"]]:
                    numberOfImproved += 1
            except:
                # print >> stderr, ep["entityPropertyValue"], " is not an integer!"
                # ignore problem !?!?
                pass

        
        self.status.set("Calculated improvedIndicator for WorldState with id {}: {}".format (worldStateId, numberOfImproved), 90)

        # create indicator value structure
        indicatorData = {
            'id': "improvedIndicator",
            'name': "improved",
            'description': "Number of patients with actual life status better or equal then base life status",
            'worldstates': [baseWorldStateId, worldStateId],
            'type': "number",
            'data': numberOfImproved
            }

        self.value.setValue (json.dumps (indicatorData))

        # write result to OOI-WSR
        indicatorValue = json.dumps (indicatorData)
        #indicatorValue = indicatorData['data']

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


def findParentId (id, list):
    """Go throu list and find id of parent worldstate for given worldstate id"""
    for e in list:
        if e['worldStateId'] == id:
            return e['worldStateParentId']
    return None;


def findBaseId (id, list):
    """Go up the list of parents till the beginning"""
    parent = findParentId (id, list)
    while parent is not None:
        id = parent
        parent = findParentId (id, list)
    return id
