#!/usr/local/bin/python

import atexit, calendar, datetime, hashlib, json, os, sqlite3, sys, time, pytz
from copy import deepcopy

os.environ["TZ"] = "GMT"

defaultUnits = {}

###############################################################################
# SQLite3 database schema

schemas = {
    "seriescatalog": [
        "parentid", "isfolder", "sortorder", "iconname", "name", "siteid",
        "units", "timeinterval", "parameter", "tablename", "provider",
        "connectionstring", "expression", "notes", "enabled"
    ],
    "seriesproperties": ["id", "seriesid", "name", "value"],
    "sitecatalog": [
        "siteid", "description", "state", "latitude", "longitude", "elevation",
        "timezone", "install", "horizontal_datum", "vertical_datum",
        "vertical_accuracy", "elevation_method", "active_flag", "responsibility"
    ]
}

###############################################################################
# Fill out a site template
#    input: rec object mapped to the sitecatalog table in the sqlite3 database
#           time_format = strftime for ISO 8601
#   output: nested dictionary


def new_site(s, conf={}):

  def conv(s):
    try:
      return float(s)
    except:
      return 0.0

  output = {
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

  output["name"] = s["description"]
  output["responsibility"] = s["responsibility"]
  output["coordinates"]["latitude"] = conv(s["latitude"])
  output["coordinates"]["longitude"] = conv(s["longitude"])
  output["coordinates"]["datum"] = s["horizontal_datum"]
  output["elevation"]["value"] = conv(s["elevation"])
  output["elevation"]["accuracy"] = conv(s["vertical_accuracy"])
  output["elevation"]["datum"] = s["vertical_datum"]
  output["elevation"]["method"] = s["elevation_method"]
  output["timezone"] = s["timezone"]
  output["tz_offset"] = s["tz_offset"]
  output["time_format"] = conf["time_format"]
  output["active_flag"] = s["active_flag"]
  output["location_type"] = s["type"]

  if "timezone" in conf:
    output["timezone"] = conf["timezone"]
  if "tz_offset" in conf:
    output["tz_offset"] = conf["tz_offset"]

  return output


def strftime(dt, fmt, usemidnight=False):
  """
    local strftime which allows one to specify using midnight (2400)values
    """
  if dt.hour == 0 and dt.minute == 0 and usemidnight == True:
    dt2 = dt - datetime.timedelta(days=1)
    return dt2.strftime(fmt).replace("00:00", "24:00").replace("0000", "2400")
  else:
    return dt.strftime(fmt)


###############################################################################
# Fill out a site template
#   input:           s - rec object mapped to the seriescatalog table in sqlite3
#                   ts - timeSeries Object
#          time_format - strftime for ISO 8601
#  output: nested dictionary


def new_timeseries(s, ts, conf={}):
  if len(ts.data) == 0:
    return {}

  output = {
      "values": [],
      "site_quality": [],
      "notes": "",
      "quality_type": "string",
      "parameter": "",
      "duration": "",  # interval over which the duration applies
      "interval": "",  # nominal frequency
      "units": "",
      "count": 0,  # count of values in the timeseries
      "min_value": 0.0,  # a timeslice e.g. [timestamp,value]
      "max_value": 0.0,  # a timeslice e.g. [timestamp,value]
      "start_timestamp": "",
      "end_timestamp": ""
  }

  time_format = "%Y-%m-%dT%H:%M:%S%z"
  if "time_format" in conf:
    time_format = conf["time_format"]

  if "tz_offset" in conf:
    if conf["tz_offset"] != 0:
      ts = ts.timeshift(datetime.timedelta(hours=conf["tz_offset"]))

  output["site_quality"] = []
  output["sigfig"] = 3
  output["notes"] = s["notes"]
  output["quality_type"] = "int"
  output["parameter"] = s["parameter"]
  output["active_flag"] = s["enabled"]
  output["duration"] = s["duration"]
  output["interval"] = s["interval"]
  output["units"] = s["units"]
  output["count"] = len(ts.data)

  if len(ts.data) > 0:
    _max = ts.data[0][1]
    _min = ts.data[0][1]
    for slice in ts.data:
      output["values"].append([
          strftime(
              slice[0], time_format, usemidnight=conf.get("midnight", False)),
          slice[1], slice[2]
      ])
      if slice[1] > _max:
        _max = slice[1]
      if slice[1] < _min:
        _min = slice[1]
    output["min_value"] = _min
    output["max_value"] = _max
    output["start_timestamp"] = output["values"][0][0]
    output["end_timestamp"] = output["values"][-1][0]
  return output


###############################################################################


def readTS(tsid, start_time=None, end_time=None, units="default", timezone=None):
  global status
  cur = dbconn.cursor()
  ts = timeSeries()
  sqltxt = "SELECT * FROM " + tsid
  if start_time != None and end_time != None:
    start = time.mktime(start_time.timetuple())
    end = time.mktime(end_time.timetuple())
    sqltxt += " WHERE datetime >= %s AND datetime <= %s" % (start, end)
  try:
    cur.execute(sqltxt)
    rows = cur.fetchall()
    for d in rows:
      row = [datetime.datetime.fromtimestamp(d[0])]
      row.append(d[1])
      row.append(0)
      ts.data.append(row)
  except Exception, e:
    status = "\nCould not read %s\n" % tsid
    status += "\n%s" + str(e)
  cur.close()
  return ts


###############################################################################


def writeTS(tsid, ts, replace_table=False):
  output = []
  status = ""
  cur = dbconn.cursor()

  def execute(s):
    try:
      cur.execute(s)
      output.append(s + ";")
    except Exception, e:
      status = "\nCould not store " + tsid
      status += "\n%s" % str(e)

  if replace_table == True:
    execute("DROP TABLE " + tsid)
  execute("CREATE TABLE IF NOT EXISTS " + tsid +
          "(DateTime INTEGER PRIMARY KEY, value FLOAT)")
  for line in ts.data:
    sqltxt = "INSERT OR REPLACE INTO %s VALUES(%d,%f)" % (
        tsid, int(time.mktime(line[0].timetuple())), line[1])
    execute(sqltxt)
  dbconn.commit()
  cur.close()
  #if status != "":
  #  print status
  return ("\n".join(output))


###############################################################################
# Makes a table name from supplied pathname


def makeTablename(ts_id):
  return "TS_" + hashlib.sha1(ts_id).hexdigest().upper()[:10]


def max_datetime(ts_id):
  max = None
  sql = "SELECT MAX( datetime ) FROM %s" % (makeTablename(ts_id))
  cur = dbconn.cursor()
  try:
    if cur.execute(sql) is not None:
      (max,) = cur.fetchone()
  except sqlite3.Error as e:
    print e.args[0]

  if max is not None:
    max = datetime.datetime.fromtimestamp(max)
  return max


def min_datetime(ts_id):
  min = None
  sql = "SELECT MIN( datetime ) FROM %s" % (makeTablename(ts_id))
  cur = dbconn.cursor()
  try:
    if cur.execute(sql) is not None:
      (min,) = cur.fetchone()
  except sqlite3.Error as e:
    print e.args[0]

  if min is not None:
    min = datetime.datetime.fromtimestamp(min)
  return min


###############################################################################
# Generic database record object that can map to any table.
# Basically a dependency free ORM.


class rec:

  def __init__(self, d, table="", keys=[]):
    self.keys = keys
    self.data = {}
    self.table = table
    for k in self.keys:  # initialize data
      self.data[k] = ""
    if type(d) == dict:
      for k in self.keys:
        if k in d:
          self.data[k] = d[k]
    elif type(d) == list or type(d) == tuple:
      i = 0
      while i < len(d) and i < len(self.keys):
        self.data[self.keys[i]] = d[i]
        i += 1

  def __getitem__(self, key):
    return self.data.get(key, " ")

  def __setitem__(self, key, value):
    self.data[key] = value

  def tableColumns(self):
    return ", ".join(self.keys)

  def placeHolders(self):
    return "(" + ", ".join("?" * len(self.keys)) + ")"

  def get(self, cursor, key, value):
    cursor.execute("select %s from %s where %s = ?" %
                   (self.tableColumns(), self.table, key), (value,))
    rows = cursor.fetchone()
    return rec(rows, table=self.table, keys=self.keys)

  def get_many(self, cursor, key, value):
    cursor.execute("select %s from %s where %s like ?" %
                   (self.tableColumns(), self.table, key), (value,))
    rows = cursor.fetchall()
    output = {}
    for line in rows:
      t = rec(line, table=self.table, keys=self.keys)
      output[t[key]] = t
    return output

  def search(self, cursor, key, value):
    cursor.execute("select %s from %s where %s like ?" %
                   (self.tableColumns(), self.table, key), (value,))
    rows = cursor.fetchall()
    output = {}
    for row in rows:
      output[row[self.keys.index(key)]] = rec(row,
                                              table=self.table,
                                              keys=self.keys)
    return output

  def toList(self):
    output = []
    for k in self.keys:
      output.append(self.data[k])
    return output

  def toJSON(self):
    return json.dumps(self.data)

  def store(self, cursor):
    # writes self to DB, returns sql for logging purposes
    sql = "insert or replace into %s (%s) values %s" % (
        self.table, self.tableColumns(), self.placeHolders())
    vals = self.toList()
    cursor.execute(sql, vals)
    try:
      for i in range(len(vals)):
        vals[i] = str(vals[i])
      sql = "insert or replace into %s (%s) values (\"%s\");" % (
          self.table, self.tableColumns(), "\",\"".join(vals))
    except:
      sql = ""
    return sql

  def delete(self, cursor, key, value):
    # deletes rows from table whre key = value, returns sql for logging purposes
    cursor.execute("DELETE FROM %s WHERE %s = ?" % (self.table, key), (value,))
    return "DELETE FROM %s WHERE %s = '%s';" % (self.table, key, value)


###############################################################################


class timeseries:

  def __init__(self, data=None):
    self.status = "OK"

    # Data is an array of arrays with the following structure:
    #   [ datetime, float value, float quality ]

    self.data = []
    if data != None:
      for line in data:
        if line != []:
          if line[1] != None:
            self.data.append(line)

  def __str__(self):
    output = ""
    for line in self.data:
      try:
        output += "%s\t%.2f\t%.2f\n" % (line[0].strftime("%d-%b-%Y %H%M"),
                                        line[1], line[2])
      except:
        output += "%s\t\t\n" % (line[0].strftime("%d-%b-%Y %H%M"))
    return output

  #gets status message of object and resets it to "OK"

  def getStatus(self):
    s = self.status
    self.status = "OK"
    return s

  def findValue(self, timestamp):
    for line in self.data:
      if line[0] == timestamp:
        return line[1]
    return None

  # interpolates timeseries based on a given interval of type timedelta
  # returns a timeseries object

  def interpolate(self, interval):

    def interp_val(x0, y0, x1, y1, x):
      m = (y1 - y0) / (x1 - x0)
      return y0 + (x - x0) * m

    _data = []
    try:
      for i in xrange(0, len(self.data) - 1):
        startTime = self.data[i][0]
        deltaT = self.data[i + 1][0] - startTime
        steps = int(deltaT.total_seconds() / interval.total_seconds())
        quality = self.data[i][2]
        for j in xrange(0, steps):
          value = interp_val(0, self.data[i][1],
                             deltaT.total_seconds(), self.data[i + 1][1],
                             j * interval.total_seconds())
          _data.append([startTime + (interval * j), value, quality])
    except Exception, e:
      self.status = str(e)
    return timeSeries(_data)

  def accumulate(self, interval, override_startTime=None):
    '''accumulates timeseries based on a given interval of type timedelta
     returns a timeseries object'''
    _data = []
    if self.data == []:
      return timeseries()
    try:
      i = 0
      count = len(self.data)
      if override_startTime != None:
        endTime = override_startTime
      else:
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
          _data.append([endTime, sum, quality])
    except Exception, e:
      self.status = str(e)
    return timeseries(_data)

  # averages timeseries based on a given interval of type timedelta
  # returns a timeseries object

  def average(self, interval):
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
          _data.append([endTime, sum / n, quality])
    except Exception, e:
      self.status = str(e)
    return timeSeries(_data)

  # averages timeseries based on a given interval of type timedelta
  # returns a timeseries object

  def rollingaverage(self, interval):
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
        while self.data[i + n][0] <= endTime:
          sum += self.data[i + n][1]
          n += 1
          if i + n >= count:
            break
        if n != 0:
          _data.append([endTime, sum / n, quality])
        i += 1
    except Exception, e:
      self.status = str(e)
    return timeSeries(_data)

  #numerator : self
  #denominator : denom
  #returns a timeseries object of percentages

  def percent(self, denom):
    _data = []
    denom_data = {}
    try:
      # turn denominator data into a dictionary and filter out zeros
      # (no division by 0 allowed!)
      for line in denom.data:
        if line[1] != 0:
          denom_data[line[0]] = line
      for line in self.data:
        key = line[0]
        if key in denom_data:
          _data.append(
              [line[0], 100 * float(line[1] / denom_data[key][1]), line[2]])
    except Exception, e:
      self.status = str(e)
      return timeSeries()
    return timeSeries(_data)

  # Shifts each timestamp a given time interval
  # tdelta: timedelta to shift
  # returns a timeseries object

  def timeshift(self, tdelta):
    _data = []
    if self.data == []:
      return timeSeries()
    try:
      for line in self.data:
        _data.append([line[0] + tdelta, line[1], line[2]])
    except Exception, e:
      self.status = str(e)
      print e
      return timeSeries()
    return timeSeries(_data)

  def snap(self, interval, buffer, starttime=None):
    ''' Snaps a timeseries
        interval: interval at which time series is snapped
        buffer : lookahead and lookback
        returns a snapped timeseries '''
    output = timeseries()
    if self.data == []:
      return output
    try:
      if buffer > interval / 2:
        buffer = interval / 2
      #setup the initial start and end  time
      endtime = self.data[-1][0]
      if starttime != None:
        t = starttime
      else:
        t = self.data[0][0]
      pos = 0
      while pos < len(self.data) and t <= endtime:
        a = pos
        curdiff = abs(self.data[a][0] - t).seconds
        while pos < len(self.data) and self.data[pos][0] <= t + buffer:
          newdiff = abs(self.data[pos][0] - t).seconds
          if (curdiff > newdiff):
            curdiff = newdiff
            a = pos
          pos += 1
        if self.data[a][0] >= t - buffer and self.data[a][0] <= t + buffer:
          output.data.append([t, self.data[a][1], self.data[a][2]])
        t += interval
    except Exception, e:
      self.status = str(e)
      return timeseries()
    return output


  # Performs an operation on self
  # op: lambda function to perform eg lambda x,y: x+y
  # operand: could be a timeseries or a float
  # returns a timeseries object

  def operation(self, op, operand):
    _data = []
    if self.data == []:
      return timeSeries()
    try:
      if type(operand) is float:
        for line in self.data:
          _data.append([line[0], op(line[1], operand), line[2]])
      else:
        for line in self.data:
          val = operand.findValue(line[0])
          if val != None:
            _data.append([line[0], op(line[1], val), line[2]])
    except Exception, e:
      self.status = str(e)
      print e
      return timeSeries()
    return timeSeries(_data)

  def cull(self, op, operand):
    ''' culls data from self
        op: lambda function to perform eg lambda x,y: x>y
        operand: could be a timeseries or a float
        returns a timeseries object
    '''
    _data = []
    if self.data == []:
      return timeseries()
    try:
      if type(operand) is float:
        for line in self.data:
          if op(line[1], operand):
            _data.append(line)
      else:
        for line in self.data:
          val = operand.findValue(line[0])
          if val != None:
            if op(val, operand):
              _data.append([line])
    except Exception, e:
      self.status = str(e)
      print e
      return timeseries()
    return timeseries(_data)

  # This takes a relative time and turns it into a timedelta
  # eg input 7d6h9m

  def parseTimedelta(self, input):
    input = input.lower()
    sign = 1
    output = datetime.timedelta(seconds=0)
    t = ""
    try:
      for c in input:
        if c == "-":
          sign *= -1
        elif c == "y":
          output += datetime.timedelta(days=float(t) * 365)
          t = ""
        elif c == "w":
          output += datetime.timedelta(days=float(t) * 7)
          t = ""
        elif c == "d":
          output += datetime.timedelta(days=float(t))
          days = 0
          t = ""
        elif c == "h":
          output += datetime.timedelta(hours=float(t))
          t = ""
        elif c == "m":
          output += datetime.timedelta(minutes=float(t))
          t = ""
        else:
          if c != " ":
            t += c
    except:
      self.status = "Could not parse" + input + " into a time interval"
    return output * sign

  # averages entire timeseries returns a timeslice

  def globalAverage(self):
    if len(self.data) != 0:
      interval = self.data[-1][0] - self.data[0][0]
      return self.average(interval).data[0]
    return None

  # finds the maximum of timeseries returns a timeslice

  def globalMax(self):
    if len(self.data) != 0:
      interval = self.data[-1][0] - self.data[0][0]
      return self.maxmin(interval, lambda x, y: x > y).data[0]
    return None

  # finds the minimum of timeseries returns a timeslice

  def globalMin(self):
    if len(self.data) != 0:
      interval = self.data[-1][0] - self.data[0][0]
      return self.maxmin(interval, lambda x, y: x < y).data[0]
    return None

  # returns a max or a min based for a given interval of type datetime
  # returns a timeseries object

  def maxmin(self, interval, cmp):
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
          if cmp(self.data[i][1], probe):
            probe = self.data[i][1]
          i += 1
          if i >= count:
            break
        _data.append([endTime, probe, quality])
    except Exception, e:
      self.status = str(e)
    return timeseries(_data)


def getDefaultUnits(tsid, dFamily):
  """ Return default display units for a given pathname.
   input:   tsid - CWMS pathname
         dFamily - Class of display units, defaults
  """
  if dFamily not in defaultUnits:
    dFamily = "default"
  try:
    tsid = tsid.lower()
    tokens = tsid.split(".")

    # check to see if full Parameter is in default units and return
    param = tokens[1]
    if param in defaultUnits[dFamily]:
      return defaultUnits[dFamily][param]

    # check to see if parameter is in default units and return
    param = tokens[1].split("-")[0]
    if param in defaultUnits[dFamily]:
      return defaultUnits[dFamily][param]
  except:
    pass

  return ""  # Use database default

timeSeries = timeseries

def connect(dbpath):
  global dbconn
  global cur
  try:
    config = json.load(open("../config/config.json","r"))
    defaultUnits = config.get("units",{})
    dbconn = sqlite3.connect(dbpath)
    cur = dbconn.cursor()
    if not dbconn:
      status = "\nCould not connect to %s\n" % dbpath
      status += "\n%s"
  except Exception, e:
    status = "\nCould not connect to %s\n" % dbpath
    status += "\n%s" + str(e)


#---setup database connection

dbconn = None
cur = None
status = "OK"
connect("../data/hydro.db")
