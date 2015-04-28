# def anaylyzeDataWithZeroCrossing(inputData, byteWidth, sampleRate):
# ### this must be refactored for the appropiate type of data
# ### for signed data
# maxValueForInputData = 2**((byteWidth*8)-1)
# sampleData = []
# for i in range(0,len(inputData), byteWidth):
#     try:
#         sampleData.append(les24toles32Value(inputData[i:i+byteWidth]) * 1.0/maxValueForInputData)
#     except Exception as e:
#         print e.message

# sig = np.array(sampleData)
# indices = matplotlib.mlab.find((sig[1:] >= 0) & (sig[:-1] < 0))
# crossings = [i - sig[i] / (sig[i+1] - sig[i]) for i in indices]
# return sampleRate / np.mean(np.diff(crossings))

title = 'MEHELP'
filePath = '/Users/patrickcusack/Desktop/DA000131702_E7206_MEHELP_EPS_CSP_audio_51D.wav'
numberOfChannels = 2

if title.lower() in filePath.lower():
	print title.lower()
	print filePath.lower()
	
	layout = 'MONO' if numberOfChannels == 1 else 'MULTI-MONO'
	print {"status":"pass", "resultString":"The file contains {} in its file name and will not be analyzed.".format(title), "layout":layout, "warningString":""}

