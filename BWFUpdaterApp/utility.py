import os
import sys
import logging
from configurationoptions import configurationOptions

def DefaultLogger():
	options = configurationOptions()
	logPath = options.logPath
	
	if not os.path.exists(logPath):
		os.makedirs(logPath)

	logPath = os.path.join(logPath, 'bwflog.log')
	logging.basicConfig(filename=logPath,level=logging.DEBUG, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
	return logging

def DefaultDatabasePath():
	
	options = configurationOptions()
	dataBasePath = options.dataBasePath	

	if not os.path.exists(dataBasePath):
		os.makedirs(dataBasePath)

	return os.path.join(dataBasePath, 'bwf_database.db')

def getsizeFolder(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


if __name__ == '__main__':
	print DefaultLogger()
	print DefaultDatabasePath()