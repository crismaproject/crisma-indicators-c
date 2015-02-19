#!/usr/bin/env python
#
# Peter.Kutschera@ait.ac.at, 2014-03-13
# Time-stamp: "2015-02-19 13:58:45 peter"
#
# test ICMMtools

import ICMMtools

if __name__ == "__main__":

    for c in ["worldstates", "transitions", "dataitems"]:
        print "{0}: {1}".format (c, ICMMtools.getId (c)) 

    parsedICMMUrl = ICMMtools.ICMMAccess ('https://crisma.cismet.de/pilotC/icmm_api/CRISMA.worldstates/1')
    print parsedICMMUrl

    parsedICMMUrl = ICMMtools.ICMMAccess ('http://crisma.cismet.de/icmm_api/CRISMA.worldstates/1?level=4&omitNullValues=true&deduplicate=false')
    print parsedICMMUrl

    if (parsedICMMUrl is not None):
        for c in ["worldstates", "transitions", "dataitems"]:
            print "{0}: {1}".format (c, ICMMtools.getId (c, baseUrl=parsedICMMUrl.endpoint))
