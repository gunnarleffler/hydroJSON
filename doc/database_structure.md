---
## Database Structure
#### SiteCatalog
Name | Type | Description
:----|:----|:----
siteid | string |	identifier for the site example: LakeMead
description| string |	description for this site location
state | string |	state code i.e. ID = Idaho
latitude | string |	latitude of site
longitude | string |	longitude of site
elevation | string |	elevation of the site (in units of vertical datum description)
timezone | string |	full name example: US/Pacific
install | string |	date site was installed
horizontal_datum | string |	datum description for lat/long. Example: (WGS84)
vertical_datum | string |	description of vertical datum for the site. example(NGVD29)
vertical | float | accuracy	accuracy of elevation
elevation_method | string |	method used to determine elevation
tz_offset | string |	optional hours -08:00
active_flag | string |	site is currently being used T/F default T if blank
responsibility | string |	maintenance responsibility
agency_region | string |	grouping by organization regions
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

---
