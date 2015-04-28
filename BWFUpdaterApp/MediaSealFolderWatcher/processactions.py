import os
import sys
import shutil
from time import sleep
import datetime
import sqlite3
import logging
import portalocker
from hashfile import hashForFile
from utility import DefaultLogger
from configurator import configurationOptions
from datastore import DataStore
from datastore import DataStoreRecord
from datastore import ArchiveManagerRecord
from pathutilities import pathAfterSafelyMovingFileToDestinationFolder
from pathutilities import pathAfterSafelyMovingFileToDestinationFile
from pathutilities import pathAfterSafelyMovingFolderToDestinationFolder
from pathutilities import createSafeFolderInDestinationFolder
from pathutilities import visibleFilesInFolder
from objectdefinitionxml import writeXmlObjectDefinitionRepresentationToFilePath

from daisyretrieval import getDaisyNumber
from daisyretrieval import DaisyMetadataLookup
from emailnotifier import sendSuccessEmail
from emailnotifier import sendFailureEmail

#should rename this module to post processing

def preprocess(dbPath):
	'''
	This is a preprocess module
	'''
	logging = DefaultLogger()

	if not os.path.exists(dbPath):
		logging.debug('PreProcess: can\'t find database at path')
		return

	datastore = DataStore(dbPath)
	loopcount = 0

	while True:
		sleep(5)

		if loopcount % 10 == 0:
			logging.debug('PreProcess is alive')
		loopcount += 1

		data = datastore.recordsForHashing()
		for record in data:
			logging.debug(record)

			key_id = record.id
			filePath = record.fileName

			if not os.path.exists(filePath):
				logging.debug('PreProcess: Will update record status as the file no longer exists')
				datastore.updateRecordAsMissingWithID(key_id)
				continue

			try:
				logging.debug('PreProcess: locking file to calculate hash...')
				##UPDATE HASH OPERATION START HERE
				startTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				datastore.updateRecordWithHashStart(startTime, key_id)

				fileToHash = open(filePath, 'rb')
				portalocker.lock(fileToHash, portalocker.LOCK_SH)
				hashString = "NO_OP"#hashForFile(fileToHash) 
				endTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				fileToHash.close()

				logging.debug('PreProcess: unlocking file...')
				logging.debug('PreProcess: Will update record status with Hash string and times')

				datastore.updateRecordWithHashForStartTimeAndEndTime(hashString, startTime, endTime, key_id)

			except Exception as e:
				info = 'PreProcess: There was an error when calculating the hash for file: ' + os.path.basename(filePath) + ' ' + e.message
				sendFailureEmail(info)
				logging.error(e.message)


def processRecordsReadyToBeHashed(data, datastore):

	logging = DefaultLogger()

	for record in data:
		logging.debug(record)

		key_id 				= record.id
		sourceFilePath 		= record.fileName
		filePath 			= record.operationFileName
		recordOperationType = record.operationType
		pathStructureName 	= record.pathStructureName			
		isBatch				= record.isBatch
		batchName			= record.batchName

		currentPathStructure = configurationOptions().pathStructureWithName(pathStructureName)
		finalPath = currentPathStructure['outBox']
		finalOriginalDestinationPath = currentPathStructure['originalBox']
		errorPath = currentPathStructure['errorBox']

		if not os.path.exists(filePath):
			# if the processed file doesn't exist, then move update the record and move to the error box
			# ADD LOGIC FOR BATCH PROCESSING
			logging.debug('PostProcess: Will update record status as the encrypted file does not exist')
			newPath = pathAfterSafelyMovingFileToDestinationFolder(sourceFilePath, errorPath)
			datastore.updateRecordAsMissingWithFileNameAndID(newPath, key_id)
			continue

		#CALCULATE HASH
		startTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		datastore.updateRecordWithReHashStart(startTime, key_id)
		hashString = 'NO_HASH'

		#only hash files being decrypyted
		if recordOperationType == 'Decrypt':
			try:
				fileToHash = open(filePath, 'rb')
				logging.debug('PostProcess: locked file to calculate hash...')
				portalocker.lock(fileToHash, portalocker.LOCK_SH)
				hashString = hashForFile(fileToHash)
				logging.debug('PostProcess Hasher: unlocking file...')
				fileToHash.close()
			except Exception as e:
				hashString = 'HASH_GEN_ERROR'
		else:
			hashString = "NO_HASH_FOR_ENCRYPTED_FILES"

		endTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		
		#ONLY DECRYPTED FILES' HASH IS CHECKED
		didChecksumFail = False
		checkSumErrorString = None

		if recordOperationType == 'Decrypt':
			fileBaseName = os.path.basename(filePath)
			if isBatch:
				fileBaseName = os.path.basename(filePath).split((batchName + "_"))[1]

			daisyNumber = getDaisyNumber(fileBaseName)

			try:
				errorRecordStatus = 0
				if daisyNumber == None:
					errorString = 'There was an error Decrypting the file: ' + fileBaseName + '.\n'
					errorString = errorString + 'Unable to retrieve Daisy Number for ' + filePath + ' ' + batchName
					logging.debug(errorString)
					errorRecordStatus = datastore.daisyEntryNotFoundStatusCode()
					raise Exception(errorString)

				originalChecksum = DaisyMetadataLookup(daisyNumber).checksumForFile(fileBaseName)
				
				if originalChecksum == None:
					errorString = 'There was an error Decrypting the file: ' + fileBaseName + '.\n'
					errorString = errorString + 'Unable to retrieve Checksum for ' + filePath + ' ' + batchName
					logging.debug(errorString)
					errorRecordStatus = datastore.checksumLookupFailedStatusCode()
					raise Exception(errorString)

				if originalChecksum.upper() != hashString.upper():
					errorString = 'Checksums do not match for file ' + filePath + '\n'
					errorString = errorString + ' ' + batchName + " expected the checksum: " + originalChecksum + '\n'
					errorString = errorString + " but found this checksum instead:" + hashString
					logging.debug(errorString)
					errorRecordStatus = datastore.checksumComparisonFailedStatusCode()
					raise Exception(errorString)

			except Exception as checksumException:
				#we have an error, so we must create a new folder in the error path
				#if the file is non-batch, then 
				logging.debug('PostProcess: The checksum failed. Please see the appropriate Error Box')
				checkSumErrorString = 'There was a checksum error.' + '\n' + checksumException.message
				didChecksumFail = True

			#If the file failed a checksum and is not a bacth file, then move it to the error box
			if didChecksumFail == True and isBatch == False:
				errorPathInformation = ''
				try:
					logging.debug('PostProcess: creating a Decrypted Checksum folder')
					errorDestination = createSafeFolderInDestinationFolder(errorPath, 'DECRYPTED_CHECKSUM_ERROR')
					try: 
						info = 'Moving the file that errored into the folder at ' + errorDestination
						logging.debug(info)
						shutil.move(filePath, os.path.join(errorDestination,fileBaseName))
						errorPathInformation = info
					except Exception as e:
						info = "PostProcess: " + e.message + ' an error occurred moving the file: ' + fileBaseName + ' to ' + errorDestination
						logging.debug(info)
				except Exception as e:
					info = 'PostProcess: An error occurred when moving the decrypted file in to the Error box'
					logging.debug(info)

				#THEN MOVE THE ENCRYPTED FILE ASIDE TO THE ERROR BOX
				try:
					info = 'Moving  the source file into the error box at ' + errorPath
					logging.debug(info)
					newPath = pathAfterSafelyMovingFileToDestinationFolder(sourceFilePath, errorPath)
					errorPathInformation = errorPathInformation + '\n' + info
				except Exception as e:
					info = "PostProcess: " + e.message + ' an error occurred moving the file: ' + sourceFilePath
					logging.debug(info)

				datastore.updateRecordStatusWithID(errorRecordStatus, key_id)
				info = checksumException.message + '\n' + errorPathInformation
				logging.debug(info)
				sendFailureEmail(info)
				continue
	
		#Lets now address the batch decrypted files

		newPath = filePath
		success = False

		if isBatch == True and recordOperationType == 'Decrypt':
			#create the destination folder for the Archive Manager Job
			amRecord = datastore.recordWithNumberFromAMJobsTable(batchName)
			if amRecord is None:
				#This should not happen as we don't even allow for the logic to proceed to this point without
				#a valid Archive Manager Record
				info = 'An error occurred where no data was found for the Archive Manager job ' + batchName + '\n'
				info = info + 'This error should not happen. Please check ' + os.path.dirname(filePath) + '\n'
				info = info + 'The files will need to be manually removed from the Decryption Queue.'
				logging.debug(info)
				sendFailureEmail(info)
				continue

			if didChecksumFail == True:
				#add checksum error string to archive manager job
				amRecord.errorString = amRecord.errorString + '\n' + checkSumErrorString
				datastore.updateArchiveManagerJobErrorString(amRecord, amRecord.errorString)

			#create the new folder in interim where we will push all of the batch files
			destinationAMFolder = os.path.join(os.path.dirname(filePath), batchName)
			if not os.path.exists(destinationAMFolder):
				try:
					os.mkdir(destinationAMFolder)
				except OSError as e:
					pass
			
			#get the file name, strip leading archive manager number
			originalFileName = os.path.basename(filePath)
			if isBatch == True:
				originalFileName = os.path.basename(filePath).split((batchName + "_"))[1]

			#this is where we will move the interim file, a new folder with its original name
			proposedAMPath = os.path.join(destinationAMFolder, originalFileName)

			#at this point the file should be in the a folder named after the batch
			try:
				newPath = pathAfterSafelyMovingFileToDestinationFile(filePath, proposedAMPath)
			except Exception as e:
				info = 'There was an error moving a file at %s for Archive Manager job %s. This will need to be manually addressed.' % (filePath, batchName)
				sendFailureEmail(info)
				continue

			if os.path.basename(originalFileName) != os.path.basename(newPath):
				#there was a collision, there really is no reason why this should happen, but lets account for it
				errorString = 'For some reason, there already exists a file in %s labeled %s' % (destinationAMFolder, originalFileName) + '\n'
				amRecord.errorString = amRecord.errorString + '\n' + errorString
				datastore.updateArchiveManagerJobErrorString(amRecord, amRecord.errorString)

			success = datastore.updateRecordWithFinalEncryptedPathAndHashForStartTimeAndEndTime(newPath, hashString, startTime, endTime, key_id)
			currentFiles = visibleFilesInFolder(destinationAMFolder)

			amPath = amRecord.amPath
			filesInJob = amRecord.allFilesInRecord()
			
			#are we finished, are all the files in place or the batch job?
			try:
				areAllFilesInPlace = True			
				for nFile in filesInJob:
					if nFile not in currentFiles:
						areAllFilesInPlace = False

				if areAllFilesInPlace == False:
					continue

				logging.debug('All files are in place')
				try:
					#remove old source folder
					logging.debug('PostProcess: removing original inbox')
					shutil.rmtree(amPath)
				except OSError as e:
					info = "PostProcess: " + e.message
					logging.debug(info)
					info = 'There was a problem removing the folder %s from the inbox after decrypting all of the files in the job.' % (amPath)
					sendFailureEmail(info)

				#refresh the record
				amRecord = datastore.recordWithNumberFromAMJobsTable(batchName)
				if amRecord is None:
					#This should not happen as we don't even allow for the logic to proceed to this point without
					#a valid Archive Manager Record
					info = 'An error occurred where no data was found for the Archive Manager job ' + batchName + '\n'
					info = info + 'This error should not happen. Please check ' + destinationAMFolder + '\n'
					info = info + 'The files will need to be manually removed from the Decryption Queue.'
					logging.debug(info)
					sendFailureEmail(info)
					continue

				#if there is an error, the redirect to the error box
				if amRecord.errorString != '':
					finalPath = errorPath
					#move the error files into a folder that indicates they are errors, it will live in the error box
					try:
						if datastore.updateArchiveManagerJobAsErrored(amRecord) == True:
							logging.debug('Job has finished, but there were some errors')
							logging.debug('PostProcess: will send email')
							info = 'Job %s has some errors! Please see the ErrorBox at %s' % (batchName, errorPath)
							info = info + '\n' + amRecord.errorString
							sendFailureEmail(info)
						else:
							logging.debug('PostProcess: Error saving Job')

						errDirname = os.path.dirname(destinationAMFolder)
						errBasename = os.path.basename(destinationAMFolder) + '_DECRYPTED_ERROR'
						os.rename(destinationAMFolder, os.path.join(errDirname, errBasename))
						destinationAMFolder = os.path.join(errDirname, errBasename)
						# shutil.move(destinationAMFolder, errorPath)
						pathAfterSafelyMovingFolderToDestinationFolder(destinationAMFolder, errorPath)

					except Exception as e:
						info = 'An error occurred when moving the errored files to %s.' % (errorPath,)
						logging.debug(info)
						sendFailureEmail(info)
				else:
					#No errors, move the files to the appropriate place
					print "No Errors finalPath", finalPath
					try:
						logging.debug('PostProcess: moving archive mananger folder to final destination')
						if os.path.exists(os.path.join(finalPath, os.path.basename(destinationAMFolder))):
							logging.debug('PostProcess: collision moving to duplicate box')
							altPath = pathAfterSafelyMovingFileToDestinationFolder(destinationAMFolder, finalPath)
						else:
							shutil.move(destinationAMFolder, finalPath)

						if datastore.updateArchiveManagerJobAsReadyToComplete(amRecord) == True:
							logging.debug('PostProcess: job is ready to complete')
							logging.debug('PostProcess: moving files and sending email')
							info = 'Job %s is complete! All of the files are decrypted and have appropriate matching checksums.' % (batchName)
							sendSuccessEmail(info)
						else:
							logging.debug('PostProcess: Error saving Job')	

					except OSError as e:
						#again, I am accounting for this error, I just don't know why I would ever encounter a situation like this
						info = 'There was a problem moving the folder %s to the outbox. You will have to move the file manually.' % (destinationAMFolder)
						info = info + " " + e.message
						sendFailureEmail(info)
						logging.debug(info)
						continue

			except Exception as e:
				info = 'An error occurred. Please see check the Decryption Queue for job %s. See Error: %s' % (batchName, e.message)
				logging.debug(info)
				sendFailureEmail(info)

		else:
			#LAST CASE FOR SINGLE MODE FILES LIKE ENCRYPTION AND SINGLE MODE DECRYPTION 
			newPath = pathAfterSafelyMovingFileToDestinationFolder(filePath, finalPath)	

			if not os.path.exists(newPath):
				logging.debug('PostProcess: Error moving file')
				continue

			logging.debug('PostProcess: Will update record status with Hash string and times')

			success = datastore.updateRecordWithFinalEncryptedPathAndHashForStartTimeAndEndTime(newPath, 
				hashString, startTime, endTime, key_id)

			if success == True:
				# move original file to original box
				try:
					newPath = pathAfterSafelyMovingFileToDestinationFolder(sourceFilePath, finalOriginalDestinationPath)
				except Exception as e:
					logging.debug('There was an error moving the file into place')
					info = 'There was an error moving file %s into the outbox at %s' % (sourceFilePath, finalOriginalDestinationPath)
					sendFailureEmail(info)

				if configurationOptions().shouldDeleteOriginal == True:
					try:
						os.remove(newPath)
					except OSError as e:
						logging.debug('PostProcess: Unable to delete the file', newPath)



def postprocess(dbPath):
	'''
	This is the post process module
	'''
	
	if not os.path.exists(dbPath):
		logging.debug('PreProcess: can\'t find database at path')
		return

	datastore = DataStore(dbPath)

	loopcount = 0	

	while True:
		sleep(5)

		if loopcount % 10 == 0:
			logging.debug('PostProcess is alive')
		loopcount += 1

		#calculate checksums on decrypted files
		data = datastore.recordsForReHashing()

		processRecordsReadyToBeHashed(data, datastore)
		
		#delete associated files as the job was successful
		amRecords = datastore.archiveManagerJobsReadyToComplete()
		for amRecord in amRecords:
			dataStoreRecords = datastore.recordsForUUID(amRecord.uuid)
			for record in dataStoreRecords:
				recordPath = record.fileName
				if configurationOptions().shouldDeleteOriginal == True:
					try:
						os.remove(recordPath)
					except OSError as e:
						info = 'PostProcess: Unable to delete the file %s' % (recordPath,)
						logging.debug(info)
			datastore.updateArchiveManagerJobAsComplete(amRecord)


		#move the associated files to the error box as the job had problems
		amRecords = datastore.archiveManagerJobsThatErrored()
		for amRecord in amRecords:
			logging.debug('performing clean up with ' + amRecord.amNumber)

			batchName 			= amRecord.amNumber
			destinationAMFolder = ''
			errorPath 			= ''

			dataStoreRecords = datastore.recordsForUUID(amRecord.uuid)
			for record in dataStoreRecords:
				pathStructureName 		= record.pathStructureName
				filePath 				= record.fileName
				currentPathStructure 	= configurationOptions().pathStructureWithName(pathStructureName)
				errorPath 				= currentPathStructure['errorBox']
				print filePath

				destinationAMFolder = os.path.join(os.path.dirname(filePath), batchName)
				print 'This is where the working files will go.', destinationAMFolder

				if not os.path.exists(destinationAMFolder):
					try:
						os.mkdir(destinationAMFolder)
					except OSError as e:
						pass

				originalFileName = os.path.basename(filePath).split((batchName + "_"))[1]
				proposedAMPath = os.path.join(destinationAMFolder, originalFileName)

				try:
					# newPath = pathAfterSafelyMovingFileToDestinationFile(filePath, proposedAMPath)
					print filePath, proposedAMPath
					shutil.move(filePath, proposedAMPath)
				except Exception as e:
					info = 'There was an error moving a file at %s for Archive Manager job %s. This will need to be manually addressed.' % (filePath, batchName)
					sendFailureEmail(info)
					continue

				currentFiles = os.listdir(destinationAMFolder)
				filesInJob = amRecord.allFilesInRecord()

				areAllFilesInPlace = True			
				for nFile in filesInJob:
					if nFile not in currentFiles:
						areAllFilesInPlace = False
				if areAllFilesInPlace == True:
					print "moving files to the error path"
					try:
						pathAfterSafelyMovingFolderToDestinationFolder(destinationAMFolder,errorPath)
					except Exception as e:
						info = 'PostProcess: Unable to move the file %s' % (filePath,)
						logging.debug(info)
						info = 'There was an error moving the folder %s into the outbox at %s' % (destinationAMFolder, errorPath)
						info = info + '\n' + 'This will need to be addressed manually'
						sendFailureEmail(info)
						continue

			datastore.updateArchiveManagerJobAsComplete(amRecord)


def test():
	fileToHash = open('/Users/patrickcusack/Documents/Rebuild.MOV', 'r')
	print('Hasher: locking file...')
	portalocker.lock(fileToHash, portalocker.LOCK_SH)
	sleep(20)
	print('Hasher: unlocking file...')
	fileToHash.close()

def main():
	test()	

if __name__ == '__main__':
	main()
