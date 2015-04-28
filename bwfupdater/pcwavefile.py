
import sys
import struct
import binascii
import os

class PCWaveFile:
	'class for examining wave files'
	'chunkName is the 4 letter code for the chunk'
	'size is the length of the following data'
	'position is the location in the file where the data starts'

	WAVE_FORMAT_PCM 					= 0x0001
	WAVE_FORMAT_MPEG 					= 0x0050
	WAVE_FORMAT_EXTENSIBLE 				= 0xFFFE

	SPEAKER_FRONT_LEFT                 	= 0x00000001
	SPEAKER_FRONT_RIGHT                 = 0x00000002
	SPEAKER_FRONT_CENTER                = 0x00000004
	SPEAKER_LOW_FREQUENCY               = 0x00000008
	SPEAKER_BACK_LEFT                   = 0x00000010
	SPEAKER_BACK_RIGHT                  = 0x00000020
	SPEAKER_FRONT_LEFT_OF_CENTER        = 0x00000040
	SPEAKER_FRONT_RIGHT_OF_CENTER       = 0x00000080
	SPEAKER_BACK_CENTER                 = 0x00000100
	SPEAKER_SIDE_LEFT                   = 0x00000200
	SPEAKER_SIDE_RIGHT                  = 0x00000400
	SPEAKER_TOP_CENTER                  = 0x00000800
	SPEAKER_TOP_FRONT_LEFT              = 0x00001000
	SPEAKER_TOP_FRONT_CENTER            = 0x00002000
	SPEAKER_TOP_FRONT_RIGHT             = 0x00004000
	SPEAKER_TOP_BACK_LEFT               = 0x00008000
	SPEAKER_TOP_BACK_CENTER             = 0x00010000
	SPEAKER_TOP_BACK_RIGHT              = 0x00020000
	SPEAKER_ALL                         = 0x80000000

	SPEAKER_STEREO_LEFT					= 0x20000000
	SPEAKER_STEREO_RIGHT				= 0x40000000

	#not presently used
	SPEAKER_BITSTREAM_1_LEFT            = 0x00800000
	SPEAKER_BITSTREAM_1_RIGHT           = 0x01000000
	SPEAKER_BITSTREAM_2_LEFT            = 0x02000000
	SPEAKER_BITSTREAM_2_RIGHT           = 0x04000000

	speakerDict = {}
	speakerDict["SPEAKER_FRONT_LEFT"] = SPEAKER_FRONT_LEFT
	speakerDict["SPEAKER_FRONT_RIGHT"] = SPEAKER_FRONT_RIGHT
	speakerDict["SPEAKER_FRONT_CENTER"] = SPEAKER_FRONT_CENTER
	speakerDict["SPEAKER_LOW_FREQUENCY"] = SPEAKER_LOW_FREQUENCY
	speakerDict["SPEAKER_BACK_LEFT"] = SPEAKER_BACK_LEFT
	speakerDict["SPEAKER_BACK_RIGHT"] = SPEAKER_BACK_RIGHT
	speakerDict["SPEAKER_FRONT_LEFT_OF_CENTER"] = SPEAKER_FRONT_LEFT_OF_CENTER
	speakerDict["SPEAKER_FRONT_RIGHT_OF_CENTER"] = SPEAKER_FRONT_RIGHT_OF_CENTER
	speakerDict["SPEAKER_BACK_CENTER"] = SPEAKER_BACK_CENTER
	speakerDict["SPEAKER_SIDE_LEFT"] = SPEAKER_SIDE_LEFT
	speakerDict["SPEAKER_SIDE_RIGHT"] = SPEAKER_SIDE_RIGHT
	speakerDict["SPEAKER_TOP_CENTER"] = SPEAKER_TOP_CENTER
	speakerDict["SPEAKER_TOP_FRONT_LEFT"] = SPEAKER_TOP_FRONT_LEFT
	speakerDict["SPEAKER_TOP_FRONT_CENTER"] = SPEAKER_TOP_FRONT_CENTER
	speakerDict["SPEAKER_TOP_FRONT_RIGHT"] = SPEAKER_TOP_FRONT_RIGHT
	speakerDict["SPEAKER_TOP_BACK_LEFT"] = SPEAKER_TOP_BACK_LEFT
	speakerDict["SPEAKER_TOP_BACK_CENTER"] = SPEAKER_TOP_BACK_CENTER
	speakerDict["SPEAKER_TOP_BACK_RIGHT"] = SPEAKER_TOP_BACK_RIGHT
	speakerDict["SPEAKER_ALL"] = SPEAKER_ALL
	speakerDict["SPEAKER_STEREO_LEFT"] = SPEAKER_STEREO_LEFT
	speakerDict["SPEAKER_STEREO_RIGHT"] = SPEAKER_STEREO_RIGHT
	speakerDict["SPEAKER_BITSTREAM_1_LEFT"] = SPEAKER_BITSTREAM_1_LEFT
	speakerDict["SPEAKER_BITSTREAM_1_RIGHT"] = SPEAKER_BITSTREAM_1_RIGHT
	speakerDict["SPEAKER_BITSTREAM_2_LEFT"]  = SPEAKER_BITSTREAM_2_LEFT
	speakerDict["SPEAKER_BITSTREAM_2_RIGHT"] = SPEAKER_BITSTREAM_2_RIGHT

	def __init__(self, filename):

		self.filePath = filename
		self.isWaveFile = False
		self.isBWFFile = False
		self.isWide = False
		self.numberOfChunks = 0
		self.chunks = []
		self.wideChunkSizes = []
		self.bextChunkInfoDict = {}
		self.fmtChunkInfoDict = {}
		self.regnChunkInfoDict = {}
		self.sampleCount = 0
		self.timestamp = 0L

		if os.path.exists(filename) == False:
			return

		self.parseFile(filename)

	def parseFile(self, filename):
		self.fileSize = os.path.getsize(filename)

		try:
			file = open(filename, 'rb')
			riff = file.read(4);
			file.seek(8)
			wave = file.read(4);

			# should actually check for fmt and data before saying that this file is a wave file
			if (riff == "RIFF" or riff == "RF64") and (wave == "WAVE"):

				if riff == "RF64":
					self.isWide = True
					self.parseDataSizeChunk(filename)
				
				self.parseChunks(filename)

				if self.hasFmt_Chunk():
					self.isWaveFile = True
					self.parseFmtChunk(filename)

				if self.hasBextChunk():
					self.parseBextChunk(filename)
					self.isBWFFile = True

				if self.hasRegnChunk():
					self.parseRegnChunk(filename)

		finally:
			file.close


	def info(self):
		if self.isValidWaveFile() == True:
			print "The file is valid and is", "wide64" if self.isWide else "not wide64"
			print "-----------------------------------------------------"
			print self.bextChunkInfoDict
			print self.fmtChunkInfoDict
			print self.wideChunkSizes
			print self.chunks
		else:
			print "The file does not appear to be a wave file"

	def parseDataSizeChunk(self, filePath):
		with open(filePath, 'rb') as f:
			f.seek(16)
			dsChunkSize = struct.unpack('<I', f.read(4))[0]
			rf64ChunkSize = struct.unpack('<Q', f.read(8))[0]
			self.wideChunkSizes.append({"chunkSize":rf64ChunkSize, "chunkName":"RF64"})

			dataChunkSize = struct.unpack('<Q', f.read(8))[0]
			self.wideChunkSizes.append({"chunkSize":dataChunkSize, "chunkName":"data"})
			
			sampleCountSize = struct.unpack('<Q', f.read(8))[0]
			self.sampleCount = sampleCountSize
			
			tableLength = struct.unpack('<I', f.read(4))[0]
			# file position is at head of table so we can iterate through the other chunks that exceed 32 bits
			for i in range(0, tableLength):
				chunkName = f.read(4)
				chunkSize = struct.unpack('<Q', f.read(8))[0]
				self.wideChunkSizes.append({"chunkSize":chunkSize, "chunkName":chunkName})

	def wideChunkSizeForChunkName(self, chunkName):
		for chunk in enumerate(self.wideChunkSizes):
			if chunk[1]["chunkName"] == chunkName:
				return chunk[1]["chunkSize"]

	def parseChunks(self, filePath):
		currentFilePosition = 12

		with open(filePath, 'rb') as f:
			f.seek(currentFilePosition)
			fileLength = self.fileSize - 1;
			chunkName = f.read(4)

			while (chunkName != b"" and currentFilePosition < fileLength):
				chunkSize = struct.unpack('<I', f.read(4))[0]
				if chunkSize == 0xFFFFFFFF: #its a wide chunk
					chunkSize = self.wideChunkSizeForChunkName(chunkName)

				nextChunk = {"chunkName":chunkName, "chunkSize":chunkSize, "chunkPosition":f.tell()}
				self.chunks.append(nextChunk)
				currentFilePosition = (f.tell() + chunkSize)
				f.seek(currentFilePosition)
				chunkName = f.read(4)

	def isValidWaveFile(self):
		return self.isWaveFile				
		
	def allChunks(self):
		return self.chunks

	def hasFmt_Chunk(self):
		found = False
		for element in self.chunks:
			if 'fmt ' in element.values():
				found = True
		return found	

	def getFmtChunkDict(self):
		return self.fmtChunkInfoDict

	def getFmtChunk(self):
		for element in self.chunks:
			if 'fmt ' in element.values():
				return element

	def getDataChunk(self):
		for element in self.chunks:
			if 'data' in element.values():
				return element			

	def parseFmtChunk(self, filePath):
		with open(filePath, 'rb') as f:
			f.seek(self.getFmtChunk()['chunkPosition'])
			self.fmtChunkInfoDict['wFormatTag'] 		= struct.unpack('<H', f.read(2))[0]
			self.fmtChunkInfoDict['nChannels'] 			= struct.unpack('<H', f.read(2))[0]
			self.fmtChunkInfoDict['nSamplesPerSec'] 	= struct.unpack('<I', f.read(4))[0]
			self.fmtChunkInfoDict['nAvgBytesPerSec'] 	= struct.unpack('<I', f.read(4))[0]
			self.fmtChunkInfoDict['nBlockAlign'] 		= struct.unpack('<H', f.read(2))[0]
			self.fmtChunkInfoDict['wBitsPerSample'] 	= struct.unpack('<H', f.read(2))[0]
			self.fmtChunkInfoDict['cbSize'] 			= struct.unpack('<H', f.read(2))[0]

			if (self.fmtChunkInfoDict['wFormatTag'] == PCWaveFile.WAVE_FORMAT_EXTENSIBLE):
				self.fmtChunkInfoDict['validBitsPerSample'] = struct.unpack('<H', f.read(2))[0]
				self.fmtChunkInfoDict['channelMask'] 		= struct.unpack('<I', f.read(4))[0] 
				self.fmtChunkInfoDict['guidData1']			= struct.unpack('<I', f.read(4))[0]
				self.fmtChunkInfoDict['guidData2']			= struct.unpack('<H', f.read(2))[0]
				self.fmtChunkInfoDict['guidData3']			= struct.unpack('<H', f.read(2))[0] 
				self.fmtChunkInfoDict['guidData4']			= struct.unpack('<I', f.read(4))[0]
				self.fmtChunkInfoDict['guidData5']			= struct.unpack('<I', f.read(4))[0]
				self.fmtChunkInfoDict['channelMaskDescription'] = self.parseChannelMask(self.fmtChunkInfoDict['channelMask'])

	def parseRegnChunk(self, filePath):
		with open(filePath, 'rb') as f:
			f.seek(self.getRegnChunk()['chunkPosition']+44)
			self.regnChunkInfoDict['userTimeStamp'] 			= struct.unpack('<Q', f.read(8))[0]
			self.regnChunkInfoDict['originalTimeStamp'] 		= struct.unpack('<Q', f.read(8))[0]

	def getLastChunck(self):
		return self.chunks[-1]

	def getds64Chunk(self):
		for element in self.chunks:
			if 'ds64' in element.values():
				return element	

	def hasRegnChunk(self):
		found = False
		for element in self.chunks:
			if 'regn' in element.values():
				found = True
		return found

	def getRegnChunk(self):
		for element in self.chunks:
			if 'regn' in element.values():
				return element	

	def hasIXMLChunk(self):
		found = False
		for element in self.chunks:
			if 'iXML' in element.values():
				found = True
		return found			

	def getIXMLChunk(self):
		for element in self.chunks:
			if 'iXML' in element.values():
				return element		

	def hasBextChunk(self):
		found = False
		for element in self.chunks:
			if 'bext' in element.values():
				found = True
		return found

	def getBextChunkDict(self):
		return self.bextChunkInfoDict

	def getBextChunk(self):
		for element in self.chunks:
			if 'bext' in element.values():
				return element	

	def parseBextChunk(self, filePath):
		with open(filePath, 'rb') as f:
			f.seek(self.getBextChunk()['chunkPosition'])

			self.bextChunkInfoDict["bwDescription"] 		= f.read(256).split('\0')[0]
			self.bextChunkInfoDict["bwOriginator"] 			= f.read(32).split('\0')[0]
			self.bextChunkInfoDict["bwOriginatorReference"] = f.read(32).split('\0')[0]
			self.bextChunkInfoDict["bwOriginationDate"] 	= f.read(10).split('\0')[0]
			self.bextChunkInfoDict["bwOriginationTime"] 	= f.read(8).split('\0')[0]
			self.bextChunkInfoDict["bwTimeReferenceLow"] 	= struct.unpack('<I', f.read(4))[0]
			self.bextChunkInfoDict["bwTimeReferenceHigh"] 	= struct.unpack('<I', f.read(4))[0]
			self.bextChunkInfoDict["bwVersion"] 			= struct.unpack('<H', f.read(2))[0]

			time = struct.pack('II', self.bextChunkInfoDict["bwTimeReferenceLow"], self.bextChunkInfoDict["bwTimeReferenceHigh"])
			self.timestamp = struct.unpack('<Q', time)[0]

			if self.bextChunkInfoDict["bwVersion"] > 0:
				self.bextChunkInfoDict["bwSMPTEUMID"] 			= f.read(64)
				if  self.bextChunkInfoDict["bwVersion"] == 1:
					self.bextChunkInfoDict["bwReserved"] 			= f.read(190)
				elif self.bextChunkInfoDict["bwVersion"] == 2:
					self.bextChunkInfoDict["LoudnessValue"]			= struct.unpack('<H', f.read(2))[0]
					self.bextChunkInfoDict["LoudnessRange"]			= struct.unpack('<H', f.read(2))[0]
					self.bextChunkInfoDict["MaxTruePeakLevel"]		= struct.unpack('<H', f.read(2))[0]
					self.bextChunkInfoDict["MaxMomentaryLoudness"]	= struct.unpack('<H', f.read(2))[0]
					self.bextChunkInfoDict["MaxShortTermLoudness"]	= struct.unpack('<H', f.read(2))[0]
					self.bextChunkInfoDict["bwReserved"] 			= f.read(180)
			else:
				self.bextChunkInfoDict["bwSMPTEUMID"] 			= 0
				self.bextChunkInfoDict["bwReserved"] 			= f.read(254)

			self.bextChunkInfoDict["bwCodingHistory"] 		= f.read(self.getBextChunk()['chunkSize'] - (f.tell() - self.getBextChunk()['chunkPosition'])).split('\0')[0]

	def parseChannelMask(self, channelMask):
		speakerConfigList = []
		for key in PCWaveFile.speakerDict.keys():
			if channelMask & PCWaveFile.speakerDict[key]:
				speakerConfigList.append(key)
		return speakerConfigList

	def addChunkAndUpdateSize(self, chunkData):

		mandatoryKeys = ['chunkSize', 'chunkName', 'chunkData'] 

		for key in mandatoryKeys:
			if key not in chunkData.keys():
				print "ERROR: Invalid ChunkData Passed to addChunkAndUpdateSize"
				return

		with open(self.filePath, 'r+b') as f:
			# add
			lastPosition = self.getLastChunck()['chunkPosition'] + self.getLastChunck()['chunkSize']
			f.seek(lastPosition)
			f.write(chunkData['chunkName'])
			f.write(struct.pack('<I', chunkData['chunkSize']))
			f.write(chunkData['chunkData'])
			# update
			newsize = f.tell()
			if self.isWide == True:
				# go to byte offset 20, should be 20
				f.seek(self.getds64Chunk()['chunkPosition'])
				f.write(struct.pack("<Q", newsize-8))
			else:
				f.seek(4)
			 	f.write(struct.pack("<I", newsize-8))

		# self.parseFile(filename)

	def clearIXMLChunk(self):
		if self.hasIXMLChunk() == False:
			return 

		with open(self.filePath, 'r+b') as f:
			chunkLength = self.getIXMLChunk()['chunkSize']
			chunkPosition = (self.getIXMLChunk()['chunkPosition'])
			f.seek(chunkPosition-8)
			f.write("????")
			f.seek(self.getIXMLChunk()['chunkPosition'])
			for x in range(0, chunkLength):
				f.write(struct.pack('B', 0))

	def clearChunk(self, chunkName):
		chunkToErase = None
		for chunk in self.allChunks():
			if chunk['chunkName'] == chunkName:
				chunkToErase = chunk
		
		if chunkToErase == None:
			return

		with open(self.filePath, 'r+b') as f:
			print 'erasing'
			chunkLength = chunkToErase['chunkSize']
			chunkPosition = chunkToErase['chunkPosition']
			f.seek(chunkPosition-8)
			f.write("????")
			f.seek(chunkToErase['chunkPosition'])
			for x in range(0, chunkLength):
				f.write(struct.pack('B', 0))	

	def setBextTimeReference(self, nLongValue):
		with open(self.filePath, 'r+b') as f:
			timePosition = (self.getBextChunk()['chunkPosition'] + 256 + 32 + 32 + 10 + 8)
			packedTime = struct.pack("<Q", nLongValue)
			f.seek(timePosition)
			f.write(packedTime)

	def setREGNUserTimeStamp(self, nLongValue):
		with open(self.filePath, 'r+b') as f:
			timePosition = (self.getRegnChunk()['chunkPosition'] + 44)
			packedTime = struct.pack("<Q", nLongValue)
			f.seek(timePosition)
			f.write(packedTime)

	def setREGNOriginalTimeStamp(self, nLongValue):
		with open(self.filePath, 'r+b') as f:
			timePosition = (self.getRegnChunk()['chunkPosition'] + 52)
			packedTime = struct.pack("<Q", nLongValue)
			f.seek(timePosition)
			f.write(packedTime)		

	def setTimeReference(self, nLongValue):
		if os.path.exists(self.filePath) == False:
			return "ERROR: Unable To Set Time Reference"

		if self.hasBextChunk() == True:
			self.setBextTimeReference(nLongValue)

		if self.hasRegnChunk() == True:
			self.setREGNUserTimeStamp(nLongValue)
			self.setREGNOriginalTimeStamp(nLongValue)
			
	def numberOfChannels(self):
		return self.fmtChunkInfoDict['nChannels']

	def numberOfSamplesPerSecond(self):
		return self.getFmtChunkDict()["nSamplesPerSec"]

	def numberOfBitsPerSample(self):
		return self.getFmtChunkDict()["wBitsPerSample"]

	def numberOfBytesPerSample(self):
		return self.getFmtChunkDict()["wBitsPerSample"]/8

	def timeStampReferenceHigh(self):
		if self.isBWFFile == True:	
			return self.getBextChunkDict()["bwTimeReferenceHigh"]
		else:
			return 0

	def timeStampReferenceLow(self):
		if self.isBWFFile == True:	
			return self.getBextChunkDict()["bwTimeReferenceLow"]		
		else:
			return 0

def test():

    filePath = None
    try:
        filePath = sys.argv[1]
    except Exception:
        print "No file specified"
        return

    if os.path.isdir(filePath):
        for path, dirs, files in os.walk(filePath):
            for name in files:
				filePath = os.path.join(path, name)
				wavefile = PCWaveFile(filePath)
				wavefile.info()
    else:
		wavefile = PCWaveFile(filePath)
		wavefile.info()

if __name__ == '__main__':
	test()



