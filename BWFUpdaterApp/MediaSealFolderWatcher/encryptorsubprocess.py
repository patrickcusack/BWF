import sys
import os
import shutil
from time import sleep
import datetime
import sqlite3
import logging
from utility import DefaultLogger
from utility import DefaultDatabasePath
from encryptoraction import singleShotEncryptor
from configurator import configurationOptions
from datastore import DataStore
from pathutilities import pathAfterSafelyMovingFileToDestinationFolder
from emailnotifier import sendSuccessEmail
from emailnotifier import sendFailureEmail
import portalocker

def encrypt(dbPath):
	'''
	This process examines the database pointed to by dbPath. It 
	Looks for any records which have status 2 and has had a hash value calculated for it.
	'''
	logging = DefaultLogger()

	if not os.path.exists(dbPath):
		logging.debug('can\'t find database at path')
		return

	datastore = DataStore(dbPath)
	loopcount = 0

	while True:
		sleep(5)

		if loopcount % 10 == 0:
			logging.debug('Encryptor Process is alive')
		loopcount += 1

		data = datastore.recordsReadyToEncrypt()
		for record in data:
			logging.debug(record)

			key_id = record.id
			filePath = record.fileName	
			pathStructureName = record.pathStructureName

			if not os.path.exists(filePath):
				logging.debug('Encryptor: will update record status as the file no longer exists')
				datastore.updateRecordAsMissingWithID(key_id)
			else:
				options = configurationOptions()
				currentPathStructure = options.pathStructureWithName(pathStructureName)
				encryptionErrorPath = currentPathStructure['errorBox']
				encryptionInterimPath = currentPathStructure['interimBox']

				encryptedFilePath = os.path.join(encryptionInterimPath, os.path.basename(filePath))
				encryptionStart = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				nextStatusValue = datastore.operationCompleteStatusCode()

				options.inputPath = filePath
				options.destinationPath = os.path.dirname(encryptedFilePath)

				##UPDATE THAT ENCRYPTION STARTS HERE
				datastore.updateRecordStatusWithOperationStart(encryptionStart, key_id)

				message = 'Encryptor: encrypting file ' + filePath
				logging.debug(message)

				#there is a bug with MediaSeal when encrypting an encrypted file,
				#this checks for this so that MediaSeal doesn't blow away the file.
				returnCode = -7
				fileToEncrypt = None
				try:
					fileToEncrypt = open(filePath, 'rb')
					portalocker.lock(fileToEncrypt, portalocker.LOCK_SH)
					returnCode = singleShotEncryptor(options)
				except Exception as e:
					logging.debug('unable to lock file')

				if fileToEncrypt is not None:
					fileToEncrypt.close()

				message = 'Encryptor: encrypted file with return code ' +  str(returnCode)
				logging.debug(message)

				encryptionStop = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

				#try again should the connection be bad
				if returnCode == 2:
					sleep(5)
					returnCode = singleShotEncryptor(options)
					encryptionStart = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

				#as we are encrypting single files, we can leave this logic the same
				if returnCode != 0:
					info = "There was a problem encrypting " + filePath + ". Encountered Error Code: " + str(returnCode) + ". The file will be moved to the path's Error box: " + encryptionErrorPath 
					sendFailureEmail(info)

					nextStatusValue = datastore.operationFailedStatusCode()
					encryptionStart = datetime.datetime(2000,1,1)
					encryptionStop = datetime.datetime(2000,1,1)

					if os.path.abspath(os.path.dirname(filePath)) != os.path.abspath(encryptionErrorPath):
						logging.debug('moving file to error path')
						if os.path.exists(encryptionErrorPath):
							try:
								newPath = pathAfterSafelyMovingFileToDestinationFolder(filePath, encryptionErrorPath)
							except Exception as e:
								logging.debug('Encryptor: Error moving file')
								
							nextStatusValue = datastore.errorMovingFileStatusCode()
						else:
							logging.debug('Encryptor: encryptionErrorPath doesnt exist')
							nextStatusValue = datastore.errorPathDoesntExistStatusCode()

				datastore.updateRecordStatusWithEncryptedFileNameAndStartAndEndTime(nextStatusValue, encryptedFilePath, encryptionStart, encryptionStop, key_id)

if __name__ == "__main__":
	encrypt(DefaultDatabasePath())


