import sys
import os
from pcwavefile import PCWaveFile
from analyzefilelevels import analyzeLevels
from toneanalyzer import analyzeTwoPopAlt, analyzeHeadAlt, analyzeTwoPopInEighths
from pctimecode import convertUnsignedLongLongToTimeCode, onePercentPullUp
from serializedata import writeDataToFile
import json

def prettyPrintJSON(data):
	return json.dumps(data, sort_keys = True, indent=4, separators=(',', ': '))

def prettyTimeCode2398(timeStamp, sampleRate):
	pulledUpSampleRate = onePercentPullUp(sampleRate)
	return convertUnsignedLongLongToTimeCode(timeStamp, pulledUpSampleRate, 24)

def addStatusToInformation(info):
	
	errors 		= []
	warnings 	= []

	if info['bitDepth'] != 24:
		errors.append('The file bitDepth is {} bits. It should be 24 bits.'.format(info['bitDepth']))
	
	if info['sampleRate'] != 48000:
		errors.append('The file sampleRate is {}. It should be 48kHz.'.format(info['sampleRate']))
	
	if info['bextChunk'] == False:
		errors.append('The file does NOT contain a BEXT chunk.')
	
	if info['timeStamp'] != 165765600:
		correctStartTimeTC = prettyTimeCode2398(165765600, info['sampleRate'])
		fileTimeStampTC = prettyTimeCode2398(info['timeStamp'], info['sampleRate'])
		errors.append('The file timestamp is {} or {}. It should be 165765600 or {}'.format(info['timeStamp'], fileTimeStampTC, correctStartTimeTC))
	
	if info['fileLevels']['layout'] not in ['SMPTE', 'STEREO', 'MONO', 'MULTI-MONO']:
		errors.append('The file has the following layout: {}.'.format(info['fileLevels']['layout']))
	
	if info['headTones']['status'] != 'pass':
		errors.append(info['headTones']['resultString'])
 
 	print json.dumps(info)

	if info['headTones']['warningString'] != "":
		warnings.append(info['headTones']['warningString'])

	if info['pops']['status'] != 'pass':
		errors.append(info['pops']['resultString'])
	
	if info['pops']['warningString'] != "":
		warnings.append(info['pops']['warningString'])

	if len(errors) > 0:
		info['result'] = "fail"
		info['errors'] = errors
	else:
		info['result'] = "success"
		info['errors'] = ['No Errors',]

	if len(warnings) > 0:
		info['warnings'] = warnings
	else:
		info['warnings'] = ['No Warnings',]	

	return info

def formatInformationForFile(filePath):
	wavefile = PCWaveFile(filePath)

	if wavefile == None or wavefile.isValidWaveFile() == False:
		badInfo = {}
		badInfo["fileName"] = os.path.basename(filePath)
		badInfo["fullPath"] = filePath
		badInfo["bitDepth"] = 0
		badInfo["sampleRate"] = 0
		badInfo["bextChunk"] = False
		badInfo["timeStamp"] = 0
		badInfo["timeStampTC"] = "00:00:00:00"
		badInfo["regnChunk"] = False
		badInfo["channelCount"] = 0
		badInfo["status"] = 'fail'
		badInfo["errors"] = ["{} is not a wave file.".format(os.path.basename(filePath)),]
		badInfo['fileLevels'] = {'status':'fail','layout':'unknown', "warningString":""}
		badInfo['headTones'] = {'status':'fail', 'resultString':'Unable to analyze head tones on account of invalid format.', "warningString":""}
		badInfo['pops'] = {'status':'fail', 'resultString':'Unable to analyze pops on account of invalid format.', "warningString":""}

		return badInfo

	info = {}
	info['fileName'] 		= os.path.basename(filePath)
	info['fullPath'] 		= filePath
	info['bitDepth'] 		= wavefile.numberOfBitsPerSample()
	info['sampleRate']		= wavefile.numberOfSamplesPerSecond()
	info['bextChunk'] 		= True if wavefile.hasBextChunk() else False
	info['timeStamp'] 		= wavefile.timestamp
	info['timeStampTC']		= prettyTimeCode2398(wavefile.timestamp, info['sampleRate']) 
	info['regnChunk'] 		= True if wavefile.hasBextChunk() else False
	
	if wavefile.hasRegnChunk() == True:
		info['regnChunkUserTimeStamp'] = wavefile.regnChunkInfoDict['userTimeStamp']
		info['regnChunkOriginalTimeStamp'] = wavefile.regnChunkInfoDict['originalTimeStamp']
	info['channelCount']	= wavefile.numberOfChannels()
	
	if info['bitDepth'] != 24 or info['sampleRate'] != 48000:
		info['fileLevels'] 		= {'status':'fail','layout':'unknown', "warningString":""}
		info['headTones'] 		= {'status':'fail', 'resultString':'Unable to analyze head tones on account of invalid format.', "warningString":""}
		info['pops'] 			= {'status':'fail', 'resultString':'Unable to analyze pops on account of invalid format.', "warningString":""}
	else:
		info['fileLevels'] 		= analyzeLevels(filePath)
		info['headTones'] 		= analyzeHeadAlt(filePath)
		info['pops'] 			= analyzeTwoPopInEighths(filePath)

	return addStatusToInformation(info)

def multiChannelBWFFileAnalysis(filePath):
	return formatInformationForFile(filePath)

def main():
	filePath = None
	results = []
	try:
		filePath = sys.argv[1]
	except Exception:
		print "No file specified"
		return

	if os.path.isdir(filePath):
		for path, dirs, files in os.walk(filePath):
		    for name in files:
		    	fullpath = os.path.join(path, name)
		    	results.append(formatInformationForFile(fullpath))
	else:
		wavefile = PCWaveFile(filePath)
		results.append(formatInformationForFile(filePath))

	#display the results to the screen in case of single file
	if os.path.isdir(filePath):
		resultFile = os.path.join(filePath, 'resultFile.json')
		writeDataToFile(resultFile, prettyPrintJSON({"results":results}))
	else:
		print prettyPrintJSON({"results":results})

if __name__ == '__main__':
	main()