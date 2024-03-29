import string

# Convert time from JSON string to military/decimal float for algorithm
def jsonToAlgorithm(jsonTime):
    # Time starts after "T"
    timeStart = string.find(jsonTime, "T") + 1

    # Get hour and minute after that
    hour = float(jsonTime[timeStart: timeStart + 2])
    minute = float(jsonTime[timeStart + 3: timeStart + 5])

    hour -= 5 # adjust for tz

    # Sum hour and minute/60 to get newTime, round to two decimals
    algorithmTime = round(hour + minute / 60, 2)

    return algorithmTime

# Convert time from algorithm float to user-readable string
def algorithmToUser(algorithmTime):
    # Hour is before decimal
    hour = int(algorithmTime)
    # Adjust hour to non-military time, choose am or pm
    if hour > 12:
        hour -= 12
        suffix = "pm"
    else:
        suffix = "am"

    # Minute is after decimal, as a fraction of 60
    minute = int((algorithmTime % 1) * 100) * 60 / 100

    userTime = "%02d:%02d%s" % (hour, minute, suffix)

    return userTime

# Convert time from algorithm tuple floats to super-readable string
def algorithmTupleToUser(algorithmTuple):
    (start, end) = (algorithmTuple[0], algorithmTuple[1])
    newStartHour = int(start)
    newEndHour = int(end)

    if newStartHour > 12:
        newStartHour -= 12
    if newEndHour > 12:
        newEndHour -= 12
        suffix = "p"
    else:
        suffix = "a"

    newStartMinute = int((start % 1) * 100) * 60 / 100
    newEndMinute = int((end % 1) * 100) * 60 / 100

    userTime = "%d:%02d - %d:%02d%s" % (newStartHour, newStartMinute, newEndHour, newEndMinute, suffix)

    return userTime

# Convert time from algorithm float to JSON string of just time, no date
def algorithmToJson(algorithmTime):
    # Hour is same as algorithmTime hour
    hour = int(algorithmTime)
    #hour += 5 # adjust for tz
    # Minute is algorithmTime after decimal as fraction of 60
    minute = int((algorithmTime % 1) * 100) * 60 / 100

    jsonTime = "%02d:%02d:00" % (hour, minute)

    return jsonTime

# Convert date from user MM/DD to JSON YYYY-MM-DD
def userDateToJsonDate(userDate):
    year = 2015
    monthEnd = string.find(userDate, "/")
    month = int(userDate[:monthEnd])
    day = int(userDate[monthEnd + 1:])
    return "%04d-%02d-%02d" % (year, month, day)

#test
# print jsonToAlgorithm("2015-02-24T19:30:00-05:00")
# print jsonToAlgorithm("2015-02-22T17:30:00Z")
# print algorithmToUser(19.50)
# print algorithmToJson(19.50)
# print userDateToJsonDate("2/24")
# print algorithmTupleToUser((9.25, 11.5))

