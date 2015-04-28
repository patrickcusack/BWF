import sys
import os 
from daisy import setStatusAsAvailable
from daisy import setComments
from daisy import DaisyMetadataLookup
from daisy import getDaisyNumber
from stringparsing import stringMinusBWFAnalyzerInfo


def cleanRecords(path):

	print path
	if not os.path.isdir(path):
		print path, "is not a folder"
		return

	files = os.listdir(path)

	for fileName in files:
		dLookup = DaisyMetadataLookup(getDaisyNumber(fileName))
		if dLookup.isValid == True:
			comments = stringMinusBWFAnalyzerInfo(dLookup.comments())
			setStatusAsAvailable(getDaisyNumber(fileName))
			setComments(getDaisyNumber(fileName), comments)

		dLookup = DaisyMetadataLookup(getDaisyNumber(fileName))
		if dLookup.isValid == True:
			print fileName, dLookup.comments(), dLookup.status()

if __name__ == '__main__':
	cleanRecords(sys.argv[1])