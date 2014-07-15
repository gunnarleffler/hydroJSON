
Potential Usage examples:

Requirements
---
User Can specify Units, if none specifed, return default units.A (done)
If invalid units specified return error.
We need a list of default units and precision.
Multiple timeseries can be requested by name
Multiple sites can be requested
Multiple data types (Parameters)
One intervals at a time (Done)
Start time or back  (8WY2Y1M14d2h5m3s) Literal time has precedence if both are specified
End Time or forward (-2WY2Y2M4d2h5m3s) Literal Time has precedence if both are specified
preferred method is to use HTTP GET, however post can be used

Request Specification
---
{
  "timeseries" : [["tsid1","units1","interval1"], ["tsid2","units2","interval2"], ["tsid3","units3","interval3"]],

}

Discussion of Timeseries, units, interval 
---
getjson?timeseries=[["CHJ Q","cfs","Daily"], ["CHJ.Flow.Inst.1Day.0.CBT-REV","kcfs"], ["12437990 00060","cfs"]]
units and interval are optional parameters
TODO: Define interval and duration
TODO: Include specification for default units, DECODES spec will be used as an inital cut (Ktarbet)

USBR Strawman
---
GET /hydro/sites?interval=daily    # just get site meta-data for all sites with 'daily' data
GET /hydro/series/daily?sites=boii,bigi,13206000&t1=2014-07-1&t2=2014-07-02     # two days of data
GET /hydro/series/daily/13206000

Default Units
---
   initial cut from decodes:

