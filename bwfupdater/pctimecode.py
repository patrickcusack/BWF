import sys
import re
import random
import struct
import os
import math

def onePercentPullUp(samplerate):
	return int(math.ceil(samplerate * 1.001))

def formattedTimeCodeStringFromComponents(hours, minutes, seconds, frames, isDrop):
	tcString = "{0:0>2}".format(hours)
	tcString += ":" + "{0:0>2}".format(minutes)  
	tcString += ":" + "{0:0>2}".format(seconds)
	if isDrop == True:
		tcString += ";" + "{0:0>2}".format(frames)
	else:
		tcString += ":" + "{0:0>2}".format(frames)
	return tcString

def convertTimeCodeToUnsignedLongLong(timecode, samplesPerSecond, framerate):
	if timecode == "" or samplesPerSecond == 0 or framerate == 0:
		return 0

	if isTimeCodeSafe(timecode, str(framerate)) is not True:
		return 0

	components 	= re.split(':|;', timecode)
	dropFrameComponents = timecode.split(";")
	isDropFrame = False

	totalSamples = 0

	if len(dropFrameComponents) > 1:
		isDropFrame = True	

	if len(components) == 4:
		totalSamples += (int(components[0]) * 60 * 60 * framerate)
		totalSamples += (int(components[1]) * 60 * framerate)
		totalSamples += (int(components[2]) * framerate)
		totalSamples += int(components[3])
		totalSamples *= (samplesPerSecond/framerate)
	else:
		return 0

	return long(round(totalSamples))

def convertUnsignedLongLongToTimeCode(uLLValue, samplesPerSecond, framerate):
	if uLLValue == 0 or samplesPerSecond == 0 or framerate == 0:
			return "00:00:00:00"

	# Start
	remainder 	= int(uLLValue/(samplesPerSecond/int(framerate)))
	
	# Hour
	denominator = (60*60*framerate)
	hour 		= remainder / denominator
	remainder 	%=  denominator

	# Minutes
	denominator = (60*framerate)
	minutes 	= remainder / denominator
	remainder 	%=  denominator

	# Seconds
	denominator = framerate
	seconds 	= remainder / denominator
	remainder 	%=  denominator		

	# Frames
	frames 		= remainder

	return formattedTimeCodeStringFromComponents(hour, minutes, seconds, frames, False)

		
def convertDropFrameTimeCodeToDiscreetFrames(timecode, framerate):
	if timecode == "" or framerate == 0:
		return 0;

	components 	= re.split(':|;', timecode)
	totalFrames = 0

	hours 	= 0
	minutes = 0
	seconds = 0
	frames 	= 0

	if len(components) == 4:
		hours 	= int(components[0])
		minutes = int(components[1])
		seconds = int(components[2])
		frames  = int(components[3])
	else:
		return 0

	# dropFrames 		= round(((framerate*1000.0)/1001) * 0.06666666)
	# timebase 		= round((framerate*1000.0)/1001)
	# changed this from 30000/1001 to 30/1

	dropFrames 		= round(framerate * 0.06666666)
	timebase 		= round(framerate)	

	hourFrames 		= int(timebase * 60 * 60)
	minuteFrames 	= int(timebase * 60)
	totalMinutes	= int((60 * hours) + minutes)

	frameNumber		= ((hourFrames * hours) + (minuteFrames * minutes) + (timebase * seconds) + frames)
	frameNumber		-= (dropFrames * (totalMinutes - (totalMinutes / 10)))

	totalFrames = frameNumber
	return long(totalFrames)

def convertTimeCodeToDiscreetFrames(timecode, framerate):
	if timecode == "" or framerate == 0:
		return 0

	components 	= re.split(':|;', timecode)
	dropFrameComponents = timecode.split(";")
	totalFrames = 0

	if len(dropFrameComponents) > 1:
		return 0	

	if len(components) == 4:
		totalFrames += (int(components[0]) * 60 * 60 * framerate)
		totalFrames += (int(components[1]) * 60 * framerate)
		totalFrames += (int(components[2]) * framerate)
		totalFrames += int(components[3])
	else:
		return 0

	return totalFrames	

def convertDiscreetFramesToTimeCode(totalFrames, framerate):
	if totalFrames == 0 or framerate == 0:
			return "00:00:00:00"

	# Start
	remainder 	= totalFrames;

	# Hour
	denominator = (60*60*framerate)
	hour 		= remainder / denominator
	remainder 	%=  denominator

	# Minutes
	denominator = (60*framerate)
	minutes 	= remainder / denominator
	remainder 	%=  denominator

	# Seconds
	denominator = framerate
	seconds 	= remainder / denominator
	remainder 	%=  denominator		

	# Frames
	frames 		= remainder

	return formattedTimeCodeStringFromComponents(hour, minutes, seconds, frames, False)

def convertDiscreetFramesToDropFrameTimeCode(totalFrames, framerate):	
	timebase = (framerate * 1000.0)/ 1001;
	
	dropFrames			= int(round(timebase * .066666))						#Number of frames to drop on the minute marks is the nearest integer to 6% of the framerate
	framesPerHour		= int(round(timebase * 60 * 60))						#Number of frames in an hour
	framesPer24Hours	= int(framesPerHour * 24)							#Number of frames in a day - timecode rolls over after 24 hours
	framesPer10Minutes	= int(round(timebase * 60 * 10))						#Number of frames per ten minutes
	framesPerMinute		= int((round(timebase)* 60) -  dropFrames)			#Number of frames per minute is the round of the framerate * 60 minus the number of dropped frames

	d = totalFrames / framesPer10Minutes
	m = totalFrames % framesPer10Minutes

	# print timebase, dropFrames, framesPerHour, framesPer24Hours, framesPer10Minutes, framesPerMinute, d, m

	if m > dropFrames:
		totalFrames = totalFrames + (dropFrames * 9 * d) + dropFrames * ((m - dropFrames) / framesPerMinute)
	else:
		totalFrames = totalFrames + dropFrames * 9 * d;

	roundedTimeBase = round(timebase);
	frames 			= int(totalFrames % roundedTimeBase)
	seconds 		= int((totalFrames / roundedTimeBase) % 60)
	minutes 		= int(((totalFrames / roundedTimeBase) / 60) % 60)
	hours 			= int((((totalFrames / roundedTimeBase) / 60) / 60))

	return formattedTimeCodeStringFromComponents(hours, minutes, seconds, frames, True)

def convertTimeCodeToDropFrameTimeCode(timecode):
	if timecode == "" or framerate != 30:
		return "00:00:00;00"
	totalFrames = convertTimeCodeToDiscreetFrames(timecode, 30)
	return convertDiscreetFramesToDropFrameTimeCode(totalFrames, 30)

def convertDropFrameTimeCodeToTimeCode(timecode):
	if timecode == "":
		return "00:00:00:00"
	totalFrames = convertDropFrameTimeCodeToDiscreetFrames(timecode, 30)
	return convertDiscreetFramesToTimeCode(totalFrames, 30)	

def convertTimeCodeToUnsignedLongLong2398(timecode, samplerate):
	return convertTimeCodeToUnsignedLongLong(timecode, samplerate * 1.001, 24)

def convertTimeCodeToUnsignedLongLong24(timecode, samplerate):
	return convertTimeCodeToUnsignedLongLong(timecode, samplerate, 24)

def convertTimeCodeToUnsignedLongLong25(timecode, samplerate):
	return convertTimeCodeToUnsignedLongLong(timecode, samplerate, 25)

def convertTimeCodeToUnsignedLongLong2997DF(timecode, samplerate):
	nTimeCode = convertDropFrameTimeCodeToTimeCode(timecode)
	return convertTimeCodeToUnsignedLongLong2997(nTimeCode, samplerate)

def convertTimeCodeToUnsignedLongLong2997(timecode, samplerate):
	return convertTimeCodeToUnsignedLongLong(timecode, samplerate * 1.001, 30)

def convertTimeCodeToUnsignedLongLong30(timecode, samplerate):
	return convertTimeCodeToUnsignedLongLong(timecode, samplerate, 30)

def isTimeCodeSafe(timecode, framerateString):
	components 	= re.split(':|;', timecode)

	if len(components) != 4:
		return False;

	for component in components:
		try:
			int(component)
		except:
			return False

	if int(components[0]) > 23:
		return False

	if int(components[1]) > 59:
		return False

	if int(components[2]) > 59:
		return False

	if framerateString == '2398':
		if int(components[3]) > 23:
			return False
	elif framerateString == '24':
		if int(components[3]) > 23:
			return False
	elif framerateString == '25':
		if int(components[3]) > 24:
			return False
	elif int(components[3]) > 29:
			return False

	return True


def randomTest():
	print convertTimeCodeToUnsignedLongLong2398("00:59:30:00", 48000)
	print convertTimeCodeToUnsignedLongLong24("00:59:30:00", 48000)
	print convertTimeCodeToUnsignedLongLong25("00:59:30:00", 48000)
	print convertTimeCodeToUnsignedLongLong2997DF("00:59:30:00", 48000)
	print convertTimeCodeToUnsignedLongLong2997("00:59:30:00", 48000)
	print convertTimeCodeToUnsignedLongLong30("00:59:30:00", 48000)
	print convertTimeCodeToUnsignedLongLong30("00:59:30:00", 48000)
	print convertTimeCodeToUnsignedLongLong2997(convertDropFrameTimeCodeToTimeCode("00:59:30;00"), 48000)

	roundTripTest("23:59:59:29", 48000, 30)
	roundTripTest("23:59:59:29", 188000, 30)
	roundTripTest("23:59:59:23", 48000, 24)
	roundTripTest("23:59:59:24", 188000, 25)

def timecodeTest():
		for i in range(0,188000 * 60 * 60 * 24, 188000/30):
			timecode 	= convertUnsignedLongLongToTimeCode(i, 188000, 30)
			print timecode

def dropFrameTest():
		for i in range(0,100000*24, random.randrange(1000,4000)):
			timecode 	= convertDiscreetFramesToTimeCode(i, 30)
			dfTimeCode 	= convertTimeCodeToDropFrameTimeCode(timecode)	
			print timecode, dfTimeCode

def timecodeValidationTest():
	print "Starting TimeCode Conversion Test 1:"
	testVars = ["02:00:03:12", "23:59:59:29", "01:00:00:00", "12:15:45:02", "18:43:13:01", "05:19:23:08", "0", "Hello", "01;01:01<:012", "99:99:99:99"]

	for test in testVars:
		print test, convertUnsignedLongLongToTimeCode(convertTimeCodeToUnsignedLongLong(test, 48000, 30), 48000, 30)

def roundTripTest(timecode, samplesPerSecond, framerate):
	samples = convertTimeCodeToUnsignedLongLong(timecode, samplesPerSecond, framerate)
	result = convertUnsignedLongLongToTimeCode(samples, samplesPerSecond, framerate)
	print "SamplesPerSecond:", samplesPerSecond, "FrameRate:", framerate, "In:", timecode, "Out:", timecode

def timecodeConversionTest(samplesPerSecond, framerate):

	print "Starting TimeCode Conversion Test 2:", samplesPerSecond, framerate
	maxTime = samplesPerSecond * 60 * 60 * 24
	currentTime = 0

	while currentTime < maxTime:
	 if currentTime != convertTimeCodeToUnsignedLongLong(convertUnsignedLongLongToTimeCode(currentTime, samplesPerSecond, framerate), samplesPerSecond, framerate):
	  	print "Error", currentTime, convertTimeCodeToUnsignedLongLong(convertUnsignedLongLongToTimeCode(currentTime, samplesPerSecond, framerate), samplesPerSecond, framerate)
	 currentTime += (samplesPerSecond/framerate)

def testRoutines():
	# print convertTimeCodeToUnsignedLongLong2398("00:57:30:00", 48000)
	# print convertTimeCodeToUnsignedLongLong24("00:57:30:00", 48000)
	# print convertTimeCodeToUnsignedLongLong25("00:57:30:00", 48000)
	# print convertTimeCodeToUnsignedLongLong2997DF("00:57:30:00", 48000)
	# print convertTimeCodeToUnsignedLongLong2997("00:57:30:00", 48000)
	# print convertTimeCodeToUnsignedLongLong30("00:57:30:00", 48000)
	# print convertTimeCodeToUnsignedLongLong30("00:57:30:00", 48000)
	# print convertUnsignedLongLongToTimeCode(165765600, 48000, 30)
	print convertUnsignedLongLongToTimeCode(165765600, 48048, 24)
	print convertUnsignedLongLongToTimeCode(172876704, 48048, 24)

if __name__ == '__main__':
	testRoutines()
 

 