import os
import sys
import pathutilities

if __name__ == '__main__':

	allFiles = []
	foundDirectories = False
	
	if pathutilities.doesPathContainFolders(sys.argv[1]):
		print 'Found folders in...'

	files = pathutilities.visibleFilesInFolder(sys.argv[1])
	print files
	print len(files)
