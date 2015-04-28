import os
import sys
from time import sleep
import datetime
import sqlite3
import logging
import portalocker
import shutil
from pathutilities import fileNameForUUIDFileWithPath
from utility import DefaultLogger
from configurator import configurationOptions
from datastore import DataStore
from datastore import DataStoreRecord
from pathutilities import pathAfterSafelyMovingFileToDestinationFolder
from emailnotifier import sendSuccessEmail
from emailnotifier import sendFailureEmail

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
		pathStructureName 	= record.pathStructureName
		operationType		= record.operationType
		isBatch				= record.isBatch
		batchName			= record.batchName

		dateLastModified = datetime.datetime.strptime(dateModifiedString, '%Y-%m-%d %H:%M:%S')
		timeDifference = datetime.datetime.now() - dateLastModified

		#This can change with an if/else should I decide I want to put temp files to be decrypted in another place
		sourcePath = configurationOptions().pathStructureWithName(pathStructureName)['inBox']
		workingPath = configurationOptions().pathStructureWithName(pathStructureName)['workingBox']

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

		if datastore.doesTheFilePathExistElseWhereInThePathStructure(filePath, operationType, pathStructureName) == True:
			duplicatePath = configurationOptions().pathStructureWithName(pathStructureName)['duplicateBox']
			newPath = pathAfterSafelyMovingFileToDestinationFolder(filePath, duplicatePath)
			datastore.updateRecordAsDuplicateWithNewPath(newPath, key_id)
			continue

		newPath = filePath
		#Only update 
		if isBatch == 1 and operationType == 'Decrypt':
			amRecord = None
			uuidString = fileNameForUUIDFileWithPath(os.path.dirname(filePath))

			if uuidString == None:
				#if I can't resolve the UUID, then resovle it though an AM Record
				#Does file's Archive Manager have data associated with it
				amRecord = datastore.recordWithNumberFromAMJobsTable(batchName)
				if amRecord == None:
					info = "Acquire File: Archive Manager data doesn't exist for " + filePath
					info = info + " " + "Marking file as having no AM Data. File will not be moved through the processing queue."
					logging.debug(info)
					datastore.updateRecordStatusWithID(datastore.noArchiveManagerDataExistsForRecord(), key_id)
					continue
			else:
				logging.debug('Updating record %s with UUID %s' % (filePath, uuidString))
				amRecord = datastore.archiveManagerJobsTableRecordWithUUID(uuidString)
				datastore.updateRecordAWithBatchUUIDReference(uuidString, key_id)
		else:
			#at this point, I need to subtract the file's main folder from the pathStructure['inBox']
			#this moves the file from the inbox to the working path
			try:
				newPath = pathAfterSafelyMovingFileToDestinationFolder(filePath, workingPath)
			except Exception as e:
				logging.debug('This shouldn\'t happen as pathAfterSafelyMovingFileToDestinationFolder should create a unique name that avoids any collisions, otherwise the file has been moved')
				logging.debug('Acquire File: Error moving file')
				info = 'There was a problem moving the file into into the queue for: ' + os.path.basename(filePath)
				info = info + '\n' + 'This will require manual intervention as the occurrence is unique.'
				sendFailureEmail(info)
				continue

			logging.debug('Acquire File: updating record file status and path....')
			datastore.updateRecordAsStaticWithNewPath(newPath, key_id)

def checkArchiveManagerJobs(dbPath):
	logging = DefaultLogger()

	datastore = DataStore(dbPath)
	amRecords = datastore.archiveManagerJobsReadyToStart()

	for amRecord in amRecords:
		areAllFilesAvailableAndReady = True
		
		recordsInAMRecord = datastore.recordsForUUID(amRecord.uuid)
		filesInAMRecord = [x.fileName for x in recordsInAMRecord]
		filesInCurrentFolder = []

		try:
			filesInCurrentFolder = os.listdir(amRecord.amPath)
		except Exception as e:
			pass

		isThereAnUnknownFilePresent = False
		for currentFile in filesInCurrentFolder:
			if currentFile not in filesInAMRecord:
				isThereAnUnknownFilePresent = True

		if isThereAnUnknownFilePresent == True:
			logging.debug('Unknown files are present')
			pass
			#report error

		for currentFile in filesInAMRecord:
			logging.debug('%s' % (currentFile))
			lastComponent = os.path.basename(currentFile)
			if lastComponent not in filesInCurrentFolder:
				logging.debug('The following file is not yet available: %s' % (lastComponent))
				areAllFilesAvailableAndReady = False

		if areAllFilesAvailableAndReady == False:
			logging.debug('Not all of the files are staged yet')
			continue

		canLockAllRecords = True

		data = datastore.recordsForUUID(amRecord.uuid)

		for record in data:
			
			filePath = record.fileName

			try:
				fileToCheck = open(filePath, 'rb')
				portalocker.lock(fileToCheck, portalocker.LOCK_EX)
				fileToCheck.close()
				logging.debug('Acquire File: proceeding to update the file status knowing that no one else is using it...')
			except Exception as e:
				logging.debug('Acquire File: unable to lock file as it is likely in use')
				canLockAllRecords = False

		if canLockAllRecords == False:
			logging.debug('Can not lock all of the records yet')
			continue

		for record in data:

			key_id 				= record.id
			filePath 			= record.fileName
			recordSize 			= int(record.fileSize)
			dateModifiedString 	= record.dateModified
			pathStructureName 	= record.pathStructureName
			operationType		= record.operationType
			isBatch				= record.isBatch
			batchName			= record.batchName
			pathStructureName 	= record.pathStructureName

			newPath = filePath
			workingPath = configurationOptions().pathStructureWithName(pathStructureName)['workingBox']

			proposedBatchName = batchName + "_" + os.path.basename(filePath)
			proposedPath = os.path.join(os.path.dirname(filePath), proposedBatchName) 

			#we prepend the job name to the file here as it belongs to a batch
			try:
				if os.path.exists(proposedPath):
					raise Exception('file already exists')
				os.rename(filePath, proposedPath)
				filePath = proposedPath
			except Exception as e:
				#this is an unlikely occurrence
				info = 'There is a duplicate file in the queue for: ' + os.path.basename(filePath) + " " + e.message
				logging.debug(info)
				sendFailureEmail(info)
				continue

			#at this point, I need to subtract the file's main folder from the pathStructure['inBox']
			#this moves the file from the inbox to the working path
			try:
				newPath = pathAfterSafelyMovingFileToDestinationFolder(filePath, workingPath)
			except Exception as e:
				logging.debug('This shouldn\'t happen as pathAfterSafelyMovingFileToDestinationFolder should create a unique name that avoids any collisions, otherwise the file has been moved')
				logging.debug('Acquire File: Error moving file')
				info = 'There was a problem moving the file into into the queue for: ' + os.path.basename(filePath)
				info = info + '\n' + 'This will require manual intervention as the occurrence is unique.'
				sendFailureEmail(info)
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

	while True:
		sleep(5)
		
		loopcount = 0

		if loopcount % 10 == 0:
			logging.debug('Hash Process is alive')
		loopcount += 1

		checkSingleFiles(dbPath)
		checkArchiveManagerJobs(dbPath)





if __name__ == "__main__":
  path = os.path.join(os.path.expanduser('~/mediasealwatch'), 'database.db')
  verify(path)

