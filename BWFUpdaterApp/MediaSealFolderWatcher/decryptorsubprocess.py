import sys
import os
import shutil
from time import sleep
import datetime
import sqlite3
import logging
import subprocess
from utility import DefaultLogger
from utility import DefaultDatabasePath
from encryptoraction import singleShotEncryptor
from configurator import configurationOptions
from datastore import DataStore
from pathutilities import pathAfterSafelyMovingFileToDestinationFolder

def decrypt(dbPath):
	'''
	This process examines the database pointed to by dbPath. It 
	Looks for any records which have status 2 and has had a hash value calculated for it.
	'''
	logging = DefaultLogger()

	if not os.path.exists(dbPath):
		logging.debug('Decryptor: can\'t find database at path')
		return

	datastore = DataStore(dbPath)
	loopcount = 0

	while True:
		sleep(5)

		if loopcount % 10 == 0:
			logging.debug('Decryptor Process is alive')
		loopcount += 1

		data = datastore.recordsReadyToDecrypt()
		for record in data:
			logging.debug(record)

			key_id 			   = record.id
			filePath 		   = record.fileName
			pathStructureName  = record.pathStructureName	
			isBatch			   = record.isBatch
			batchName		   = record.batchName

			if not os.path.exists(filePath):
				logging.debug('Decryptor: will update record status as the file no longer exists')
				datastore.updateRecordAsMissingWithID(key_id)
			else:
				options = configurationOptions()
				currentPathStructure = options.pathStructureWithName(pathStructureName)
				decryptionErrorPath = currentPathStructure['errorBox']
				decryptionInterimPath = currentPathStructure['interimBox']
				options.inputPath = filePath

				decryptedFilePath = os.path.join(decryptionInterimPath, os.path.basename(filePath))
				operationStart = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				nextStatusValue = datastore.operationCompleteStatusCode()

				message = 'Decryptor: decrypting file ' + filePath
				logging.debug(message)

				##UPDATE OPERATION START
				datastore.updateRecordStatusWithOperationStart(operationStart, key_id)

				args = [options.decryptorApplicationPath, filePath, decryptedFilePath]
				process = subprocess.Popen(args)
				out, err = process.communicate()
				returnCode = process.returncode

				message = 'Decryptor: decrypted file with return code ' +  str(returnCode)
				logging.debug(message)

				operationStop = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

				if returnCode != 0:
					info = 'An error occurred with the Decryption operation when decrypting %s.' % (filePath)
					logging.debug(info)
					
					operationStart = datetime.datetime(2000,1,1)
					operationStop = datetime.datetime(2000,1,1)

					if isBatch == 0:
						
						nextStatusValue = datastore.operationFailedStatusCode()

						if os.path.abspath(os.path.dirname(filePath)) != os.path.abspath(decryptionErrorPath):
							logging.debug('moving file to error path')
							if os.path.exists(decryptionErrorPath):
								# shutil.move(filePath, decryptionErrorPath)
								# newPath = os.path.join(decryptionErrorPath, os.path.basename(filePath))
								newPath = pathAfterSafelyMovingFileToDestinationFolder(filePath, decryptionErrorPath)
								if not os.path.exists(newPath):
									logging.debug('Decryptor: Error moving file')
									nextStatusValue = datastore.errorMovingFileStatusCode()
							else:
								logging.debug('Decryptor: decryptionErrorPath doesnt exist')
								nextStatusValue = datastore.errorPathDoesntExistStatusCode()
					else:
						#don't move batch files, just update the batch's am errorString to reflect the problem
						#the file's checksum will fail
						#we don't update the batch file's status
						amRecord = datastore.recordWithNumberFromAMJobsTable(batchName)
						if amRecord == None:
							#This should not happen as we don't even allow for the logic to proceed to this point without
							#a valid Archive Manager Record
							info = 'An error occurred where no data was found for the Archive Manager job ' + batchName + '\n'
							info = info + 'This error should not happen. Please check ' + os.path.dirname(filePath) + '\n'
							info = info + 'The files will need to be manually removed from the Decryption Queue.'
							logging.debug(info)
							sendFailureEmail(info)
							continue
						
						errorString = 'A problem was encountered while decrypting %s.' % (filePath)
						errorString = errorString + 'The file\'s checksum will be calculated and compared against that in Daisy should the error have occurred ater the file was decrypted.'
						if amRecord.errorString != '':
							amRecord.errorString = amRecord.errorString + '\n' + errorString
						else:
							amRecord.errorString = errorString

						datastore.updateArchiveManagerJobErrorString(amRecord, amRecord.errorString)

				# we update the status value
				datastore.updateRecordStatusWithDecryptedFileNameAndStartAndEndTime(nextStatusValue, decryptedFilePath, operationStart, operationStop, key_id)

if __name__ == "__main__":
	encrypt(DefaultDatabasePath())


