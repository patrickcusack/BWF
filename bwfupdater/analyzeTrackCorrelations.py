import os
import sys
import datetime
import logging
import numpy as np
from pcwavefile import PCWaveFile
from pcwavefilefunctions import listOfTimeCodeValuesForFile
from runningtotalscounter import RunningTotalCounter
from byteconversion import les24toles32Value

def analyzeTrackCorrelations(filePath):
	wavefile = None

	if os.path.exists(filePath):
		wavefile = PCWaveFile(filePath)
	else:
		return

	if wavefile == None or wavefile.isValidWaveFile() == False:
		return {"status":"fail", "resultString":"file is not a wavefile", "layout":"Unknown"} 

	sampleRate = wavefile.fmtChunkInfoDict['nSamplesPerSec']
	channelByteWidth = wavefile.fmtChunkInfoDict['wBitsPerSample'] / 8
	bitsPerSample = wavefile.fmtChunkInfoDict['wBitsPerSample']
	numberOfChannels = wavefile.fmtChunkInfoDict['nChannels']
	packetByteWidth = channelByteWidth * numberOfChannels

	if numberOfChannels != 6:
		if numberOfChannels == 2:
			return {"status":"pass", "resultString":"File contains {} audio channels".format(numberOfChannels), "layout":"STEREO"}
		else:
			return {"status":"pass", "resultString":"File contains {} audio channels".format(numberOfChannels), "layout":"Unknown"} 	 

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

		blockWidthInSeconds = 1
		samplesToReadBlockSize = (sampleRate * blockWidthInSeconds)/2
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
				analysis = {}
				for i in range(0,numberOfChannels):
					analysis[str(i)] = []

				# read the file or current analysis into memory and sum all of the samples and raise to the 2nd pow
				if shouldReadEntireFile == True or (initialAnalyses % analysisSpacing == 0):
					for i in range(0, bytesToRead, packetByteWidth):
						subdata = data[i:(i+packetByteWidth)]
						for chPos in range(0, numberOfChannels):
							trackoffset = chPos * channelByteWidth
							extendedValue = les24toles32Value(''.join(subdata[trackoffset:trackoffset+channelByteWidth]))
							extendedValue = int(((1.0 * extendedValue) / constantBitDepth24) * constantBitDepth16)
							analysis[str(chPos)].append(extendedValue)

					maxValue = 0
					track = 0
					srcTrack = '0'
					for i in [0,1,2,3,4,5]:
						if int(srcTrack) == i:
							continue
						result = np.cov(analysis[srcTrack], analysis[str(i)])[0,1]
						if result > maxValue:
							maxValue = result
							track = i

					print srcTrack, "matches", track, "with", maxValue
					

				initialAnalyses += 1

			else:
				data = f.read(packetByteWidth * numberOfSamplesRemaining)
				numberOfSamplesRemaining = 0

		return {"OK":"OK"}


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
		    	print analyzeTrackCorrelations(fullpath)
	else:
		print analyzeTrackCorrelations(filePath)

if __name__ == '__main__':
	main()
