/*
 Peter.Kutschera@ait.ac.at, 2014-02-11
 Time-stamp: "2014-02-19 08:40:42 peter"

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
*/

var IndicatorApp = angular.module('IndicatorApp', []);

IndicatorApp.controller('IndicatorCtrl', function ($scope, $http) {
    $scope.worldStateList = [];
    $scope.baselines = [];
    $scope.baseline = null;
    $scope.baselineSelected = 0;

    $scope.selectedWorldStates = [];
    $scope.indicators = {};

    $scope.groupBy = "worldstate";

    $scope.spinner = new Spinner();

    $scope.loadWorldStates = function() {
	$('#table').spin(true);
	$http({
	    method: "GET",
	    url: "http://crisma-ooi.ait.ac.at/api/WorldState"
	}).
	    success(function(data, status, headers, config) {
		$('#table').spin(false);
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
		} else {
		    alert ("Got no WorldState data!");
		}
	    }).
	    error(function(data, status, headers, config) {
		$('#table').spin(false);
		alert ("Pub/Sub server " + $scope.service.name + " not available");
	    });
    };


    $scope.createWorldStateTree = function () {
	$scope.selectedWorldStates = [];
	$scope.indicators = {};
	if ($scope.baseline == null) {
	    alert ("No WorldState selected!");
	} else {
	    createWorldStateTree("#worldstate-tree", $scope.baseline.worldStateId, $scope.worldStateList, $scope.selectWorldStates);
	    $scope.baselineSelected = 1;
	}
    };


    $scope.selectWorldStates = function (wsIds) {
	wsIds.sort();
	// console.log ("selectedWorldStates (" + JSON.stringify (wsIds) + ")");
	$scope.selectedWorldStates = wsIds;
	$scope.indicators = {};
	$scope.loadIndicatorValues ($scope.selectedWorldStates, 0);
    };

    $scope.loadIndicatorValues = function (wsIds, index) {
	if ((wsIds != null) && (wsIds.length > index)) {
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
			$scope.indicators[wsIds[index]] = values;
			// console.log ("indicators: " + JSON.stringify ($scope.indicators));
			$scope.drawIndicatorBars();
		    } else {
			alert ("Got no WorldState data!");
		    }
		}).
		error(function(data, status, headers, config) {
		    $('#list').spin(false);
		    alert ("Pub/Sub server " + $scope.service.name + " not available");
		});
	    $scope.loadIndicatorValues (wsIds, index + 1);
	}
    };

    $scope.drawIndicatorBars = function () {
	drawIndicators ( "#indicatorBars", $scope.indicators, $scope.groupBy === "worldstate" )
    };

    $scope.loadWorldStates();
});
