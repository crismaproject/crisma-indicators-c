/*
 Peter.Kutschera@ait.ac.at, 2013-10-25
 Time-stamp: "2014-02-26 14:09:48 peter"

 See http://blog.pixelingene.com/2011/07/building-a-tree-diagram-in-d3-js/

*/
/*

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
  
function createTreeData (wsid, list) {
    var treeData = getFromList (wsid, list);
    var branches = setBranchNumber (0, treeData);
    return treeData;
}

////////////////////////
/*
  get tree of WorldStates from list of all WorldStates
  Start with wsid
*/
function getFromList (wsid, list) {
    // console.log ("getFromList (" + wsid + ", list)");
    var tmp = { wsid : wsid, label: "id: " + wsid, children : [] };
    for (var i = 0; i < list.length; i++) {
	if (list[i]["worldStateId"] === wsid) {
	    if (list[i].description) {
		tmp.label = list[i].description;
	    }
	    tmp.time = list[i].dateTime; // "2012-01-01T12:34:56.789"
	    tmp.data = list[i];
	    break;
	}
    }
    //    console.log ("label = " + tmp.label);
    for (var i = 0; i < list.length; i++) {
	if (list[i]["worldStateParentId"] === wsid) {
	    tmp['children'].push (getFromList (list[i]["worldStateId"], list));
	}
    }
    return tmp;
}


function setBranchNumber (number, node) {
    node.branchNumber = number;
    for (var i = 0; i < node.children.length; i++) {
	number = setBranchNumber (number, node.children[i]);
	if (i + 1 < node.children.length) {
	    number++;
	}
    }
    return number;
}

