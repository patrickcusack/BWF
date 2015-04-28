import os
import time
import shutil
import uuid

def fileNameForUUIDFileWithPath(folderPath):
	files = os.listdir(folderPath)
	for fileElem in files:
		if fileElem.startswith('UUID_'):
			return fileElem
	return None

def createFileWithUUIDatPath(path):
	uuidString = 'UUID_' + str(uuid.uuid1())
	with open(os.path.join(path, uuidString), 'a') as f:
		f.write(uuidString)
	return uuidString

def doesPathContainFolders(path):
	for root, dirs, files in os.walk(path):
		if len(dirs) > 0:
			return True
		return False

def visibleFilesInFolder(path):
	allFiles = []
	for root, dirs, files in os.walk(path):
		for name in files:
			if not name.startswith('.'):
				allFiles.append(name)
	return allFiles

def pathAfterSafelyMovingFileToDestinationFolder(filePath, destinationFolder):
	#if the file already exists, then we need to rename the file we are moving so we can avoid collisions
	if os.path.exists(os.path.join(destinationFolder, os.path.basename(filePath))):
		origbase = os.path.basename(filePath)
		base = os.path.splitext(origbase)[0]
		ext = ''
		if len(os.path.splitext(origbase)) > 1:
			ext = os.path.splitext(origbase)[1]
		newbase = base + "_" + time.strftime("%H%M%m%d%y") + ext
		renamedFilePath = os.path.join(os.path.dirname(filePath), newbase)
		shutil.move(filePath, renamedFilePath)
		shutil.move(renamedFilePath, destinationFolder)
		return os.path.join(destinationFolder, os.path.basename(renamedFilePath))
	else:
		shutil.move(filePath, destinationFolder)
		return os.path.join(destinationFolder, os.path.basename(filePath))

def pathAfterSafelyMovingFileToDestinationFile(filePath, destinationFile):
	#if the file already exists, then we need to rename the file we are moving so we can avoid collisions
	if os.path.exists(destinationFile):
		origbase = os.path.basename(filePath)
		base = os.path.splitext(origbase)[0]
		ext = ''
		if len(os.path.splitext(origbase)) > 1:
			ext = os.path.splitext(origbase)[1]
		newbase = base + "_" + time.strftime("%H%M%m%d%y") + ext
		renamedFilePath = os.path.join(os.path.dirname(filePath), newbase)
		shutil.move(filePath, renamedFilePath)
		return renamedFilePath
	else:
		shutil.move(filePath, destinationFile)
		return destinationFile

def pathAfterSafelyMovingFolderToDestinationFolder(folder, destinationFolder):
	#if the file already exists, then we need to rename the file we are moving so we can avoid collisions
	if os.path.exists(os.path.join(destinationFolder, os.path.basename(folder))):
		print os.path.join(destinationFolder, os.path.basename(folder)), ' already exists'
		origbase = os.path.basename(folder)
		newbase = origbase + "_" + time.strftime("%H%M%m%d%y") 
		newFolderPath = os.path.join(os.path.dirname(folder), newbase)
		os.rename(folder, newFolderPath)
		shutil.move(newFolderPath, destinationFolder)
		return os.path.join(newFolderPath, destinationFolder)
	else:
		print os.path.join(destinationFolder, os.path.basename(folder)), ' does not already exist'
		shutil.move(folder, destinationFolder)
		return os.path.join(destinationFolder, os.path.basename(folder))

def createSafeFolderInDestinationFolder(destinationFolder, folderPath):
	#if the file already exists, then we need to rename the file we are moving so we can avoid collisions
	if os.path.exists(os.path.join(destinationFolder, os.path.basename(folderPath))):
		origbase = os.path.basename(folderPath)
		newbase = origbase + "_" + time.strftime("%H_%M_%m_%S_%d_%y")
		renamedFolderPath = os.path.join(destinationFolder, newbase)
		os.mkdir(renamedFolderPath)
		return renamedFolderPath
	else:
		newFolder = os.path.join(destinationFolder, os.path.basename(folderPath))
		os.mkdir(newFolder)
		return newFolder	

def main():
	print pathAfterSafelyMovingFileToDestinationFolder(os.path.expanduser('~/Desktop/EXAMPLE.xml'), os.path.expanduser('~/Desktop/destination'))

if __name__ == '__main__':
	# main()
	# print createSafeFolderInDestinationFolder("/Users/patrickcusack/Desktop/Propman", 'TestFolder')
	# print pathAfterSafelyMovingFileToDestinationFile('/Users/patrickcusack/Desktop/kris/IMG_0845.jpg', '/Users/patrickcusack/Desktop/Folder1/IMG_0845.jpg')
	createFileWithUUIDatPath(os.path.expanduser('~/Desktop/'))

