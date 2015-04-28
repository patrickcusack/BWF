import math
from pctimecode import convertUnsignedLongLongToTimeCode, convertTimeCodeToUnsignedLongLong

class PopDetector(object):
    def __init__(self, divisor=8):
        self.analysisDict = {}
        self.divisor = divisor

    def addAnalysis(self, analysis, channel):
        if str(channel) not in self.analysisDict:
            self.analysisDict[str(channel)] = []
        self.analysisDict[str(channel)].append(analysis)

    def analysisResult(self):
        statusDict = {"status":"pass","resultString":""}
        errors = []

        if len(self.analysisDict.keys()) == 0:
            return statusDict

        for channel in sorted(self.analysisDict.keys()):
            tones = [x for x in self.analysisDict[channel] if x['mainFreq']['dbRep'] > -50.0]
            if not len(tones) >= (self.divisor * 2 - 1):
                statusDict["status"] = 'fail'
                statusDict["resultString"] += "The pop is too small on channel {}.".format(channel)

        return statusDict

class SilenceDetector(object):
    def __init__(self):
        self.analysisDict = {}

    def area(self):
        return "pop area of"

    def addAnalysis(self, analysis, channel):
        if str(channel) not in self.analysisDict:
            self.analysisDict[str(channel)] = []
        self.analysisDict[str(channel)].append(analysis)

    def analysisResult(self):
        statusDict = {"status":"pass","resultString":""}
        errors = []

        if len(self.analysisDict.keys()) == 0:
            return statusDict

        for channel in sorted(self.analysisDict.keys()):
            tones = [x for x in self.analysisDict[channel] if x['mainFreq']['dbRep'] > -70.0]
            
            if len(tones) > 1 and len(tones) < 20:
                errors.append('There appears to be some audible audio signal in the {} track {}.'.format(self.area(),channel))
            if len(tones) > 20:
                errors.append('There appears to be program material in what should be the {} track {}.'.format(self.area(), channel))

        if len(errors) > 0:
            statusDict['status'] = 'fail'
            statusDict['resultString'] = " ".join(errors)

        return statusDict

class HeadSilenceDetector(SilenceDetector):
    def __init__(self):
        SilenceDetector.__init__(self)

    def area(self):
        return "area before the pop on"

class TailSilenceDetector(SilenceDetector):
    def __init__(self):
        SilenceDetector.__init__(self)

    def area(self):
        return "area after the pop on"

class TwoPopCounterAlt:
    def __init__(self):
    	self.analysisDict = {}
        self.analyses = []
        self.timeCodeSampleRate = 0
        self.timeBase = 0 

    def addAnalysisForChannelAndTimeStamp(self, analysis, channel, timeStamp):
        if channel not in self.analysisDict:
            self.analysisDict[channel] = []

        analysis['timeStamp'] = timeStamp
        analysis['channel'] = channel
        self.analysisDict[channel].append(analysis)

    def isPopWithInSpec(self, result):

        if math.isnan(result['mainFreq']['freqHz']):
            return {"status":"fail","error":"No Tone", "description":"no tone"}

        if result['mainFreq']['dbRep'] < -70.0:
            return {"status":"fail","error":"No Tone", "description":"Likely no tone"}

        if result['mainFreq']['freqHz'] < 996 or result['mainFreq']['freqHz'] > 1004:
            return {"status":"fail","error":"Not 1 kHz", "description":"{} Hz".format(result['mainFreq']['freqHz'])}

        #all tones are expressed as RMS, will add 3.2 to arrive at supposed PEAK value
        if result['mainFreq']['dbRep'] > -22.5 or result['mainFreq']['dbRep'] < -24.5:
            adjustedDb = result['mainFreq']['dbRep'] + 3.2
            return {"status":"fail","error":"Not -20 Peak", "description":"{:3.1f} db".format(adjustedDb)}

        return {"status":"pass","error":"none"}

    def isAnalysisFreqSafe(self, analysis):
        return (analysis['mainFreq']['freqHz'] > 990 and analysis['mainFreq']['freqHz'] < 1010)

    def isAnalysisVolumeSafe(self, analysis):
        return (analysis['mainFreq']['dbRep'] < -22.5 and analysis['mainFreq']['dbRep'] > -24.5)    

    def analysisOfLikelyPop(self, analyses):
        analyisWithHighestLevel = None

        for analysis in analyses:
            if analyisWithHighestLevel == None:
                analyisWithHighestLevel = analysis

            if analyisWithHighestLevel['mainFreq']['dbRep'] < analysis['mainFreq']['dbRep']:
                analyisWithHighestLevel = analysis

        # print analyisWithHighestLevel
        # print convertUnsignedLongLongToTimeCode(analyisWithHighestLevel['timeStamp'], self.timeCodeSampleRate, self.timeBase)
        return analyisWithHighestLevel

    def doesAPopExistAtTheProperPlace(self, analyses):
        popAnalysis = self.analysisAtPopLocation(analyses)
        if popAnalysis is not None:
                return self.isAnalysisFreqSafe(popAnalysis)

        return False

    def analysisAtPopLocation(self, analyses):
        for analysis in analyses:
            if convertUnsignedLongLongToTimeCode(analysis['timeStamp'], self.timeCodeSampleRate, self.timeBase) == "00:59:58:00":
                return analysis
        
        return None

    def activeAnalyses(self, analyses):
        activeAnalyses = []
        for analysis in analyses:
            if analysis['mainFreq']['dbRep'] > -70.0:
                activeAnalyses.append(analysis)
        
        return activeAnalyses

    def activityStatusForPopArea(self, analyses):
        likelyPop = self.analysisOfLikelyPop(analyses)
        likelyPrePop = None
        likelyPostPop = None
        popsToIgnore = []

        errorsStrings = []
        warningStrings = []
        additionalErrorStrings = []

        indexOfLikelyPop = analyses.index(likelyPop)
        popsToIgnore.append(likelyPop)

        if indexOfLikelyPop > 0:
            #look at the previos pop
            likelyPrePopIndex = indexOfLikelyPop - 1
            likelyPrePop = analyses[likelyPrePopIndex]
            if likelyPrePop['mainFreq']['dbRep'] > -40.0:
                additionalErrorStrings.append("the frame before the pop is too loud {:3.0f}db".format(likelyPrePop['mainFreq']['dbRep']))

            popsToIgnore.append(likelyPrePop)

        if indexOfLikelyPop < (len(analyses) - 1):
            likelyPostPopIndex = indexOfLikelyPop + 1
            likelyPostPop = analyses[likelyPostPopIndex]
            if likelyPostPop['mainFreq']['dbRep'] > -40.0:
                additionalErrorStrings.append("the frame after the pop is too loud {:3.0f}db".format(likelyPostPop['mainFreq']['dbRep']))
            popsToIgnore.append(likelyPostPop)

        for analysis in analyses:
            if analysis not in popsToIgnore:
                if analysis['mainFreq']['dbRep'] > -50.0: #and (analysis['timeStamp'] < likelyPop['timeStamp'])
                    errorsStrings.append("{:3.0f}db".format(analysis['mainFreq']['dbRep']))
                elif analysis['mainFreq']['dbRep'] < -50.0 and analysis['mainFreq']['dbRep'] > -70.0:
                    warningStrings.append("{:3.0f}db".format(analysis['mainFreq']['dbRep']))

        return tuple([list(set(errorsStrings)), list(set(warningStrings)), list(set(additionalErrorStrings))])                    

    def result(self):

        status = "pass"
        resultString    = ""
        warningString   = ""
        successStrings  = []
        errorStrings    = []
        warningStrings  = []

        #does a pop exist at 00:59:58:00

        for channel in self.analysisDict.keys():

            # activityErrors, activityWarnings, additionalErrors = self.activityStatusForPopArea(self.analysisDict[channel])
            # if len(activityErrors) > 0:
            #     errorStrings.append("Found signal with a level of {} in the pop area on channel {}.".format(activityErrors, channel))
            # if len(activityWarnings) > 0:
            #     warningStrings.append("Found signal with a level of {} in the pop area on channel {}.".format(activityWarnings, channel))
            # if len(additionalErrors) > 0:
            #     errorStrings.append("Check the head pop area on channel {} as {}.".format(channel, " ".join(additionalErrors)))

            foundPop = False

            if self.doesAPopExistAtTheProperPlace(self.analysisDict[channel]) == False:
                #if the pop doesn't exist at 00:59:58:00, can we attempt to find it?
                errorStrings.append("No pop found at TimeCode 00:59:58:00 on channel {}.".format(channel))

                analysis = self.analysisOfLikelyPop(self.analysisDict[channel])
                
                tcvalue = convertUnsignedLongLongToTimeCode(analysis['timeStamp'], self.timeCodeSampleRate, self.timeBase)
                if self.isAnalysisFreqSafe(analysis) == True:
                    errorStrings.append("Found a pop on channel {} at the wrong location: {}.".format(channel, tcvalue))
                else:
                    freqValue = analysis['mainFreq']['freqHz']
                    if math.isnan(freqValue):
                        errorStrings.append("No discernable pop found on channel {}.".format(channel))
                    else:
                        errorStrings.append("Found signal on channel {} at the wrong location {} outside of 1 kHz.".format(channel, tcvalue))
            else:
                analysis = self.analysisAtPopLocation(self.analysisDict[channel])
                #make sure there is nothing else in the track
                foundPop = True
                if self.isAnalysisVolumeSafe(analysis) == True:
                    successStrings.append("A properly defined 1 kHz pop was found on channel {}.".format(channel))
                elif analysis['mainFreq']['dbRep'] < -23.3 and analysis['mainFreq']['dbRep'] > -28.0:
                    adjustedDb = analysis['mainFreq']['dbRep'] + 3.2
                    warningStrings.append('The pop on channel {} is a low level {:3.2f}db.'.format(channel, adjustedDb))
                elif analysis['mainFreq']['dbRep'] < -28.0:
                    adjustedDb = analysis['mainFreq']['dbRep'] + 3.2
                    errorStrings.append('The pop on channel {} is too low {:3.2f}db.'.format(channel, adjustedDb))
                elif analysis['mainFreq']['dbRep'] > -23.0:
                    adjustedDb = analysis['mainFreq']['dbRep'] + 3.2
                    warningStrings.append('The pop on channel {} is hot: {:3.2f}db.'.format(channel, adjustedDb))


        if len(errorStrings) > 0:
            status = "fail"
            resultString = resultString + " ".join(errorStrings)

        if len(warningStrings) > 0:
            warningString = " ".join(warningStrings)

        if len(successStrings) > 0:
            resultString = resultString + " " + " ".join(successStrings)

        if resultString == "":
            resultString = "All tracks have a well defined pop at 00:59:58:00."

        return {"status":status, "resultString":resultString, "warningString":warningString, "foundPop":("pass" if foundPop else 'fail')}







