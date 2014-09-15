
Potential Usage examples:

Requirements
---
User Can specify Units, if none specifed, return default units.A (done)
If invalid units specified return error.
We need a list of default units and precision.
Multiple timeseries can be requested by name
Multiple sites can be requested 
Multiple data types (Parameters)
One interval at a time (e.g. one start date and end date per query) (Done)
Start time or back  (ISO 8601 Period P2Y1M14d2h5m3s) Literal time has precedence if both are specified
End Time or forward (ISO 8601 Period -2WY2Y2M4d2h5m3s) Literal Time has precedence if both are specified
preferred method is to use HTTP GET, however post can be used

Timeseries Query
--
{
  "timeseries" : [["tsid1","units1","interval1"], ["tsid2","units2","interval2"], ["tsid3","units3","interval3"]],
  "startdt":"ISO-8601",
  "enddt":"ISO-8601",
  "forward":"ISO-8601", //referenced from startdt, or datetime.now() if nothing specified
  "back": "ISO-8601", //referenced from enddt, or datetime.now() if nothing specified
  "query" : {"Stations":["BON","12340000","BIGI"], "Parameters":["Flow","03065","QD"]}
}

getjson?timeseries=[["CHJ Q","cfs","Daily"], ["CHJ.Flow.Inst.1Day.0.CBT-REV","kcfs"], ["12437990 00060","cfs"]]

General Abstract Query
--
General abstract queries allow the end user to provide keywords. The service will return hydroJSON timeseries objects with the data they want.

getjson?query=["CHJ Daily Avg Flow"]

Catalog Query
--
getjson?catalog=["CHJ Daily Avg Flow"]

Most Recent Value Query
--
getjson?mostrecent=[["12437990",  "cfs"]]

units and interval are optional parameters
TODO: Include specification for default units, DECODES spec will be used as an inital cut (Ktarbet)

Reference Implementation
---
DB -> ETL -> (SQLITE) -> Reference implementation (USACE/USBR)
