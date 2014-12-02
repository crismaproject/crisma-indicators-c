// see http://codepen.io/odiseo42/pen/bCwkv

var WstApp = angular.module ("wstApp", []);


WstApp.controller ('treeCtrl', function ($scope, $http) {
    $scope.worldStateList = [];
    $scope.baselines = [];
    $scope.baseline = null;
    $scope.baselineSelected = 0;

    $scope.treeData = {};
    $scope.selectedWorldStates = []; // list of ids

    $scope.indicators = {};
    
    $scope.groupIndicatorsByWorldstate = 1;
    $scope.groupIndicatorsBy = "worldstate";

    // comunication between graphs
    $scope.minTime = null;
    $scope.maxTime = null;

    $scope.spinner = new Spinner();

    $scope.loadWorldStates = function() {
	$('#wsTree').spin(true);
	$http({
	    method: "GET",
	    url: "http://crisma-ooi.ait.ac.at/api/WorldState"
	}).
	    success(function(data, status, headers, config) {
		$('#wsTree').spin(false);
		// console.log (JSON.stringify (data));
		if (data != null) {
		    $scope.worldStateList = data;
		    var baselines = [];
		    for (var i = 0; i < data.length; i++) {
			if (data[i]["worldStateParentId"] == null) {
			    // console.log ("baseline: " + JSON.stringify (data[i]));
			    //baselines.push ({worldStateId: data[i].worldStateId});
			    baselines.push (data[i]);
			}
		    }
		    if (baselines.length > 0) {
			$scope.baselines = baselines;
			$scope.baseline = $scope.baselines[0];
		    }
		    // console.log ("baselines: " + JSON.stringify ($scope.baselines));
		    // Testing only:
		    for (var i = 0; i < $scope.baselines.length; i++) {
			if ($scope.baselines[i].worldStateId == 59) {
			    $scope.baseline = $scope.baselines[i];
			    break;
			}
		    }
		} else {
		    alert ("Got no WorldState data!");
		}
	    }).
	    error(function(data, status, headers, config) {
		$('#wsTree').spin(false);
		alert ("Pub/Sub server " + $scope.service.name + " not available");
	    });
    };


    $scope.createWorldStateTree = function () {
	$scope.selectedWorldStates = [];
	$scope.indicators = {};
	if ($scope.baseline == null) {
	    alert ("No WorldState selected!");
	} else {
	    // createWorldStateTree("#worldstate-tree", $scope.baseline.worldStateId, $scope.worldStateList, $scope.selectWorldStates);
	    $scope.treeData = createTreeData ($scope.baseline.worldStateId, $scope.worldStateList);
	    $scope.baselineSelected = 1;
	}
    };


    var testIndicators = {
	"82":[
	    {"worldstates":[81],"description":"Number of patients with life status less then 20","data":0,"type":"number","id":"deathsIndicator","name":"Deaths"},
	    {"worldstates":[81],"description":"Life status categoized and summed up per category",
	     "data":[{"color":"#000000","value":0,"key":"dead","desc":"life status below 10"},
		     {"color":"#ff0000","value":7,"key":"red","desc":"life status 10..50"},
		     {"color":"yellow","value":33,"key":"yellow","desc":"life status 50..85"},
		     {"color":"#00FF00","value":10,"key":"green","desc":"live status 85 or better"}],
	     "type":"histogram","id":"lifeIndicator","name":"health status summary"},
	    {"worldstates":[59,81],"description":"Number of patients with actual life status less then base life status - 50","data":0,"type":"number","id":"seriouslyDeterioratedIndicator","name":"Seriously deteriorated"},
	    {"worldstates":[59,81],"description":"Number of patients with actual life status better or equal then base life status","data":50,"type":"number","id":"improvedIndicator","name":"improved"},
	    {"id":"timeIntervalsTest",
	     "name":"Just some test data",
	     "description":"List of time intervals",
	     "worldstates":[59,81],
	     "type":"timeintervals",
	     "data": {
		 intervals: [
		     {
			 startTime: "2012-01-01T12:19:00.000",
			 endTime: "2012-01-01T12:24:00.000",
		     },
		     {
			 startTime: "2012-01-01T12:41:00.000",
			 endTime: "2012-01-01T12:45:00.000",
		     }
		 ],
		 color: "#00cc00",
		 linewidth: 2
		 // stroke
		 // heads: [circle, arrow
	     }
	    },
	    {"id":"timeIntervalsTest2",
	     "name":"Just some other test data",
	     "description":"List of time intervals",
	     "worldstates":[59,81],
	     "type":"timeintervals",
	     "data": {
		 intervals: [
		     {
			 startTime: "2012-01-01T12:10:00.000",
			 endTime: "2012-01-01T12:19:00.000",
		     }
		 ],
		 color: "#0000cc",
		 linewidth: 2
	     }
	    }
	]};


    $scope.selectWorldStates = function (wsIdList) {
	console.log ("selectWS (" + JSON.stringify (wsIdList) + ")");
	$scope.selectedWorldStates = wsIdList;
	// now get e.g. indicators
    	$scope.indicators = {};
	$scope.loadIndicatorValues ($scope.selectedWorldStates, 0);
    };

    var tmpIndicators;
    $scope.loadIndicatorValues = function (wsIds, index) {
	if (index === 0) {
	    // start
	    tmpIndicators = {};
	    // console.log ("start, wsIds = " + JSON.stringify (wsIds));
	    // console.log ("start, tmpIndicators = " + JSON.stringify (tmpIndicators));
	} 
	if ((wsIds != null) && (index < wsIds.length)) {
	    // start and in between
	    $('#list').spin(true);
	    $http({
		method: "GET",
		url: "http://crisma-ooi.ait.ac.at/api/Entity/101?wsid=" + wsIds[index]
	    }).
		success(function(data, status, headers, config) {
		    $('#list').spin(false);
		    // console.log (JSON.stringify (data));
		    if (data != null) {
			var values = [];
			for (var i = 0; i < data.entityInstancesProperties.length; i++) {
			    values.push (JSON.parse (data.entityInstancesProperties[i].entityPropertyValue));
			}
			tmpIndicators[wsIds[index]] = values;
			$scope.loadIndicatorValues (wsIds, index + 1);
		    } else {
			alert ("Got no WorldState data!");
		    }
		}).
		error(function(data, status, headers, config) {
		    $('#list').spin(false);
		    alert ("Pub/Sub server " + $scope.service.name + " not available");
		});
	} 
	if ((wsIds != null) && (index == wsIds.length)) {
	    // end
	    // console.log ("end,   tmpIndicators = " + JSON.stringify (tmpIndicators));
	    $scope.indicators = tmpIndicators;
	}
    };


    $scope.test = function () {
	console.log ("test: selectedWorldStates: " + JSON.stringify ($scope.selectedWorldStates));
	console.log ("test: minTime: " + JSON.stringify ($scope.minTime));
	console.log ("test: maxTime: " + JSON.stringify ($scope.maxTime));
	// $scope.indicators = testIndicators;
	console.log ("test: groupIndicatorsByWorldstate: " + $scope.groupIndicatorsByWorldstate);
    };

    $scope.loadWorldStates();

});
