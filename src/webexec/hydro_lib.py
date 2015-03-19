#!/usr/local/bin/python
#hydro_lib hydroJSON webservice library
#22 Aug 2014
#Please annotate changes in changelog.md

import sys,os,time,datetime,json,atexit,sqlite3, hashlib
from copy import deepcopy

dbpath = "../data/hydro.db"

#---------------------------------------------------------------
#Schema Definition in SQLITE3 database
#---------------------------------------------------------------

defaultUnits =   {
    "%": "%",
    "airtemp": "F",
    "area": "ft2",
    "area-basin": "mi2",
    "area-impacted": "acre",
    "area-reservoir": "acre",
    "area-surface": "acre",
    "ati-cold": "degF-day",
    "ati-melt": "degF-day",
    "code": "n/a",
    "coeff": "n/a",
    "cold content": "in",
    "conc": "ppm",
    "conc-salinity": "g/l",
    "cond": "umho/cm",
    "count": "unit",
    "currency": "$",
    "density": "lbs/ft3",
    "depth": "ft",
    "depth-swe": "in",
    "dir": "deg",
    "dist": "mi",
    "elev": "ft",
    "energy": "MWh",
    "evap": "in",
    "evaprate": "in/day",
    "fish": "unit",
    "flow": "kcfs",
    "frost": "in",
    "growthrate": "in/day",
    "head": "ft",
    "interception": "in",
    "irrad": "langley/min",
    "liquid water": "in",
    "lwass": "in",
    "opening": "ft",
    "ph": "su",
    "power": "MW",
    "precip": "in",
    "pres": "mm-hg",
    "rad": "langley",
    "ratio": "n/a",
    "speed": "mph",
    "spinrate": "rpm",
    "stage": "ft",
    "stor": "kaf",
    "swe": "in",
    "temp": "F",
    "thick": "in",
    "timing": "sec",
    "travel": "mi",
    "turb": "jtu",
    "turbf": "fnu",
    "turbj": "jtu",
    "turbn": "ntu",
    "volt": "volt",
    "volume": "kaf"
} 


#---------------------------------------------------------------
#Schema Definition in SQLITE3 database
#---------------------------------------------------------------

#Schema definition in sqlite3 database
schemas =  {"seriescatalog": ["parentid", "isfolder", "sortorder", "iconname", "name", "siteid", "units", "timeinterval", "parameter", "tablename", "provider", "connectionstring", "expression", "notes", "enabled"],
 "seriesproperties": ["id","seriesid","name", "value"],
 "sitecatalog":["siteid",  "description", "state",  "latitude", "longitude", "elevation", "timezone", "install", "horizontal_datum", "vertical_datum", "vertical_accuracy", "elevation_method", "active_flag", "responsibility"]
}

#---------------------------------------------------------------
#Site metadata 
#---------------------------------------------------------------
site_template =  {
  "name": "",
  "responsibility": "",
  "coordinates": {
    "latitude": 0.0,
    "longitude": 0.0,
    "datum": ""
  },
  "HUC": "",
  "elevation": {
    "value": 0.0,
    "accuracy": 0.0,
    "datum": "string",
    "method": "string (full explanation)"
  },
  "timezone": "US/Pacific",
  "tz_offset": "-08:00", 
  "time_format": "%Y-%m-%dT%H:%M:%S%z",
  "active_flag": "T",
  "location_type": "",
  "timeseries": {}
}

def new_site(s, time_format = "%Y-%m-%dT%H:%M:%S%z"):
  '''This method fills out a site template
     input: rec object mapped to the sitecatalog table in the sqlite3 database
            time_format = strftime for ISO 8601
     output: nested dictionary
  '''
  def conv (s):
    try:
      return float(s)
    except:
      return 0.0
  output = deepcopy(site_template)
  output ["name"] = s["description"]
  output ["responsibility"] = s["responsibility"]
  output ["coordinates"]["latitude"] = conv(s["latitude"])
  output ["coordinates"]["longitude"] = conv(s["longitude"])
  output ["coordinates"]["datum"] =  s["horizontal_datum"]
  output ["elevation"]["value"] = conv(s["elevation"])
  output ["elevation"]["accuracy"] = conv(s["vertical_accuracy"])
  output ["elevation"]["datum"] = s["vertical_datum"]
  output ["elevation"]["method"] = s["elevation_method"]
  output ["timezone"] = s["timezone"]
  output ["tz_offset"] = s["tz_offset"]
  output ["time_format"] = time_format
  output ["active_flag"] = s["active_flag"]
  output ["location_type"] = s["type"]
  return output 
    

#--------------------------------------------------------------
#Template for timeseries data and metadata
#---------------------------------------------------------------

timeseries_template = {
  "values": [],
  "site_quality": [],
  "hash": "string md5", #hash of the timeseries, optional
  "quality_type": "string",
  "parameter": "",
  "duration": "", #interval over which the duration applies
  "interval": "", #nominal frequency
  "units": "",
  "count": 0, #count of values in the timeseries
  "min_value": 0.0, #a timeslice e.g. [timestamp,value]
  "max_value": 0.0, #a timeslice e.g. [timestamp,value]
  "start_timestamp": "",
  "end_timestamp":"" 
}

def new_timeseries(s, ts, conf = {}, dFamily = None ):
  '''This method fills out a site template
     input: s - rec object mapped to the seriescatalog table in the sqlite3 database
            ts - timeSeries Object   
            time_format = strftime for ISO 8601
     output: nested dictionary
  '''
  def conv (s):
    try:
      return float(s)
    except:
      return 0.0
  output = deepcopy(timeseries_template)
  time_format = "%Y-%m-%dT%H:%M:%S%z"
  if "time_format" in conf:
    time_format = conf["time_format"]
  if "tz_offset" in conf:
    if conf["tz_offset"] != 0: ts = ts.timeshift(datetime.timedelta(hours=conf["tz_offset"]))
  _max = ts.data[0][1]
  _min = ts.data[0][1] 
  for slice in ts.data:
    output ["values"].append([slice[0].strftime(time_format),slice[1],slice[2]])
    if slice[1] > _max: _max = slice[1]
    if slice[1] < _min: _min = slice[1]
  output ["site_quality"] = []
  output ["sigfig"] = 3
  output ["hash"] = "TODO"
  output ["quality_type"] = "string"
  output ["parameter"] = s["parameter"]
  output ["active_flag"] = s["enabled"]
  output ["duration"] = s["duration"]
  output ["interval"] = s["interval"]
  output ["units"] = s["units"]
  output ["count"] = len (ts.data)
  output ["min_value"] = _min
  output ["max_value"] = _max
  output ["start_timestamp"] = output["values"][0][0]
  output ["end_timestamp"] = output["values"][-1][0]
  return output 


#--------------------------------------------------------------
#Timeseries storage
#---------------------------------------------------------------
def readTS (tsid, start_time =None, end_time=None):
  """Reads a time series from the database
     tsid - string
     start_time - datetime
     end_time - datetime
  """
  global status
  cur = dbconn.cursor()
  ts = timeSeries()
  sqltxt = "SELECT * FROM "+tsid
  if start_time != None and end_time != None:
    start = time.mktime(start_time.timetuple())
    end = time.mktime(end_time.timetuple())
    sqltxt += " WHERE DateTime >= "+str(start)+" AND DateTime <= "+str(end)
  try:
    cur.execute (sqltxt)
    rows = cur.fetchall()
    for d in rows:
      row = [datetime.datetime.fromtimestamp(d[0])]
      row.append(d[1])
      #row.append(d[2])
      row.append(0)
      ts.data.append(row)
  except Exception,e:
      status = "\nCould not read %s\n" % tsid
      status += "\n%s"+str(e)
  cur.close()
  return ts

def writeTS (tsid,ts, replace_table = False):
  """Writes a time series from the database
     tsid - string
     replace_table - overwrites table (
  """

  try:
    cur = dbconn.cursor()
    if replace_table == True:
      try:
        cur.execute ("DROP TABLE "+tsid)
      except:
        pass
    cur.execute ("CREATE TABLE IF NOT EXISTS "+tsid+"(DateTime INTEGER PRIMARY KEY, value FLOAT)")#, flag INTEGER)")
    for line in ts.data:
      sqltxt = "INSERT OR REPLACE INTO "+tsid+" VALUES(%d,%f)" % (int(time.mktime(line[0].timetuple())),line[1])#,int(line[2]))
      cur.execute(sqltxt)
    dbconn.commit()
  except Exception, e:
    status = "\nCould not store "+tsid
    status += "\n%s" % str(e)
    print status
  cur.close()

def makeTablename (_tsid):
  """Makes a tablename from supplied pathname"
  """
  return"TS_"+hashlib.sha1(_tsid).hexdigest().upper()



#---------------------------------------------------------------
#Generic database record object that can map to any table.
# Basically a dependency free ORM.
#---------------------------------------------------------------

class rec:
  def __init__ (self, d, table = "", keys = []):
    self.keys = keys
    self.data =  {}
    self.table = table
    for k in self.keys: # initialize data
      self.data[k] = ""
    if type (d) == dict:
      for k in self.keys:
        if k in d: self.data[k] = d[k]
    elif type (d) == list or type (d) == tuple:
      i = 0
      while i < len(d) and i < len (self.keys):
        self.data[self.keys[i]] = d[i]
        i+= 1

  def __getitem__ (self,key):
    return self.data.get(key, " ")

  def __setitem__ (self,key,value):
    self.data[key] = value

  def tableColumns(self): #makes table columns
    return ", ".join(self.keys)

  def placeHolders (self):
    return "("+", ".join("?"*len(self.keys))+")"

  def get (self,cursor,key, value): #get one from the DB where key matches value
    q = (value,)
    cursor.execute("select "+self.tableColumns()+" from "+self.table+" where "+key+" = ?",q)
    rows = cursor.fetchone()
    return rec(rows, table = self.table, keys = self.keys )

  def get_many (self, cursor, key, value):
    q = (value,)
    cursor.execute("select "+self.tableColumns()+" from "+self.table+" where "+key+" like ?",q)
    rows = cursor.fetchall()
    output = {}
    for line in rows:
      t = rec(line, table = self.table, keys = self.keys )
      output [t[key]] = t
    return output

  def search (self,cursor,key, value): #
    '''returns a dict of objects from the DB where key is like value, Empty dict if not found'''
    cursor.execute("select "+self.tableColumns()+" from "+self.table+" where "+key+" like ?",(value,))
    rows = cursor.fetchall()
    output = {}
    for row in rows:
      output[row[self.keys.index(key)]] = rec(row, table = self.table, keys = self.keys)
    return output

  def toList (self):
    output = []
    for k in self.keys: output.append(self.data[k])
    return output

  def toJSON (self):
    return json.dumps(self.data)

  def store (self, cursor): #writes self to DB
    cursor.execute ("insert or replace into "+self.table+" ("+self.tableColumns()+") values "+self.placeHolders(),self.toList())

  def delete (self, cursor, key,value):
    q = (value,)
    cursor.execute("delete from "+self.table+" where "+key+" = ?",q)

##Timeseries Object
class timeSeries:
  #"overloaded" timeSeries constructor
  def __init__ (self, data = None):
    self.status = "OK"
    #Data is an array of arrays with the following structure [datetime,float value, float quality]
    self.data = []
    if data != None:
      #set internal data memebr to data and filter out blanks
      for line in data:
        if line != []:
          if line[1] != None:
            self.data.append(line)

  #Equivalent to toString()
  def __str__ (self):
    output = ""
    for line in self.data:
      try:
        output += "%s\t%.2f\t%.2f\n" % (line[0].strftime("%d-%b-%Y %H%M"),line[1],line[2])
      except:
        output += "%s\t\t\n" % line[0].strftime("%d-%b-%Y %H%M")
    return output

  #gets status message of object and resets it to "OK"
  def getStatus(self):
    s = self.status
    self.status = "OK"
    return s

  #returns a valuea at a given timestamp
  #returns None type if not found
  def findValue(self,timestamp):
    for line in self.data:
      if line[0] == timestamp:
        return line [1]
    return None

  #interpolate values
  def interpolateValue(self, x0, y0, x1, y1, x):
    m = (y1 - y0) / (x1 - x0)
    output = y0 + (x - x0) * m
    return output

  #interpolates timeseries based on a given interval of type timedelta
  #returns a timeseries object
  def interpolate(self,interval):
    _data = []
    try:
      for i in xrange(0,len(self.data)-1):
        startTime = self.data[i][0]
        deltaT = (self.data[i+1][0] - startTime)
        steps = int(deltaT.total_seconds()/interval.total_seconds())
        quality = self.data[i][2]
        for j in xrange(0,steps):
          value = self.interpolateValue(0,self.data[i][1],deltaT.total_seconds(),self.data[i+1][1],j*interval
.total_seconds())
          _data.append([startTime+(interval*j),value,quality])
    except Exception,e:
      self.status = str(e)
    return timeSeries(_data)
  #averages timeseries based on a given interval of type timedelta
  #returns a timeseries object
  def average(self,interval):
    _data = []
    if self.data == []:
      return timeSeries()
    try:
      i = 0
      count = len(self.data)
      endTime = self.data[i][0]
      while i < count:
        startTime = endTime
        endTime = startTime + interval
        quality = self.data[i][2]
        n = 0
        sum = 0
        while self.data[i][0] < endTime:
          sum += self.data[i][1]
          n += 1
          i += 1
          if i >= count:
            break
        if n != 0:
          _data.append([endTime,sum/n,quality])
    except Exception,e:
      self.status = str(e)
    return timeSeries(_data)

  #averages timeseries based on a given interval of type timedelta
  #returns a timeseries object
  def rollingaverage(self,interval):
    _data = []
    if self.data == []:
      return timeSeries()
    try:
      i = 0
      count = len(self.data)
      while i < count:
        startTime = self.data[i][0]
        endTime = startTime + interval
        if endTime > self.data[-1][0]:
          break
        quality = self.data[i][2]
        n = 0
        sum = 0
        while self.data[i+n][0] <= endTime:
          sum += self.data[i+n][1]
          n += 1
          if i+n >= count:
            break
        if n != 0:
          _data.append([endTime,sum/n,quality])
        i+=1
    except Exception,e:
      self.status = str(e)
    return timeSeries(_data)

  #numerator : self
  #denominator : denom
  #returns a timeseries object of percentages
  def percent(self,denom):
    _data = []
    denom_data = {}
    try:
      #turn denominator data into a dictionary and filter out zeros (no division by 0 allowed!)
      for line in denom.data:
        if line[1] != 0:
          denom_data[line[0]] = line
      for line in self.data:
        key = line[0]
        if key in denom_data:
          _data.append([line[0],100*float(line[1]/denom_data[key][1]),line[2]])
    except Exception,e:
      self.status = str(e)
      return timeSeries()
    return timeSeries(_data)

  #Shifts each timestamp a given time interval
  #tdelta: timedelta to shift
  #returns a timeseries object
  def timeshift(self,tdelta):
    _data = []
    if self.data == []:
      return timeSeries()
    try:
      for line in self.data:
        _data.append([line[0]+tdelta,line[1],line[2]])
    except Exception,e:
      self.status = str(e)
      print e
      return timeSeries()
    return timeSeries(_data)

  #Snaps a timeseries
  #interval: interval at which time series is snapped
  #buffer : lookahead and lookback
  #returns a snapped timeseries
  def snap(self,interval,buffer,starttime = None):
    _data = []
    if self.data == []:
      return timeSeries()
    try:
      if buffer > interval/2:
        buffer = interval/2
      #setup the initial start time
      endtime = self.data[-1][0]+buffer
      if starttime != None:
        t = starttime
      else:
        t = self.data[0][0]
      while t <= endtime:
        tlist = []
        for line in self.data:
          if line[0] >= t - buffer:
            if line[0] <= t+ buffer:
              tlist.append(line)
            else:
              break
        if len(tlist) > 0:
          tline = tlist[0]
          for line in tlist:
            curdiff = abs(tline[0] - t).seconds
            newdiff = abs(line[0] - t).seconds
            if (curdiff > newdiff):
              tline = line
          _data.append([t,tline[1],tline[2]])
        t += interval
    except Exception,e:
      self.status = str(e)
      return timeSeries()
    return timeSeries(_data)

  #Performs an operation on self
  #op: lambda function to perform eg lambda x,y: x+y
  #operand: could be a timeseries or a float
  #returns a timeseries object
  def operation(self,op,operand):
    _data = []
    if self.data == []:
      return timeSeries()
    try:
      if type (operand) is float:
        for line in self.data:
          _data.append([line[0],op(line[1],operand),line[2]])
      else:
        for line in self.data:
          val = operand.findValue(line[0])
          if val != None:
            _data.append([line[0],op(line[1],val),line[2]])
    except Exception,e:
      self.status = str(e)
      print e
      return timeSeries()
    return timeSeries(_data)

  #This takes a relative time and turns it into a timedelta
  #eg input 7d6h9m
  def parseTimedelta (self, input):
    input = input.lower()
    sign = 1
    output = datetime.timedelta(seconds = 0)
    t = ""
    try:
      for c in input:
        if c == "-":
          sign *= -1
        elif c =="y":
          output += datetime.timedelta(days=float(t)*365)
          t = ""
        elif c =="w":
          output += datetime.timedelta(days=(float(t)*7))
          t = ""
        elif c =="d":
          output += datetime.timedelta(days=float(t))
          days = 0
          t = ""
        elif c =="h":
          output += datetime.timedelta(hours=float(t))
          t = ""
        elif c =="m":
          output += datetime.timedelta(minutes=float(t))
          t = ""
        else:
          if c != " ":
            t += c
    except:
      self.status = "Could not parse"+input+" into a time interval"
    return output*sign

  def globalAverage (self):
    '''averages entire timeseries returns a timeslice'''
    if len (self.data) != 0:
      interval = self.data[-1][0] - self.data[0][0]
      return self.average(interval).data[0]
    return None

  def globalMax (self):
    '''finds the max of a timeseries returns a timeslice'''
    if len (self.data) != 0:
      interval = self.data[-1][0] - self.data[0][0]
      return self.maxmin(interval, lambda x,y: x > y).data[0]
    return None

  def globalMin (self):
    '''averages minimum of a timeseries returns a timeslice'''
    if len (self.data) != 0:
      interval = self.data[-1][0] - self.data[0][0]
      return self.maxmin(interval, lambda x,y: x < y).data[0]
    return None

  def maxmin(self,interval,cmp):
    '''returns a max or a min based for a given interval of type datetime
       returns a timeseries object
    '''
    _data = []
    if self.data == []:
      return timeseries()
    try:
      i = 0
      count = len(self.data)
      endTime = self.data[i][0]
      while i < count:
        startTime = endTime
        endTime = startTime + interval
        quality = self.data[i][2]
        n = 0
        probe = self.data[i][1]
        while self.data[i][0] < endTime:
          if cmp (self.data[i][1],probe):
            probe = self.data[i][1]
          i += 1
          if i >= count:
            break
        _data.append([endTime,probe,quality])
    except Exception,e:
      self.status = str(e)
    return timeseries(_data)

def connect(dbpath):
  global dbconn
  global cur
  try :
    dbconn = sqlite3.connect(dbpath)
    cur = dbconn.cursor()
    if not dbconn :
      status = "\nCould not connect to %s\n" % dbpath
      status += "\n%s"
  except Exception,e:
    status = "\nCould not connect to %s\n" % dbpath
    status += "\n%s"+str(e)
  
#---setup database connection
dbconn = None
cur = None
status = "OK"
connect(dbpath)

