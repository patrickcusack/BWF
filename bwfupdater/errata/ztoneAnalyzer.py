wimport os
import sys
import struct
import numpy as np
import logging
import math
import datetime
from pcwavefile import PCWaveFile

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

def anaylyzeData(inputData, byteWidth, sampleRate):
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
    data = np.array(sampleData)
    p = np.fft.fft(data)
    uniquePts = math.ceil(len(data)+1.0/2.0)
    p = p[0:uniquePts]
    freqs = np.fft.fftfreq(len(p))

    #### Find the peak in the coefficients
    idx = np.argmax(np.abs(p)**2)
    freq = freqs[idx]
    freqHz = abs(freq*sampleRate)

    ### Find the next highest peak which should exclude a nice band around the frequency of interest
    ### high end
    safeIdx = (idx + 10) if (idx + 10) < len(p) else idx
    pNext = p[safeIdx:len(p)-safeIdx]
    if len(pNext) > 0:
        idxNext = np.argmax(np.abs(pNext)**2)
        idxNext += safeIdx
        nextHighest = idxNext
    else:
        nextHighest = 0

    ### low end
    safeIdx = (idx - 10) if (idx - 10) > 0 else idx
    pNext = p[0:safeIdx]
    if len(pNext) > 0:
        idxNext = np.argmax(np.abs(pNext)**2)
    else:
        idxNext = 0

    if abs(p[idxNext]) > abs(p[nextHighest]):
        nextHighest = idxNext

    freqNext = freqs[nextHighest]
    freqHzNext = abs(freqNext*sampleRate)

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
    hightestdbRep = dbRepresentation(rms/dataLength)

    ### calculate the power of the next highest frequency index
    rmsNext = math.sqrt(p[nextHighest])
    dataLength = (len(inputData)/byteWidth)
    highestdbRepNext = dbRepresentation(rmsNext/dataLength)

    return tuple([freqHz,hightestdbRep, freqHzNext, highestdbRepNext])


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

                    print anaylyzeData(data, byteWidth, frate)    
                    dataRemaining -= len(data)
        else:
            print "The file",filename,"doesn't exist"
    except:
        print "No file was passed in as a variable" 

def smallSampleSize():
    data_size = 48000/24 #1 second of audio
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

                dataToReadChunkSize = data_size*byteWidth
                dataRemaining = dataLength
               
                while dataRemaining > 0:
                    if dataRemaining > dataToReadChunkSize:
                        data = f.read(dataToReadChunkSize)
                    else:
                        data = f.read(dataRemaining)

                    print anaylyzeData(data, byteWidth, sampleRate)    
                    dataRemaining -= len(data)
        else:
            print "The file",filename,"doesn't exist"
    except:
        print "No file was passed in as a variable" 


def multichannel():
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
            numberOfChannels = wavefile.numberOfChannels()
            print byteWidth, numberOfChannels

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

                    print "Next second", second
                    for channel in range(0, numberOfChannels):
                        subdata = ""
                        for x in range(channel*byteWidth,len(data),byteWidth*numberOfChannels):
                            # subdata.extend(data[x:x+3])
                            subdata += (data[x] + data[x+1] + data[x+2])

                        print anaylyzeData(subdata, byteWidth, sampleRate)

                    second += 1

        else:
            print "The file",filename,"doesn't exist"
    except IndexError as e:
        print "No file was passed in as a variable"         

def examine2pop():
    data_size = 48000/24 #1 second of audio
    frate = 48000.0 
    
    try:
        filePath = sys.argv[1]
        if os.path.exists(filePath):
            wavefile = PCWaveFile(filePath)

            if wavefile.isValidWaveFile() != True:
                print "File is not a wave file"
                return

            print wavefile.getFmtChunkDict()
            dataStartPos = wavefile.getDataChunk()["chunkPosition"]
            dataLength = wavefile.getDataChunk()["chunkSize"]
            sampleRate = wavefile.numberOfSamplesPerSecond()
            byteWidth = wavefile.numberOfBytesPerSample()


            with open(filePath, 'rb') as f:
                startTime = datetime.datetime.now()
                f.seek(dataStartPos)

                dataToReadChunkSize = data_size*byteWidth
                dataRemaining = dataLength
               
                while dataRemaining > 0:
                    if dataRemaining > dataToReadChunkSize:
                        data = f.read(dataToReadChunkSize)
                    else:
                        data = f.read(dataRemaining)

                    print anaylyzeData(data, byteWidth, sampleRate)    
                    dataRemaining -= len(data)
        else:
            print "The file",filename,"doesn't exist"
    except:
        print "No file was passed in as a variable" 

if __name__=='__main__':
    main()
    # multichannel()
    # smallSampleSize()
    # examine2pop()

