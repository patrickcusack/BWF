import operator
from tonecounter import ToneCounter
from pctimecode import convertUnsignedLongLongToTimeCode, convertTimeCodeToUnsignedLongLong

class ToneCounterResult:
	def __init__(self, timeCodeSampleRate, timeBase):
		self.timeCodeSampleRate = timeCodeSampleRate
		self.timeBase = timeBase
		self.errors = []

	def isToneRun(self, run, channel):
		correctRunStart = self.doesToneRunStartAtCorrectTime(run)
		correctRunLength = self.isToneRunLongEnough(run)
		correctRunLevel = self.isRunTheProperToneLevel(run)
		correctRunFrequency = self.isRunAtTheCorrectFrequency(run)
		
		successfulResult = "The tracks contain 1 kHz tones for one minute"
		result = True
		status = "pass"
		currentError = ""
		resultString = successfulResult

		if correctRunStart is False:
			timeStart = convertUnsignedLongLongToTimeCode(run["start"], self.timeCodeSampleRate, self.timeBase)
			currentError = "The Tones on track {} start at {}. ".format(channel, timeStart)
			status = "fail"
			result = False

		if correctRunLength is False:
			currentError = currentError + "The Tones on track {} start are not in spec: {} seconds.".format(channel, run["count"])
			status = "fail"
			result = False

		if correctRunLevel is False:
			currentError = currentError + "The levels on track {} are not in spec: {} db.".format(channel, run["freqDBRep"])
			status = "fail"
			result = False

		if correctRunFrequency is False:
			currentError = currentError + "The frequency on track {} is not in spec: {} seconds.".format(channel, run["freq"])
			status = "fail"
			result = False

		if currentError is not "":
			resultString = currentError

		return tuple([result, {"status":status, "resultString":resultString}])

	def isPopRun(self, run, channel):
		correctRunStart = self.doesRunStartAtPopTime(run)
		correctRunFrequency = self.isRunAtTheCorrectFrequency(run)
		
		successfulResult = "Found a pop on channel {}".format(channel)
		status = "pass"
		currentError = ""
		resultString = successfulResult
		result = True

		if correctRunStart is False:
			timeStart = convertUnsignedLongLongToTimeCode(run["start"], self.timeCodeSampleRate, self.timeBase)
			currentError = "The pop on track {} start at {}. ".format(channel, timeStart)
			status = "fail"
			result = False

		if run["count"] != 1:
			currentError = currentError + "There doesn't appear to be a pop on channel {}".format(channel)
			status = "fail"
			result = False

		if correctRunFrequency is False:
			currentError = currentError + "The frequency of the pop on channel {} is not correct: {} Hz".format(channel, run["freq"])
			status = "fail"
			result = False

		if currentError is not "":
			resultString = currentError

		return tuple([result, {"status":status, "resultString":resultString}])

	def isThereALong1kHZToneInHead(self, runs):
		for run in runs:
			if run["count"] > 1:
				return True
		return False

	def doesValidHeadToneExistOnTrack(self, runs):
		for run in runs:
			if self.doesToneRunStartAtCorrectTime(run) == True and  self.isToneRunLongEnough(run) == True:
				return True
		return False

	def doesValidPopToneExistOnTrack(self, runs):
		for run in runs:
			if self.doesRunStartAtPopTime(run) == True and  run['count'] == 1:
				return True
		return False	

	def doesToneRunStartAtCorrectTime(self, run):
		#165765600 at 48048 (basically 23.98 @ 48kHz) is 57:30:00
		if run["start"] == convertTimeCodeToUnsignedLongLong("00:57:30:00",self.timeCodeSampleRate, 24):
			return True
		return False

	def doesRunStartAtPopTime(self, run):
		#165765600 at 48048 (basically 23.98 @ 48kHz) is 57:30:00
		if run["start"] == convertTimeCodeToUnsignedLongLong("00:59:58:00",self.timeCodeSampleRate, 24):
			return True
		return False	

	def isToneRunLongEnough(self, run):
		if run["count"] > 58 or run["count"] < 62:
			return True
		return False

	def isRunTheProperToneLevel(self, run):
		if run["freqDBRep"] < -22.5 and run["freqDBRep"] > -24.5:
			return True
		return False	

	def isRunAtTheCorrectFrequency(self, run):
		if run["freq"] < 1004 and run["freq"] > 996:
			return True
		return False		

	def sortedKeysForDict(self, toneCounterDict):
		return sorted(toneCounterDict.keys())

	def result(self, toneCounterDict): 
		status = "pass"
		resultString = "Tones are valid across all tracks."
		currentError = ""

		#lets hust find out if there's a tone and pop
		for channel in self.sortedKeysForDict(toneCounterDict):
			cRuns = toneCounterDict[channel].runs()

			if self.doesValidHeadToneExistOnTrack(cRuns) == False:
				if self.isThereALong1kHZToneInHead(cRuns) == True:
					currentError = currentError + "There appears to be a head tone on channel {} but it either doesn't start at the right time or is the wrong length.".format(channel) + " "
				else:
					currentError = currentError + "There doesn't appear to be a full head tone on channel {}.".format(channel) + " "
				status = "fail"

			if self.doesValidPopToneExistOnTrack(cRuns) == False:
				currentError = currentError + "There doesn't appear to be a pop on channel {}.".format(channel) + " "
				status = "fail"

		#now lets check for errors
		for channel in self.sortedKeysForDict(toneCounterDict):
			errors = toneCounterDict[channel].errors
			if len(errors) > 0:
				currentError = currentError + "There appear to be tones other than 1kHz in track {}.".format(channel) + " "
				status = "fail"

		#now lets account for the fact that I found more than two snippets at 1kHz
		for channel in self.sortedKeysForDict(toneCounterDict):
			cRuns = toneCounterDict[channel].runs()
			#we expect two find only two snippets of tone, 1 at the head, and the pop
			if len(cRuns) > 2:
				currentError = currentError + "There appears to be discontinuous or off-level tone on channel {}. ".format(channel)
				status = "fail"

		if currentError != "":
			resultString = currentError

		return {"status":status, "resultString":resultString}

