/*
 Peter.Kutschera@ait.ac.at, 2014-02-11
 Time-stamp: "2014-02-28 13:06:10 peter"

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
 <indicator-bars 
         indicator-data="listOfIndicatorObjects" // required
	 indicator-filter="listOfIndicatorIds"   // optional, untested
	 ws-filter="listOfWsIds"                 // optional, untested
	 groupIndicatorsBy="worldstate"          // optional, "worldstate" or "indicator"
	 width="960"                             // width in pixel
 >
 </indicator-bars>
*/

WstApp.directive ('indicatorBars', function ($parse) {
    var directiveDefinitionObject = {
        restrict: 'E',
        replace: false,
        scope: {
	    allIndicators: "=indicatorData",
	    wsFiler: '=?wsFilter',
	    indicatorFilter: "=?indicatorFilter",
	    groupBy: "=?groupIndicatorsBy",
	},
        link: function (scope, element, attrs) {

	    var graph = d3.select(element[0]);

	    // build the options object
	    // indicatorHeight > fontSize + 4
	    var options = $.extend ({fontSize : 12, indicatorHeight: 20, width : 960, height : 300}, attrs);
	    
	    // create tool-tip container
	    var div =  d3.select(element[0])
		.append("div")   
		.attr("class", "indicator-bars-tooltip")               
		.style("opacity", 0);

	    var data = [];
	    var data_wss = [];
	    var data_inds = [];

	    scope.$watch ('allIndicators', function (newVal, oldVal) {
		console.log ('change allIndicators ' + JSON.stringify (oldVal) + ' --> ' + JSON.stringify (newVal));
		buildDataset();
		redraw();
	    });

	    scope.$watch ('groupBy', function (newVal, oldVal) {
		console.log ('change groupBy ' + JSON.stringify (oldVal) + ' --> ' + JSON.stringify (newVal));
		if (newVal === oldVal) { return; }
		rearrange();
	    });

	    var margin = {top: 20, right: 20, bottom: 30, left: 40};
	    var width, height;
	    var svg, x0, x1, y, color, groups, bars, legend, xAxis, xAxisSvg;

	    function redraw () {
		graph.select('svg').remove();

		width = options.width - margin.left - margin.right,
		height = options.height - margin.top - margin.bottom;

		x0 = d3.scale.ordinal()
		    .rangeRoundBands([0, width], .1);

		x1 = d3.scale.ordinal();

		y = d3.scale.linear()
		    .range([height, 0]);

		color = d3.scale.ordinal()
		    .range(["#98abc5", "#8a89a6", "#7b6888", "#6b486b", "#a05d56", "#d0743c", "#ff8c00"]);

		xAxis = d3.svg.axis()
		    .scale(x0)
		    .orient("bottom");

		var yAxis = d3.svg.axis()
		    .scale(y)
		    .orient("left")
		    .tickFormat(d3.format(".2s"));

		svg = graph.append("svg")
		    .attr("width", width + margin.left + margin.right)
		    .attr("height", height + margin.top + margin.bottom)
		    .append("g")
		    .attr("class", "container")
		    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");


		color.domain (scope.groupBy === "worldstate" ? data_inds : data_wss);
		x0.domain    (scope.groupBy === "worldstate" ? data_wss : data_inds);
		x1.domain    (scope.groupBy === "worldstate" ? data_inds : data_wss)
		    .rangeRoundBands([0, x0.rangeBand()]);
		y.domain([0, d3.max(data, function(d) { return d.max; }) ]);

		xAxisSvg = svg.append("g")
		    .attr("class", "x axis")
		    .attr("transform", "translate(0," + height + ")")
		    .call(xAxis);

		svg.append("g")
		    .attr("class", "y axis")
		    .call(yAxis)
		    .append("text")
		    .attr("transform", "rotate(-90)")
		    .attr("y", 6)
		    .attr("dy", ".71em")
		    .style("text-anchor", "end")
		    .text("Indicator-Value");

		groups = svg.selectAll(".group")
		    .data(data)
		    .enter().append("g")
		    .attr("class", "g")
		    .attr("transform", function(d) { 
			return "translate(" + x0(scope.groupBy === "worldstate" ? d.worldstate : d.id) + ",0)"; });


		bars = groups.selectAll("rect")
		    .data(function(d) { return d.bars; })
		    .enter().append("rect")
		    .attr("width", x1.rangeBand())
		    .attr("x", function(d) { return x1(scope.groupBy === "worldstate" ? d.iId : d.wsId); })
		    .attr("y", function(d) { return y(d.y1); })
		    .attr("height", function(d) { return y(d.y0) - y(d.y1) + 1; })
		    .style("fill", function(d) { return d.color ? d.color : color(scope.groupBy === "worldstate" ? d.iId : d.wsId); })
		    .style("stroke-width", 2)
		    .style("stroke", function(d) { return color(scope.groupBy === "worldstate" ? d.iId : d.wsId); })
		    .on("mouseover", function(d) {      
			div.transition()        
			    .duration(200)      
			    .style("opacity", .9);      
			div.html(d.tip)  
			    .style("left", (d3.event.pageX) + "px")     
			    .style("top", (d3.event.pageY - 28) + "px");    
		    })                  
		    .on("mouseout", function(d) {       
			div.transition()        
			    .duration(500)      
			    .style("opacity", 0);   
		    });


		legend = svg.selectAll(".legend")
		    .data((scope.groupBy === "worldstate" ? data_inds : data_wss).slice().reverse())
		    .enter().append("g")
		    .attr("class", "legend")
		    .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

		legend.append("rect")
		    .attr("x", width - 18)
		    .attr("width", 18)
		    .attr("height", 18)
		    .style("fill", color);

		legend.append("text")
		    .attr("x", width - 24)
		    .attr("y", 9)
		    .attr("dy", ".35em")
		    .style("text-anchor", "end")
		    .text(function(d) { return d; });

	    };

	    function rearrange () {

		legend.remove();


		color.domain (scope.groupBy === "worldstate" ? data_inds : data_wss);
		x0.domain    (scope.groupBy === "worldstate" ? data_wss : data_inds);
		x1.domain    (scope.groupBy === "worldstate" ? data_inds : data_wss)
		    .rangeRoundBands([0, x0.rangeBand()]);

		groups 
		    .transition()        
		    .duration(500)
		    .attr("transform", function(d) { 
			return "translate(" + x0(scope.groupBy === "worldstate" ? d.worldstate : d.id) + ",0)"; });

		bars 
		    .transition()        
		    .duration(500)
		    .attr("width", x1.rangeBand())
		    .attr("x", function(d) { return x1(scope.groupBy === "worldstate" ? d.iId : d.wsId); })
		    .style("fill", function(d) { return d.color ? d.color : color(scope.groupBy === "worldstate" ? d.iId : d.wsId); })
		    .style("stroke", function(d) { return color(scope.groupBy === "worldstate" ? d.iId : d.wsId); })

		xAxisSvg
		    .call(xAxis);

		legend = svg.selectAll(".legend")
		    .data((scope.groupBy === "worldstate" ? data_inds : data_wss).slice().reverse())
		    .enter().append("g")
		    .attr("class", "legend")
		    .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

		legend.append("rect")
		    .attr("x", width - 18)
		    .attr("width", 18)
		    .attr("height", 18)
		    .style("fill", color);

		legend.append("text")
		    .attr("x", width - 24)
		    .attr("y", 9)
		    .attr("dy", ".35em")
		    .style("text-anchor", "end")
		    .text(function(d) { return d; });

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
		console.log ('buildDataset: wss =  ' + JSON.stringify (wss));
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
			    if (["number", 'histogram'].indexOf (scope.allIndicators[wss[w]][i].type) != -1) {
				inds[scope.allIndicators[wss[w]][i].id] = 1;
			    }
			}
		    }
		}
		inds = d3.keys (inds);
		console.log ('buildDataset: inds = ' + JSON.stringify (inds));
		if (inds.length == 0) {
		    return;
		}

		/*
		  create:
		  data = [
		  { 
		    id: "deathsIndicator",
		    worldstate : "81",
		    type: "number",
		    bars : [
		     {
		      id: "deathsIndicator", // same as ../id
		      name: "value",  // constant
		      y0: 0,
		      y1: 42.5,  // y0 + ../data
		      tip: "some text" // ../description, ../worldstate, ../data
		      iId : ../id
		      wsId : ../id
                      }
		    ],
		    max : 42.5
		  },
		  {
		    "id":"lifeIndicator",
		    "worldstate" : 81,
		    "type":"histogram",
		    "name":"health status summary"
		    bars : [
		     {
		      id: "dead"   // ../data[0].key
		      name: "life status below 10" // ../data[0].desc
		      y0 : 0 // y1 of the previous value
		      y1 : y0 + data[0].value
		      tip: data[0].desc
		      iId : ../id
		      wsId : ../id
		      color : ../data[0].color // optional
                     }
                    ]
		    max : y1 // of last the bars
		  }
		 */

		for (var w = 0; w < wss.length; w++) {
		    for (var i = 0; i < scope.allIndicators[wss[w]].length; i++) {
			// filter by indicators found above
			var indi = scope.allIndicators[wss[w]][i];
			if (inds.indexOf (indi.id) != -1) {
			    // filter by indicator type - keep only what I know to visualize
			    if (["number", "histogram"].indexOf (indi.type) != -1) {
				indi.worldstate = wss[w];
				bars = [];
				if ("number" === indi.type) {
				    bars[0] = {
					y0 : 0,
					y1 : indi.data,
					tip : "WorldState: " + indi.worldstate
					    + ", Indicator: " + indi.description
					    + "<br>Value: " + indi.data,
					iId : indi.id,
					wsId : indi.worldstate
				    };
				    indi.max = bars[0].y1;
				} else if ("histogram" === indi.type) {
				    y0 = 0;
				    for (var d = 0; d < indi.data.length; d++) {
					bars[d] = {
					    y0 : y0,
					    y1 : y0 += indi.data[d].value,
					    tip : "WorldState: " + indi.worldstate
						+ ", Indicator: " + indi.description
						+ "<br>" + indi.data[i].desc + ": " + indi.data[i].value,
					    iId : indi.id,
					    wsId : indi.worldstate,
					    color : indi.data[d].color
					};
				    }
				    indi.max = y0;
				}
				indi.bars = bars;
				indicators.push (indi);
			    }
			}
		    }
		}
		data = indicators;
		data_wss = wss;
		data_inds = inds;
		console.log ('buildDataset: data = ' + JSON.stringify (data));
	    };

        }
    };
    return directiveDefinitionObject;
});
