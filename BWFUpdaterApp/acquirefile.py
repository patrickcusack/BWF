import os
import sys
import datetime
import sqlite3
import portalocker
import shutil

from time import sleep
from utility import DefaultLogger

from configurationoptions import configurationOptions
from datastore import DataStore
from datastore import DataStoreRecord

from pathutilities import pathAfterSafelyMovingFileToDestinationFolder

verificationWaitTime = 60

def checkSingleFiles(dbPath):
	logging = DefaultLogger()

	if not os.path.exists(dbPath):
		logging.debug('Acquire File: can\'t find database at path')
		return
	
	datastore = DataStore(dbPath)
	data = datastore.recordsForVerifying()

	for record in data:

		key_id 				= record.id
		filePath 			= record.fileName
		recordSize 			= int(record.fileSize)
		dateModifiedString 	= record.dateModified

		dateLastModified = datetime.datetime.strptime(dateModifiedString, '%Y-%m-%d %H:%M:%S')
		timeDifference = datetime.datetime.now() - dateLastModified

		#This can change with an if/else should I decide I want to put temp files to be decrypted in another place
		sourcePath = configurationOptions().defaultPathStructure()['inBox']
		workingPath = configurationOptions().defaultPathStructure()['workingBox']

		if timeDifference.seconds < verificationWaitTime:
			continue

		lastSize = recordSize
		currentSize = 0

		if not os.path.exists(filePath):
			logging.debug('Acquire File: Will update record status as the file no longer exists')
			datastore.updateRecordAsMissingWithID(key_id)
			continue

		currentSize = os.path.getsize(filePath)

		if lastSize != currentSize:
			logging.debug(record)
			logging.debug('Acquire File: attempting db modify as file size has changed...')
			datastore.updateRecordWithCurrentSizeAndDateModifiedWithID(currentSize, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), key_id)
			continue

		if currentSize == 0:
			continue
			# if the current size is zero, then continue until it isn't or never will be
			# its likely the file has been queued to copy but no data has been moved yet (actual OSX case) 
			
		logging.debug('Acquire File: attempting to lock the file to see if I own the file yet...')

		try:
			fileToCheck = open(filePath, 'rb')
			portalocker.lock(fileToCheck, portalocker.LOCK_EX)
			fileToCheck.close()
			logging.debug('Acquire File: proceeding to update the file status knowing that no one else is using it...')
		except Exception as e:
			logging.debug('Acquire File: unable to lock file as it is likely in use')
			continue

		#must test that file doesn't exist elsewhere in the path

		newPath = filePath
		try:
			newPath = pathAfterSafelyMovingFileToDestinationFolder(filePath, workingPath)
		except Exception as e:
			info = '''This shouldn\'t happen as pathAfterSafelyMovingFileToDestinationFolder should create a unique name that avoids any collisions, otherwise the file has been moved'''
			logging.debug(info)
			logging.debug('Acquire File: Error moving file')
			info = 'There was a problem moving the file into into the queue for: ' + os.path.basename(filePath)
			info = info + '\n' + 'This will require manual intervention as the occurrence is unique.'
			#SEND FAILURE EMAIL
			continue

		logging.debug('Acquire File: updating record file status and path....')
		datastore.updateRecordAsStaticWithNewPath(newPath, key_id)


def acquirefile(dbPath):
	'''
	This process examines the database pointed to by dbPath. It  looks for any records which 
	have status 0 and looks at the dateModified time. If the
	elapsed time since the record was modified is greater than two minutes, then it checks
	the record's size. If the file pointed to by the record doesn't exist, then I change 
	this to another status like -1. If the file size is the same, then the databse marks 
	the file status as 1 or ready to hash. If the filesize is different, then the file's
	dateModified is updated and the status is unchanged, resulting in the file being re-examined
	in the next loop. Once the file is verified, the file is moved to a path defined by 
	workingPath (that is if the path is different).
	'''

	logging = DefaultLogger()
	loopcount = 0

	while True:
		sleep(5)
		if loopcount % 10 == 0:
			logging.debug('acquire loop is active...')
		loopcount += 1

		checkSingleFiles(dbPath)



if __name__ == "__main__":
  path = os.path.join(os.path.expanduser('~/mediasealwatch'), 'database.db')
  verify(path)

