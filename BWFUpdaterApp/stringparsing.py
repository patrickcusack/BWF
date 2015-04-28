import requests
import json
import types
import re
import datetime

def doesStringContainBWFAnalyzerInfo(nString):
	try:
		daisyPattern = re.compile(r"""(.*)(<BWFAnalyzerInfo>.*</BWFAnalyzerInfo>)(.*)""")
		match = daisyPattern.match(nString)
		if match:
			return true
	except Exception as e:
		return nString
	return False

def stringMinusBWFAnalyzerInfo(nString):
	try:
		daisyPattern = re.compile(r"""(.*)(<BWFAnalyzerInfo>.*</BWFAnalyzerInfo>)(.*)""")
		match = daisyPattern.match(nString)
		if match == None or match.groups < 2:
			return nString
		return (match.group(1).strip() + " " + match.group(3).strip()).strip()
	except Exception as e:
		return nString

def BWFAnalyzerInfoForErrors(errors):
	return "{}{}{}".format("<BWFAnalyzerInfo>", " ".join(errors), "</BWFAnalyzerInfo>")

def BWFAnalyzerInfoForSuccess(fileName):
	dateString = datetime.datetime.now().strftime("%m-%d-%Y")
	timeString = datetime.datetime.now().strftime("%H:%M")
	return "{}{}{}".format("<BWFAnalyzerInfo>", "The file {} was analyzed on {} at {} and passed the criteria for BWF Analyzer".format(fileName, dateString, timeString), "</BWFAnalyzerInfo>")


def test():
	testString = '''<BWFAnalyzerInfo>No pop found at TimeCode 00:59:58:00 on channel 0. Found a tone on channel 0 at the wrong location 00:59:58:15 outside of 1 kHz 488. No pop found at TimeCode 00:59:58:00 on channel 1. Found a tone on channel 1 at the wrong location 00:59:57:16 outside of 1 kHz 977. No pop found at TimeCode 00:59:58:00 on channel 2. Found a tone on channel 2 at the wrong location 00:59:58:14 outside of 1 kHz 488. No pop found at TimeCode 00:59:58:00 on channel 3. Found a tone on channel 3 at the wrong location 00:59:59:07 outside of 1 kHz 63. No pop found at TimeCode 00:59:58:00 on channel 4. Found a tone on channel 4 at the wrong location 00:59:57:07 outside of 1 kHz 325. No pop found at TimeCode 00:59:58:00 on channel 5. Found a tone on channel 5 at the wrong location 00:59:57:05 outside of 1 kHz 1323.</BWFAnalyzerInfo>'''
	precomments = 'This file information is really important.'
	postcomments = 'And don\'t forget about this information as well.'

	joinedString = precomments + testString + postcomments
	print stringMinusBWFAnalyzerInfo(joinedString)

	joinedString = precomments + postcomments + testString 
	print stringMinusBWFAnalyzerInfo(joinedString)

	joinedString = testString + precomments + postcomments
	print stringMinusBWFAnalyzerInfo(joinedString)

	joinedString = precomments +  postcomments
	print stringMinusBWFAnalyzerInfo(joinedString)

	joinedString = testString +  postcomments
	print stringMinusBWFAnalyzerInfo(joinedString)

	joinedString = postcomments + testString
	print stringMinusBWFAnalyzerInfo(joinedString)

	joinedString = testString
	print stringMinusBWFAnalyzerInfo(joinedString)

	for a in [precomments,testString, postcomments]:
		for b in [testString, postcomments, precomments]:
			for c in [postcomments, precomments,testString]:
				nString = a + b + c
				if doesStringContainBWFAnalyzerInfo(nString):
					print a+b+c+ ' contains the string'
					print '\n'
				print stringMinusBWFAnalyzerInfo(a+b+c)
				print '\n'

if __name__ == '__main__':
	print stringMinusBWFAnalyzerInfo("Hello")
	print stringMinusBWFAnalyzerInfo('')
	print BWFAnalyzerInfoForSuccess('MyBWFFile.wav')


