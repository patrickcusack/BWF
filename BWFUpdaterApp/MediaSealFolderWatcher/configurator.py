import os
import sys
import json
import time

def configurationOptions():
		options = None

		if sys.platform == 'win32':
			path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'encryptorconfigwin.json')
			options = Configurator(path)
		else:
			path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'encryptorconfigosx.json')
			options = Configurator(path)

		return options

class Configurator():

	def __init__(self, configFilePath):
		self.pathStructures = []
		if not os.path.exists(configFilePath):
			raise Exception('No Config File Found')
		else:
			self.readJSONfile(configFilePath)

	def isValid(self):
		result = 0

		for pathDescription in self.mandatoryPaths():
			try:
				getattr(self, pathDescription)
			except AttributeError as e: 
				print "Error: " + pathDescription + " doesn't exist in your configuration document"
				result += 1

		for pathElement in self.pathStructures:
			for path in self.mandatoryPathStructurePaths():
				if not os.path.exists(pathElement[path]):
					print "Error: " + path + " " + pathElement[path]+ " doesn't exist in your configuration document"
					result += 1

		for folderDescription in self.mandatoryFolders():
			try:
				getattr(self, folderDescription)
			except AttributeError as e:
				print "Error: " + folderDescription +  " doesn't exist in your configuration document"
				result += 1

		if result > 0:
			print 'Error: Please add any missing path address to your configuation before continuing'
			return False
		else:
			return True

	def allKeys(self):
		return ["applicationPath", "decryptorApplicationPath", "jobStatusOuputPath",
		"inputPath","templateID","templateJobName","username","password", "destinationPath",
		"logPath", "dataBasePath", "pathStructure", "healthStatusPath", "shouldDeleteOriginal", 
		"emailRecipients", "smtpServer"]

	def pathKeys(self):
		return ["applicationPath", "decryptorApplicationPath", "jobStatusOuputPath", "inputPath",
		"logPath", "dataBasePath", "healthStatusPath"]

	def multiPathKeys(self):
		return ["pathStructure",]		

	def mandatoryPaths(self):
		return ["applicationPath", "decryptorApplicationPath"]

	def mandatoryFolders(self):
		return ["logPath", "dataBasePath"]	

	def mandatoryPathStructurePaths(self):
		return ["inBox", "outBox", "workingBox", "interimBox", "errorBox", "originalBox", "duplicateBox"]

	def pathStructurePathsToCheckForDuplicates(self):
		#we don't care about the error box as we will move files their with a new name should a file exist
		return ["outBox", "workingBox", "interimBox", "originalBox"]		

	def pathStructureWithName(self, name):
		for structure in self.pathStructures:
			if structure['name'] == name:
				return structure
		return None

	def encryptorArguments(self):
		return [self.applicationPath, '-o', self.jobStatusOuputPath, '-templateid', self.templateID, 
		'-templatejobname', self.templateJobName, '-outputpath', self.destinationPath, '-u', self.username, 
		'-p', self.password, self.inputPath]

	def readJSONfile(self, pathToFile):
		try:
			configFile = open(pathToFile, 'r')
			configOptions = json.loads(configFile.read())
			
			for key in self.allKeys():
				if not configOptions.has_key(key):
					configOptions[key] = None
				setattr(self, key, configOptions[key])

			#expand any paths
			for key in self.pathKeys():
				setattr(self, key, os.path.expanduser(configOptions[key]))

			#expand any paths in the pathStructure
			if configOptions['pathStructure'] != None:
				for element in configOptions['pathStructure']:
					for key in element.keys():
						if key in self.mandatoryPathStructurePaths():
							element[key] = os.path.expanduser(element[key])
					self.pathStructures.append(element)
			else:
				print 'No Path Structures defined'

			configFile.close()

		except Exception as e:
			print e.message

	def updateProcessStatus(self, statusString):
		if os.path.exists(self.healthStatusPath):
			with open(os.path.join(self.healthStatusPath, 'status'), 'w') as f:
				f.write('{} {}'.format(statusString, time.strftime("%H_%M_%m_%d_%y")))

def main():
	if configurationOptions().isValid():
		print 'valid config'
	else:
		print 'invalid config'

if __name__ == '__main__':
	main()