hydroJSON
=========

## Synopsis
A JSON based standard for interchanging hydro, meteorological and environmental data. The main goal of this standard is to have a common way of interchanging  and using HydroMet data via web services. Given the ease with importing JSON formatted objects programmatically, this standard has use cases in modeling as well.

## Examples

#### Retrieve 7 days of flow from a dam

[/getjson?query=\["dwr flow"\]&backward=7d&time\_format=%s](http://www.nwd-wc.usace.army.mil/dd/common/web\_service/webexec/getjson?query=%5B%22dwr%20flow%22%5D%26backward%3D7d "Get last 7 Days of data")

#### Format time to be seconds past the epoch for use in client side plotting

[/getjson?query=\["dwr flow"\]&backward=7d&time\_format=%s](http://www.nwd-wc.usace.army.mil/dd/common/web\_service/webexec/getjson?query=%5B%22dwr%20flow%22%5D%26backward%3D7d%26time_format%3D%25s "Get last 7 Days of data")

#### List all available timeseries names for a given site:

[/getjson?tscatalog=\["GCL"\]](http://www.nwd-wc.usace.army.mil/dd/common/web_service/webexec/getjson?tscatalog=%5B%22GCL%22%5D "Catalog for all GCL timeseries")

#### All available sites/Stations with metadata:

[/getjson?catalog=\[\]](http://www.nwd-wc.usace.army.mil/dd/common/web_service/webexec/getjson?catalog=[] "All sites in catalog")


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

---
## Database Structure
#### SiteCatalog
Name | Type | Description
:----|:----|:----
siteid | string | identifier for the site example: LakeMead
description| string | description for this site location
state | string |  state code i.e. ID = Idaho
latitude | string | latitude of site
longitude | string |  longitude of site
elevation | string |  elevation of the site (in units of vertical datum description)
timezone | string | full name example: US/Pacific
install | string |  date site was installed
horizontal_datum | string | datum description for lat/long. Example: (WGS84)
vertical_datum | string | description of vertical datum for the site. example(NGVD29)
vertical | float | accuracy accuracy of elevation
elevation_method | string | method used to determine elevation
tz_offset | string |  optional hours -08:00
active_flag | string |  site is currently being used T/F default T if blank
responsibility | string | maintenance responsibility
agency_region | string |  grouping by organization regions
type | string | EX: agrimet, stream, reservoir, weather, canal, diversion, snotel

#### SeriesCatalog
|Name|Type|Description
|:----|:----|:----
|id|integer|Primary key|
|parentid|integer|SiteDataTypeID of containing folder|
|isfolder|integer|When true this row represents a folder not a series|
|sortorder|integer|Sort order within a folder for user interface|
|iconname|string|Use to render an icon based on the source of data|
|name|string|Display Name and name for equations referencing this Series/row|
|siteid|string|Reference to site/location information|
|units|string|Units of measurement such as: feet,cfs, or acre-feet|
|timeinterval|string|One of : (Instant, Daily, Monthly)|
|parameter|string|Description for data such as: daily average flow|
|tablename|string|Unique database table name for this Series/row|
|provider|string|Name of a class derived from Reclamation.TimeSeries.Series (or Series)|
|connectionstring|string|Provider specific connection information such as a path to an excel file, sheet name, or specific parameter code|
|expression|string|Equation expression for computed series|
|notes|string|User notes|
|enabled|integer|Used to active or deactive calculations and presentation of data|

#### TableName
*Refers to the TableName column in SeriesCatalog*

Name | Type
:----|:----
datetime | datetime
value | float
flag | string

[Database Description](doc/DBSCHEMA.md)

--

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
