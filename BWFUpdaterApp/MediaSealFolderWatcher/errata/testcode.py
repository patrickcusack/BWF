import os
import re

def main():
	try:
		mainPath = os.path.expanduser("F:\\ArchiveTest\\PathStructure\\inBox\\WAV\\09 Mr. Wrong (feat. Drake).wav")
		subPath = mainPath.split("F:\\ArchiveTest\\PathStructure\\inBox\\")
		print mainPath.split("F:\\ArchiveTest\\PathStructure\\inBox\\")
		print subPath[0]
		os.makedirs(os.path.expanduser("~/Documents/ArchiveTest/inBox/GrandFather/Father/Son"))
	except OSError as e:
		print dir(e)
		print e.errno
		print e.strerror
		print e.message

def other():
		mainPath = os.path.expanduser("F:\\ArchiveTest\\PathStructure\\inBox\\WAV\\09 Mr. Wrong (feat. Drake).wav")
		subPath = mainPath.split("F:\\ArchiveTest\\PathStructure\\inBox\\")
		print mainPath.split("F:\\ArchiveTest\\PathStructure\\inBox\\")[1]
		path = os.path.normpath("F:\\ArchiveTest\\PathStructure\\inBox\\")
		print path.split(os.sep)

if __name__ == '__main__':
	# other()
	print '/1234567'.split(os.sep)[1]
	batchName = "12345678"
	filePath = "/A/B/C/12345678_FILEA.mov"
	originalFileName = os.path.basename(filePath).split((batchName + "_"))[1]
	print originalFileName
	daisyNumber = "DA000446098_31359_FTR_133_SM_ENG_01".split('_')
	print daisyNumber

	daisyPattern = re.compile(r"""(.*?)(DA[0-9]{0,12})(\_)(.+?$)""")
	m = daisyPattern.match('TESTFILE_DA000446098_31359_FTR_133_SM_ENG_01')
	if m != None:
		print m.groups()
	else:
		print 'm is invalid'

	returnCode = 0
	info = "There was a problem encrypting " + filePath + ". Encountered Error Code: " + str(returnCode) + ". The file will be moved to the path's Error box." 
	print info

	checksumA = "BE6680A51F2781631122ACB84645EFA4" 
	checksumB = "be6680a51f2781631122acb84645efa4"

	if checksumB.upper() != checksumA:
		print 'not equal'

	print checksumA.upper()
	print checksumB.upper()

	formattedString = '''ABCDEFGHIJKLMNOP %s'''
	print formattedString % ('Hello')


	print '123456789'
	print str('123456789')

	testBaseName = 'BaseName'
	print os.path.basename(testBaseName)



