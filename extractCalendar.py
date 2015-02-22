# made by Rajat Mehndiratta (github/rajatmehndiratta) at Hack-A-Startup 2015
# part of Project Opti

#@DESC: This is a module with the following purposes:
# - extract a user's contacts' Google Calendar events
# - extract events for a given day for each contact
# - resolve conflicts and determine available times

import json
import thread
import timeConversion

def getSchedule(attendee, day):
    # given an attendee, produces a list of tuples indicating "busy" times that day

class Meeting(object):

    def __init__(self, begin, end, *attendees):
        self.idealtimes = []
        self.besttimes = []
        self.begin = begin
        self.end = end
        self.busyTimes = dict()
        for attendee in attendees:
            self.busyTimes[attendee] = getSchedule(attendee)

    def resolve(self):



meeting = Meeting(....)
meeting.idealtimes
meeting.settime()