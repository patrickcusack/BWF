import sys
import os
from pcwavefile import PCWaveFile
import pctimecode

def timeCodeDisplayTest(sampleRate=48000):
	try:
		filename = sys.argv[1]
		if os.path.exists(filename):
			wavefile = PCWaveFile(filename)
			print wavefile.filePath
			print "23.976\t\t", pctimecode.convertUnsignedLongLongToTimeCode(wavefile.timestamp, sampleRate*1.001, 24)
			print "24\t\t", pctimecode.convertUnsignedLongLongToTimeCode(wavefile.timestamp, sampleRate, 24)
			print "25\t\t", pctimecode.convertUnsignedLongLongToTimeCode(wavefile.timestamp, sampleRate, 25)
			print "29.97\t\t", pctimecode.convertUnsignedLongLongToTimeCode(wavefile.timestamp, sampleRate*1.001, 30)
			print "30\t\t", pctimecode.convertUnsignedLongLongToTimeCode(wavefile.timestamp, sampleRate, 30)	
			print wavefile.regnChunkInfoDict
			print wavefile.timestamp

		else:
			print "The file",filename,"doesn't exist"
	except:
		print "No file was passed in as a variable"

def listOfTimeCodeValuesForFile(fullpath):
	wavefile = PCWaveFile(fullpath)
	if wavefile.isValidWaveFile() == False:
		print 'File is not valid'
		return

	tcList = []
	sampleRate = wavefile.fmtChunkInfoDict['nSamplesPerSec']
	tcList.append(wavefile.timestamp)
	tcList.append(pctimecode.convertUnsignedLongLongToTimeCode(wavefile.timestamp, sampleRate*1.001, 24)) 	#23976
	tcList.append(pctimecode.convertUnsignedLongLongToTimeCode(wavefile.timestamp, sampleRate, 24))			#24
	tcList.append(pctimecode.convertUnsignedLongLongToTimeCode(wavefile.timestamp, sampleRate, 25))			#25
	tcList.append(pctimecode.convertUnsignedLongLongToTimeCode(wavefile.timestamp, sampleRate*1.001, 30)) 	#2997
	tcList.append(pctimecode.convertUnsignedLongLongToTimeCode(wavefile.timestamp, sampleRate, 30))			#30	
	return tcList	

def clearIXML():
	try:
		filename = sys.argv[1]
		if os.path.exists(filename):
			wavefile = PCWaveFile(filename)
			wavefile.clearIXMLChunk()
		else:
			print "The file",filename,"doesn't exist"
	except:
		print "No file was passed in as a variable"

def infoTest():
	try:
		filename = sys.argv[1]
		if os.path.exists(filename):
			wavefile = PCWaveFile(filename)
			wavefile.info()
		else:
			print "The file",filename,"doesn't exist"
	except:
		print "No file was passed in as a variable"	

def showNonStandardChunks():
	filePath = None
	try:
		filePath = sys.argv[1]
	except Exception:
		print "No file specified"
		return

	if os.path.isdir(filePath):
		for path, dirs, files in os.walk(filePath):
		    for name in files:
		    	fullpath = os.path.join(path, name)
		    	wavefile = PCWaveFile(fullpath)
		    	for chunk in wavefile.allChunks():
		    		if chunk['chunkName'] in ['minf','elm1', 'regn','umid','DGDA']:
		    			print chunk
		    	print "\n"
	else:
		wavefile = PCWaveFile(filePath)
		for chunk in wavefile.allChunks():
			if chunk['chunkName'] in ['minf','elm1', 'regn','umid','DGDA']:
				print chunk

def showNonStandardChunks():
	filePath = None
	try:
		filePath = sys.argv[1]
	except Exception:
		print "No file specified"
		return

	if os.path.isdir(filePath):
		for path, dirs, files in os.walk(filePath):
		    for name in files:
		    	fullpath = os.path.join(path, name)
		    	wavefile = PCWaveFile(fullpath)
		    	for chunk in wavefile.allChunks():
		    		if chunk['chunkName'] in ['minf','elm1', 'regn','umid','DGDA']:
		    			print chunk
		    	print "\n"
	else:
		wavefile = PCWaveFile(filePath)
		for chunk in wavefile.allChunks():
			if chunk['chunkName'] in ['minf','elm1', 'regn','umid','DGDA']:
				print chunk				

def clearChunkWithName(name):
	filePath = None
	try:
		filePath = sys.argv[1]
	except Exception:
		print "No file specified"
		return

	if os.path.isdir(filePath):
		for path, dirs, files in os.walk(filePath):
		    for name in files:
		    	fullpath = os.path.join(path, name)
		    	wavefile = PCWaveFile(fullpath)
		    	wavefile.clearChunk(name)
	else:
		wavefile = PCWaveFile(filePath)
		wavefile.clearChunk(name)

def formatInformationForFile(wavefile):
	info = {}
	info['bitDepth'] = wavefile.numberOfBitsPerSample()
	info['sampleRate'] = wavefile.numberOfSamplesPerSecond()
	info['bextChunk'] = True if wavefile.hasBextChunk() else False
	info['timeStamp'] = wavefile.timestamp
	info['regnChunk'] = True if wavefile.hasBextChunk() else False
	if wavefile.hasRegnChunk() == True:
		info['regnChunkUserTimeStamp'] = wavefile.regnChunkInfoDict['userTimeStamp']
		info['regnChunkOriginalTimeStamp'] = wavefile.regnChunkInfoDict['originalTimeStamp']
	info['channelCount'] = wavefile.numberOfChannels()

	print info


def examine():
	filePath = None
	try:
		filePath = sys.argv[1]
	except Exception:
		print "No file specified"
		return

	if os.path.isdir(filePath):
		for path, dirs, files in os.walk(filePath):
		    for name in files:
		    	fullpath = os.path.join(path, name)
		    	wavefile = PCWaveFile(fullpath)
		    	formatInformationForFile(wavefile)
	else:
		wavefile = PCWaveFile(filePath)
		formatInformationForFile(wavefile)	

if __name__ == '__main__':
	# timeCodeDisplayTest(48000)
	# clearIXML()
	# showNonStandardChunks()
	# clearChunkWithName('regn')
	# infoTest()
	examine()