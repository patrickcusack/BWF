import os
import sys
import time
import logging
from utility import DefaultLogger 
from datetime import datetime
from datastore import DataStore
from utility import DefaultDatabasePath
from configurationoptions import Configurator

from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import LoggingEventHandler

class singleFileWatcher(LoggingEventHandler):
    '''
    This class enters all file 'created' events to a database pointed to by dbFolder
    '''
    def __init__(self, pathStructure, dbFolder):
        super(LoggingEventHandler, self).__init__()
        self.pathStructure = pathStructure
        self.dataStore = DataStore(dbFolder) 

    def on_created(self, event):
        
        for ignoreFile in ['.DS_Store', 'Thumbs.db']:
            if ignoreFile in os.path.abspath(event.src_path):
                info = 'File ignored: ' +  os.path.abspath(event.src_path)
                logging.debug(info)
                return

        info = 'On created: ' +  os.path.abspath(event.src_path)
        logging.debug(info)

        if os.path.isdir(os.path.abspath(event.src_path)):
            info = 'Directory analysis is not available'
            logging.debug(info)
            return

        self.dataStore.addFileToDatabase(os.path.abspath(event.src_path))
        info = 'adding ' + event.src_path + ' to the database'
        logging.debug(info)


def folderObserver(pathStructure, dbPath):

    logging = DefaultLogger()

    if pathStructure == None or pathStructure['inBox'] == None:
        message = 'Watch: Unable to run as pathStructure is undefined'
        logging.debug(message)
        return
    
    event_handler = singleFileWatcher(pathStructure, dbPath)
    observer = PollingObserver()
    observer.schedule(event_handler, pathStructure['inBox'], recursive=False)
    observer.start()

    try:
        while True and observer.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def test():
    if 'win32' in os.name:
        pathStructure = {"inBox":"F:\\ArchiveTest\\PathStructure\\inBox", 
                  "outBox":"F:\\ArchiveTest\\PathStructure\\outBox", 
                  "workingBox":"F:\\ArchiveTest\\PathStructure\\working", 
                  "name":"BWFPath"}
    else:
        pathStructure = {"inBox":"~/Documents/BWFTest/inBox", 
                  "outBox":"~/Documents/BWFTest/outBox", 
                  "workingBox":"~/Documents/BWFTest/working", 
                  "name":"BWFPath"}

    for k,v in pathStructure.items():
        pathStructure[k] = os.path.expanduser(v)

    folderObserver(pathStructure, DefaultDatabasePath())

if __name__ == "__main__":
    test()

