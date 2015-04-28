## http://pythonhosted.org//lockfile/lockfile.html#examples
import os
import sys
import shutil
import random

from lockfile import LockFile
from time import sleep
from multiprocessing import Process

def name():
  return "lockfileBWF"

def lockFilePath():
  if 'win32' in sys.platform:
    return os.path.join("C:\\ProgramData\\locktestBWF\\",name())

  return os.path.expanduser(os.path.join("~/Documents/locktestBWF/", name()))

def cleanUpLockFiles():
  try:
    shutil.rmtree(lockfolderpath())
  except Exception as e:
    pass

  sleep(1)
  
  try:
    os.mkdir(lockfolderpath())
  except Exception as e:
    print 'Unable to create lock path. Exiting...'
    #sys.exit()

def lockpath():
  dirname = os.path.dirname(lockFilePath())
  if not os.path.exists(dirname):
    try:
      os.mkdir(dirname)
    except Exception as e:
      print 'There was an error creating a lock folder'

  return lockFilePath()

def lockfolderpath():
  return os.path.dirname(lockFilePath())

def lockWithFile():
  return LockFile(lockpath())

def locktest(identifier):
  while True:
    sleep(random.randint(1,5))

    lock = lockWithFile()
    try:
      print 'I will attempt the lock', identifier
      lock.acquire(timeout=-1)    # nowaiting
      if lock.i_am_locking():
        print 'LOCKED', identifier  
      sleep(random.randint(1,5))
      print 'RELEASING', identifier  
      lock.release()
    except Exception as e:
      pass
      # print 'CANT LOCK', identifier

def main():

  cleanUpLockFiles()
  print lockFilePath()

  processObjects = []

  #Operations 
  processObjects.append({"target":locktest, "args":("1",)})
  processObjects.append({"target":locktest, "args":("2",)})
  processObjects.append({"target":locktest, "args":("3",)})
  processObjects.append({"target":locktest, "args":("4",)})
  processObjects.append({"target":locktest, "args":("5",)})

  for processObject in processObjects:
    processObject["process"] = Process(target=processObject['target'], args=processObject['args'][0])

  for processObject in processObjects:
    processObject["process"].start()

if __name__ == '__main__':
  main()