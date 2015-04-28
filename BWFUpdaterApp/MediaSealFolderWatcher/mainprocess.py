import os
import sys
import datetime
from time import sleep
from multiprocessing import Process
from datetime import datetime
from utility import DefaultLogger
from utility import DefaultDatabasePath
from configurator import configurationOptions
import logging

from acquirefileprocess import acquirefile	
from watchpathsubprocess import encryptorWatch
from watchpathsubprocess import decryptorWatch
from processactions import preprocess
from processactions import postprocess
from encryptorsubprocess import encrypt
from decryptorsubprocess import decrypt

def main():
  
  options = configurationOptions()
  if not options.isValid():
    return

  logging = DefaultLogger()
  dbPath = DefaultDatabasePath()

  encryptionPathToWatch = options.pathStructureWithName('ArchivePath')
  decryptionPathToWatch = options.pathStructureWithName('DecryptPath')
  decryptionPathToWatch2 = options.pathStructureWithName('DecryptPath2')
  decryptionPathToWatch3 = options.pathStructureWithName('DecryptPath3')
  decryptionPathToWatch4 = options.pathStructureWithName('DecryptPath4')
  decryptionPathToWatch5 = options.pathStructureWithName('DecryptPath5')

  processObjects = []
  #Paths
  processObjects.append({"target":encryptorWatch, "args":(encryptionPathToWatch, dbPath), "info":'recreating encryptorWatcher process...'})
  processObjects.append({"target":decryptorWatch, "args":(decryptionPathToWatch, dbPath), "info":'recreating decryptionWatcher process...'})
  processObjects.append({"target":decryptorWatch, "args":(decryptionPathToWatch2, dbPath), "info":'recreating decryptionWatcher process...'})
  processObjects.append({"target":decryptorWatch, "args":(decryptionPathToWatch3, dbPath), "info":'recreating decryptionWatcher process...'})
  processObjects.append({"target":decryptorWatch, "args":(decryptionPathToWatch4, dbPath), "info":'recreating decryptionWatcher process...'})
  processObjects.append({"target":decryptorWatch, "args":(decryptionPathToWatch5, dbPath), "info":'recreating decryptionWatcher process...'})

  #Operations 
  processObjects.append({"target":acquirefile, "args":(dbPath,), "info":'recreating verifier process...'})
  processObjects.append({"target":preprocess, "args":(dbPath,), "info":'recreating the preprocess process...'})
  processObjects.append({"target":encrypt, "args":(dbPath,), "info":'recreating encrypt process...'})
  processObjects.append({"target":decrypt, "args":(dbPath,), "info":'recreating decrypt process...'})
  processObjects.append({"target":postprocess, "args":(dbPath,), "info":'recreating the postProcess process...'})  

  for processObject in processObjects:
    processObject["process"] = Process(target=processObject['target'], args=processObject['args'])

  for processObject in processObjects:
    processObject["process"].start()

  try:
    while True:
      sleep(2)
      options.updateProcessStatus("MainProcess is up")

      for processObject in processObjects:
        if not processObject['process'].is_alive() or processObject['process'].exitcode is not None:
          options.updateProcessStatus(processObject['info'])
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


