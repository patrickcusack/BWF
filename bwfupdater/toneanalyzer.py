import os
import sys
import numpy as np
import logging
import math
import datetime
from pcwavefile import PCWaveFile
# from numpy import argmax, sqrt, mean, diff, log
# from matplotlib.mlab import find
import matplotlib.mlab
from scipy.signal import blackmanharris, fftconvolve
from parabolic import parabolic
import json
import pctimecode
from tonecounter import ToneCounter
from tonecounteralt import ToneCounterAlt
from tonecounterresult import ToneCounterResult
from tonecounterresultalt import ToneCounterResultAlt
from twopopcounter import TwoPopCounter
from twopopcounteralt import HeadSilenceDetector
from twopopcounteralt import TailSilenceDetector
from twopopcounteralt import PopDetector
from twopopcounteralt import TwoPopCounterAlt
from byteconversion import les24toles32Value

from pctimecode import convertUnsignedLongLongToTimeCode

# hat tip to https://gist.github.com/endolith/255291

def calculateRMSForData(inputData, byteWidth):
    maxValueForInputData = 2**((byteWidth*8)-1)
    sampleData = []
    for i in range(0,len(inputData), byteWidth):
        try:
            sampleData.append(les24toles32Value(inputData[i:i+byteWidth]) * 1.0/maxValueForInputData)
        except Exception as e:
            print e.message

    signalPower = np.sum(np.power(sampleData,2))
    rms = math.sqrt(signalPower/(len(inputData)/byteWidth))
    return dbRepresentation(rms)

def dbRepresentation(value):
    if value == 0:
        value = 0.0000001
    return 20 * math.log10(value)

def highestAndNextHighestFreqAndPowerForData(inputData, byteWidth, sampleRate):
    ### this must be refactored for the appropiate type of data
    ### for signed data
    maxValueForInputData = 2**((byteWidth*8)-1)
    sampleData = []
    for i in range(0,len(inputData), byteWidth):
        try:
            sampleData.append(les24toles32Value(inputData[i:i+byteWidth]) * 1.0/maxValueForInputData)
        except Exception as e:
            print e.message

    ### take sample data and make numpy array from which we take the fft and keep the lower half of the data
    ### I am not applying a window
    data = np.array(sampleData)
    p = np.fft.fft(data)
    uniquePts = math.ceil(len(data)/2.0) + 1.0 
    p = p[0:uniquePts]
    freqs = np.fft.fftfreq(len(data))

    #### Find the peak in the coefficients
    idx = np.argmax(np.abs(p)**2)
    freq = freqs[idx]
    freqHz = abs(freq*sampleRate)

    ### Find the next highest peak which should exclude a nice band around the frequency of interest
    ### high end
    ### since we can be certain that each frequency band has a resolution of 1 Hz
    ### I can calculate the 1/3 octave frequency by using the idx
    upperBand = idx * pow(2,1.0/6)
    safeIdx = upperBand if upperBand < len(p) else idx
    pNext = p[safeIdx:len(p)-safeIdx]
    if len(pNext) > 0:
        idxNext = np.argmax(np.abs(pNext)**2)
        idxNext += safeIdx
        nextHighest = idxNext
    else:
        nextHighest = 0

    ### low end
    lowerBand = idx / pow(2,1.0/6)
    safeIdx = lowerBand if lowerBand > 1 else idx
    pNext = p[0:safeIdx]
    if len(pNext) > 0:
        idxNext = np.argmax(np.abs(pNext)**2)
    else:
        idxNext = 0

    if abs(p[idxNext]) > abs(p[nextHighest]):
        nextHighest = idxNext

    nextHighestFreq = freqs[nextHighest]
    nextHighestFreqHz = abs(nextHighestFreq*sampleRate)

    ### normalize fft length
    p = np.divide(p,float(len(data)))
    p = np.abs(p)
    p = np.power(p,2)

    ### make up for the power loss we deleted the the right side of the fft
    if len(data) % 2 > 0:
        p[1:len(p)] = np.multiply(p[1:len(p)], 2)
    else:
        p[1:len(p) - 1] = np.multiply(p[1:len(p) -1], 2)

    ### calculate the power of the highest frequency index
    rms = math.sqrt(p[idx])
    dataLength = (len(inputData)/byteWidth)
    hightestdbRep = dbRepresentation(rms)
    highestFreqDict = {"freqHz":freqHz, "dbRep":hightestdbRep}

    ### calculate the power of the next highest frequency index
    rmsNext = math.sqrt(p[nextHighest])
    dataLength = (len(inputData)/byteWidth)
    nextHighestdbRep = dbRepresentation(rmsNext)
    nextHighestFreqDict = {"freqHz":nextHighestFreqHz, "dbRep":nextHighestdbRep}

    return {"mainFreq":highestFreqDict, "nextFreq":nextHighestFreqDict}


def ultimateFreqAndPowerForData(inputData, byteWidth, sampleRate):
    ### this must be refactored for the appropiate type of data
    ### for signed data
    maxValueForInputData = 2**((byteWidth*8)-1)
    sampleData = []
    for i in range(0,len(inputData), byteWidth):
        try:
            sampleData.append(les24toles32Value(inputData[i:i+byteWidth]) * 1.0/maxValueForInputData)
        except Exception as e:
            print e.message

    signal = np.array(sampleData)

    signalPower = np.sum(np.power(signal,2))
    rms = math.sqrt(signalPower/(len(inputData)/byteWidth))
    highestdbRep = dbRepresentation(rms)

    # Compute Fourier transform of windowed signal
    windowed = signal * blackmanharris(len(signal))
    f = np.fft.rfft(windowed)
    # Find the peak and interpolate to get a more accurate peak
    i = np.argmax(abs(f)) # Just use this for less-accurate, naive version

    try:
        #defensive code around divide by zero issue, basically creating noise
        np.seterr(all='ignore')    
        a = np.arange(len(f), dtype=np.float)
        a.fill(10**-10)
        nf = np.where(f == 0., a, f)
        i = i if i != 0. else 10**-10
        if i > len(nf)-2:
            i = len(nf) -2
        true_i = parabolic(np.log(abs(nf)), i)[0]  
        # Convert to equivalent frequency
        freqHz =  (sampleRate * true_i / len(windowed))
    except ValueError:
        freqHz = 0.0

    return {"mainFreq":{"freqHz":freqHz, "dbRep":highestdbRep}, "nextFreq":{"freqHz":"0", "dbRep":"0"}}
        
def headTestAlt():

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
                print fullpath
                print analyzeHeadAlt(fullpath)
    else:
        print analyzeHeadAlt(filePath)       

def popTestAlt():

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
                print analyzeTwoPopAlt(fullpath)
    else:
        print analyzeTwoPopAlt(filePath)

def popTestEighths():

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
                print analyzeTwoPopInEighths(fullpath)
    else:
        print analyzeTwoPopInEighths(filePath)

def analyzeHeadAlt(filePath):

    if os.path.exists(filePath):
        wavefile = PCWaveFile(filePath)

        if wavefile.isValidWaveFile() != True:
            return {"status":"fail", "resultString":"file is not a wavefile"} 

        dataStartPos = wavefile.getDataChunk()["chunkPosition"]
        dataLength = wavefile.getDataChunk()["chunkSize"] 
        sampleRate = wavefile.numberOfSamplesPerSecond()
        timeCodeSampleRate = int(math.ceil(sampleRate * 1.001))
        byteWidth = wavefile.numberOfBytesPerSample()
        numberOfChannels = wavefile.numberOfChannels()
        data_size = int(math.ceil(sampleRate * 1.001)) #1 second of audio
        dataLengthInSamples = dataLength / (numberOfChannels * byteWidth)
        dataStartPosOffset = 0
        normalizedTimeStamp = wavefile.timestamp #

        # print "dataStartPosOffset",dataStartPosOffset

        toneStartTimeStamp = pctimecode.convertTimeCodeToUnsignedLongLong("00:57:30:00", timeCodeSampleRate, 24)
        # print "normalizedTimeStamp",normalizedTimeStamp
        # print "toneStartTimeStamp",toneStartTimeStamp

        #assume file starts at 00:57:30:00, in the case that the file doesn't have a bext extension
        #also gets into an issue of what to favor, bext over regn? I assume that the encoders user bext
        #as you couldn't reliably expect a regn chunk
        if normalizedTimeStamp == 0 or (normalizedTimeStamp % (timeCodeSampleRate * 60 * 60 * 24) == 0) : 
            normalizedTimeStamp = toneStartTimeStamp

        #the head length should be 150 seconds
        secondsInSamplesToRead = 150 * timeCodeSampleRate
        # print "secondsInSamplesToRead",secondsInSamplesToRead

        if secondsInSamplesToRead > dataLengthInSamples:
            return {"status":"fail", "resultString":"the file is too short", "warningString":""}


        #make sure that the timestamp starts on the second, otherwise normalize the timestamp
        normalizedTimestampOffset = wavefile.timestamp % timeCodeSampleRate
        if normalizedTimestampOffset > 0:
            dataStartPosOffset += (timeCodeSampleRate - normalizedTimestampOffset) * byteWidth * numberOfChannels
            normalizedTimeStamp = wavefile.timestamp + (timeCodeSampleRate - normalizedTimestampOffset)

        # print "(timeCodeSampleRate - normalizedTimestampOffset)", (timeCodeSampleRate - normalizedTimestampOffset)
        # print "normalizedTimestampOffset", normalizedTimestampOffset
        # print "dataStartPosOffset", dataStartPosOffset
        # print "normalizedTimeStamp", normalizedTimeStamp

        if normalizedTimeStamp > toneStartTimeStamp:
            # print 'if wavefile.timestamp > toneStartTimeStamp:'
            secondsInSamplesToRead -= (normalizedTimeStamp - toneStartTimeStamp)
        
        if normalizedTimeStamp < toneStartTimeStamp:
            # print 'if wavefile.timestamp < toneStartTimeStamp:'
            secondsInSamplesToRead += (toneStartTimeStamp - normalizedTimeStamp)

        #lets only look at the first 150 seconds of the file
        sizeToRead = secondsInSamplesToRead * byteWidth * numberOfChannels
        sizeToRead = sizeToRead if dataLength > sizeToRead else dataLength

        second = 0
        with open(filePath, 'rb') as f:
            startTime = datetime.datetime.now()
            dataStartPos += dataStartPosOffset
            f.seek(dataStartPos)

            dataToReadChunkSize = timeCodeSampleRate*byteWidth*numberOfChannels
            dataRemaining = sizeToRead
           
            counterDict = {}
            for channel in range(0, numberOfChannels):
                counterDict[str(channel)] = ToneCounterAlt()

            while dataRemaining > 0:
                if dataRemaining > dataToReadChunkSize:
                    data = f.read(dataToReadChunkSize)
                else:
                    data = f.read(dataRemaining)
                dataRemaining -= len(data)

                currentPositionInFile = normalizedTimeStamp + (second * data_size)
                # print currentPositionInFile, pctimecode.convertUnsignedLongLongToTimeCode(currentPositionInFile, 48048, 24)

                for channel in range(0, numberOfChannels):
                    subdata = ""
                    for x in range(channel*byteWidth,len(data),byteWidth*numberOfChannels):
                        subdata += (data[x] + data[x+1] + data[x+2])
                    result = highestAndNextHighestFreqAndPowerForData(subdata, byteWidth, sampleRate)
                    toneCounter = counterDict[str(channel)]
                    toneCounter.addAnalysis({
                        "currentTimeStamp":currentPositionInFile, 
                        "timeCodeSampleRate":timeCodeSampleRate,
                        "freqs":result,
                        "RMSForInputData":calculateRMSForData(subdata, byteWidth)})
                second += 1

        #Questions to answer 1) Does it have at least 60 secs of tone 2) Does it start at head 3) Does it have a Pop 4) Does it have other tones?
        toneCounterResult = ToneCounterResultAlt(timeCodeSampleRate, 24)
        return toneCounterResult.result(counterDict)
    else:
        return {"status":"fail", "resultString":"file doesn't exist","warningString":""} 

def analyzeTwoPopAlt(filePath):

    if not os.path.exists(filePath):
        return {"status":"fail", "resultString":"file doesn't exist", "warningString":""}

    wavefile = PCWaveFile(filePath)

    if wavefile.isValidWaveFile() != True:
        return {"status":"fail", "resultString":"file is not a wavefile"} 

    dataStartPos = wavefile.getDataChunk()["chunkPosition"]
    dataLength = wavefile.getDataChunk()["chunkSize"]
    sampleRate = wavefile.numberOfSamplesPerSecond()
    timeCodeSampleRate = int(math.ceil(sampleRate * 1.001))
    byteWidth = wavefile.numberOfBytesPerSample()
    numberOfChannels = wavefile.numberOfChannels()
    data_size = int(math.ceil(sampleRate * 1.001))/24 #1 second of audio
    dataStartPosOffset = 0
    normalizedTimeStamp = wavefile.timestamp #
    currentPositionInFile = 0
    dataLengthInSamples = dataLength / (numberOfChannels * byteWidth)

    # print "dataStartPosOffset",dataStartPosOffset

    toneStartTimeStamp = pctimecode.convertTimeCodeToUnsignedLongLong("00:57:30:00", timeCodeSampleRate, 24)
    popSafeStartTimeStamp = pctimecode.convertTimeCodeToUnsignedLongLong("00:59:57:00", timeCodeSampleRate, 24)
    hourOneTimeStamp = pctimecode.convertTimeCodeToUnsignedLongLong("01:00:00:00", timeCodeSampleRate, 24)
    # print "normalizedTimeStamp",normalizedTimeStamp
    # print "toneStartTimeStamp",toneStartTimeStamp

    #assume file starts at 00:57:30:00, in the case that the file doesn't have a bext extension
    #also gets into an issue of what to favor, bext over regn? I assume that the encoders user bext
    #as you couldn't reliably expect a regn chunk
    if normalizedTimeStamp == 0: 
        normalizedTimeStamp = toneStartTimeStamp

    #we're going to read 3 seconds total
    secondsInSamplesToRead = 3 * timeCodeSampleRate
    # print "secondsInSamplesToRead",secondsInSamplesToRead

    #make sure that the timestamp starts on the second, otherwise normalize the timestamp
    normalizedTimestampOffset = wavefile.timestamp % timeCodeSampleRate
    if normalizedTimestampOffset > 0:
        dataStartPosOffset += (timeCodeSampleRate - normalizedTimestampOffset) * byteWidth * numberOfChannels
        normalizedTimeStamp = wavefile.timestamp + (timeCodeSampleRate - normalizedTimestampOffset)

    # print "(timeCodeSampleRate - normalizedTimestampOffset)", (timeCodeSampleRate - normalizedTimestampOffset)
    # print "normalizedTimestampOffset", normalizedTimestampOffset
    # print "dataStartPosOffset", dataStartPosOffset
    # print "normalizedTimeStamp", normalizedTimeStamp

    if normalizedTimeStamp > popSafeStartTimeStamp:
        # print 'if wavefile.timestamp > toneStartTimeStamp:'
        return {"status":"fail", "resultString":"timecode start exceeds pop location","warningString":""}

    if dataLengthInSamples < (hourOneTimeStamp - toneStartTimeStamp):
        return {"status":"fail", "resultString":"the file is too short", "warningString":""}
    
    if normalizedTimeStamp < popSafeStartTimeStamp:
        # print 'if wavefile.timestamp < toneStartTimeStamp:'
        sampleDifference = (popSafeStartTimeStamp - normalizedTimeStamp)
        currentPositionInFile = sampleDifference + normalizedTimeStamp
        dataStartPosOffset += (sampleDifference * byteWidth * numberOfChannels)

    #lets only look at the 3 seconds of the file from 00:59:57:00 to 01:00:00:00
    sizeToRead = secondsInSamplesToRead * byteWidth * numberOfChannels
    sizeToRead = sizeToRead if dataLength > sizeToRead else dataLength
    # print "sizeToRead",sizeToRead

    with open(filePath, 'rb') as f:
        f.seek(dataStartPos + dataStartPosOffset)

        dataToReadChunkSize = data_size*byteWidth*numberOfChannels
        dataRemaining = sizeToRead
       
        twoPopCounter = TwoPopCounterAlt()
        twoPopCounter.timeCodeSampleRate = timeCodeSampleRate
        twoPopCounter.timeBase = 24

        while dataRemaining > 0:
            if dataRemaining > dataToReadChunkSize:
                data = f.read(dataToReadChunkSize)
            else:
                data = f.read(dataRemaining)
            dataRemaining -= len(data)

            for channel in range(0, numberOfChannels):
                subdata = ""
                for x in range(channel*byteWidth,len(data),byteWidth*numberOfChannels):
                    subdata += (data[x] + data[x+1] + data[x+2])
                analysis = ultimateFreqAndPowerForData(subdata, byteWidth, sampleRate)
                twoPopCounter.addAnalysisForChannelAndTimeStamp(analysis, channel, currentPositionInFile)
            
            currentPositionInFile += data_size

        return twoPopCounter.result()

def analyzeTwoPopInEighths(filePath):

    if not os.path.exists(filePath):
        return {"status":"fail", "resultString":"file doesn't exist", "warningString":""}

    wavefile = PCWaveFile(filePath)

    if wavefile.isValidWaveFile() != True:
        return {"status":"fail", "resultString":"file is not a wavefile"} 

    dataStartPos = wavefile.getDataChunk()["chunkPosition"]
    dataLength = wavefile.getDataChunk()["chunkSize"]
    sampleRate = wavefile.numberOfSamplesPerSecond()
    timeCodeSampleRate = int(math.ceil(sampleRate * 1.001))
    byteWidth = wavefile.numberOfBytesPerSample()
    numberOfChannels = wavefile.numberOfChannels()
    data_size = int(math.ceil(sampleRate * 1.001))/24 #1 second of audio
    dataStartPosOffset = 0
    normalizedTimeStamp = wavefile.timestamp #
    currentPositionInFile = 0
    dataLengthInSamples = dataLength / (numberOfChannels * byteWidth)

    # print "dataStartPosOffset",dataStartPosOffset

    toneStartTimeStamp = pctimecode.convertTimeCodeToUnsignedLongLong("00:57:30:00", timeCodeSampleRate, 24)
    popSafeStartTimeStamp = pctimecode.convertTimeCodeToUnsignedLongLong("00:59:57:00", timeCodeSampleRate, 24)
    hourOneTimeStamp = pctimecode.convertTimeCodeToUnsignedLongLong("01:00:00:00", timeCodeSampleRate, 24)
    # print "normalizedTimeStamp",normalizedTimeStamp
    # print "toneStartTimeStamp",toneStartTimeStamp

    #assume file starts at 00:57:30:00, in the case that the file doesn't have a bext extension
    #also gets into an issue of what to favor, bext over regn? I assume that the encoders user bext
    #as you couldn't reliably expect a regn chunk
    if normalizedTimeStamp == 0 or (normalizedTimeStamp % (timeCodeSampleRate * 60 * 60 * 24) == 0): 
        normalizedTimeStamp = toneStartTimeStamp

    #we're going to read 3 seconds total
    secondsInSamplesToRead = 3 * timeCodeSampleRate
    # print "secondsInSamplesToRead",secondsInSamplesToRead

    #make sure that the timestamp starts on the second, otherwise normalize the timestamp
    normalizedTimestampOffset = wavefile.timestamp % timeCodeSampleRate
    if normalizedTimestampOffset > 0:
        dataStartPosOffset += (timeCodeSampleRate - normalizedTimestampOffset) * byteWidth * numberOfChannels
        normalizedTimeStamp = wavefile.timestamp + (timeCodeSampleRate - normalizedTimestampOffset)

    # print "(timeCodeSampleRate - normalizedTimestampOffset)", (timeCodeSampleRate - normalizedTimestampOffset)
    # print "normalizedTimestampOffset", normalizedTimestampOffset
    # print "dataStartPosOffset", dataStartPosOffset
    # print "normalizedTimeStamp", normalizedTimeStamp

    if normalizedTimeStamp > popSafeStartTimeStamp:
        # print 'if wavefile.timestamp > toneStartTimeStamp:'
        return {"status":"fail", "resultString":"timecode start exceeds pop location","warningString":""}

    if dataLengthInSamples < (hourOneTimeStamp - toneStartTimeStamp):
        return {"status":"fail", "resultString":"the file is too short", "warningString":""}
    
    if normalizedTimeStamp < popSafeStartTimeStamp:
        #seek to start time to analyze
        sampleDifference = (popSafeStartTimeStamp - normalizedTimeStamp)
        currentPositionInFile = sampleDifference + normalizedTimeStamp
        dataStartPosOffset += (sampleDifference * byteWidth * numberOfChannels)

    #lets only look at the 3 seconds of the file from 00:59:57:00 to 01:00:00:00
    sizeToRead = secondsInSamplesToRead * byteWidth * numberOfChannels
    sizeToRead = sizeToRead if dataLength > sizeToRead else dataLength

    #this scans the head to make sure there is no signal in the head up to a sixteenth of frame before the pop
    headResult = preScanHead(filePath, data_size, dataStartPos, dataStartPosOffset, byteWidth, numberOfChannels, sampleRate)

    #this scans the tail to make sure there is no signal in the tail after an eighth of a frame after the pop
    nextByteOffset = (data_size * 25 * byteWidth * numberOfChannels) #seek 25 frames from the initial start which would be 59:58:01
    tailResult = preScanTail(filePath, data_size, dataStartPos, (dataStartPosOffset + nextByteOffset), byteWidth, numberOfChannels, sampleRate)

    overallResult = {"status":"pass", "resultString":""}
    suppressSuperfluousWarnings = False

    if headResult['status'] == 'fail':
        overallResult['status'] = 'fail'
        overallResult["resultString"] += headResult["resultString"]

    if tailResult['status'] == 'fail':
        overallResult['status'] = 'fail'
        overallResult["resultString"] += tailResult["resultString"]

    if overallResult['status'] == 'pass':
        overallResult["resultString"] = "Pop area contains no discernable problems."

    twoPopCounter = TwoPopCounterAlt()
    twoPopCounter.timeCodeSampleRate = timeCodeSampleRate
    twoPopCounter.timeBase = 24

    with open(filePath, 'rb') as f:
        f.seek(dataStartPos + dataStartPosOffset)

        dataToReadChunkSize = data_size*byteWidth*numberOfChannels
        dataRemaining = sizeToRead

        while dataRemaining > 0:
            if dataRemaining > dataToReadChunkSize:
                data = f.read(dataToReadChunkSize)
            else:
                data = f.read(dataRemaining)
            dataRemaining -= len(data)

            for channel in range(0, numberOfChannels):
                subdata = ""
                for x in range(channel*byteWidth,len(data),byteWidth*numberOfChannels):
                    subdata += (data[x] + data[x+1] + data[x+2])
                analysis = ultimateFreqAndPowerForData(subdata, byteWidth, sampleRate)
                twoPopCounter.addAnalysisForChannelAndTimeStamp(analysis, channel, currentPositionInFile)
            
            currentPositionInFile += data_size

    twoPopResult = twoPopCounter.result()

    #likely that the pop is off as we are checking an area of up to a sixteenth of frame prior to the pop and area an eighth of a frame
    #after the pop
    if overallResult['status'] == 'fail' and twoPopResult['status'] == 'pass':
        twoPopResult['status'] = 'fail'
        twoPopResult['resultString'] = "Check your pop as it is likely off. " + overallResult['resultString']

    if overallResult['status'] == 'fail' and twoPopResult['status'] == 'fail' and twoPopResult['foundPop'] == 'pass':
        twoPopResult['status'] = 'fail'
        twoPopResult['resultString'] = "Check your pop as it is likely off. " + overallResult['resultString']

    popIntegrityResult = {"status":"pass", "resultString":""}
    if overallResult['status'] == 'pass' and twoPopResult['status'] == 'pass'  and twoPopResult['foundPop'] == 'pass':
        #lets make sure the pop actually starts consists of a frame
        nextByteOffset = (data_size * 23 * byteWidth * numberOfChannels) #seek 23 frames from the initial start which would be 59:57:23
        popIntegrityResult = scanPop(filePath, data_size, dataStartPos, (dataStartPosOffset + nextByteOffset), byteWidth, numberOfChannels, sampleRate)
        if popIntegrityResult['status'] == 'fail':
            twoPopResult['status'] = 'fail'
            twoPopResult['resultString'] = popIntegrityResult['resultString']

    return twoPopResult

def scanPop(filePath, data_size, dataStartPos, dataStartPosOffset, byteWidth, numberOfChannels, sampleRate):
    #we come in at 1 frame before the pop and offset an eighth of a frame
    print filePath
    with open(filePath, 'rb') as f:
        #counters for our initial analysis up to an eightth of a frame before the pop
        divisor = 8
        currentSamplePosition = data_size/divisor
        maxSamplePosition = data_size*2

        dataToReadChunkSize = data_size*byteWidth*numberOfChannels  #bytes once second 
        offset = dataStartPosOffset

        detector = PopDetector(divisor=divisor)

        while currentSamplePosition < maxSamplePosition:
            currentByteOffset = (currentSamplePosition * byteWidth * numberOfChannels)
            f.seek(dataStartPos + offset + currentByteOffset) #this is initially 00:59:57:23:1/16
            data = f.read(dataToReadChunkSize)
            for channel in range(0, numberOfChannels):
                subdata = ""
                for x in range(channel*byteWidth,len(data),byteWidth*numberOfChannels):
                    subdata += (data[x] + data[x+1] + data[x+2])
                analysis = ultimateFreqAndPowerForData(subdata, byteWidth, sampleRate)
                detector.addAnalysis(analysis, channel)
            
            currentSamplePosition += (data_size / divisor)

        return detector.analysisResult()

def preScanHead(filePath, data_size, dataStartPos, dataStartPosOffset, byteWidth, numberOfChannels, sampleRate):
    with open(filePath, 'rb') as f:
        #counters for our initial analysis up to an eightth of a frame before the pop
        currentSamplePosition = 0
        divisor = 16
        maxSamplePosition = (data_size * 23) - (data_size / divisor)

        dataToReadChunkSize = data_size*byteWidth*numberOfChannels  #bytes once second 
        offset = dataStartPosOffset

        detector = HeadSilenceDetector()

        while currentSamplePosition < maxSamplePosition:
            currentByteOffset = (currentSamplePosition * byteWidth * numberOfChannels)
            f.seek(dataStartPos + offset + currentByteOffset) #this is initially 00:59:57:00
            data = f.read(dataToReadChunkSize)
            for channel in range(0, numberOfChannels):
                subdata = ""
                for x in range(channel*byteWidth,len(data),byteWidth*numberOfChannels):
                    subdata += (data[x] + data[x+1] + data[x+2])
                analysis = ultimateFreqAndPowerForData(subdata, byteWidth, sampleRate)
                detector.addAnalysis(analysis, channel)
            
            currentSamplePosition += (data_size / divisor)

        return detector.analysisResult()

def preScanTail(filePath, data_size, dataStartPos, dataStartPosOffset, byteWidth, numberOfChannels, sampleRate):
    with open(filePath, 'rb') as f:
        #we want to start our analysis an eighth of a frame after 00:59:58:01 or 10 subframes (base 80)
        divisor = 4
        currentSamplePosition = data_size / divisor
        maxSamplePosition = (data_size * (23+22)) - (data_size / divisor)

        dataToReadChunkSize = data_size*byteWidth*numberOfChannels  #bytes once second 
        offset = dataStartPosOffset #this is 00:59:58:01

        detector = TailSilenceDetector()

        while currentSamplePosition < maxSamplePosition:
            currentByteOffset = (currentSamplePosition * byteWidth * numberOfChannels)
            f.seek(dataStartPos + offset + currentByteOffset)
            data = f.read(dataToReadChunkSize)
            for channel in range(0, numberOfChannels):
                subdata = ""
                for x in range(channel*byteWidth,len(data),byteWidth*numberOfChannels):
                    subdata += (data[x] + data[x+1] + data[x+2])
                analysis = ultimateFreqAndPowerForData(subdata, byteWidth, sampleRate)
                detector.addAnalysis(analysis, channel)
            
            currentSamplePosition += (data_size / divisor)

        return detector.analysisResult()


if __name__=='__main__':
    # main()
    # multichannel()
    # smallSampleSize()
    # findTwoPop()
    # findTwoPopAlt()
    # print analyzeTwoPop(sys.argv[1])
    # popTest()
    # headTestAlt()
    # popTestAlt()
    popTestEighths()

