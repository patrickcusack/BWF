import os
import sys
import time
import logging
from utility import DefaultLogger 
from datetime import datetime
from datastore import DataStore
from utility import DefaultDatabasePath
from utility import getsizeFolder
from configurator import Configurator
from amretrieval import jsonStringForAMNumber
from amretrieval import isAMDataValid
from emailnotifier import sendSuccessEmail
from emailnotifier import sendFailureEmail
from pathutilities import createFileWithUUIDatPath

from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import LoggingEventHandler

class EncryptorWatcher(LoggingEventHandler):
    '''
    This class enters all file 'created' events to a database pointed to by dbFolder
    '''
    def __init__(self, pathStructure, dbFolder):
        super(LoggingEventHandler, self).__init__()
        self.pathStructure = pathStructure
        self.dataStore = DataStore(dbFolder) 

    def on_modified(self, event):
        path = os.path.join(self.pathStructure['inBox'], event.src_path)
        logging.debug("encryptorWatch on_modified file")
        info = "Modified: " +  event.src_path + " " + str(os.path.getsize(path))
        logging.debug(info)

    def on_created(self, event):
        path = os.path.join(self.pathStructure['inBox'], event.src_path)
        
        if os.path.isdir(os.path.abspath(event.src_path)):
            logging.debug('WatchProcess: Folder Encryption is not supported.')
            return

        self.dataStore.addFilePathToDataBaseStoreWithType(os.path.abspath(event.src_path), self.pathStructure['watchType'], self.pathStructure['name'])

        info = "Created: " +  event.src_path + " " + str(os.path.getsize(path))
        logging.debug("encryptorWatch on_created file")
        logging.debug(info)

class DecryptorWatcher(LoggingEventHandler):
    '''
    This class enters all file 'created' events to a database pointed to by dbFolder
    '''
    def __init__(self, pathStructure, dbFolder):
        super(LoggingEventHandler, self).__init__()
        self.pathStructure = pathStructure
        self.dataStore = DataStore(dbFolder) 

    def on_modified(self, event):

        if os.path.isdir(event.src_path):
            info = "Modified: " +  event.src_path + " " + str(getsizeFolder(event.src_path))
            logging.debug(info)
        else:
            info = "Modified: " +  event.src_path + " " + str(os.path.getsize(event.src_path))
            logging.debug(info)

    def on_created(self, event):
        '''
        if the path is a folder, then retrieve the archive manager request, save the the result to a new table called amjobs.
        the table will have the following columns id, data, complete. The data will have the json data from which i can retrieve 
        all of the files.
        '''
        if os.path.isdir(os.path.abspath(event.src_path)):
            info = "Created Folder: " +  event.src_path + " " + str(getsizeFolder(event.src_path))
            logging.debug(info)

            try:
                droppedFolder = event.src_path.split(self.pathStructure['inBox'])[1].split(os.sep)[1]
                pathComponents = [elem for elem in droppedFolder.split(os.sep) if elem != '']

                if len(pathComponents) == 1:
                    info = "will add " +  droppedFolder +  " to path"
                    logging.debug(info)

                    amDataAsString = jsonStringForAMNumber(droppedFolder)
                    if isAMDataValid(amDataAsString) == False:
                        self.dataStore.addAndMarkArchiveManagerJobToDataBaseAsUnkown(droppedFolder, event.src_path)
                        errorString = '''A folder was added to the Decrypt Path %s for which no Archive Manager Data was found. Check the name of the folder that was dropped and make sure that the Archive Manager request exists and that the Archive Manager is accessible. Files added to this folder will not be Decrypted until the error is resolved.'''
                        errorString = errorString % self.pathStructure['inBox']
                        raise Exception(errorString)

                    uuid = createFileWithUUIDatPath(event.src_path)
                    self.dataStore.addArchiveManagerJobToDataBaseWithUUID(droppedFolder, amDataAsString, event.src_path, uuid)

                elif len(pathComponents) > 1:
                    logging.debug('This folder path is nested and will not be accepted')
                    raise Exception('failed to get data from server')

            except Exception as e:
                info = e.message
                logging.debug(info)
                sendFailureEmail(info)

        else:
            #file

            try:
                droppedFile = event.src_path.split(self.pathStructure['inBox'])[1]
                pathComponents = [elem for elem in droppedFile.split(os.sep) if elem != '']
                
                if os.path.basename(event.src_path) in ['Thumbs.db', '.DS_Store']:
                    pass
                elif os.path.basename(event.src_path).startswith('UUID_'):
                    pass
                elif len(pathComponents) == 1:
                    #single file
                    pathToAdd = pathComponents[0]
                    self.dataStore.addFilePathToDataBaseStoreWithType(os.path.abspath(event.src_path), self.pathStructure['watchType'], self.pathStructure['name'])
                    info = "Created: " +  pathToAdd + " " + str(os.path.getsize(event.src_path))
                    logging.debug(info)
                elif len(pathComponents) == 2:
                    #ADD BATCH FLAG AND AM FOLDER NAME
                    batchName = pathComponents[0]
                    self.dataStore.addBatchFilePathToDataBaseStoreWithType(os.path.abspath(event.src_path), self.pathStructure['watchType'], self.pathStructure['name'], batchName)
                    info = "Created File: " +  event.src_path + " " + str(os.path.getsize(event.src_path))
                    logging.debug(info)
                    info = "will add " +  str(pathComponents) +  " to path"
                    logging.debug(info)  
                else:
                    raise Exception('This file path is nested OR incomplete and will not be accepted')
            except Exception as e:
                #GENERATE ERROR EMAIL
                info = e.message
                logging.debug(info)
                sendFailureEmail(info)


def encryptorWatch(pathStructure, dbPath):

    logging = DefaultLogger()

    if pathStructure == None or pathStructure['inBox'] == None:
        message = 'Watch: Unable to run as pathStructure is undefined'
        logging.debug(message)
        return
    
    event_handler = EncryptorWatcher(pathStructure, dbPath)
    observer = PollingObserver()
    observer.schedule(event_handler, pathStructure['inBox'], recursive=False)
    observer.start()

    try:
        while True and observer.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def decryptorWatch(pathStructure, dbPath):

    logging = DefaultLogger()

    if pathStructure == None or pathStructure['inBox'] == None:
        message = 'Watch: Unable to run as pathStructure is undefined'
        logging.debug(message)
        return
    
    event_handler = DecryptorWatcher(pathStructure, dbPath)
    observer = PollingObserver()
    observer.schedule(event_handler, pathStructure['inBox'], recursive=True)
    observer.start()

    try:
        while True and observer.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def test():
    if 'nt' in os.name:
        pathStructure = {"inBox":"F:\\ArchiveTest\\PathStructure\\inBox", 
                  "outBox":"F:\\ArchiveTest\\PathStructure\\outBox", 
                  "workingBox":"F:\\ArchiveTest\\PathStructure\\working", 
                  "interimBox":"F:\\ArchiveTest\\PathStructure\\interim", 
                  "errorBox":"F:\\ArchiveTest\\PathStructure\\errorBox", 
                  "originalBox":"F:\\ArchiveTest\\PathStructure\\originalBox",
                  "watchType":"Encrypt",
                  "name":"ArchivePath"}
    else:
        pathStructure = {"inBox":"~/Documents/ArchiveTest/Decrypt/inBox", 
                  "outBox":"~/Documents/ArchiveTest/Decrypt/outBox", 
                  "workingBox":"~/Documents/ArchiveTest/Decrypt/working", 
                  "interimBox":"~/Documents/ArchiveTest/Decrypt/interim", 
                  "errorBox":"~/Documents/ArchiveTest/Decrypt/errorBox", 
                  "originalBox":"~/Documents/ArchiveTest/Decrypt/originalBox",
                  "watchType":"Decrypt",
                  "name":"ArchivePath"}

    for k,v in pathStructure.items():
        pathStructure[k] = os.path.expanduser(v)

    decryptorWatch(pathStructure, DefaultDatabasePath())

if __name__ == "__main__":
    test()

