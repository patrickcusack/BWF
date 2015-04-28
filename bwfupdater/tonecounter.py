class ToneCounter:
    def __init__(self):
        self.toneStart = False
        self.averageMainFrequencyLoudness = 0
        self.initialRuns = []
        self.currentRun = None
        self.errors = []

    def resetRun(self):
            self.currentRun = None
            self.toneStart = False

    def runs(self):
        newRuns = []
        for run in self.initialRuns:
            nRun = {}

            count                       = run['count']
            freqDBRep                   = run['freqDBRep']
            freq                        = run['freq']

            nRun['start']               = run['start']
            nRun['timeCodeSampleRate']  = run['timeCodeSampleRate']
            nRun['currentTime']         = run['currentTime']
            nRun['count']               = run['count']
            nRun['freqDBRep']           = run['freqDBRep']
            nRun['freq']                = run['freq']
            nRun['freqDBRep']           = ((freqDBRep * 1.0)/count)
            nRun['freq']                = ((freq * 1.0)/count)
            newRuns.append(nRun)        

        return newRuns

    def lengthOfLongestRun(self):
        pass

    def isFrequencySafe(self, freq):
        return (freq > 997 and freq < 1003)

    def addAnalysis(self, analysis):
        nearestFreq             = analysis['freqs']['nextFreq']['freqHz']
        loudnessOfNearestFreq   = analysis['freqs']['nextFreq']['dbRep']
        mainFreq                = analysis['freqs']['mainFreq']['freqHz']
        mainFreqDbRep           = analysis['freqs']['mainFreq']['dbRep']
        overallRMSValue         = analysis['RMSForInputData']

        if overallRMSValue < -96.0:
            #if there's silence, then just return
            self.resetRun()
            return

        if loudnessOfNearestFreq > -65.0: 
            #if there's a frequency that's greater than -70 then we have a multiple tones
            #just bail as this is an error regardless of the frequencies involved
            errorRun = {}
            errorRun['start'] = analysis['currentTimeStamp']
            errorRun['timeCodeSampleRate'] = analysis['timeCodeSampleRate']
            errorRun['currentTime'] = analysis['currentTimeStamp']
            errorRun['freqDBRep'] = loudnessOfNearestFreq
            errorRun['freq'] = nearestFreq
            self.errors.append(errorRun)
            self.resetRun()
            return
    
        # banding of frequency & checking RMS value which should be -23.0 RMS or -20 PEAK
        # if we see the frequenc at any level, we'll start, otherwise if its not in scope
        # on the second pass, we'll drop it.
        if self.isFrequencySafe(mainFreq):
            if self.toneStart == True:            
                if (mainFreqDbRep > -24.5 and mainFreqDbRep < -22.5):
                    self.currentRun['currentTime'] = analysis['currentTimeStamp']
                    self.currentRun['freqDBRep'] += mainFreqDbRep
                    self.currentRun['freq'] += mainFreq
                    self.currentRun['count'] += 1
                else:
                    self.resetRun()
            else:
                nextRun = {}
                nextRun['start'] = analysis['currentTimeStamp']
                nextRun['timeCodeSampleRate'] = analysis['timeCodeSampleRate']
                nextRun['currentTime'] = analysis['currentTimeStamp']
                nextRun['freqDBRep'] = mainFreqDbRep
                nextRun['freq'] = mainFreq
                nextRun['count'] = 1
                self.initialRuns.append(nextRun)
                self.currentRun = nextRun
                self.toneStart = True
        else:
            self.resetRun()

