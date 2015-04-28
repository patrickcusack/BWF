import os
import sys
import datetime
from time import sleep
from multiprocessing import Process
from datetime import datetime
from utility import DefaultLogger
from utility import DefaultDatabasePath
from configurationoptions import configurationOptions
import logging
from locktest import cleanUpLockFiles

from acquirefile import acquirefile	
from watchprocess import folderObserver
from analyzefileprocess import analyzeBWFFile
# from processactions import preprocess

def main():
  
  options = configurationOptions()
  if not options.isValid():
    return

  logging = DefaultLogger()
  dbPath = DefaultDatabasePath()
  cleanUpLockFiles()

  pathToWatch = options.defaultPathStructure()

  processObjects = []
  #paths
  processObjects.append({"target":folderObserver, "args":(pathToWatch, dbPath), "info":'recreating folder observer process...'})
  
  #Operations 
  processObjects.append({"target":acquirefile, "args":(dbPath,), "info":'recreating verifier process...'})
  
  #Processors
  for x in range(0,8):
    processObjects.append({"target":analyzeBWFFile, "args":(dbPath,('process ' + str(x))), "info":('recreating analyzer process %s...' % (str(x),))})

  for processObject in processObjects:
    processObject["process"] = Process(target=processObject['target'], args=processObject['args'])

  for processObject in processObjects:
    processObject["process"].start()

  try:
    while True:
      sleep(2)

      for processObject in processObjects:
        if not processObject['process'].is_alive() or processObject['process'].exitcode is not None:
          logging.debug(processObject['info'])
          processObject['process'].terminate()
          processObject['process'] = Process(target=processObject['target'], args=processObject['args'])
          processObject['process'].start()

  except KeyboardInterrupt:
    for processObject in processObjects:
      processObject['process'].stop()

  for processObject in processObjects:
    processObject['process'].join()

if __name__ == '__main__':
  main()


