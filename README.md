hydroJSON
=========

## Synopsis
A JSON based standard for interchanging hydro, meteorological and environmental data. The main goal of this standard is to have a common way of interchanging  and using HydroMet data via web services. Given the ease with importing JSON formatted objects programmatically, this standard has use cases in modeling as well.

## Examples

#### Retrieve 7 days of flow from a dam

[/getjson?query=\["dwr flow"\]&backward=7d](http://www.nwd-wc.usace.army.mil/dd/common/web\_service/webexec/getjson?query=["dwr flow"]&backward=7d)

#### Format time to be seconds past the epoch for use in client side plotting

[/getjson?query=\["dwr flow"\]&backward=7d&time\_format=%s](http://www.nwd-wc.usace.army.mil/dd/common/web\_service/webexec/getjson?query=["dwr flow"]&backward=7d&time\_format=%s )


#### List all available timeseries names for a given site:

[/getjson?tscatalog=\["GCL"\]](http://www.nwd-wc.usace.army.mil/dd/common/web\_service/webexec/getjson?tscatalog=["GCL"])

#### All available sites/Stations with metadata:

[/getjson?catalog=\[\]](http://www.nwd-wc.usace.army.mil/dd/common/web\_service/webexec/getjson?catalog=[])


## Motivation

the purpose of hydroJSON is to standardize the interchange of timeseries data and metadata in a more modern, browser/mobile friendly format.

## Installation


## API Reference

#### Timeseries Query

    {
      "timeseries" : [["tsid1","units1","interval1"], ["tsid2","units2","interval2"], ["tsid3","units3","interval3"]],
      "startdt":"ISO-8601",
      "enddt":"ISO-8601",
      "forward":"ISO-8601", //referenced from startdt, or datetime.now() if nothing specified
      "back": "ISO-8601", //referenced from enddt, or datetime.now() if nothing specified
      "query" : {"Stations":["BON","12340000","BIGI"], "Parameters":["Flow","03065","QD"]}
    }
    
    getjson?timeseries=[["CHJ Q","cfs","Daily"], ["CHJ.Flow.Inst.1Day.0.CBT-REV","kcfs"], ["12437990 00060","cfs"]]

#### General Abstract Query

General abstract queries allow the end user to provide keywords. The service will return hydroJSON timeseries objects with the data they want.

`getjson?query=["CHJ Daily Avg Flow"]`

#### Catalog Query

`getjson?catalog=["CHJ Daily Avg Flow"]`

#### Most Recent Value Query

`getjson?mostrecent=[["12437990",  "cfs"]]`

[Database Description](doc/database_structure.md)


## Tests

TBD

## Contributors
* Gunnar Leffler
* Karl Tarbet
* Art Armour
* Mike Stanfill
* Mike Nielson
* Jeremy Kellett
* Dave Coyle
