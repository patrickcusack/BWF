from time import sleep
from lockfile import LockFile

lock = LockFile("./Battleship.mov")

with lock:
    print lock.path, 'is locked.'
    while True:
        sleep(5);
        print "sleeping..."