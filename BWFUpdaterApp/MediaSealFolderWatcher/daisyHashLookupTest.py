import sys
import os
from hashfile import hashForFilePath
from daisyretrieval import getDaisyNumber
from daisyretrieval import DaisyMetadataLookup

def main():
	try:
		filePath = sys.argv[1]
		daisyNumber = getDaisyNumber(os.path.basename(filePath))
		print daisyNumber
		if daisyNumber != None:
			md5Hash = hashForFilePath(filePath)
			basename = os.path.basename(filePath)
			originalChecksum = DaisyMetadataLookup(daisyNumber).checksumForFile(basename)
			if md5Hash != originalChecksum:
				print 'Error: Checksums don\'t match', md5Hash, originalChecksum
			else:
				print 'Match', md5Hash, originalChecksum
		else:
			print 'couldnt get daisy number' 

	except Exception as e:
		print e.message

if __name__ == '__main__':
	# print getDaisyNumber('ChicagoPd_DA000464551_CML04_EPS_Television_2398_16x9FF_178_ENG_HD_ProResHQ_220M.mov')
	# print DaisyMetadataLookup('DA000464551').checksumForFile('ChicagoPd_DA000464551_CML04_EPS_Television_2398_16x9FF_178_ENG_HD_ProResHQ_220M.mov')
	# print DaisyMetadataLookup('DA000464551').fileSizeForFile('ChicagoPd_DA000464551_CML04_EPS_Television_2398_16x9FF_178_ENG_HD_ProResHQ_220M.mov')
	# print DaisyMetadataLookup('DA000464551').assetFiles()
	print DaisyMetadataLookup('DA000400824').assetFiles()
	# main()