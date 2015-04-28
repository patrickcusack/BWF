import wave
import struct
import numpy as np

def les24toles32Value(fileDataAsString):
    if len(fileDataAsString) != 3:
        print "error"

    return struct.unpack('<i', fileDataAsString + ('\xff' if ord(fileDataAsString[2]) & 0x80 else '\0'))[0]

#16384

if __name__=='__main__':
    data_size=192000
    frate=48000.0 

    with open('/Users/patrickcusack/Desktop/440.wav', 'rb') as f:
        f.seek(16384)
        data = f.read(data_size*3)
        print len(data)

        sampleData = []
        for i in range(0,data_size*3, 3):
            sampleData.append(les24toles32Value(data[i:i+3]))

        # data=struct.unpack('{n}h'.format(n=data_size), data)
        data=np.array(sampleData)

        w = np.fft.fft(data)
        freqs = np.fft.fftfreq(len(w))
        print(freqs.min(),freqs.max())
        # (-0.5, 0.499975)

        # Find the peak in the coefficients
        idx=np.argmax(np.abs(w)**2)
        freq=freqs[idx]
        freq_in_hertz=abs(freq*frate)
        print(freq_in_hertz)
        # 439.8975


# import wave
# import struct
# import numpy as np

# if __name__=='__main__':
#     data_size=40000
#     fname="test.wav"
#     frate=11025.0 
#     wav_file=wave.open(fname,'r')
#     data=wav_file.readframes(data_size)
#     wav_file.close()
#     data=struct.unpack('{n}h'.format(n=data_size), data)
#     data=np.array(data)

#     w = np.fft.fft(data)
#     freqs = np.fft.fftfreq(len(w))
#     print(freqs.min(),freqs.max())
#     # (-0.5, 0.499975)

#     # Find the peak in the coefficients
#     idx=np.argmax(np.abs(w)**2)
#     freq=freqs[idx]
#     freq_in_hertz=abs(freq*frate)
#     print(freq_in_hertz)
#     # 439.8975        