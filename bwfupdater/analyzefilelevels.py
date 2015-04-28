import os
import sys
import datetime
import logging
import numpy as np
from pcwavefile import PCWaveFile
from pcwavefilefunctions import listOfTimeCodeValuesForFile
from runningtotalscounter import RunningTotalCounter
from byteconversion import les24toles32Value

def analyzeLevels(filePath):
	wavefile = None

	if os.path.exists(filePath):
		wavefile = PCWaveFile(filePath)
	else:
		return

	if wavefile == None or wavefile.isValidWaveFile() == False:
		return {"status":"fail", "resultString":"file is not a wavefile", "layout":"Unknown", "warningString":""} 

	sampleRate = wavefile.fmtChunkInfoDict['nSamplesPerSec']
	channelByteWidth = wavefile.fmtChunkInfoDict['wBitsPerSample'] / 8
	bitsPerSample = wavefile.fmtChunkInfoDict['wBitsPerSample']
	numberOfChannels = wavefile.fmtChunkInfoDict['nChannels']
	packetByteWidth = channelByteWidth * numberOfChannels

	for title in ['MEHELP']:
		if title.lower() in filePath.lower():
			layout = 'MONO' if numberOfChannels == 1 else 'MULTI-MONO'
			return {"status":"pass", "resultString":"The file contains {} in its file name and will not be analyzed.".format(title), "layout":layout, "warningString":""}

	if numberOfChannels != 6:
		if numberOfChannels == 2:
			return {"status":"pass", "resultString":"File contains {} audio channels".format(numberOfChannels), "layout":"STEREO", "warningString":""}
		else:
			return {"status":"pass", "resultString":"File contains {} audio channels".format(numberOfChannels), "layout":"Unknown", "warningString":""} 	 			

	isSigned = True
	if channelByteWidth == 1:
		isSigned = False

	chunkPosition = wavefile.getDataChunk()['chunkPosition']
	numberOfSamples = wavefile.getDataChunk()['chunkSize'] / packetByteWidth

	#open the file, read through the packets and do a running mean of each track in the file
	#what this does do is ASSUME that the input file is 24 bit signed data, otherwise 16 bit would be signed, but 8 bit wouldn't
	#not that 8 bit is an issue

	with open(filePath, 'rb') as f:
		f.seek(chunkPosition)

		blockWidthInSeconds = 4
		samplesToReadBlockSize = (sampleRate * blockWidthInSeconds)
		numberOfSamplesRemaining = numberOfSamples
		bufferAmount = samplesToReadBlockSize if numberOfSamples > samplesToReadBlockSize else numberOfSamples
		
		totalBlocksInFile = numberOfSamplesRemaining // samplesToReadBlockSize
		shouldReadEntireFile = False
		analysisSpacing = 0
		numberOfAnalyses = 34
		initialAnalyses = 0

		if totalBlocksInFile < (2 * numberOfAnalyses):
			shouldReadEntireFile = True
		else:
			analysisSpacing = totalBlocksInFile / numberOfAnalyses

		startTime = datetime.datetime.now()
		constantBitDepth16 = pow(2,15)
		constantBitDepth24 = pow(2,23)
		#totalsCounter = RunningTotalCounter(pow(2,(bitsPerSample-1)), samplesToReadBlockSize, numberOfChannels)
		totalsCounter = RunningTotalCounter(constantBitDepth16, samplesToReadBlockSize, numberOfChannels)
		# you need to constrain the size of the input as we will be calculating RMS values which require exponential math

		
		while numberOfSamplesRemaining > 0:
			#read a buffer's amount of samples
			if numberOfSamplesRemaining > bufferAmount:

				bytesToRead = packetByteWidth * bufferAmount 
				data = f.read(bytesToRead)
				numberOfSamplesRemaining -= (len(data)/packetByteWidth)

				if len(data) != bytesToRead:
					logging.error("IO Error: bytes returned do not match bytes asked for")

				#read a buffer's amount of samples
				analysis = totalsCounter.emptyAnalysisDictionary()

				# read the file or current analysis into memory and sum all of the samples and raise to the 2nd pow
				if shouldReadEntireFile == True or (initialAnalyses % analysisSpacing == 0):
					for i in range(0, bytesToRead, packetByteWidth):
						subdata = data[i:(i+packetByteWidth)]
						for chPos in range(0, numberOfChannels):
							trackoffset = chPos * channelByteWidth
							extendedValue = les24toles32Value(''.join(subdata[trackoffset:trackoffset+channelByteWidth]))
							extendedValue = int(((1.0 * extendedValue) / constantBitDepth24) * constantBitDepth16)
							analysis[str(chPos)] += (extendedValue**2)

					totalsCounter.addAnalysis(analysis)

				initialAnalyses += 1

			else:
				data = f.read(packetByteWidth * numberOfSamplesRemaining)
				numberOfSamplesRemaining = 0

		return totalsCounter.performAnalysis()


def main():

	logging.basicConfig(filename='bwfexaminer.log',level=logging.DEBUG);

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
		    	print analyzeLevels(fullpath)
	else:
		print analyzeLevels(filePath)

if __name__ == '__main__':
	main()
