CRISMA Indicators for Pilot C

This container offers an WPS endpoint to calculate indicator values as needed for Pilot C

There is also an web page to get information and use the WPS at /

The container also offers to register at a crisma-orion content broker (see crisma-orion container).


Usage: 
1. Start an orion context broker
   docker run -P -d --name e_orion peterkutschera/crisma-orion
2. Start the indicator WPS
   docker run -P -d --name e1_indicators --link e_orion:orion peterkutschera/crisma-indicator_e1

