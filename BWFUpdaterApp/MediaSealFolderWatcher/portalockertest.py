from time import sleep
import portalocker

file = open('./Despicable Me 2.mov', 'r')
portalocker.lock(file, portalocker.LOCK_SH)
print "File is locked"

shouldSleep = True
sleepDuration = 300

while shouldSleep == True:
	sleepDuration -= 30
	print 'sleeping....'
	sleep(30)
	if sleepDuration <= 0:
		shouldSleep = False

print "File will close"
file.close()
