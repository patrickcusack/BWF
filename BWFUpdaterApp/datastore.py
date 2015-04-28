import os
import sys
import datetime
import sqlite3
import logging
from utility import DefaultLogger
from configurationoptions import configurationOptions

#status

class DataStoreRecord():
    def __init__(self, dbRecord):
        self.id                      = dbRecord[0]
        self.fileName                = dbRecord[1]
        self.fileSize                = dbRecord[2]
        self.dateAdded               = dbRecord[3]
        self.dateModified            = dbRecord[4]
        self.status                  = dbRecord[5]
        self.analysis                = dbRecord[6]
        self.vendor                  = dbRecord[7]

    def __str__(self):
        return 'ID:{0} NAME:{1} STATUS:{2} and more...'.format(self.id, self.fileName, self.status)   

class DataStoreReadOnly():

    def __init__(self, storePath):
        self.storePath = storePath

    def dbConnection(self):
        db = None
        try:
            db = sqlite3.connect(self.storePath)
        except Exception as e:
            print e.message
        return db

    def recordsForDateStartAndDateEnd(self, start, stop):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''SELECT * FROM jobs WHERE dateModified>? AND dateModified<? AND status=30''', (start,stop))
            dbRecords = cursor.fetchall()
            records = [DataStoreRecord(record) for record in dbRecords]
            db.close()
            return records
        except Exception as e:
            print e.message
        
        return []

class DataStore():

    def __init__(self, storePath):
        self.debugLog = DefaultLogger()
        self.storePath = storePath
        self.createJobsTable(storePath)

    def fileHasNoDaisyNumber(self):
        return -70

    def errorAnalyzingFile(self):
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

    def inProcessStatusCode(self):
        return 15

    def fileHasBeenAnalyzedStatusCode(self):
        return 20

    def fileHasBeenMovedToFinalLocation(self):
        return 30

    def dbConnection(self):
        db = None
        try:
            db = sqlite3.connect(self.storePath)
        except Exception as e:
            DefaultLogger().debug(e.message)
        return db

    def createJobsTable(self, pathToDBFolder):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS 
            jobs(id INTEGER PRIMARY KEY, 
            fileName TEXT, 
            fileSize INTEGER,
            dateAdded DATETIME, 
            dateModified DATETIME, 
            status INTEGER,  
            analysis TEXT,
            vendor TEXT,
            daisyComments TEXT,
            commentsUpdatedToDaisy INTEGER,
            daisyStatus TEXT,
            statusUpdatedToDaisy INTEGER)''')
            db.commit()
        except Exception as e:
            info = 'Error: Unable to call createJobsTable' + e.message
            logger = DefaultLogger()
            self.debugLog.debug(info)

        db.close()
   
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

    def addFileToDatabase(self, filePath):
        '''
        add a file to the database and mark its status as zero, if the file doesn't exist (which is unlikely) then return,  but I should log this
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
                dateAdded,
                dateModified,  
                status, 
                analysis,
                vendor,
                daisyComments,
                commentsUpdatedToDaisy,
                daisyStatus,
                statusUpdatedToDaisy) 
            VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (filePath, fileSize, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),0,'','UNKNOWN', '', '0','','0'))
            db.commit()
        except Exception as e:
            print 'addBWFFileToDatabase Error'
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

    def recordsForVerifying(self):
        return self.recordsForStatus(self.addedStatusCode())

    def recordsReadyForProcessing(self):
        return self.recordsForStatus(self.verifyStatusCode())

    def oneRecordReadyForProcessing(self):
        return self.oneRecordForStatus(self.verifyStatusCode())

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

    def oneRecordForStatus(self, status):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''SELECT * FROM jobs WHERE status=? LIMIT 1''', (status,))
            dbRecords = cursor.fetchall()
            records = [DataStoreRecord(record) for record in dbRecords]
            db.close()
            if len(records) == 0:
                return None
            return records[0]
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

    def updateRecordAsCompleteWithFinalPath(self, newPath, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET fileName=?, status=?, dateModified=? WHERE id=?;''',(newPath, self.fileHasBeenMovedToFinalLocation(), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()

    def updateRecordAsMissingWithID(self, key_id):
        self.updateRecordStatusWithID(self.missingRecordStatusCode(), key_id)

    def updateRecordAsInProcess(self, key_id):
        self.updateRecordStatusWithID(self.inProcessStatusCode(), key_id)

    def updateRecordWithAnalysisError(self, key_id):
        self.updateRecordStatusWithID(self.errorAnalyzingFile(), key_id)
    
    def updateRecordAsNotHavingADaisyNumber(self, key_id):
        self.updateRecordStatusWithID(self.fileHasNoDaisyNumber(), key_id)
    
    def updateRecordWithAnalysisData(self, analysisData, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET analysis=?, status=? WHERE id=?;''', (analysisData, self.fileHasBeenAnalyzedStatusCode(), key_id))
            db.commit()
            db.close()
            return True
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()

        return False

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

    def updateRecordWithVendor(self, vendor, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET vendor=? WHERE id=?;''', (vendor, key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()

    def updateRecordWithComments(self, nComments, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET daisyComments=? WHERE id=?;''', (nComments, key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()

    def updateRecordWithDaisyStatus(self, nStatus, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET daisyStatus=? WHERE id=?;''', (nStatus, key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()
 
    def successfullyUpdatedDaisyComments(self, key_id):
        self.setDaisyCommentsPosted(1, key_id)

    def failedToUpdateDaisyComments(self, key_id):
        self.setDaisyCommentsPosted(-1, key_id)

    def setDaisyCommentsPosted(self, posted, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET commentsUpdatedToDaisy=? WHERE id=?;''', (posted, key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()

    def successfullyUpdatedDaisyStatus(self, key_id):
        self.setDaisyStatusPosted(1, key_id)

    def failedToUpdateDaisyStatus(self, key_id):
        self.setDaisyStatusPosted(-1, key_id)

    def setDaisyStatusPosted(self, posted, key_id):
        try:
            db = self.dbConnection()
            cursor = db.cursor()
            cursor.execute('''UPDATE jobs SET statusUpdatedToDaisy=? WHERE id=?;''', (posted, key_id))
            db.commit()
            db.close()
        except Exception as e:
            self.debugLog.debug(e.message)
            db.rollback()
             


if __name__ == '__main__':
    dataStore = DataStore(os.path.expanduser('~/mediasealwatch/bwf_database.db'))
    print dataStore.oneRecordReadyForProcessing()

