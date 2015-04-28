import os
import sys
import subprocess
import logging

from time import sleep
from threading import Thread
from Queue import Queue

from encryptorparser import EncryptorParser
from utility import DefaultLogger

class StatusReader():
	def __init__(self, filePathToRead, messageQueue):
		self.queue = messageQueue
		self.filePath = filePathToRead
		self.isRunning = True

	def terminate(self):
		self.isRunning = False

	def run(self):
		while self.isRunning == True:
			sleep(0.5)
			if os.path.exists(self.filePath):
				try:
					with open(self.filePath, 'r') as f:
						contents = f.read()
						if contents is not None:
							self.queue.put(EncryptorParser(contents).shortStatusString())
							# print statusResult
				except Exception as e:
					self.queue.put(e.message)
					# print e.message

class EncryptorProcess():
	def __init__(self, arguments):
		self.args = arguments
		self.isRunning = True
		self.returncode = 0

	def run(self):
		logging = DefaultLogger()
		logging.debug('Beginning Encryption')

		try:
			process = subprocess.Popen(self.args)
			out, err = process.communicate()
			self.returncode = process.returncode
		except Exception as e:
			info = e.message
			logging.debug(info)
			self.returncode = -10
		
		message = 'Process Encryption Finished with code'+ str(process.returncode)
		logging.debug(message)
		self.isRunning = False

def singleShotEncryptor(options):

	logging = DefaultLogger()

	destinationPath  = options.destinationPath
	jobStatusOuputPath  = options.jobStatusOuputPath

	if not os.path.exists(destinationPath):
		logging.debug('Encryptor: error as destination path doesn\'t exist')
		return

	if not os.path.exists(os.path.dirname(jobStatusOuputPath)):
		os.mkdir(os.path.dirname(jobStatusOuputPath))

	if os.path.exists(jobStatusOuputPath):
		os.remove(jobStatusOuputPath)

	queue = Queue()

	encryptor = EncryptorProcess(options.encryptorArguments())
	reader = StatusReader(jobStatusOuputPath, queue)

	encryptThread = Thread(target=encryptor.run)
	readerThread = Thread(target=reader.run)

	encryptThread.start()
	readerThread.start()

	while encryptor.isRunning == True:
		sleep(0.5)
		if not queue.empty():
			status = queue.get()
			logging.debug(status)

	while not queue.empty():
		status = queue.get()
		logging.debug(status)

	reader.terminate()

	if encryptor.returncode == 2:
		logging.debug('unable to communicate with studio server')

	statusString = "Encryption Process Return Code", str(encryptor.returncode)
	logging.debug(statusString)

	return encryptor.returncode

def main():
	print '__NO__ACTION__'

if __name__ == '__main__':
	main()