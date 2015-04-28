import operator
from tonecounteralt import ToneCounterAlt
from pctimecode import convertUnsignedLongLongToTimeCode, convertTimeCodeToUnsignedLongLong
import json
import copy

def prettyPrintJSON(data):
	return json.dumps(data, sort_keys = True, indent=4, separators=(',', ': '))

class ToneCounterResultAlt:
	def __init__(self, timeCodeSampleRate, timeBase=24):
		self.timeCodeSampleRate = timeCodeSampleRate
		self.timeBase = timeBase
		self.errors = []

	def doesRunExistWithInSilentZone(self, run):
		silentZoneStart = convertTimeCodeToUnsignedLongLong("00:58:33:00",self.timeCodeSampleRate, self.timeBase)
		silentZoneStop = convertTimeCodeToUnsignedLongLong("00:59:57:00",self.timeCodeSampleRate, self.timeBase)

		runStart = run['start']
		runStop = run['start']+ (run['length']*self.timeCodeSampleRate)

		if runStop > silentZoneStart and runStop <= silentZoneStop:
			return True

		return False

	def doesRunExistWithInToneZone(self, run):
		zoneStart = convertTimeCodeToUnsignedLongLong("00:57:30:00",self.timeCodeSampleRate, self.timeBase)
		zoneStop = convertTimeCodeToUnsignedLongLong("00:58:31:00",self.timeCodeSampleRate, self.timeBase)

		runStart = run['start']
		runStop = run['start']+ (run['length']*self.timeCodeSampleRate)

		if runStart >= zoneStart and runStop <= zoneStop:
			return True

		return False	

	def resultForBasicToneExistAtHead(self, runs):

		contiguousRuns = self.contiguousRuns(runs)
		result = False

		for run in contiguousRuns:
			zoneStart = convertTimeCodeToUnsignedLongLong("00:57:30:00",self.timeCodeSampleRate, self.timeBase)
			zoneStop = convertTimeCodeToUnsignedLongLong("00:58:31:00",self.timeCodeSampleRate, self.timeBase)

			runStart = convertUnsignedLongLongToTimeCode(run['start'], self.timeCodeSampleRate, self.timeBase)
			runStop = convertUnsignedLongLongToTimeCode(run['start']+ (run['length']*self.timeCodeSampleRate), self.timeCodeSampleRate, self.timeBase)
			runLength = run['length']

			if runStart >= zoneStart and runStop <= runStop and runLength >= 54:
				
				runsToCheck = runs[runs.index(run):run['length']]
				runsToCheck = runsToCheck[1:-1]
				doesRunHaveTheCorrectLevelResultString = self.descriptionForLevelsInRuns(runsToCheck)

				if doesRunHaveTheCorrectLevelResultString != 'success':
					return {"status":"fail", "resultString":doesRunHaveTheCorrectLevelResultString}
				else:
					return {"status":"pass"}

		description = ""
		if len(contiguousRuns) > 0:
			description = "No proper 1kHz tones were found, only 1kHz tones with the following lengths in seconds: {}.".format(" ".join([str(run['length']) for run in contiguousRuns]))
		else:
			description = "No proper 1kHz tones were found."

		return {"status":"fail", "resultString":description}

	def descriptionForLevelsInRuns(self,runs):
		toneLevels = [] 
		for run in runs:
			if self.isRunAtTheCorrectLevel(run) != True:
				adjustedLevel = run["freqDBRep"] + 3.2
				toneLevels.append("{:3.2f}".format(adjustedLevel))

		if len(toneLevels) > 0:
			uniqueValues = set(toneLevels)
			return "Found the following level errors {}".format(list(uniqueValues))

		return "success"

	def isRunAtTheCorrectFrequency(self, run):
		if run["freq"] < 1004 and run["freq"] > 996:
			return True
		return False		

	def isRunAtTheCorrectLevel(self, run):
		if run["freqDBRep"] > -23.5 and run["freqDBRep"] < -22.5:
			return True
		return False	

	def sortedKeysForDict(self, toneCounterDict):
		return sorted(toneCounterDict.keys())

	def contiguousRuns(self, cRuns):
		if len(cRuns) <= 1:
			return []

		consecutiveRuns = []
		currentRun = cRuns[0]
		previousTime = currentRun['currentTime']		

		for run in cRuns[1:]:
			currentTime =  run['currentTime']
			if previousTime + self.timeCodeSampleRate == currentTime:
				# print (previousTime + self.timeCodeSampleRate), currentTime 
				currentRun['length'] += 1
				if currentRun not in consecutiveRuns:
					consecutiveRuns.append(currentRun)
			else:
				currentRun = run
				# consecutiveRuns.append(currentRun)

			previousTime = run['currentTime']

		return consecutiveRuns

	def deepRunsCopy(self, runs):
		return copy.deepcopy(runs)

	def result(self, toneCounterDict): 
		status = "pass"
		resultString = "Tones are valid across all tracks."
		warningString = ""
		currentError = ""

		successStrings 	= []
		errorStrings 	= []
		warningStrings 	= []

		#lets hust find out if there's a tone and pop
		for channel in self.sortedKeysForDict(toneCounterDict):
			runs = toneCounterDict[channel].runs
			badRuns = toneCounterDict[channel].badRuns
			errorRuns = toneCounterDict[channel].errors

			# are there any errors in the first minute of the track
			# is the tone longth enough ?
			# is the silence present from 00:58:30:00 to 00:59:57:00?
			# is there any other frequency from 00:59:57:00 to 01:00:00:00

			#is the area from 00:58:33:00 to 00:59:57:00 silent?
			for run in self.contiguousRuns(self.deepRunsCopy(runs)):
				if self.doesRunExistWithInSilentZone(run) == True:
					errorStrings.append("There appears to be tone within the silence area of the head on channel {}. The tone runs for {} seconds.".format(channel, run['length']))
					status = 'fail'

			for run in self.contiguousRuns(self.deepRunsCopy(errorRuns)):
				if self.doesRunExistWithInSilentZone(run) == True:
					errorStrings.append("There appears to be non 1kHz frequency content within the silence area of the head on channel {}.".format(channel))				
					status = 'fail'

			#do we have at least 55 seconds of unmolested tone?
			resultForBasicToneExistAtHeadValue = self.resultForBasicToneExistAtHead(self.deepRunsCopy(runs))
			if resultForBasicToneExistAtHeadValue['status'] == 'fail':
				errorStrings.append("The head on channel {} doesn't have proper 1 kHz tones as defined as falling in within 00:57:30:00 to 00:58:30:00 for at least 55 seconds at -20db.".format(channel))
				errorStrings.append(resultForBasicToneExistAtHeadValue['resultString'])
				status = 'fail'
			else:
				successStrings.append("A proper 1 kHz tone of at least 55 seconds exists on channel {}.".format(channel))

			#where is the schmutz in the track and what kind of concern is it?
			for run in self.contiguousRuns(self.deepRunsCopy(errorRuns)):
				if self.doesRunExistWithInToneZone(run) == True:
					if resultForBasicToneExistAtHeadValue == False:
						errorStrings.append("There appears to be non 1kHz frequency content within the tone area of the head on channel {}.".format(channel))				
						status = 'fail'
					else:
						warningStrings.append("There appears to be non 1kHz frequency content within the tone area of the head on channel {}.".format(channel))				

		if status == 'fail':
			resultString = " ".join(errorStrings)

		if len(warningStrings) > 0:
			warningString = " ".join(warningStrings)

		return {"status":status, "resultString":resultString, "warningString":warningString}

