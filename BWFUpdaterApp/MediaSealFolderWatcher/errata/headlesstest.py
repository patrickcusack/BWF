from configurator import configurationOptions
import datetime
from time import sleep
import os

if __name__ == '__main__':
	path = 'C:\\ProgramData\\mediasealwatch\\statuslog.log'
	# path = os.path.expanduser('~/Desktop/result.txt')
	while (1):
		with open(path, 'a') as f:
			status = str(datetime.datetime.now()) + " " + 'Valid' if configurationOptions().isValid() == True else 'Invalid'
			f.write(status)
			f.write('\n')
		sleep(60)