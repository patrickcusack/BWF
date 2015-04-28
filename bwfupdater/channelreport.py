import sys
import os
import json

def tabDelimitedResult(jsonObject):
	fileName = jsonObject['fileName']

	if 'fullPath' not in jsonObject.keys():
		return "\t".join([fileName,"file is not a wave file"])

	fileName = jsonObject['fileName']
	fullPath = jsonObject['fullPath']
	result 	 = jsonObject['result']
	layout 	 = jsonObject['fileLevels']['layout']

	LRCorrelation = ""
	LRExceedLsRs = ""
	LSRSCorrelation = ""

	if layout not in ['STEREO','Unknown']:
		LRCorrelation = str(jsonObject['fileLevels']['LRCorrelation'])
		LRExceedLsRs = str(jsonObject['fileLevels']['LRExceedLsRs'])
		LSRSCorrelation = str(jsonObject['fileLevels']['LSRSCorrelation'])

	errors 	 = jsonObject['errors']
	
	errorString  = ""
	warningString = ""

	if type(errors) is int:
		errorString = "No Errors"
	else:
		if len(errors) > 0:
			errorString = " ".join(jsonObject['errors'])
		else:
			errorString = "No Errors"

	if 'warnings' in jsonObject.keys():
		warnings = jsonObject['warnings']
		warningString = " ".join(jsonObject['warnings'])
	else:
		warningString = 'No Warnings'

	return "\t".join([fileName,fullPath,result,layout,errorString,warningString,LRCorrelation, LRExceedLsRs, LSRSCorrelation])

def jsonObjectForFileContents(filePath):
	with open(filePath, "r") as f:
		data = f.read()
		return json.loads(data)

def prettyPrintJSON(data):
	return json.dumps(data, sort_keys = True, indent=4, separators=(',', ': '))

def main():
	filePath = None
	allResults = []
	resultFilePath = ''

	try:
		filePath = sys.argv[1]
	except Exception:
		print "No file specified"
		return

	if os.path.isdir(filePath):
		resultFilePath = os.path.join(filePath, 'tabresults.txt')
	else:
		resultFilePath = os.path.join(os.path.dirname(filePath), 'tabresults.txt')

	if os.path.isdir(filePath):
		for path, dirs, files in os.walk(filePath):
		    for name in files:
		    	if '.json' in name:
			    	fullpath = os.path.join(path, name)
			    	allResults.extend(jsonObjectForFileContents(fullpath)['results'])
	else:
		allResults.extend(jsonObjectForFileContents(filePath)['results'])

	tabDelimitedString = ''
 	for result in allResults:
 		tabDelimitedString += (tabDelimitedResult(result) + '\n')

 	if tabDelimitedString != '':
	 	with open(resultFilePath, 'w') as f:
	 		f.write(tabDelimitedString)


if __name__ == '__main__':
	main()