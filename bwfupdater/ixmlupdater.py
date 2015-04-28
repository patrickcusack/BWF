import os
import sys
from pcwavefile import PCWaveFile
import pctimecode

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import parse, tostring

def frameRateDescriptionDictionary(frameRateDescription):
	try:
	    return {
	        "2398" : "24000/1001",
	        "24": "24/1",
	        "25": "25/1",
	        "2997": "30000/1001",
	        "2997DF": "30000/1001",
	        "30": "30/1",
	        }.get(frameRateDescription)
	except:
		return "30/1"

def bextXMLDataDictFromWaveFile(wavefile):
		if wavefile.isBWFFile == True:	
			bextDict = wavefile.getBextChunkDict()
			info = {}
			info["BWF_DESCRIPTION"] 				= bextDict["bwDescription"]
			info["BWF_ORIGINATOR"] 					= bextDict["bwOriginator"]
			info["BWF_ORIGINATOR_REFERENCE"] 		= bextDict["bwOriginatorReference"]
			info["BWF_ORIGINATION_DATE"] 			= bextDict["bwOriginationDate"]
			info["BWF_ORIGINATION_TIME"] 			= bextDict["bwOriginationTime"]
			info["BWF_TIME_REFERENCE_LOW"] 			= bextDict["bwTimeReferenceLow"]
			info["BWF_TIME_REFERENCE_HIGH"] 		= bextDict["bwTimeReferenceHigh"]
			info["BWF_VERSION"]				 		= bextDict["bwVersion"]
			info["BWF_UMID"]				 		= bextDict["bwSMPTEUMID"]

			# Must handle this a special way, can't display null
			myByteArray = bytearray(bextDict["bwReserved"])
			nextString = ""
			for byte in myByteArray:
				nextString += str(byte)
			info["BWF_RESERVED"]				 	= nextString
			info["BWF_CODING_HISTORY"]				= bextDict["bwCodingHistory"]
			return info
		else:
			return None

def speedAttributeDictionaryForWavefile(wavefile, isDropFrame, frameRateDescription):
	if wavefile.isBWFFile == True:
		dataDict = {}	
		dataDict["MASTER_SPEED"] 						= frameRateDescriptionDictionary(frameRateDescription)
		dataDict["CURRENT_SPEED"] 						= frameRateDescriptionDictionary(frameRateDescription)
		dataDict["TIMECODE_RATE"] 						= frameRateDescriptionDictionary(frameRateDescription)
		dataDict["TIMECODE_FLAG"] 						= "DF" if isDropFrame == True else "NDF"
		dataDict["FILE_SAMPLE_RATE"]					= str(wavefile.numberOfSamplesPerSecond())
		dataDict["AUDIO_BIT_DEPTH"] 					= str(wavefile.numberOfBitsPerSample())
		dataDict["DIGITIZER_SAMPLE_RATE"] 				= str(wavefile.numberOfSamplesPerSecond())
		dataDict["TIMESTAMP_SAMPLES_SINCE_MIDNIGHT_HI"] = str(wavefile.timeStampReferenceHigh())
		dataDict["TIMESTAMP_SAMPLES_SINCE_MIDNIGHT_LO"] = str(wavefile.timeStampReferenceLow())
		dataDict["TIMESTAMP_SAMPLE_RATE"] 				= str(wavefile.numberOfSamplesPerSecond())
		return dataDict
	else:
		return None

def addiXMLToWaveFile(wavefile, xmlstring):

	xmlByteArray = bytearray(xmlstring)

	if len(xmlByteArray) % 2 != 0:
		xmlByteArray.append(0)

	chunkToAdd = {'chunkSize':len(xmlByteArray), 'chunkName':bytearray("iXML"), 'chunkData':xmlByteArray}
	wavefile.addChunkAndUpdateSize(chunkToAdd)	

def xmlStringForWaveFile(wavefile, isDropFrame, frameRateString, suggestedTrackLayoutDictionary):
	if wavefile.isBWFFile == False:
		print "File is not a BWF File"
		return

	root = Element('BWFXML')
	nextElement = Element("IXML_VERSION")
	nextElement.text = "1.52"
	root.append(nextElement)

	startElements = ["PROJECT", "SCENE", "TAKE", "TAPE", "CIRCLED", "NO_GOOD", "FALSE_START", "WILD_TRACK", "FILE_UID"]

	for nextTag in startElements:
		nextElement = Element(nextTag)
		nextElement.text = "Unused"
		root.append(nextElement)

	masterSpeedElement = Element("SPEED")
	root.append(masterSpeedElement)	

	speedElements = []
	speedElements.extend(["MASTER_SPEED", "CURRENT_SPEED", "TIMECODE_FLAG", "TIMECODE_RATE", "FILE_SAMPLE_RATE"])
	speedElements.extend(["AUDIO_BIT_DEPTH", "DIGITIZER_SAMPLE_RATE", "TIMESTAMP_SAMPLES_SINCE_MIDNIGHT_HI"])
	speedElements.extend(["TIMESTAMP_SAMPLES_SINCE_MIDNIGHT_LO", "TIMESTAMP_SAMPLE_RATE"])

	print frameRateString, isDropFrame
	speedDictionary = speedAttributeDictionaryForWavefile(wavefile, isDropFrame, frameRateString)

	for nextTag in speedElements:
		nextElement = Element(nextTag)
		nextElement.text = speedDictionary[nextTag]
		masterSpeedElement.append(nextElement)

	nextElement = Element("NOTE")
	nextElement.text = "Unused"
	masterSpeedElement.append(nextElement)

	trackCountElement = Element("TRACK_LIST")
	root.append(trackCountElement)	

	nextElement = Element("TRACK_COUNT")
	nextElement.text = str(wavefile.numberOfChannels())
	trackCountElement.append(nextElement)

	tracknames = []
	trackFunctions = []

	try:
		suggestedTrackNameLayoutArray = suggestedTrackLayoutDictionary['suggestedTrackNameLayoutArray']
		suggestedTrackFunctionLayoutArray = suggestedTrackLayoutDictionary['suggestedTrackFunctionLayoutArray']
	except:
		suggestedTrackNameLayoutArray = []

	if len(suggestedTrackNameLayoutArray) == 0:
		for track in range(1, wavefile.numberOfChannels()+1):
			nextName = "Track %d" % track
			nextFunction = "Generic_%d" % track
			tracknames.append(nextName)
			trackFunctions.append(nextFunction)

	elif len(suggestedTrackNameLayoutArray) > wavefile.numberOfChannels():
		for track in range(0, wavefile.numberOfChannels()):
			nextName = suggestedTrackNameLayoutArray[track]
			nextFunction = suggestedTrackFunctionLayoutArray[track]
			tracknames.append(nextName)
			trackFunctions.append(nextFunction)

	elif len(suggestedTrackNameLayoutArray) < wavefile.numberOfChannels():

		for track in range(0, len(suggestedTrackNameLayoutArray)):
			nextName = suggestedTrackNameLayoutArray[track]
			nextFunction = suggestedTrackFunctionLayoutArray[track]
			tracknames.append(nextName)
			trackFunctions.append(nextFunction)

		for track in range(len(suggestedTrackNameLayoutArray), wavefile.numberOfChannels()+1):
			nextName = "Track %d" % track
			nextFunction = "Generic_%d" % track
			tracknames.append(nextName)
			trackFunctions.append(nextFunction)
	else:

		for track in range(0, len(suggestedTrackNameLayoutArray)):
			nextName = suggestedTrackNameLayoutArray[track]
			nextFunction = suggestedTrackFunctionLayoutArray[track]
			tracknames.append(nextName)
			trackFunctions.append(nextFunction)

	for track in range(0,wavefile.numberOfChannels()):
		nextElement = Element("TRACK")
		trackCountElement.append(nextElement)
		subElement = Element("CHANNEL_INDEX")
		subElement.text = str(track+1)
		nextElement.append(subElement)
		subElement = Element("INTERLEAVE_INDEX")
		subElement.text = str(track+1)
		nextElement.append(subElement)
		subElement = Element("NAME")
		subElement.text = tracknames[track]
		nextElement.append(subElement)
		subElement = Element("FUNCTION")
		subElement.text = trackFunctions[track]
		nextElement.append(subElement)

	bextElement = Element("BEXT")
	root.append(bextElement)

	bextDataDict = bextXMLDataDictFromWaveFile(wavefile);
	bextKeys = [] 
	bextKeys.extend(["BWF_DESCRIPTION", "BWF_ORIGINATOR", "BWF_ORIGINATOR_REFERENCE"])
	bextKeys.extend(["BWF_ORIGINATION_DATE", "BWF_ORIGINATION_TIME"])
	bextKeys.extend(["BWF_TIME_REFERENCE_LOW", "BWF_TIME_REFERENCE_HIGH", "BWF_VERSION", "BWF_UMID"])
	bextKeys.extend(["BWF_RESERVED", "BWF_CODING_HISTORY"])

	for key in bextKeys:
		nextElement = Element(key)
		nextElement.text =  str(bextDataDict[key])
		bextElement.append(nextElement)


	xmlheader = '<?xml version="1.0" encoding="UTF-8"?>'
	xmlstr = xmlheader + tostring(root, 'utf-8', 'xml')
	return xmlstr


def test():

	try:
		filename = sys.argv[1]
	except:
		print "No file was specified"
		return

	if os.path.exists(filename):
		wavefile 	= PCWaveFile(filename)

		suggestedTrackLayoutDictionary = {}

		xmlstring 	= xmlStringForWaveFile(wavefile, True, "2997", suggestedTrackLayoutDictionary)
		# addiXMLToWaveFile(wavefile, xmlstring)
		print xmlstring
	else:
		print "file does not exist:", filename

if __name__ == '__main__':
	
	test()

