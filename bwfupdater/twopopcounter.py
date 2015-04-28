import math

class TwoPopCounter:
    def __init__(self):
    	self.analysisDict = {}

    def addAnalysisForChannel(self, analysis, channel):
        result = self.isPopWithInSpec(analysis)
    	self.analysisDict[channel] = result

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
            return {"status":"fail","error":"Not -20 Peak", "description":"{} db".format(adjustedDb)}

        return {"status":"pass","error":"none"}

    def result(self):
        status = "pass"
        resultString = "All of the tracks contain pops at -20 db Peak 1kHZ."
        
        noToneTracks = []
        badLevelTracks = []
        weirdToneTracks = []

    	for key in self.analysisDict.keys():
            if self.analysisDict[key]["error"] == "No Tone":
                noToneTracks.append(key)
            if self.analysisDict[key]["error"] == "Not 1 kHz":
                weirdToneTracks.append([key, self.analysisDict[key]["description"]])
            if self.analysisDict[key]["error"] == "Not -20 Peak":
                badLevelTracks.append([key, self.analysisDict[key]["description"]])

        errorString = ""
        if len(noToneTracks) > 0:
            errorString = "Tracks {} do not contain pops or the pops might be in the wrong place. ".format([track for track in noToneTracks])
            status = "fail"

        if len(badLevelTracks) > 0:
            errorString = errorString + "The pops on the following tracks have bad levels: "
            for track in badLevelTracks:
                errorString = errorString + " {} {}. ".format(track[0], track[1])
            status = "fail"

        if len(weirdToneTracks) > 0:
            errorString = errorString + "The pops on the following tracks have odd tones: "
            for track in weirdToneTracks:
                errorString = errorString + " {} {}. ".format(track[0], track[1])
            status = "fail"        

        if errorString is not "":
            resultString = errorString

        return {"status":status, "resultString":resultString}







