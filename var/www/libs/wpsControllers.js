var wpsApp = angular.module ("wpsApp", []);
var x2js = new X2JS();     


wpsApp.controller ('wpsCtrl', function ($scope, $http) {
    $scope.wpsEndpoint = "cgi-bin/pywps.cgi";

    // list of indicators from WPS capabilities - to be updated from WPS Capabilities
    $scope.indicators = [];  // ["deathsIndicator", "seriouslyDeterioratedIndicator", "improvedIndicator", "lifeIndicator"];
    $scope.indicator = null; // $scope.indicators[0];

    // example ICMM worldstate URL
    $scope.worldstateUrl = "https://crisma-pilotC.ait.ac.at/icmm_api/CRISMA.worldstates/263";


    $scope.descriptionTable = [];


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
			
			for (var i = 0; i < processes.length; i++) {
			    indicators.push (processes[i].Identifier.__text);
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

    $scope.loadIndicators();

});
