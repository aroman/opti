# Core scheduling functionality
# takes in a dictionary with name is key and vals are lists of tuples of conflicts
# constraints are the work day (default 9-5)
# time is in military form 
# if there's no time available, recommend a day and time in a week


# takes in a schedule, in the form of a dictionary
def coreScheduler(schedules, duration = .5, beginTime = 9, endTime = 17, increment = .25):
	possibilities = []
	while True:
		for user in schedules:
			conflicts = schedules[user]
			while beginTime < endTime:
				if not goodTime(beginTime, beginTime + duration, conflicts):
					beginTime += increment
				else: break
		if beginTime < endTime:
			possibilities.append((beginTime, beginTime + duration))
		if len(possibilities) == 4 or beginTime == endTime: break
		beginTime += increment
	if possibilities != []: return possibilities
	return "There are no schedules!"

def findBestSchedule(schedules, mainUser, duration = .5, beginTime = 9, \
						endTime = 17, increment = .25, numOutput = 4):
	numConflicts = 0
	possibilities = []
	for i in xrange(len(schedules)):
		possibilities.append([])
	while beginTime < endTime:
		isBad = False
		for user in schedules:
			conflicts = schedules[user]
			if not goodTime(beginTime, beginTime + duration, schedules[mainUser]):
				isBad = True
				break
			if not goodTime(beginTime, beginTime + duration, conflicts):
				numConflicts += 1
				continue
		if not isBad:
			possibilities[numConflicts].append((beginTime, beginTime + duration))
		beginTime += increment
		numConflicts = 0
	return possibilities

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

# takes in a list of dictionaries
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
	schedules["Chris"] = [(7,11)]
	print coreScheduler(schedules)
	print findBestSchedule(schedules, "Chris")

testCoreScheduler()

