import os
import sys
import struct
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

import pctimecode

# hat tip to https://gist.github.com/endolith/255291

def les24toles32Value(fileDataAsString):
    if len(fileDataAsString) != 3:
        print "error"
    return struct.unpack('<i', fileDataAsString + ('\xff' if ord(fileDataAsString[2]) & 0x80 else '\0'))[0]

def logString(string):
    if logging != None:
        logging.info("{} is not a WAV file".format(filePath))
           
def dbRepresentation(value):
    if value == 0:
        value = 0.0000001
    return 20 * math.log10(value)

def anaylyzeDataWithZeroCrossing(inputData, byteWidth, sampleRate):
    ### this must be refactored for the appropiate type of data
    ### for signed data
    maxValueForInputData = 2**((byteWidth*8)-1)
    sampleData = []
    for i in range(0,len(inputData), byteWidth):
        try:
            sampleData.append(les24toles32Value(inputData[i:i+byteWidth]) * 1.0/maxValueForInputData)
        except Exception as e:
            print e.message

    sig = np.array(sampleData)
    indices = matplotlib.mlab.find((sig[1:] >= 0) & (sig[:-1] < 0))
    crossings = [i - sig[i] / (sig[i+1] - sig[i]) for i in indices]
    return sampleRate / np.mean(np.diff(crossings))

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
    highestFreqDict = {freqHz:hightestdbRep}

    ### calculate the power of the next highest frequency index
    rmsNext = math.sqrt(p[nextHighest])
    dataLength = (len(inputData)/byteWidth)
    nextHighestdbRep = dbRepresentation(rmsNext)
    nextHighestFreqDict = {nextHighestFreqHz:nextHighestdbRep}

    return {"mainFreq":{freqHz:hightestdbRep}, "nextFreq":nextHighestFreqDict}

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
    hightestdbRep = dbRepresentation(rms)

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
        true_i = parabolic(np.log(abs(nf)), i)[0]  
        # Convert to equivalent frequency
        freqHz =  (sampleRate * true_i / len(windowed))
    except ValueError:
        freqHz = 0.0

    return tuple([freqHz, hightestdbRep, 0, "0"])


def main():
    data_size = 48000 #1 second of audio
    frate = 48000.0 
    
    try:
        filePath = sys.argv[1]
        if os.path.exists(filePath):
            wavefile = PCWaveFile(filePath)

            if wavefile.isValidWaveFile() != True:
                print "File is not a wave file"
                return

            dataStartPos = wavefile.getDataChunk()["chunkPosition"]
            dataLength = wavefile.getDataChunk()["chunkSize"]
            sampleRate = wavefile.numberOfSamplesPerSecond()
            byteWidth = wavefile.numberOfBytesPerSample()

            with open(filePath, 'rb') as f:
                startTime = datetime.datetime.now()
                f.seek(dataStartPos)

                dataToReadChunkSize = sampleRate*byteWidth
                dataRemaining = dataLength
               
                while dataRemaining > 0:
                    if dataRemaining > dataToReadChunkSize:
                        data = f.read(dataToReadChunkSize)
                    else:
                        data = f.read(dataRemaining)

                    print highestAndNextHighestFreqAndPowerForData(data, byteWidth, sampleRate)    
                    dataRemaining -= len(data)
        else:
            print "The file",filename,"doesn't exist"
    except:
        print "No file was passed in as a variable" 

def multichannel():
    
    try:
        filePath = sys.argv[1]
        if os.path.exists(filePath):
            wavefile = PCWaveFile(filePath)

            if wavefile.isValidWaveFile() != True:
                print "File is not a wave file"
                return

            dataStartPos = wavefile.getDataChunk()["chunkPosition"]
            dataLength = wavefile.getDataChunk()["chunkSize"]
            sampleRate = wavefile.numberOfSamplesPerSecond()
            timeCodeSampleRate = int(math.ceil(48000 * 1.001))
            byteWidth = wavefile.numberOfBytesPerSample()
            numberOfChannels = wavefile.numberOfChannels()
            data_size = 48048 #1 second of audio

            print timeCodeSampleRate
            print pctimecode.convertUnsignedLongLongToTimeCode(wavefile.timestamp, timeCodeSampleRate, 24)

            second = 0
            with open(filePath, 'rb') as f:
                startTime = datetime.datetime.now()
                f.seek(dataStartPos)

                dataToReadChunkSize = sampleRate*byteWidth*numberOfChannels
                dataRemaining = dataLength
               
                while dataRemaining > 0:
                    if dataRemaining > dataToReadChunkSize:
                        data = f.read(dataToReadChunkSize)
                    else:
                        data = f.read(dataRemaining)

                    dataRemaining -= len(data)

                    print wavefile.timestamp
                    print pctimecode.convertUnsignedLongLongToTimeCode(wavefile.timestamp + (second * data_size), timeCodeSampleRate, 24)
                    for channel in range(0, numberOfChannels):
                        subdata = ""
                        for x in range(channel*byteWidth,len(data),byteWidth*numberOfChannels):
                            subdata += (data[x] + data[x+1] + data[x+2])

                        print highestAndNextHighestFreqAndPowerForData(subdata, byteWidth, sampleRate)

                    second += 1

        else:
            print "The file",filename,"doesn't exist"
    except IndexError as e:
        print "No file was passed in as a variable"         

def smallSampleSize():

    try:
        filePath = sys.argv[1]
        if os.path.exists(filePath):
            wavefile = PCWaveFile(filePath)

            if wavefile.isValidWaveFile() != True:
                print "File is not a wave file"
                return

            dataStartPos = wavefile.getDataChunk()["chunkPosition"]
            dataLength = wavefile.getDataChunk()["chunkSize"]
            sampleRate = wavefile.numberOfSamplesPerSecond()
            timeCodeSampleRate = int(sampleRate *  1.001)
            byteWidth = wavefile.numberOfBytesPerSample()
            numberOfChannels = wavefile.numberOfChannels()

            frameNumber = 0
            print datetime.datetime.now()
            with open(filePath, 'rb') as f:
                startTime = datetime.datetime.now()
                f.seek(dataStartPos)
                data_size = int((sampleRate * 1.001) / 24) #1 frame of audio at 23.98 or 48048 sample rate

                dataToReadChunkSize = data_size*byteWidth
                #examine 160 seconds of data
                dataRemaining = (160*timeCodeSampleRate)*byteWidth*numberOfChannels #dataLength
               
                while dataRemaining > 0:
                    if dataRemaining > dataToReadChunkSize:
                        data = f.read(dataToReadChunkSize)
                    else:
                        data = f.read(dataRemaining)

                    dataRemaining -= len(data)

                    print pctimecode.convertUnsignedLongLongToTimeCode(wavefile.timestamp + (frameNumber * data_size), timeCodeSampleRate, 24)
                    frameNumber += 1

                    for channel in range(0, numberOfChannels):
                        subdata = ""
                        for x in range(channel*byteWidth,len(data),byteWidth*numberOfChannels):
                            # subdata.extend(data[x:x+3])
                            subdata += (data[x] + data[x+1] + data[x+2])

                        print ultimateFreqAndPowerForData(subdata, byteWidth, sampleRate)

            print datetime.datetime.now()
        else:
            print "The file",filename,"doesn't exist"
    except IndexError as e:
        print "No file was passed in as a variable"     

def findTwoPop():
    try:
        filePath = sys.argv[1]
        if os.path.exists(filePath):
            wavefile = PCWaveFile(filePath)

            if wavefile.isValidWaveFile() != True:
                print "File is not a wave file"
                return

            dataStartPos = wavefile.getDataChunk()["chunkPosition"]
            dataLength = wavefile.getDataChunk()["chunkSize"]
            sampleRate = wavefile.numberOfSamplesPerSecond()
            byteWidth = wavefile.numberOfBytesPerSample()
            numberOfChannels = wavefile.numberOfChannels()

            with open(filePath, 'rb') as f:
                startTime = datetime.datetime.now()
                #1 frame of audio at 23.98 or 48048 sample rate
                data_size = 2002
                #position at which to examine
                startOffset = int(round(sampleRate * 1.001)) * 148 * byteWidth * numberOfChannels
                startOffset -= (data_size * byteWidth * numberOfChannels * 2)
                dataStartPos = dataStartPos + startOffset
                f.seek(dataStartPos)

                if dataStartPos > dataLength:
                    print "file is too short to analyze"
                    return

                dataToReadChunkSize = data_size*byteWidth*numberOfChannels
                dataRemaining = data_size*byteWidth*numberOfChannels*6

                while dataRemaining > 0:
                    data = f.read(dataToReadChunkSize)
                    print pcwave
                    dataRemaining -= dataToReadChunkSize
                    print "Next Sample"
                    for channel in range(0, numberOfChannels):
                        subdata = ""
                        for x in range(channel*byteWidth,len(data),byteWidth*numberOfChannels):
                            # subdata.extend(data[x:x+3])
                            subdata += (data[x] + data[x+1] + data[x+2])

                        # print anaylyzeDataWithZeroCrossing(subdata, byteWidth, sampleRate)
                        result =  ultimateFreqAndPowerForData(subdata, byteWidth, sampleRate)
                        if math.isnan(result[0]) or result[1] < -65.0:
                            print '\tDisregard', round(result[0]), result[1]
                        elif result[0] < 1005 and result[0] > 995:
                            print '\tMatch', round(result[0]), result[1]
                        else:
                            print '\tOops', round(result[0]), result[1]


        else:
            print "The file",filename,"doesn't exist"
    except IndexError as e:
        print "No file was passed in as a variable"                


if __name__=='__main__':
    # main()
    multichannel()
    # smallSampleSize()
    # findTwoPop()

