import os
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
import xml.etree.cElementTree as ET
from xml.etree.cElementTree import ParseError

class EncryptorParser():
	"""
	parse encryptor string output
	"""
	@staticmethod
	def isEncryptorStatusMessage(xmlString):
		try:
			parser = parseString(xmlString)
			if len(parser.getElementsByTagName("Status")) > 0:
				return True
			else:
				return False
		except ExpatError:
			return False

	def __init__(self, xmlString):

		tree = None
		try:
			tree = ET.fromstring(xmlString)
		except ParseError:
			self.datarate = 'error'
			self.filebeingencrypted = 'error'
			self.taskprogress = 'error'
			self.totalprogress = 'error'
			self.logentrycount = 'error'
			self.xmlString = "ParserError"

		if tree is not None:
			try:
				self.datarate = tree[0][0].text
				self.filebeingencrypted = tree[0][1].text
				self.taskprogress = tree[0][3].text
				self.totalprogress = tree[0][4].text
				self.logentrycount = 0
				self.xmlString = xmlString
			except IndexError:
				self.datarate = 'error'
				self.filebeingencrypted = 'error'
				self.taskprogress = 'error'
				self.totalprogress = 'error'
				self.logentrycount = 'error'
				self.xmlString = 'error'

	def parsedString(self):
		return "{0}\t{1}\t{2}\t{3}\t{4}".format(self.totalprogress, self.taskprogress, self.datarate, self.logentrycount, self.filebeingencrypted)

	def parsedDictionary(self):
		return {'totalprogress':self.totalprogress, 'taskprogress':self.taskprogress, 'datarate':self.datarate, 'logentrycount':self.logentrycount, 'filebeingencrypted':self.filebeingencrypted}

	def shortStatusString(self):
		return "{0}\t{1}".format(self.filebeingencrypted, self.totalprogress)		

class EncryptorGroupParser():
	"""
	parse encryptor group information output
	"""

	@staticmethod
	def isEncryptorGroupMessage(xmlString):
		try:
			parser = parseString(xmlString)
			if len(parser.getElementsByTagName("GroupUserInfo")) > 0:
				return True
			else:
				return False
		except ExpatError:
			return False

	def __init__(self, xmlString):
		self.xmlString = xmlString
		self.groupUserList = []
		self.allGroups = []
		self.allUsers = []

		try:
			parser = parseString(xmlString)
			self.parseGroupUserlist(parser)
			self.parseAllGroups(parser)
			self.parseAllUsers(parser)
		except:
			self.currentGroups = "NODATA"
			self.currentUsers = "NODATA"			

	def parseGroupUserlist(self, parser):
		groupUserList = parser.getElementsByTagName("GroupUserList")[0]
		for node in groupUserList.childNodes:
			#listitem->SerializableIdAndId->GroupId_OR_UserId->TextNode's value
			self.groupUserList.append({"groupId":node.childNodes[0].childNodes[0].childNodes[0].nodeValue,"UserId":node.childNodes[0].childNodes[1].childNodes[0].nodeValue})

	def parseAllGroups(self, parser):
		groupList = parser.getElementsByTagName("Groups")[0]
		for node in groupList.childNodes:
			#listitem->SerializableIdAndId->GroupId_OR_UserId->TextNode's value
			self.allGroups.append({"ID":node.childNodes[0].childNodes[0].childNodes[0].nodeValue,"String":node.childNodes[0].childNodes[1].childNodes[0].nodeValue})		

	def parseAllUsers(self, parser):
		userList = parser.getElementsByTagName("Users")[0]
		for node in userList.childNodes:
			#listitem->SerializableIdAndId->GroupId_OR_UserId->TextNode's value
			self.allUsers.append({"ID":node.childNodes[0].childNodes[0].childNodes[0].nodeValue,"String":node.childNodes[0].childNodes[1].childNodes[0].nodeValue})		

	def parsedString(self):
		result = ""
		result += "Current Users and Groups:\n"
		for element in self.groupUserList:
			result += "\tGroup: {0}\tID: {1}\t\tUser: {2}\n".format(element['groupId'], element['UserId'], self.userNameForUserID(element['UserId']))

		result += "All Groups:\n"
		for element in self.allGroups:
			result += "\tGroupID: {0}\tName: {1}\n".format(element['ID'],element['String'])

		result += "All User:\n"
		for element in self.allUsers:
			result += "\tUserID: {0}\tName: {1}\n".format(element['ID'],element['String'])	
		return result

	def groupIDsInJob(self):
		groupSet = set()
		for element in self.groupUserList:
			groupSet.add(element["groupId"])

		return list(groupSet)

	def userIDsForGroupName(self,groupName):
		usersIDs = []

		for element in self.groupUserList:
			if element['groupId'] == groupName:
				usersIDs.append(element['UserId'])

		return usersIDs

	def userNamesForGroupName(self, groupName):
		userNames = []
		for userID in self.userIDsForGroupName(groupName):
			for user in self.allUsers:
				if userID == user["ID"]:
					userNames.append(user["String"])
		return userNames

	def userNameForUserID(self, userID):		
		for user in self.allUsers:
			if userID == user["ID"]:
				return user["String"]
		return ""

	def userIDsForName(self, name):		
		foundusers = []
		for user in self.allUsers:
			if name in self.userNameForUserID(user["ID"]):
				foundusers.append(user["ID"])
		return foundusers	

	def doesUserNameExistInGroup(self, username, groupID):
		for user in self.groupUserList:
			if groupID == user['groupId'] and username in self.userNameForUserID(user["UserId"]):
				return True
		return False

	def doesUserIDExistInGroup(self, userID, groupID):
		for user in self.groupUserList:
			if groupID == user['groupId'] and userID == user["UserId"]:
				return True
		return False	

def test():
	try:
		with open("multiplexmlstrings.txt", 'r') as f:
			for i in f.readlines():
				print i.strip()
				if EncryptorParser.isEncryptorStatusMessage(i) is True:
					print 'Message is a status message'
				elif EncryptorGroupParser.isEncryptorGroupMessage(i) is True:
					print 'Message is group message'
				else:
					print 'No clue what kind of message'
	except IOError as e:
		print e


	xmlString = '<?xml version="1.0" encoding="UTF-8"?><Status><CreateJobStatusOutputData><DataRate>30</DataRate><FileBeingEncrypted>/Volumes/DriveB/EVS_Large_Files/THREE_STOOGES_COLLECTION_1943_2.m4v</FileBeingEncrypted><LogEntry><listitem>Starting job processing: Mon Mar 17 12:06:05 2014</listitem><listitem>initialising log</listitem><listitem>Starting encryption of 3 files</listitem><listitem>Starting encryption of file: /Volumes/DriveA/TemplateTest2A/enc-Flame.And.Citron.2008.720p.BRRip.XviD.AC3-ViSiON.avi</listitem><listitem>Finished encrypting file</listitem><listitem>Starting encryption of file: /Volumes/DriveA/TemplateTest2A/enc-PRORES ENCODE 121211 130.mov</listitem><listitem>Finished encrypting file</listitem><listitem>Starting encryption of file: /Volumes/DriveA/TemplateTest2A/enc-THREE_STOOGES_COLLECTION_1943_2.m4v</listitem><listitem>Finished encrypting file</listitem><listitem>Finished encryption of all file(s)</listitem><listitem>Duration 147s</listitem></LogEntry><TaskProgress>99</TaskProgress><TotalProgress>99</TotalProgress></CreateJobStatusOutputData></Status>'
	print EncryptorParser(xmlString).parsedString()

	groupXmlString = '<?xml version="1.0" encoding="UTF-8"?><GroupUserInfo><GroupUsersOutputData><GroupUserList><listitem><SerializableIdAndId><GroupId>3</GroupId><UserId>26</UserId></SerializableIdAndId></listitem><listitem><SerializableIdAndId><GroupId>3</GroupId><UserId>85</UserId></SerializableIdAndId></listitem><listitem><SerializableIdAndId><GroupId>3</GroupId><UserId>188</UserId></SerializableIdAndId></listitem><listitem><SerializableIdAndId><GroupId>3</GroupId><UserId>206</UserId></SerializableIdAndId></listitem></GroupUserList><Groups><listitem><SerializableIdAndString><ID>3</ID><String>New Group</String></SerializableIdAndString></listitem></Groups><Users><listitem><SerializableIdAndString><ID>26</ID><String>milotrain@gmail.com</String></SerializableIdAndString></listitem><listitem><SerializableIdAndString><ID>56</ID><String>patrickcusack@mac.com</String></SerializableIdAndString></listitem><listitem><SerializableIdAndString><ID>82</ID><String>unimixstages+2315ilok@gmail.com</String></SerializableIdAndString></listitem><listitem><SerializableIdAndString><ID>85</ID><String>evspatrickcusack@gmail.com</String></SerializableIdAndString></listitem><listitem><SerializableIdAndString><ID>92</ID><String>jeremy.ayers@nbcuni.com</String></SerializableIdAndString></listitem><listitem><SerializableIdAndString><ID>178</ID><String>michelle.huynh@nbcuni.com</String></SerializableIdAndString></listitem><listitem><SerializableIdAndString><ID>188</ID><String>chrisaud@sbcglobal.net</String></SerializableIdAndString></listitem><listitem><SerializableIdAndString><ID>202</ID><String>matt.apice@nbcuni.com</String></SerializableIdAndString></listitem><listitem><SerializableIdAndString><ID>206</ID><String>anthony.anderson@nbcuni.com</String></SerializableIdAndString></listitem><listitem><SerializableIdAndString><ID>213</ID><String>upcoav@nbcuni.com</String></SerializableIdAndString></listitem><listitem><SerializableIdAndString><ID>240</ID><String>bluewavedmi+hpz820@gmail.com</String></SerializableIdAndString></listitem><listitem><SerializableIdAndString><ID>353</ID><String>me@davidchughes.com</String></SerializableIdAndString></listitem><listitem><SerializableIdAndString><ID>406</ID><String>paulicino@soundelux.com</String></SerializableIdAndString></listitem><listitem><SerializableIdAndString><ID>414</ID><String>kernelkangaroo@gmail.com</String></SerializableIdAndString></listitem></Users></GroupUsersOutputData></GroupUserInfo>'
	print EncryptorGroupParser(groupXmlString).parsedString()

	parser = EncryptorGroupParser(groupXmlString)
	for groupID in parser.groupIDsInJob():
		print parser.userNamesForGroupName(groupID)

	if parser.doesUserIDExistInGroup("188", "3"):
		print "Yes", parser.userNameForUserID("188")
	else:
		print "No"


	if parser.doesUserNameExistInGroup("milo", "3"):
		print "Yes", parser.userIDsForName("milo")
	else:
		print "No"

def test2():
	shouldContinueReading = True
	
	fileToOpen = '/Users/evslion/Desktop/output.txt'

	if not os.path.exists(fileToOpen):
		print fileToOpen, 'doesn\'t exist'
		return

	with open('/Users/evslion/Desktop/output.txt', 'r') as f:
		while shouldContinueReading:
			line = f.readline()
			if line is None or len(line) == 0:
				shouldContinueReading = False
				break
			else:
				print EncryptorParser(line).parsedString()

	print 'Finished'

if __name__ == '__main__':
	test2()


	




