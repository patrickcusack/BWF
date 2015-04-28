import math
import operator
import numpy as np
from collections import Counter

class RunningTotalCounter:
	'''
	How this works: iterate through periodic chunks of a file and collect analyses which 
	contain the avergage power for each track averaged across self.numberOfSamples. Once all samples are
	gathered, determine the loudest and quitest track across all of the samples. These should be Center and Sub.
	We assign a degree of probability to each of these measurements. Once those are detected, we examine the first track,
	and determine which track is next highly corelated against
	'''

	def __init__(self, maxSampleValue, numberOfSamples, numberOfTracks):
		self.maxSampleValue = maxSampleValue
		self.numberOfSamples = numberOfSamples
		self.numberOfTracks = numberOfTracks
		self.analyses = []
		self.analysesDB = []
		self.trackOrders = []
		self.interTrackDifferences = []
		self.dictOfRunningAnalyses = {}
	
	def emptyResult(self):
		return { 'analyses':[],
		'loudestTrack':[],
		'quietestTrack':[],
		'layout':'UNKNOWN',
		'LRCorrelation':False,
		'LSRSCorrelation':False, 
		'LRExceedLsRs':False}

	def emptyAnalysisDictionary(self):
		emptyDict = {}
		for i in range(0, self.numberOfTracks):
			emptyDict[str(i)] = 0
		return emptyDict

	def emptyAnalysisArrayDictionary(self):
		emptyDict = {}
		for i in range(0, self.numberOfTracks):
			emptyDict[str(i)] = []
		return emptyDict

	def percentageDifference(self, loudnessSample1, loudnessSample2):
		difference = self.decibelConversion(loudnessSample1) - self.decibelConversion(loudnessSample2)
		if difference == 0:
			return 0
		# return abs(difference) / abs(self.decibelConversion(loudnessSample1) * 1.0)
		return abs(difference)

	def addAnalysis(self, analysis):
		#an analysis contains the sum of numberOfSamples to the 2nd power
		self.analyses.append(analysis)
		#save a copy represented in decibels for calculating track orders and fo pretty display
		analysisDB = self.convertLinearAnalysisToLog(analysis)
		self.analysesDB.append(analysisDB)
		#we are building a list of track orders
		descendingLoudnessTracks = [i[0] for i in self.tracksOrderedByLoudness(analysisDB)][::-1]
		self.trackOrders.append("".join(descendingLoudnessTracks))

	def buildRunningAnalysisDict(self,  analyses):
		runningAnalysisDict = self.emptyAnalysisArrayDictionary()

		count = len(analyses)
		start = 0
		stop = count
		if count > 20:
			start = 0
			stop = count

		#go through every analysis and consolidate each channel into its own array
		for analysis in analyses[start:stop]:
			for chPos in range(0, self.numberOfTracks):
				runningAnalysisDict[str(chPos)].append(analysis[str(chPos)])

		return runningAnalysisDict

	def getLoudestTrack(self, tracks):
		#establish the loudest and lowest tracks, confidence shold be above 50%
		#trackOrders represent the order of tracks from loudest to quietest
		tracksToAnalyze = tracks[2:-3]
		loudestTracks = ["{}".format((elem)[0]) for elem in tracksToAnalyze]
		loudestTrack = Counter(loudestTracks).most_common(1)[0]
		percentage = (loudestTrack[1] * 1.0)/len(tracksToAnalyze) * 100
		return tuple([loudestTrack[0], percentage])

	def getQuietestTrack(self, tracks):
		#establish the loudest and lowest tracks, confidence shold be above 50%
		#trackOrders represent the order of tracks from loudest to quietest
		tracksToAnalyze = tracks[2:-3]
		quietestTracks = ["{}".format((elem)[-1]) for elem in tracksToAnalyze]
		quietestTrack =  Counter(quietestTracks).most_common(1)[0]
		percentage = (quietestTrack[1] * 1.0)/len(tracksToAnalyze) * 100
		return tuple([quietestTrack[0], percentage])

	def doesSourceTrackCorrelateWithDestinationTrack(self, srcTrack, dstTrack, tracksToCheck):
			maxCorr = 0
			track = 0
			for i in tracksToCheck:
				currentCorr = np.corrcoef(self.dictOfRunningAnalyses[str(srcTrack)], self.dictOfRunningAnalyses[str(i)])[0,1]
				if currentCorr > maxCorr:
					maxCorr = currentCorr
					track = i
			if track == dstTrack:
				return True
			else:
				return False

	def trackWithBestCorrelationForTrack(self, srcTrack, tracksToCheck):
			maxCorr = 0
			track = 0
			for i in tracksToCheck:
				currentCorr = np.corrcoef(self.dictOfRunningAnalyses[str(srcTrack)], self.dictOfRunningAnalyses[str(i)])[0,1]
				if currentCorr > maxCorr:
					maxCorr = currentCorr
					track = i
			return track			

	def performAnalysis(self):
		resultDict = self.emptyResult()

		resultDict['analyses'] = self.analysesDB
		#take all of the analyses and sum them together by channel
		self.dictOfRunningAnalyses = self.buildRunningAnalysisDict(self.analyses)

		# we lop off the first two and last two samples as they might be tones or full energy/silence/music
		averagedAnalysis = {}
		for chPos in range(0, self.numberOfTracks):
			averagedAnalysis[str(chPos)] = self.runningAnalysisDecibelRepresentation(self.dictOfRunningAnalyses[str(chPos)][2:-3])
		resultDict['averagedAnalysis'] = averagedAnalysis

		#find the loudest and quitest track tuple (track #, percentage)
		loudestTrack = self.getLoudestTrack(self.trackOrders)
		quietestTrack = self.getQuietestTrack(self.trackOrders)

		resultDict['loudestTrack'] 		= {"trackNumber":loudestTrack[0], "percentage":loudestTrack[1]}
		resultDict['quietestTrack'] 	= {"trackNumber":quietestTrack[0], "percentage":quietestTrack[1]}
		resultDict['layout'] 			= 'Unknown'
		resultDict['LRCorrelation'] 	= False
		resultDict['LSRSCorrelation'] 	= False
		resultDict['LRExceedLsRs']	 	= False

		#If track 2 (0 scale) is the loudest
		#if the quietest track is on 2, then likely SMPTE Layout, but should check the position of the quitest track
		if loudestTrack[0] == '2' and quietestTrack[0] == '3':
			resultDict['layout'] = 'SMPTE'
			
			if self.doesSourceTrackCorrelateWithDestinationTrack(0,1, [1,4,5]):
				resultDict['LRCorrelation'] = True
			else:
				resultDict['LRCorrelation'] = False

			if self.doesSourceTrackCorrelateWithDestinationTrack(4,5, [0,1,5]):
				resultDict['LSRSCorrelation'] 	= True
			else:
				resultDict['LSRSCorrelation'] 	= False

			#refactor to answer the question, is 01 greater than 45
			leftRightSum = np.sum(np.uint64(self.dictOfRunningAnalyses["0"][2:-3])) + np.sum(np.uint64(self.dictOfRunningAnalyses["1"][2:-3]))
			leftSurrRightSurrSum =  np.sum(np.uint64(self.dictOfRunningAnalyses["4"][2:-3])) + np.sum(np.uint64(self.dictOfRunningAnalyses["5"][2:-3]))
			if leftRightSum > leftSurrRightSurrSum:
				resultDict['LRExceedLsRs'] = True
			else:
				resultDict['LRExceedLsRs'] = False

		elif loudestTrack[0] == '2':
			#attempt to establish that it is SMPTE, otherwise just proceed with default behavior which is 'unknown'
			
			leftRightCorr = self.trackWithBestCorrelationForTrack(0, [1,4,5])
			leftSurrRightSurrCorr = self.trackWithBestCorrelationForTrack(4, [0,1,5])

			if leftRightCorr == 1 and leftSurrRightSurrCorr == 5:
				resultDict['LRCorrelation'] 	= True
				resultDict['LSRSCorrelation'] 	= True

				leftRightSum = np.sum(np.uint64(self.dictOfRunningAnalyses["0"][2:-3])) + np.sum(np.uint64(self.dictOfRunningAnalyses["1"][2:-3]))
				leftSurrRightSurrSum =  np.sum(np.uint64(self.dictOfRunningAnalyses["4"][2:-3])) + np.sum(np.uint64(self.dictOfRunningAnalyses["5"][2:-3]))
				if leftRightSum > leftSurrRightSurrSum:
					resultDict['LRExceedLsRs'] = True
				else:
					resultDict['LRExceedLsRs'] = False
				resultDict['layout'] = 'SMPTE'

		#if the quietest track is on 1, then likely FILM Layout, but should check the position of the quitest track
		if loudestTrack[0] == '1':

			if quietestTrack[0] == '5':
				resultDict['layout'] = 'LCRLsRsBM'

				if self.doesSourceTrackCorrelateWithDestinationTrack(0,2, [2,3,4,5]):
					resultDict['LRCorrelation'] = True
				else:
					resultDict['LRCorrelation'] = False

				if self.doesSourceTrackCorrelateWithDestinationTrack(3,4, [0,1,2,4]):
					resultDict['LSRSCorrelation'] 	= True
				else:
					resultDict['LSRSCorrelation'] 	= False

				#refactor to answer the question, is 01 greater than 45
				leftRightSum = np.sum(np.uint64(self.dictOfRunningAnalyses["0"])) + np.sum(np.uint64(self.dictOfRunningAnalyses["2"]))
				leftSurrRightSurrSum =  np.sum(np.uint64(self.dictOfRunningAnalyses["3"])) + np.sum(np.uint64(self.dictOfRunningAnalyses["4"]))
				if leftRightSum > leftSurrRightSurrSum:
					resultDict['LRExceedLsRs'] = True
				else:
					resultDict['LRExceedLsRs'] = False

			if quietestTrack[0] == '4':
				resultDict['layout'] = 'LCRLsBMRs'

				if self.doesSourceTrackCorrelateWithDestinationTrack(0,2, [2,3,5]):
					resultDict['LRCorrelation'] = True
				else:
					resultDict['LRCorrelation'] = False

				if self.doesSourceTrackCorrelateWithDestinationTrack(3,5, [1,2,5]):
					resultDict['LSRSCorrelation'] 	= True
				else:
					resultDict['LSRSCorrelation'] 	= False

				#refactor to answer the question, is 01 greater than 45
				leftRightSum = np.sum(self.dictOfRunningAnalyses["0"][2:-3]) + np.sum(self.dictOfRunningAnalyses["2"][2:-3])
				leftSurrRightSurrSum =  np.sum(self.dictOfRunningAnalyses["3"][2:-3]) + np.sum(self.dictOfRunningAnalyses["5"][2:-3])
				if leftRightSum > leftSurrRightSurrSum:
					resultDict['LRExceedLsRs'] = True
				else:
					resultDict['LRExceedLsRs'] = False
		# else:
		# 	#at this point try and see which tracks match which?
		# 	pass

		return resultDict

	def convertLinearAnalysisToLog(self, analysis):
		outDict = {}
		for key in analysis:
			outDict[key] = self.decibelConversion(analysis[key])
			print outDict[key]
		return outDict

	def tracksOrderedByLoudness(self, analysis):
		track = ""
		sorted_analysis = sorted(analysis.items(), key=operator.itemgetter(1))
		return sorted_analysis

	def displayRunningAnalysis(self, runningAnalysis):
		pass

	def runningAnalysisDecibelRepresentation(self, runningAnalysis):
		length = len(runningAnalysis)
		rms = math.sqrt(np.sum(np.uint64(runningAnalysis))/(self.numberOfSamples*length))
		if rms == 0 or rms == 0.0:
			rms = 0.001
		dbRep = 20 * math.log10(1.0 * rms/(self.maxSampleValue))
		return dbRep	

	def displayAnalysis(self, analysis):
		for chPos in range(0,self.numberOfTracks):
			if analysis[str(chPos)] > 0:
				dbRep = self.decibelConversion(analysis[str(chPos)])
			else:
				dbRep = 0

	def displayInterTrackDifferences(self, analysis):
		tracksByOrder = []
		for chPos in range(0,self.numberOfTracks):
			tracksByOrder.append(analysis[str(chPos)])

		interTrackDifference = {}
		for chPos in range(0, self.numberOfTracks, 2):
			percentageDifference = self.percentageDifference(tracksByOrder[chPos], tracksByOrder[chPos+1])
			interTrackDifference["{}{}".format(chPos, chPos + 1)] = percentageDifference
		self.interTrackDifferences.append(interTrackDifference)

	def displayTracksInOrderOfDescendingLoudness(self, analysis):
		descendingLoudnessTracks = [i[0] for i in self.tracksOrderedByLoudness(analysis)][::-1]

	def decibelConversion(self, loudnessSample):
		rms = math.sqrt(loudnessSample/self.numberOfSamples)
		if rms == 0 or rms == 0.0:
			rms = 0.001
		return 20 * math.log10(1.0 * rms/(self.maxSampleValue))