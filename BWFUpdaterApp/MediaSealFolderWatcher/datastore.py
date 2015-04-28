import os
import sys
import datetime
import sqlite3
import logging
from utility import DefaultLogger
from configurator import configurationOptions
from amretrieval import fileNameSizePairsForJSONString

'''
status 0 = file has been added
status 1 = file has been verified
status 2 = file has been hashed
status 3 = file has been operationed
status 4 = file has been rehashed
status -2 = encryption failed
status -3 = error path doesn't exist
status -4 = error moving file
status -5 = file exists in path chain
'''

class DataStoreRecord():
    def __init__(self, dbRecord):
        self.id                      = dbRecord[0]
        self.fileName                = dbRecord[1]
        self.fileSize                = dbRecord[2]
        self.fileHash                = dbRecord[3]
        self.operationFileHash       = dbRecord[4]
        self.dateAdded               = dbRecord[5]
        self.dateModified            = dbRecord[6]
        self.dateOperationStart      = dbRecord[7]
        self.dateOperationEnd        = dbRecord[8]
        self.dateHashStart           = dbRecord[9]
        self.dateHashEnd             = dbRecord[10]
        self.dateOperationHashStart  = dbRecord[11]
        self.dateOperationHashEnd    = dbRecord[12]
        self.operationFileName       = dbRecord[13]
        self.operationFileSize       = dbRecord[14]
        self.status                  = dbRecord[15]
        self.processComplete         = dbRecord[16]
        self.operationType           = dbRecord[17]
        self.pathStructureName       = dbRecord[18]
        self.isBatch                 = dbRecord[19]
        self.batchName               = dbRecord[20]
        self.batchUUID               = dbRecord[21]

    def __str__(self):
        return 'ID:{0} NAME:{1} STATUS:{2} and more...'.format(self.id, self.fileName, self.status)   

class ArchiveManagerRecord():
    def __init__(self, amRecord):
        self.id                      = amRecord[0]
        self.amNumber                = amRecord[1]
        self.amData                  = amRecord[2]
        self.amPath                  = amRecord[3]
        self.complete                = amRecord[4]
        self.errorString             = amRecord[5]
        self.uuid                    = amRecord[6]

    def __str__(self):
        return 'ID:{0} AMNumber:{1} AMData:{2} and more...'.format(self.id, self.amNumber, self.amData)   

    def allFilesInRecord(self):
        return [filePair['fileName'] for filePair in fileNameSizePairsForJSONString(self.amData)]

class DataStore():

    def __init__(self, storePath):
        self.storePath = storePath
        self.createJobsTable(storePath)
        self.createArchiveManagerJobsTable(storePath)
        self.debugLog = DefaultLogger()

    def dbConnection(self):
        db = None
        try:
            db = sqlite3.connect(self.storePath)
        except Exception as e:
            self.debugLog.debug(e.message)
        return db

    def createJobsTable(self, pathToDBFolder):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS 
            jobs(id INTEGER PRIMARY KEY, 
            fileName TEXT, 
            fileSize INTEGER, 
            fileHash TEXT, 
            operationFileHash TEXT, 
            dateAdded DATETIME, 
            dateModified DATETIME, 
            dateOperationStart DATETIME, 
            dateOperationEnd DATETIME,
            dateHashStart DATETIME, 
            dateHashEnd DATETIME,
            dateOperationHashStart DATETIME, 
            dateOperationHashEnd DATETIME,
            operationFileName TEXT, 
            operationFileSize INTEGER, 
            status INTEGER, 
            processComplete INTEGER, 
            operationType TEXT, 
            pathStructureName TEXT, 
            isBatch INTEGER,
            batchName TEXT,
            batchUUID TEXT)''')
            db.commit()
        except Exception as e:
            print 'Error: Unable to call createJobsTable'
            self.debugLog.debug(e.message)

        db.close()

    def createArchiveManagerJobsTable(self, pathToDBFolder):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS 
            amjobs(id INTEGER PRIMARY KEY, 
            amNumber TEXT, 
            amData TEXT,
            amPath TEXT, 
            complete INTEGER,
            errorString TEXT,
            uuid TEXT)''')
            db.commit()
        except Exception as e:
            self.debugLog.debug(e.message)
        db.close()

    def addArchiveManagerJobToDataBaseWithUUID(self, amNumber, dataString, amPath, uuid):
        '''
        add an archive manager job to the database and mark its completion status as zero
        '''
        db = self.dbConnection()
        try:
            cursor = db.cursor()
            cursor.execute('''INSERT INTO amjobs(
                amNumber, 
                amData,
                amPath, 
                complete,
                errorString,
                uuid) 
            VALUES (?,?,?,?,?,?)''', (amNumber, dataString, amPath, 0, '', uuid))
            db.commit()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()
        db.close()

    def addAndMarkArchiveManagerJobToDataBaseAsUnkown(self, amNumber, amPath):
        '''
        add an archive manager job to the database, but as we can't retrive any information about the 
        job mark its completion status as -1 and data as unknown
        '''
        db = self.dbConnection()
        try:
            cursor = db.cursor()
            cursor.execute('''INSERT INTO amjobs(
                amNumber, 
                amData,
                amPath, 
                complete,
                errorString,
                uuid) 
            VALUES (?,?,?,?,?,?)''', (amNumber, 'unknown', amPath, -1, '', ''))
            db.commit()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()
        db.close()

    def updateArchiveManagerJobAsErrored(self, amRecord):
        '''
        update an archive manager job in the database and mark its completion status as errored, since it has
        error strings
        '''
        key_id = amRecord.id
        status = False
        db = self.dbConnection()
        try:
            cursor = db.cursor()
            cursor.execute('''UPDATE amJobs SET complete=? WHERE id=?;''',(-2, key_id))
            db.commit()
            status = True
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()
        db.close()
        return status

    def updateArchiveManagerJobAsReadyToComplete(self, amRecord):
        '''
        update an archive manager job in the database and mark its completion status as ready to finish
        '''
        key_id = amRecord.id
        status = False
        db = self.dbConnection()
        try:
            cursor = db.cursor()
            cursor.execute('''UPDATE amJobs SET complete=? WHERE id=?;''',(2, key_id))
            db.commit()
            status = True
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()
        db.close()
        return status

    def updateArchiveManagerJobAsComplete(self, amRecord):
        '''
        update an archive manager job in the database and mark its completion status as finished
        '''
        key_id = amRecord.id
        status = False
        db = self.dbConnection()
        try:
            cursor = db.cursor()
            cursor.execute('''UPDATE amJobs SET complete=? WHERE id=?;''',(1, key_id))
            db.commit()
            status = True
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()
        db.close()
        return status

    def updateArchiveManagerJobErrorString(self, amRecord, errorString):
        '''
        update an archive manager job's error string in the database
        '''
        key_id = amRecord.id
        status = False
        db = self.dbConnection()
        try:
            cursor = db.cursor()
            cursor.execute('''UPDATE amJobs SET errorString=? WHERE id=?;''',(errorString, key_id))
            db.commit()
            status = True
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()
        db.close()
        return status       

    def doesTheFilePathExistElseWhereInThePathStructure(self, filePath, operationType, pathStructureName):
        '''
        Checks to make sure the file isn't already in the queue, if is, then it moves to to a duplicate folder
        '''
        result = 0

        currentPathStructure = configurationOptions().pathStructureWithName(pathStructureName)
        #exlcude inBox
        for path in configurationOptions().pathStructurePathsToCheckForDuplicates():
            if os.path.exists(os.path.join(currentPathStructure[path], os.path.basename(filePath))):
                result += 1

        if result == 0:
            return False

        return True

    def addBatchFilePathToDataBaseStoreWithType(self, filePath, operationType, pathStructureName, batchName):
        '''
        add a batch file to the database and mark its status as zero, 
        if the file doesn't exist (which is unlikely) then return, 
        but I should log this
        '''
        self.addFilePathToDataBaseStoreWithType(filePath, operationType, pathStructureName, isBatch=1, batchName=batchName)

    def addFilePathToDataBaseStoreWithType(self, filePath, operationType, pathStructureName, isBatch=0, batchName=''):
        '''
        add a file to the database and mark its status as zero, 
        if the file doesn't exist (which is unlikely) then return, 
        but I should log this
        '''
        if not os.path.exists(filePath):
            return

        fileSize = os.path.getsize(filePath)
        db = self.dbConnection()
        try:
            cursor = db.cursor()
            cursor.execute('''INSERT INTO jobs(
                fileName, 
                fileSize, 
                fileHash, 
                operationFileHash, 
                dateAdded, 
                dateModified, 
                dateOperationStart, 
                dateOperationEnd, 
                dateHashStart, 
                dateHashEnd, 
                dateOperationHashStart, 
                dateOperationHashEnd, 
                operationFileName, 
                operationFileSize, 
                status, 
                processComplete, 
                operationType, 
                pathStructureName,
                isBatch,
                batchName,
                batchUUID) 
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (filePath, fileSize, 'HASH','OPER_HASH', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), '0', '0', '0', '0', '0','0', 'operationFilePath', 0, 0, 0, operationType, pathStructureName,isBatch, batchName, 'NO_UUID'))
            db.commit()
        except Exception as e:
            print 'addFilePathToDataBaseStoreWithType Error'
            self.debugLog.debug(e.message)
            db.rollback()
        db.close()
     

    def updateModificationDateForFilePath(self, filePath):
        db = self.dbConnection()
        cursor = db.cursor()
        try:
            cursor.execute('''SELECT * FROM jobs WHERE fileName=? AND status=?''',(filePath,0))
            data = cursor.fetchall()
        except Exception as e:
            self.debugLog.debug(e.message)
            return

        if len(data) > 1:
            #logging
            self.debugLog.debug('Error: record collision')
        else:
            try:
                key_id = data[0][0]
                cursor.execute('''UPDATE jobs SET dateModified=? WHERE id=?;''',(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), key_id))
                db.commit()
            except Exception as e:
                self.debugLog.debug('Error: record collision')
                db.rollback()

        db.close()

    def dataStoreRecordsForDataBaseRecords(self, records):
        dataStoreRecords = []
        for record in records:
            dataStoreRecords.append(DataStoreRecord(record))
        return dataStoreRecords

    def displayRecordForFile(self, filePath):
        db = self.dbConnection()
        cursor = db.cursor()
        cursor.execute('''SELECT * FROM jobs WHERE fileName=?''',(filePath,))
        data = cursor.fetchall()
        db.close()

    def noArchiveManagerDataExistsForRecord(self):
        return -90

    def errorGeneratingHash(self):
        return -90

    def daisyEntryNotFoundStatusCode(self):
        return -80

    def checksumLookupFailedStatusCode(self):
        return -70

    def checksumComparisonFailedStatusCode(self):
        return -60

    def errorFileExistsInPathChain(self):
        return -50

    def errorMovingFileStatusCode(self):
        return -40

    def errorPathDoesntExistStatusCode(self):
        return -30       

    def operationFailedStatusCode(self):
        return -20

    def missingRecordStatusCode(self):
        return -10        

    def addedStatusCode(self):
        return 0

    def verifyStatusCode(self):
        return 10

    def hashStartStatusCode(self):
        return 15

    def hashStatusCode(self):
        return 20

    def operationStartedStatusCode(self):
        return 25

    def operationCompleteStatusCode(self):
        return 30

    def reHashStartStatusCode(self):
        return 35

    def reHashStatusCode(self):
        return 40            

    def recordsForHashing(self):
        return self.recordsForStatus(self.verifyStatusCode())

    def recordsForReHashing(self):
        return self.recordsForStatus(self.operationCompleteStatusCode())    

    def recordsForVerifying(self):
        return self.recordsForStatus(self.addedStatusCode())

    def recordsReadyToEncrypt(self):
        return self.recordsForEncryptionStatus(self.hashStatusCode())

    def recordsReadyToDecrypt(self):
        return self.recordsForDecryptionStatus(self.hashStatusCode())

    def recordWithNumberFromAMJobsTable(self, amNumber):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''SELECT * FROM amjobs WHERE complete=? AND amNumber=?''', (0,amNumber))
            dbRecords = cursor.fetchall()
            amRecord = None
            if len(dbRecords) > 0:
                self.debugLog.debug('More than Zero Records')
                amRecord = ArchiveManagerRecord(dbRecords[0])
            elif len(dbRecords) > 1:
                self.debugLog.debug('More than 1 Record')
            db.close()
            return amRecord
        except Exception as e:
            self.debugLog.debug('Error recordWithNumberFromAMJobsTable')
            self.debugLog.debug(e.message)
            return []

    def archiveManagerJobsTableRecordWithUUID(self, uuidString):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''SELECT * FROM amjobs WHERE complete=? AND uuid=?''', (0, uuidString))
            dbRecords = cursor.fetchall()
            amRecord = None
            if len(dbRecords) > 0:
                amRecord = ArchiveManagerRecord(dbRecords[0])
            if len(dbRecords) > 1:
                logging('found one too many records for amNumber request!!!')
            db.close()
            return amRecord
        except Exception as e:
            self.debugLog.debug(e.message)
            return []

    def archiveManagerJobsReadyToStart(self):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''SELECT * FROM amjobs WHERE complete=?''', (0,))
            dbRecords = cursor.fetchall()
            records = [ArchiveManagerRecord(record) for record in dbRecords]
            db.close()
            return records
        except Exception as e:
            self.debugLog.debug(e.message)
            return []

    def archiveManagerJobsReadyToComplete(self):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''SELECT * FROM amjobs WHERE complete=?''', (2,))
            dbRecords = cursor.fetchall()
            records = [ArchiveManagerRecord(record) for record in dbRecords]
            db.close()
            return records
        except Exception as e:
            self.debugLog.debug(e.message)
            return []

    def archiveManagerJobsThatErrored(self):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''SELECT * FROM amjobs WHERE complete=?''', (-2,))
            dbRecords = cursor.fetchall()
            records = [ArchiveManagerRecord(record) for record in dbRecords]
            db.close()
            return records
        except Exception as e:
            self.debugLog.debug(e.message)
            return []            

    def recordsForStatus(self, status):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''SELECT * FROM jobs WHERE status=?''', (status,))
            dbRecords = cursor.fetchall()
            records = [DataStoreRecord(record) for record in dbRecords]
            db.close()
            return records
        except Exception as e:
            self.debugLog.debug(e.message)
            return []

    def recordsForUUID(self, uuid):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''SELECT * FROM jobs WHERE batchUUID=?''', (uuid,))
            dbRecords = cursor.fetchall()
            records = [DataStoreRecord(record) for record in dbRecords]
            db.close()
            return records
        except Exception as e:
            self.debugLog.debug(e.message)
            return []   

    def recordsForEncryptionStatus(self, status):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''SELECT * FROM jobs WHERE status=? AND operationType=?''', (status,'Encrypt'))
            dbRecords = cursor.fetchall()
            records = [DataStoreRecord(record) for record in dbRecords]
            db.close()
            return records
        except Exception as e:
            self.debugLog.debug(e.message)
            return []   

    def recordsForDecryptionStatus(self, status):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''SELECT * FROM jobs WHERE status=? AND operationType=?''', (status,'Decrypt'))
            dbRecords = cursor.fetchall()
            records = [DataStoreRecord(record) for record in dbRecords]
            db.close()
            return records
        except Exception as e:
            self.debugLog.debug(e.message)
            return []                

    def updateRecordStatusWithID(self, status, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET status=? WHERE id=?;''',(status, key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()

    def updateRecordAsMissingWithID(self, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET status=? WHERE id=?;''',(self.missingRecordStatusCode(), key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()

    def updateRecordAsMissingWithFileNameAndID(self, filePath, key_id):
        #we update the name in case any source file that gets moved collides with another file
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET status=?, fileName=? WHERE id=?;''',(self.missingRecordStatusCode(), filePath,key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()       
                    
    def updateRecordWithCurrentSizeAndDateModifiedWithID(self, currentSize, dateModified, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET fileSize=?, dateModified=? WHERE id=?;''', (currentSize, dateModified, key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()

    def updateRecordAsStaticWithNewPath(self, newPath, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET fileName=?, status=? WHERE id=?;''',(newPath, self.verifyStatusCode(), key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()

    def updateRecordAWithBatchUUIDReference(self, uuidReference, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET batchUUID=? WHERE id=?;''',(uuidReference, key_id))
            db.commit()
            db.close()
        except Exception as e:
            print 'Error in updateRecordAWithBatchUUIDReference'
            self.debugLog.debug(e.message)
            db.rollback()            

    def updateRecordAsDuplicateWithNewPath(self, newPath, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET fileName=?, status=? WHERE id=?;''',(newPath, self.errorFileExistsInPathChain(), key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()

    def updateRecordWithHashStart(self, startTime, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET dateHashStart=?, status=? WHERE id=?;''',
                ( startTime, self.hashStartStatusCode(), key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()

    def updateRecordWithReHashStart(self, startTime, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET dateOperationHashStart=?, status=? WHERE id=?;''',
                ( startTime, self.reHashStartStatusCode(), key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()        

    def updateRecordWithHashForStartTimeAndEndTime(self, hashString, startTime, endTime, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET fileHash=?, dateHashStart=?, dateHashEnd=?, status=? WHERE id=?;''',(hashString, startTime, endTime, self.hashStatusCode(), key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()

    def updateRecordWithFinalEncryptedPathAndHashForStartTimeAndEndTime(self, newPath, hashString, startTime, endTime, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET operationFileName=?, operationFileHash=?, dateOperationHashStart=?, dateOperationHashEnd=?, status=? WHERE id=?;''',
                (newPath, hashString, startTime, endTime, self.reHashStatusCode(), key_id))
            db.commit()
            db.close()
            return True
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()  
            return False                     

    def updateRecordStatusWithOperationStart(self, startTime, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET status=?, dateOperationStart=? WHERE id=?;''', 
                            (self.operationStartedStatusCode(), startTime, key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()

    def updateRecordStatusWithEncryptedFileNameAndStartAndEndTime(self, statusValue, encryptedFilePath, startTime, endTime, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET status=?, operationFileName=?, dateOperationStart=?, dateOperationEnd=?  WHERE id=?;''', 
                            (statusValue, encryptedFilePath, startTime, endTime, key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()   

    def updateRecordStatusWithDecryptedFileNameAndStartAndEndTime(self, statusValue, decryptedFilePath, startTime, endTime, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET status=?, operationFileName=?, dateOperationStart=?, dateOperationEnd=?  WHERE id=?;''', 
                            (statusValue, decryptedFilePath, startTime, endTime, key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()                   




if __name__ == '__main__':
    dataStore = DataStore(os.path.expanduser('~/mediasealwatch/database.db'))
    print dataStore.recordWithNumberFromAMJobsTable('369018')

