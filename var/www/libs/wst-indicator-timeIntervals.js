/*
 Peter.Kutschera@ait.ac.at, 2014-02-11
 Time-stamp: "2014-02-28 08:05:08 peter"

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
 
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see http://www.gnu.org/licenses/gpl-2.0.html
*/

/*
 <indicator-time-intervals
         indicator-data="listOfIndicatorObjects" // required
	 indicator-filter="listOfIndicatorIds"   // optional, untested
	 ws-filter="listOfWsIds"                 // optional, untested
	 groupIndicatorsBy="worldstate"          // optional, "worldstate" or "indicator"
	 min-time="minTime"                      // optional, used to sync time range from <tree-graph>
	 max-time="maxTime"                      // optional, used to sync time range from <tree-graph>
	 width="960"                             // width in pixel
 >
 </indicator-time-intervals>
*/

WstApp.directive ('indicatorTimeIntervals', function ($parse) {
    var directiveDefinitionObject = {
        restrict: 'E',
        replace: false,
        scope: {
	    allIndicators: "=indicatorData",
	    wsFiler: '=?wsFilter',
	    indicatorFilter: "=?indicatorFilter",
	    groupBy: "=?groupIndicatorsBy",
	    minTime: '=?minTime',
	    maxTime: '=?maxTime'
	},
        link: function (scope, element, attrs) {
	    var graph = d3.select(element[0]);

	    // build the options object
	    // indicatorHeight > fontSize + 4
	    var options = $.extend ({fontSize : 12, indicatorHeight: 20, width : 960}, attrs);
	    
	    // create tool-tip container
	    var div =  d3.select(element[0])
		.append("div")   
		.attr("class", "indicator-interval-tooltip")               
		.style("opacity", 0);

	    var data = [];
	    var calculatedMinTime = null;
	    var calculatedMaxTime = null;

	    scope.$watch ('allIndicators', function (newVal, oldVal) {
		// console.log ('change allIndicators ' + JSON.stringify (oldVal) + ' --> ' + JSON.stringify (newVal));
		buildDataset();
		redraw();
	    });

	    scope.$watch ('minTime', function (newVal, oldVal) {
		// console.log ('change minTime ' + JSON.stringify (oldVal) + ' --> ' + JSON.stringify (newVal));
		if (newVal === oldVal) { return; }
		redraw();
	    });
	    scope.$watch ('maxTime', function (newVal, oldVal) {
		// console.log ('change maxTime ' + JSON.stringify (oldVal) + ' --> ' + JSON.stringify (newVal));
		if (newVal === oldVal) { return; }
		redraw();
	    });
	    scope.$watch ('groupBy', function (newVal, oldVal) {
		// console.log ('change groupBy ' + JSON.stringify (oldVal) + ' --> ' + JSON.stringify (newVal));
		if (newVal === oldVal) { return; }
		rearrange();
	    });


	    var svg, x, y, indicator;

	    function redraw () {
		graph.select('svg').remove();
		// size of the diagram
		var size = { width:+options.width, height: data.length * options.indicatorHeight + 15}; 
		var margin = {top: 20, right: 20, bottom: 30, left: 50};

		var minTime = scope.minTime != null ? d3.time.format.iso.parse(scope.minTime) : calculatedMinTime;
		var maxTime = scope.maxTime != null ? d3.time.format.iso.parse(scope.maxTime) : calculatedMaxTime;

		x = d3.time.scale()
		    .range([0, size.width]);

		y = d3.scale.linear()
		    .range([options.indicatorHeight, data.length * options.indicatorHeight]);

		var xAxis = d3.svg.axis()
		    .scale(x)
		    .orient("bottom");

		var yAxis = d3.svg.axis()
		    .scale(y)
		    .orient("left");


		svg = graph.append("svg")
		    .attr("width", size.width + margin.left + margin.right)
		    .attr("height", size.height + margin.top + margin.bottom)
		    .append("g")
		    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
		
		x.domain ([minTime, maxTime]);
		y.domain ([0, data.length - 1]);

// data = [{"id":"timeIntervalsTest","name":"Just some test data","description":"List of time intervals","worldstates":[59,81],"type":"timeintervals","data":{"intervals":[{"startTime":"2012-01-01T12:19:00.000","endTime":"2012-01-01T12:24:00.000","startt":"2012-01-01T11:19:00.000Z","endt":"2012-01-01T11:24:00.000Z"},{"startTime":"2012-01-01T12:41:00.000","endTime":"2012-01-01T12:45:00.000","startt":"2012-01-01T11:41:00.000Z","endt":"2012-01-01T11:45:00.000Z"}],"color":"#000000","linewidth":2,"yws":0,"yind":0},"worldstate":"82"}]"

		indicator = svg.selectAll(".indicator-intervals")
		    .data(data)
		    .enter()
		    .append ("g")
		    .attr("class", "indicator-intervals")
		    .attr("transform", function (d) {return "translate(0, " + y(scope.groupBy === "worldstate" ? d.data.yws : d.data.yind) +")"});

		var txt = indicator
		    .append ("text")
		    .attr("class", "indicator-interval")
		    .attr("dy", options.fontSize)
		    .text (function (d) { return d.name + " (" + d.worldstate + ")" });

		var intervals = indicator.selectAll("rect")
		    .data (function (d) { return d.data.intervals; })
		    .enter()
		    .append("rect")
		    .attr("class", "indicator-interval")
		    .attr("width", function (d) { return x(d.endt) - x(d.startt); })
		    .attr("height", options.fontSize + 4)
		    .attr("x", function(d) { return x(d.startt); })
		    .attr("y", 0)
		    .style("fill", function(d) { return d.color ? d.color : "#cccccc"; })
		    .style("opacity", .7)
		    .on("mouseover", function(d) {      
			div.transition()        
			    .duration(200)      
			    .style("opacity", .9);      
			div.html(d.startTime + " .. " + d.endTime)  
			    .style("left", (d3.event.pageX) + "px")     
			    .style("top", (d3.event.pageY - 28) + "px");    
		    })                  
		    .on("mouseout", function(d) {       
			div.transition()        
			    .duration(500)      
			    .style("opacity", 0);   
		    });


		svg.append("g")
		    .attr("class", "x axis")
		    .attr("transform", "translate(0," + size.height + ")")
		    .call(xAxis);
	    }

	    function rearrange () {
		indicator
		    .transition()        
		    .duration(500)
		    .attr("transform", function (d) {return "translate(0, " + y(scope.groupBy === "worldstate" ? d.data.yws : d.data.yind) +")"});

	    }

	    function buildDataset () {
		data = [];
		if (scope.allIndicators == null) {
		    return;
		}
		var indicators = [];
		// list of worldstates
		var wss = d3.keys (scope.allIndicators);
		// filter by WorldState
		if (scope.wsFilter != null) {
		    var tmp = wss;
		    wss = [];
		    for (var w = 0; w < tmp.length; w++) {
			if (scope.wsFilter.indexOf (tmp[w]) != -1) {
			    wss.push (tmp[w]);
			}
		    }
		}
		// console.log ('buildDataset: wss =  ' + JSON.stringify (wss));
		if (wss.length == 0) {
		    return;
		}
		// list of indicators
		var inds = {};
		for (var w = 0; w < wss.length; w++) {
		    for (var i = 0; i < scope.allIndicators[wss[w]].length; i++) {
			// filter by indicator id
			if ((scope.indicatorFilter == null) || (scope.indicatorFilter.indexOf (scope.allIndicators[wss[w]][i].id) != -1)) {
			    // filter by indicator type - keep only what I know how to visualize
			    if (["timeintervals"].indexOf (scope.allIndicators[wss[w]][i].type) != -1) {
				inds[scope.allIndicators[wss[w]][i].id] = 1;
			    }
			}
		    }
		}
		inds = d3.keys (inds);
		// console.log ('buildDataset: inds = ' + JSON.stringify (inds));
		if (inds.length == 0) {
		    return;
		}
		var yws = 0;  // y if sorted by WorldState
		var yind = 0; // y if sorted by Indicator
		for (var w = 0; w < wss.length; w++) {
		    yind = w;
		    for (var i = 0; i < scope.allIndicators[wss[w]].length; i++) {
			// filter by indicators found above
			if (inds.indexOf (scope.allIndicators[wss[w]][i].id) != -1) {
			    // filter by indicator type - keep only what I know to visualize
			    if (["timeintervals"].indexOf (scope.allIndicators[wss[w]][i].type) != -1) {
				scope.allIndicators[wss[w]][i].worldstate = wss[w];
				scope.allIndicators[wss[w]][i].data.yws = yws;
				yws++;
				scope.allIndicators[wss[w]][i].data.yind = yind;
				yind += wss.length;
				indicators.push (scope.allIndicators[wss[w]][i]);
			    }
			}
		    }
		}
		var parseDate = d3.time.format.iso.parse;
		for (var i = 0; i < indicators.length; i++) {
		    for (var j = 0; j < indicators[i].data.intervals.length; j++) {
			var n = indicators[i].data.intervals[j];
			n.startt = parseDate (n.startTime);
			n.endt   = parseDate (n.endTime);
 			if (!calculatedMinTime || calculatedMinTime > n.startt) {
			    calculatedMinTime = n.startt;
			}
 			if (!calculatedMaxTime || calculatedMaxTime < n.endt) {
			    calculatedMaxTime = n.endt;
			}
			n.color = indicators[i].data.color;
		    }
		}
		data = indicators;
		// console.log ('buildDataset: data = ' + JSON.stringify (data));
	    }

        }
    };
    return directiveDefinitionObject;
});
