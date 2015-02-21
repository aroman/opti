# Core scheduling functionality
# takes in a dictionary with name is key and vals are lists of tuples of conflicts
# constraints are the work day (default 9-5)
# time is in military form 
# if there's no time available, recommend a day and time in a week


def coreScheduler(schedules, duration = .25, beginTime = 9, endTime = 17):
	for user in schedules:
		conflicts = schedules[user]
		while beginTime < endTime:
			if not goodTime(beginTime, beginTime + duration, conflicts):
				beginTime += duration
			else: break
	if beginTime < endTime:
		return (beginTime, beginTime + duration)
	return "There is no good time to meet."

# determines whether or not the hypothetical meeting times are efficient
def goodTime(beginTime, endTime, conflicts):
	for time in conflicts:
		(begin, end) = time
		if (begin <= beginTime and end >= endTime) or\
			(begin >= beginTime and end <= endTime) or\
			(begin <= endTime and end >= endTime) or\
			(begin <= beginTime and end >= beginTime):
			return False
	return True

# takes in a 2d list that represents a week of days, each day is a dictionary
# passes into the core scheduler
def recommendTime(schedules, duration = .25, beginTime = 9, endTime = 17):
	for i in xrange(len(schedules)):
		day = schedules[i]
		if type(result) != str: break
		result = coreScheduler(day, duration, beginTime, endTime)
	return result

def testCoreScheduler():
	schedules = dict()
	schedules["Alice"] = [(9,10),(15.5,16),(17,18)]
	schedules["Pulkita"] = [(8,9.5), (14,15), (16,17)]
	schedules["Avi"] = [(7,10), (11, 12), (14,17)]
	print coreScheduler(schedules)

testCoreScheduler()
