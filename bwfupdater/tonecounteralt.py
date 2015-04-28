import json

def prettyPrintJSON(data):
    return json.dumps(data, sort_keys = True, indent=4, separators=(',', ': '))

class ToneCounterAlt:
    def __init__(self):
        self.toneStart = False
        self.averageMainFrequencyLoudness = 0
        self.errors = []
        self.runs = []
        self.badRuns = []
        self.toneRunStart = False

    def isProperFreq(self, freq):
        return (freq > 997 and freq < 1003)

    def isProperLevel(self, level):
        return (level >= -24.5 and level <= -22.5)    

    def addAnalysis(self, analysis):
        nearestFreq             = analysis['freqs']['nextFreq']['freqHz']
        loudnessOfNearestFreq   = analysis['freqs']['nextFreq']['dbRep']
        mainFreq                = analysis['freqs']['mainFreq']['freqHz']
        mainFreqDbRep           = analysis['freqs']['mainFreq']['dbRep']
        overallRMSValue         = analysis['RMSForInputData']

        # print convertUnsignedLongLongToTimeCode(analysis['currentTimeStamp'], 48048, 24)

        if overallRMSValue < -96.0:
            # print 'silence'
            return

        if loudnessOfNearestFreq > -65.0: 
            # print "error"
            #if there's a frequency that's greater than -70 then we have a multiple tones
            #just bail as this is an error regardless of the frequencies involved
            errorRun = {}
            errorRun['start'] = analysis['currentTimeStamp']
            errorRun['timeCodeSampleRate'] = analysis['timeCodeSampleRate']
            errorRun['currentTime'] = analysis['currentTimeStamp']
            errorRun['freqDBRep'] = loudnessOfNearestFreq
            errorRun['freq'] = nearestFreq
            errorRun['length'] = 1
            # print prettyPrintJSON(errorRun)
            self.errors.append(errorRun)
            return

        if self.isProperFreq(mainFreq) == True:
            # print "isProperFreq"
            nextRun = {}
            nextRun['start'] = analysis['currentTimeStamp']
            nextRun['timeCodeSampleRate'] = analysis['timeCodeSampleRate']
            nextRun['currentTime'] = analysis['currentTimeStamp']
            nextRun['freqDBRep'] = mainFreqDbRep
            nextRun['freq'] = mainFreq
            nextRun['length'] = 1
            self.runs.append(nextRun)
        else:
            nextRun = {}
            nextRun['start'] = analysis['currentTimeStamp']
            nextRun['timeCodeSampleRate'] = analysis['timeCodeSampleRate']
            nextRun['currentTime'] = analysis['currentTimeStamp']
            nextRun['freqDBRep'] = mainFreqDbRep
            nextRun['freq'] = mainFreq
            nextRun['length'] = 1
            self.errors.append(nextRun)

        # if self.isProperFreq(mainFreq) == True and self.isProperLevel(mainFreqDbRep) == False:
        #     nextRun = {}
        #     nextRun['start'] = analysis['currentTimeStamp']
        #     nextRun['timeCodeSampleRate'] = analysis['timeCodeSampleRate']
        #     nextRun['currentTime'] = analysis['currentTimeStamp']
        #     nextRun['freqDBRep'] = mainFreqDbRep
        #     nextRun['freq'] = mainFreq
        #     nextRun['length'] = 1
        #     self.badRuns.append(nextRun)


