var wpsApp = angular.module ("wpsApp", []);
var x2js = new X2JS();     


wpsApp.controller ('wpsCtrl', function ($scope, $http) {
    // default values
    $scope.serverTmp = "https://crisma-pilotC.ait.ac.at"
    $scope.wpsEndpointTmp = $scope.serverTmp + "/indicators/cgi-bin/pywps.cgi";
    $scope.icmmEndpointTmp = $scope.serverTmp + "/icmm_api";

    // really used values
    $scope.wpsEndpoint = $scope.wpsEndpointTmp;
    $scope.icmmEndpoint = $scope.icmmEndpointTmp;

    // list of indicators from WPS capabilities - to be updated from WPS Capabilities
    $scope.indicators = [];  // ["deathsIndicator", "seriouslyDeterioratedIndicator", "improvedIndicator", "lifeIndicator"];
    $scope.indicator = null; // $scope.indicators[0];
    $scope.indicatorsSelected = []; 
    $scope.descriptionTable = [];


    // example ICMM worldstate URLs:
    //$scope.worldstateUrl = "https://crisma-pilotC.ait.ac.at/icmm_api/CRISMA.worldstates/263";
    // first of simulation
    //$scope.worldstateUrl = "http://crisma.cismet.de/pilotEv2/staging/icmm_api/CRISMA.worldstates/373";
    // last of a PilotE simulation
    // $scope.worldstateUrl = "https://crisma-pilotE.ait.ac.at/icmm_api/CRISMA.worldstates/445";

    $scope.worldstateUrl = $scope.icmmEndpoint + "/CRISMA.worldstates/445";
    $scope.worldstateURLsBaseline = [];
    $scope.worldstateUrlBaseline = null;
    $scope.worldstateURLsLeaf = [];
    $scope.worldstateUrlLeaf = null;


    $scope.worldstateOptionSelected = "Single";

    // ask WPS for indicators (Processes in GetCapabilities)
    $scope.loadIndicators = function() {
	$http({
	    method: "GET",
	    url: $scope.wpsEndpoint + "?service=WPS&request=GetCapabilities"
	}).
	    success(function(data, status, headers, config) {
		// console.log (data);
		if (data != null) {
		    var response = x2js.xml_str2json (data)
		    // console.log (JSON.stringify (response));

		    if ('Process' in response.Capabilities.ProcessOfferings) {
			var processes = response.Capabilities.ProcessOfferings.Process;
			var indicators = [];
			
			if (angular.isArray (processes)) {
			    for (var i = 0; i < processes.length; i++) {
				indicators.push (processes[i].Identifier.__text);
			    }
			} else {
			    indicators.push (processes.Identifier.__text);
			}
			$scope.indicators = indicators;
			$scope.indicator = $scope.indicators.length > 0 ? $scope.indicators[0] : null;

			$scope.loadDescription (0);

		    } else {
			alert ("No processes defined within this WPS!");
		    }
		} else {
		    alert ("Got no Capabilities from WPS!");
		}
	    }).
	    error(function(data, status, headers, config) {
		alert ("WPS server " + $scope.wpsEndpoint + " not available");
	    });
    };

    $scope.loadDescription = function(number) {
	if (number < $scope.indicators.length) {
	    var identifier = $scope.indicators[number];
	    $http({
		method: "GET",
		url: $scope.wpsEndpoint + "?service=WPS&request=DescribeProcess&version=1.0.0&identifier=" + identifier
	    }).
		success(function(data, status, headers, config) {
		    // console.log (data);
		    if (data != null) {
			var response = x2js.xml_str2json (data)
			// console.log (JSON.stringify (response));
			
			if (('ProcessDescription' in response.ProcessDescriptions) && ('Abstract' in response.ProcessDescriptions.ProcessDescription)) {
			    var abstract = response.ProcessDescriptions.ProcessDescription.Abstract;
			
			    abstract = abstract["__text"];
			    var lines = abstract.split ("\n");

			    var tmpTable = $scope.descriptionTable;

			    for (var i = 0; i < lines.length; i++) {
				var description = lines[i].split (";");
				if (description.length === 5) {
				    description.splice (0, 0, identifier);
				    tmpTable.push (description);
				}
			    }
			    
			    $scope.descriptionTable = tmpTable;

			    // console.log (JSON.stringify ($scope.descriptionTable));
			    
			    $scope.loadDescription (number + 1);	
			} else {
			    alert ("No Abstract found for Process " + identifier + "!");
			}
		    } else {
			alert ("Got no ProcessDescription for " + identifier + " from WPS!");
		    }
		}).
		error(function(data, status, headers, config) {
		    alert ("WPS server " + $scope.wpsEndpoint + " not available");
		});
	};
    };

    $scope.allWorldstateData = null;

    $scope.getAllWorldstates = function (fp) {
	if ($scope.allWorldstateData == null) {
    	    $http({
		method: "GET",
		url: $scope.icmmEndpoint + "/CRISMA.worldstates/?level=1&fields=childworldstates,categories&deduplicate=true&ommitNullValues=true&limit=10000"
	    }).
		success(function(data, status, headers, config) {
		    // console.log (JSON.stringify (data));
		    $scope.allWorldstateData = data;
		    fp();
		}).
		error(function(data, status, headers, config) {
		    alert ("WPS server " + $scope.wpsEndpoint + " not available");
		$scope.allWorldstateData = null;
	    });
	} else {
	    fp();
	}
    };


    $scope.loadNoWorldstates = function () {
	$scope.setWorldstatesToExecute();
    };

    $scope.loadBaseWorldstates = function() {
	$scope.getAllWorldstates (function() {
	    if ($scope.allWorldstateData != null) {
		var baseWSs = [];
		for (var i = 0; i < $scope.allWorldstateData['$collection'].length; i++) {
		    for (var c = 0; c < $scope.allWorldstateData['$collection'][i]['categories'].length; c++) {
			// Only baseline worldstates
			if ($scope.allWorldstateData['$collection'][i]['categories'][c]['$ref'] === "/CRISMA.categories/2") {
			    baseWSs.push ($scope.icmmEndpoint + $scope.allWorldstateData['$collection'][i]['$self']);
			    break;
			}
		    }
		}
		$scope.worldstateURLsBaseline = baseWSs;
		$scope.worldstateUrlBaseline = $scope.worldstateURLsBaseline.length > 0 ? $scope.worldstateURLsBaseline[0] : null;
	    } else {
		alert ("No respones from icmm service!");
		$scope.worldstateURLsBaseline = [];
	    }
	    $scope.setWorldstatesToExecute();
	});
    };


    $scope.loadLeafWorldstates = function() {
	$scope.getAllWorldstates (function() {
	    if ($scope.allWorldstateData != null) {
		var baseWSs = [];
		for (var i = 0; i < $scope.allWorldstateData['$collection'].length; i++) {
		    // skip worldstates with children
		    if (('childworldstates' in $scope.allWorldstateData['$collection'][i]) && ($scope.allWorldstateData['$collection'][i]['childworldstates'].length > 0)) {
			continue;
		    }
		    var isTemplate = false;
		    for (var c = 0; c < $scope.allWorldstateData['$collection'][i]['categories'].length; c++) {
			// aciod template worldstates
			if ($scope.allWorldstateData['$collection'][i]['categories'][c]['$ref'] === "/CRISMA.categories/1") {
			    isTemplate = true;
			    break;
			}
		    }
		    if (isTemplate) {
			continue;
		    }	
		    baseWSs.push ($scope.icmmEndpoint + $scope.allWorldstateData['$collection'][i]['$self']);
		}
		$scope.worldstateURLsLeaf = baseWSs;
		$scope.worldstateUrlLeaf = $scope.worldstateURLsLeaf.length > 0 ? $scope.worldstateURLsLeaf[0] : null;
	    }
	    $scope.setWorldstatesToExecute();
	});
    };

    $scope.loadSuccessorWorldstates = function(tmp, baseWS) {
	// This function is only called after a baseline worldstate has been selected, therefore $scope.allWorldstateData is already filled!
	if (baseWS != null) {
	    tmp.push ($scope.icmmEndpoint + baseWS);
	    for (var i = 0; i < $scope.allWorldstateData['$collection'].length; i++) {
		// only the baseWS worldstate && with children
		if ((baseWS === $scope.allWorldstateData['$collection'][i]['$self']) && ('childworldstates' in $scope.allWorldstateData['$collection'][i])) {
		    for (var c = 0; c < $scope.allWorldstateData['$collection'][i]['childworldstates'].length; c++) {
			$scope.loadSuccessorWorldstates (tmp, $scope.allWorldstateData['$collection'][i]['childworldstates'][c]['$ref']);
		    }
		}
	    }
	}
    };


    $scope.processesToExecute = [];
    $scope.setProcessesToExecute = function() {
	var tmp = []
	for (var process in $scope.indicatorsSelected) {
	    if ($scope.indicatorsSelected[process]) {
		tmp.push (process);
	    }
	} 
	$scope.processesToExecute = tmp;
    };


    $scope.worldstatesToExecute = [$scope.worldstateUrl];
    $scope.setWorldstatesToExecute = function() {
	if ("Single" === $scope.worldstateOptionSelected) {
	    $scope.worldstatesToExecute = [$scope.worldstateUrl];
	} else if ("Baseline" === $scope.worldstateOptionSelected) {
	    var tmp = [];
	    var ws = $scope.worldstateUrlBaseline.substring ($scope.icmmEndpoint.length);
	    $scope.loadSuccessorWorldstates (tmp, ws);
	    $scope.worldstatesToExecute = tmp;
	} else if ("Leaf" === $scope.worldstateOptionSelected) {
	    $scope.worldstatesToExecute = [$scope.worldstateUrlLeaf];
	} 
    };


    // results = {worldstate: [Process1:result1, Process2:result2,...],..}
    $scope.results = {};
    $scope.executeAll = function(){
	console.log ("executeAll started");
	$scope.results = {};
	$scope.executeAll2(0, 0)
    };
    $scope.executeAll2 = function(wsNo, pNo){
	if (!($scope.worldstatesToExecute[wsNo] in $scope.results)) {
	    $scope.results[$scope.worldstatesToExecute[wsNo]] = {};
	}
	$scope.executeWPS (wsNo, pNo, function (wsNo, pNo) {
	    // next process execution...
	    pNo++;
	    if (pNo >= $scope.processesToExecute.length) {
		// done with this worldstate
		pNo = 0;
		wsNo++;
	    }	    
	    if (wsNo < $scope.worldstatesToExecute.length) {
		$scope.executeAll2 (wsNo, pNo);
	    }
	    // Done :-)
	});
    };



    // 	<a href='{{wpsEndpoint}}?service=WPS&request=Execute&version=1.0.0&identifier={{indicator}}&datainputs=ICMMworldstateURL={{worldstateUrl}}' target='Execute'>{{wpsEndpoint}}?service=WPS&request=Execute&version=1.0.0&identifier={{indicator}}&datainputs=ICMMworldstateURL={{worldstateUrl}}</a>
    $scope.executeWPS = function(wsNo, pNo, fp) {
	var wsUrl = $scope.worldstatesToExecute[wsNo];
	var process = $scope.processesToExecute[pNo];
	$http({
	    method: "GET",
	    url: $scope.wpsEndpoint + "?service=WPS&request=Execute&version=1.0.0&identifier=" + process + "&datainputs=ICMMworldstateURL=" + wsUrl
	}).
	    success(function(data, status, headers, config) {
		// console.log (data);
		if (data != null) {
		    var response = x2js.xml_str2json (data)
		    // console.log (JSON.stringify (response));
		    var msgFound = false;
		    if ('ProcessOutputs' in response.ExecuteResponse) {
			// search my status output
			$scope.results[$scope.worldstatesToExecute[wsNo]][$scope.processesToExecute[pNo]] = "status ProcessOutput missing";
			for (var o = 0; o < response.ExecuteResponse.ProcessOutputs.Output.length; o++) {
			    // console.log (JSON.stringify (response.ExecuteResponse.ProcessOutputs.Output[o]))
			    if ("statusmessage" === response.ExecuteResponse.ProcessOutputs.Output[o].Identifier["__text"]) {
				$scope.results[$scope.worldstatesToExecute[wsNo]][$scope.processesToExecute[pNo]] = response.ExecuteResponse.ProcessOutputs.Output[o].Data.LiteralData["__text"];
				msgFound = true;
				break;
			    }
			} 
		    } 
		    if ((!msgFound) && ('Status' in response.ExecuteResponse) && ('ProcessFailed' in response.ExecuteResponse.Status)) {
			$scope.results[$scope.worldstatesToExecute[wsNo]][$scope.processesToExecute[pNo]] = response.ExecuteResponse.Status.ProcessFailed.ExceptionReport.Exception.ExceptionText["__text"];
			msgFound = true;
		    } 
		    if ((!msgFound) && ('Status' in response.ExecuteResponse) && ('ProcessSucceeded' in response.ExecuteResponse.Status)) {
			$scope.results[$scope.worldstatesToExecute[wsNo]][$scope.processesToExecute[pNo]] = response.ExecuteResponse.Status.ProcessSucceeded["__text"];
			msgFound = true;
		    } 
		    if (!msgFound) {
			$scope.results[$scope.worldstatesToExecute[wsNo]][$scope.processesToExecute[pNo]] = "Status missing";
		    }
		} else {
		    $scope.results[$scope.worldstatesToExecute[wsNo]][$scope.processesToExecute[pNo]] = "No WPS result";
		}
		fp (wsNo, pNo);
	    }).
	    error(function(data, status, headers, config) {
		$scope.results[$scope.worldstatesToExecute[wsNo]][$scope.processesToExecute[pNo]] = "WPS not available";
		fp (wsNo, pNo);
	    });
    };


    $scope.init = function () {
	$scope.wpsEndpoint = $scope.wpsEndpointTmp;
	$scope.icmmEndpoint = $scope.icmmEndpointTmp;
	$scope.indicators = []; 
	$scope.indicator = null; 
	$scope.indicatorsSelected = []; 
	$scope.descriptionTable = [];
	$scope.worldstateUrl = $scope.icmmEndpoint + "/CRISMA.worldstates/445";
	$scope.worldstateURLsBaseline = [];
	$scope.worldstateUrlBaseline = null;
	$scope.worldstateURLsLeaf = [];
	$scope.worldstateUrlLeaf = null;
	$scope.worldstateOptionSelected = "Single";
	$scope.allWorldstateData = null;
	$scope.processesToExecute = [];
	$scope.worldstatesToExecute = [$scope.worldstateUrl];
	$scope.results = {};

	$scope.loadIndicators();
    }

    $scope.init();

});
