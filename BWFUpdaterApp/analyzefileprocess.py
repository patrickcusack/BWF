import os
import sys
import datetime
import sqlite3
import portalocker
import shutil
import random
import json

from time import sleep
from utility import DefaultLogger

from configurationoptions import configurationOptions
from datastore import DataStore
from datastore import DataStoreRecord

from locktest import lockWithFile
from pathutilities import pathAfterSafelyMovingFileToDestinationFolder

from emailnotification import sendProcessFailureMessage
from emailnotification import sendAnalysisFailure
from emailnotification import sendPeriodicFailureMessage

from daisy import DaisyMetadataLookup
from daisy import getDaisyNumber
from daisy import isDaisyUp
from daisy import setStatusAsNeedsAttention
from daisy import setStatusAsPendingFix
from daisy import setStatusAsPendingArchive
from daisy import setStatusAsAvailable
from daisy import setComments

from stringparsing import doesStringContainBWFAnalyzerInfo
from stringparsing import stringMinusBWFAnalyzerInfo
from stringparsing import BWFAnalyzerInfoForSuccess
from stringparsing import BWFAnalyzerInfoForErrors

#is this hacky?
fileLocation = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.join(fileLocation, 'bwfupdater'))

from multichannelanalyzer import multiChannelBWFFileAnalysis

def retrieveDataForDANumber(fileName, identifier):
	daLookup = DaisyMetadataLookup(getDaisyNumber(fileName))
	while daLookup.isServiceUp == False:
		logging.debug('Process {} is sleeping for 60 seconds as service is unavailable...'.format(identifier))
		sleep(60)
		daLookup = DaisyMetadataLookup(getDaisyNumber(os.path.basename(filePath)))

	if daLookup.isValid == True:
		#if for some reason, the valid is BAD, we'll just pass DAISY_NA
		return tuple([daLookup.vendor(), daLookup.comments(), daLookup.status()])
	else:
		return None

def analyzeBWFFile(dbPath, identifier = 1):
	
	logging = DefaultLogger()
	loopcount = 0
	datastore = DataStore(dbPath)

	try:

		while True:

			sleep(60+random.randint(1,10))

			if loopcount % 20 == 0:
				logging.debug('bwf analyzer loop {} is active...'.format(identifier))
			loopcount += 1

			if not os.path.exists(dbPath):
				logging.debug('Acquire File: can not find database at path')
				return
		
			record =  None

			#if daisy is not up then just wait until it is
			if isDaisyUp() == False:
				logging.debug('Daisy does not appear to be up')
				continue

			#get a lock on the file
			lock = lockWithFile()
			try:
				lock.acquire(timeout=-1)
				if lock.i_am_locking():  
					record = datastore.oneRecordReadyForProcessing()
					if record != None:
						logging.debug('process {} is acquiring the lock'.format(identifier))
						datastore.updateRecordAsInProcess(record.id)
				lock.release()
			except Exception as e:
				pass

			if record == None:
				continue

			filePath = record.fileName

			#lets check that is has a genuine Daisy Number
			if getDaisyNumber(os.path.basename(filePath)) == None:
				errorBox = configurationOptions().defaultPathStructure()['errorBox']
				errorBox = os.path.expanduser(errorBox)	
				sendProcessFailureMessage({'subject':'BWF Error: file added that has no DANumber', 'message':'A file, %s, was deposited that does not have a Daisy Number' % (os.path.basename(filePath))})
				
				#move to errorBox
				try:
					print "Moving file %s into %s" % (filePath, errorBox)
					newPath = pathAfterSafelyMovingFileToDestinationFolder(filePath, errorBox)
				except Exception as e:
					logging.debug('Analyze File: Error moving file')
					info = '''This should not happen as pathAfterSafelyMovingFileToDestinationFolder should create a unique name that avoids any collisions, otherwise the file has been moved'''
					logging.debug(info)
					info = 'There was a problem moving the file into into the errorBox for: ' + os.path.basename(filePath)
					info = info + '\n' + 'This will require manual intervention as the occurrence is unique.'
					sendProcessFailureMessage({'subject':'BWF Error', 'message':info})
					logging.debug(info)

				datastore.updateRecordAsNotHavingADaisyNumber(record.id)
				continue

			#lets look up metadata before we even proceed, if can't get the metadata we don't want to analyze files
			dataTuple = retrieveDataForDANumber(os.path.basename(filePath), identifier)
			logging.debug('Data for {} Before: {}'.format(os.path.basename(filePath), dataTuple))

			if dataTuple == None:
				#ok, lets send an email that will be sent at a maximum of 1 per 4 hours
				result = "Process Error: Daisy Information not Available:" + e.message
				sendPeriodicFailureMessage(result)
				logging.debug('A Periodic Failure Message attempt was made.')
				continue

			result = None
			resultObject = None
			vendor = dataTuple[0]
			comments = dataTuple[1]
			status = dataTuple[2]
			
			#once we have the metadata, lets examine the file
			try:
				logging.debug('Will examine %s in loop %s' % (filePath, str(identifier)))
				resultObject = multiChannelBWFFileAnalysis(filePath)
				result = json.dumps(resultObject)
				if resultObject == None:
					logging.debug('The analysis of the file %s is "None". This should not occur.' % (filePath))
					raise Exception('The analysis of the file %s is "None". This should not occur.' % (filePath))
			except Exception as e:
				logging.debug('An exception occurred with %s in identifier %s.' % (filePath, str(identifier)))
				#mark as error
				datastore.updateRecordWithAnalysisError(record.id)
				errorBox = configurationOptions().defaultPathStructure()['errorBox']
				errorBox = os.path.expanduser(errorBox)
				
				#send email
				result = "Process Error: An Exception occurred when processing the file: %s. The file will be moved to %s" % (e.message, errorBox)
				logging.debug(result)
				sendProcessFailureMessage({'subject':'Process Error', 'message':result})

				#move to errorBox
				try:
					print "Moving file %s into %s" % (filePath, errorBox)
					logging.debug("Moving file %s into %s" % (filePath, errorBox))
					newPath = pathAfterSafelyMovingFileToDestinationFolder(filePath, errorBox)
				except Exception as e:
					logging.debug('Analyze File: Error moving file')
					info = '''This should not happen as pathAfterSafelyMovingFileToDestinationFolder should create a unique name that avoids any collisions, otherwise the file has been moved'''
					logging.debug(info)
					info = 'There was a problem moving the file into into the errorBox for: ' + os.path.basename(filePath)
					info = info + '\n' + 'This will require manual intervention as the occurrence is unique.'
					sendProcessFailureMessage({'subject':'Process Error Moving File', 'message':info})
					logging.debug(info)
				continue

			info = 'PreExisting Data for the following file %s: %s %s %s' % (os.path.basename(filePath), comments, vendor, status)
			logging.debug(info)

			resultObject['vendor'] = vendor

			#The result object is not None as we would have bailed otherwise

			if resultObject['result'] == 'success':
				if comments == None:
					comments = ''

				#update Comments 
				comments = stringMinusBWFAnalyzerInfo(comments)
				if comments != '':
					comments += " "
				comments += BWFAnalyzerInfoForSuccess(os.path.basename(filePath))
				success = setComments(getDaisyNumber(os.path.basename(filePath)), comments)
				#update local datastore
				datastore.updateRecordWithComments(comments, record.id)

				#did we successfully update the comments?
				if success == True:
					#update comments field in db and set to success
					logging.debug('updating comments successfully')
					datastore.successfullyUpdatedDaisyComments(record.id)
				else:
					#put infor in db that you couldn't update Daisy
					logging.debug('not updating comments successfully')
					datastore.failedToUpdateDaisyComments(record.id)

				#update the status to pending fix
				#only if the status is Needs Attention, otherwise we don't have any further knowledge of what is going on
				nextStatus = 'NO CHANGE'
				success = True
				if status == "Needs Attention":
					#ok to update status
					success = setStatusAsPendingFix(getDaisyNumber(os.path.basename(filePath)))
					nextStatus = 'Pending Fix'

				if status in ['Being Made', 'Ordered']:
					#ok to update status
					success = setStatusAsPendingArchive(getDaisyNumber(os.path.basename(filePath)))
					nextStatus = 'Pending Archive'
					
				datastore.updateRecordWithDaisyStatus(nextStatus, record.id)
				if success == True:
					#update staus field in db and set to success
					logging.debug('updating status successfully')
					datastore.successfullyUpdatedDaisyStatus(record.id)
				else:
					#put infor in db that you couldn't update status in Daisy		
					logging.debug('not updating status successfully')
					datastore.failedToUpdateDaisyStatus(record.id)

			else:
				sendAnalysisFailure(resultObject)

				if comments == None:
					comments = ''

				#update Comments 
				comments = stringMinusBWFAnalyzerInfo(comments)
				if comments != '':
					comments += " "
				comments += BWFAnalyzerInfoForErrors(resultObject['errors'])
				success = setComments(getDaisyNumber(os.path.basename(filePath)), comments)
				
				#update local datastore
				datastore.updateRecordWithComments(comments, record.id)

				if success == True:
					#update comments field in db and set to success
					logging.debug('updating comments successfully')
					datastore.successfullyUpdatedDaisyComments(record.id)
				else:
					#put infor in db that you couldn't update Daisy
					logging.debug('not updating comments successfully')
					datastore.failedToUpdateDaisyComments(record.id)

				#update Status
				if status not in ['Being Made', 'Ordered', 'Pending Archive']:
					#ok to update status
					success = setStatusAsNeedsAttention(getDaisyNumber(os.path.basename(filePath)))
					datastore.updateRecordWithDaisyStatus('Needs Attention', record.id)
					if success == True:
						#update staus field in db and set to success
						logging.debug('updating status successfully')
						datastore.successfullyUpdatedDaisyStatus(record.id)
					else:
						#put infor in db that you couldn't update status in Daisy
						logging.debug('not updating status successfully')		
						datastore.failedToUpdateDaisyStatus(record.id)
				else:
					success = setStatusAsPendingArchive(getDaisyNumber(os.path.basename(filePath)))
					datastore.updateRecordWithDaisyStatus('Pending Archive', record.id)
					if success == True:
						#update status field in db and set to success
						logging.debug('updating status successfully')
						datastore.successfullyUpdatedDaisyStatus(record.id)
					else:
						#put infor in db that you couldn't update status in Daisy
						logging.debug('not updating status successfully')		
						datastore.failedToUpdateDaisyStatus(record.id)

			if datastore.updateRecordWithAnalysisData(result, record.id) == False:
				info = 'Unable to save record %d %s' % (record.id, result) 
				sendProcessFailureMessage({'subject':'Process Error Unable To Save Record', 'message':info})
				continue

			#update vendor info
			datastore.updateRecordWithVendor(vendor, record.id)

			dataTuple = retrieveDataForDANumber(os.path.basename(filePath), identifier)
			logging.debug('Data for {} After: {}'.format(os.path.basename(filePath),dataTuple))

			#now that we have saved the data, we are ready to move the file
			nextBox = configurationOptions().defaultPathStructure()['outBox']
			if resultObject['result'] != 'success':
				nextBox = configurationOptions().defaultPathStructure()['failBox']
			nextBox = os.path.expanduser(nextBox)

			newPath = filePath

			try:
				newPath = pathAfterSafelyMovingFileToDestinationFolder(filePath, nextBox)
			except Exception as e:
				logging.debug('Analyze File: Error moving file')
				info = '''This should not happen as pathAfterSafelyMovingFileToDestinationFolder should create a unique name that avoids any collisions, otherwise the file has been moved'''
				logging.debug(info)
				info = 'There was a problem moving the file into into ' + nextBox + ' for: ' + os.path.basename(filePath)
				info = info + '\n' + 'This will require manual intervention as the occurrence is unique.'
				sendProcessFailureMessage({'subject':'Process Error Moving File', 'message':info})
				continue

			logging.debug('Analyze File: preparing to move file to final path...')
			datastore.updateRecordAsCompleteWithFinalPath(newPath, record.id)

	except Exception as e:
		info = 'Exception in analyzeBWFFile' + e.message
		logging.debug(info)
		sendProcessFailureMessage({'subject':'Exception!', 'message':info})


if __name__ == '__main__':
	main()

	