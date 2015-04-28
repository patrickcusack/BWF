import os
import datetime
import json
from sets import Set
from datastore import DataStoreReadOnly 

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEText import MIMEText


class GlobalCategories():

	def __init__(self):
		pass

	def categories(self):
		return ['Head Tones', 'Layout', 'Pop', 'TimeCode', 'BWav', 'Bit Depth', 'SampleRate', 'Total']
	
	def keys(self):
		return ['hasProperHeadTones', 'hasProperLayout', 'hasProperPops', 'hasCorrectTimeCode', 'isBWAV', 'isProperBitDepth', 'isProperSampleRate', 'totalStatus']	
	
	def mapping(self):
		return dict(zip(self.categories(), self.keys()))

class VendorMaster():

	def __init__(self):
		self.vendorsCollectionsDict = dict()

	def addRecord(self, record):

		vendor = record.vendor if record.vendor != None else 'UNKNOWN'

		if vendor not in self.vendorsCollectionsDict.keys():
			self.vendorsCollectionsDict[vendor] = VendorCollection(vendor)

		self.vendorsCollectionsDict[vendor].addAnalysisObject(AnalysisObject(record.analysis))

	def addRecords(self, records):
		for record in records:
			self.addRecord(record)

	def results(self):
		results = []
		for vendorName in self.vendorsCollectionsDict.keys():
			results.append({vendorName:self.vendorsCollectionsDict[vendorName].result()})
		return results

	def resultsForVendor(self, nVendorName):
		for vendorName in self.vendorsCollectionsDict.keys():
			if vendorName == nVendorName:
				return self.vendorsCollectionsDict[vendorName].result()
		return None

	def vendors(self):
		return sorted(self.vendorsCollectionsDict.keys())
		
class VendorCollection():

	def __init__(self, name):
		self.name = name
		self.groupings = {}
		for key in GlobalCategories().keys():
			self.groupings[key] = {'pass':0, 'fail':0, 'total':0, 'percentage':0.0}

	def addAnalysisObject(self, analysisObject):
		for key in GlobalCategories().keys():
			if getattr(analysisObject,key) == True:
				self.groupings[key]['pass'] +=1
			else:
				self.groupings[key]['fail'] +=1
			self.groupings[key]['total'] += 1

	def result(self):
		for key in GlobalCategories().keys():
			self.groupings[key]['percentage'] = "{:2.2f}%".format(self.groupings[key]['pass'] / (1.0 * self.groupings[key]['total']) * 100)
		return self.groupings


class AnalysisObject():

	def __init__(self,analysisString):
		try:
			self.hasProperHeadTones = False
			self.isBWAV = False
			self.hasProperPops = False
			self.hasCorrectTimeCode = False
			self.hasProperLayout = False
			self.isProperBitDepth = False
			self.isProperSampleRate = False
			self.isParsed = False
			self.totalStatus = False

			mainObject = json.loads(analysisString)
			self.parse(mainObject)
			self.mainObject = mainObject

		except Exception as e:
			return None	

	def parse(self, mainObject):
		if mainObject['headTones']['status'] == 'pass':
			self.hasProperHeadTones = True
		if mainObject['pops']['status'] == 'pass':
			self.hasProperPops = True
		if mainObject['timeStamp'] == 165765600:
			self.hasCorrectTimeCode = True
		if mainObject['bextChunk'] == True:
			self.isBWAV = True
		if mainObject['sampleRate'] == 48000:
			self.isProperSampleRate = True
		if mainObject['bitDepth'] == 24:
			self.isProperBitDepth = True
		if mainObject['fileLevels']['status'] == 'pass':
			self.hasProperLayout = True

		if mainObject['result'] == 'success':
			self.totalStatus = True
		else:
			self.totalStatus = False

		self.isParsed = True

	def categories(self):
		return GlobalCategories().categories()

	def keys(self):
		return GlobalCategories().keys()

	def result(self):
		results = [getattr(self, key) for key in self.keys()]
		return dict(zip(self.keys(), results))

def prettyPrintObject(nObject):
	return json.dumps(nObject, sort_keys=True, indent=4, separators=(',', ': '))

def formattedValue(nVar):
	if nVar == '0':
		return ''
	return nVar

def criteria():
	criteria = "A proper head tone is defined as 60 seconds of -20 db 1kHZ audio tone." + "\n"
	criteria += "A proper layout is defined as a SMPTE layout for 5.1 channel tracks." + "\n"
	criteria += "A proper pop is defined as a single frame of -20db 1kHZ tone at 00:59:58:00 that lasts for 24000/1001 of a second." + "\n"
	criteria += "A proper timecode value is defined starting at 00:57:30:00 or 165765600 samples." + "\n"
	criteria += "A Wave file is a BWav file if it has a bext chunk which will contain a timestamp field." + "\n"
	criteria += "A proper bit depth is 24 bits per audio sample." + "\n"
	criteria += "A proper sample rate is 48000Hz a second." + "\n"
	return criteria

def header():
	headers = []
	headers.append('Vendor')
	headers.extend(GlobalCategories().categories()[:-1])
	headers.append('No Errors')
	headers.append(GlobalCategories().categories()[-1])
	headers.append('Percentage')
	return "\t".join(headers)

def vendorInfo(vMaster, vendorName):
	sepString = firstline(vMaster, vendorName) + ("\n")
	sepString += secondline(vMaster, vendorName) + ("\n")
	sepString += thirdline(vMaster, vendorName)
	return sepString

def firstline(vMaster, vendorName):
	results = vMaster.resultsForVendor(vendorName)
	data = []
	data.append(vendorName)

	for key in GlobalCategories().keys()[:-1]:
		nVar = str(results[key]['fail'])
		data.append(formattedValue(nVar))

	nextKey = GlobalCategories().keys()[-1]
	data.append(formattedValue(str(results[nextKey]['pass'])))

	nextKey = 'totalStatus'
	data.append(formattedValue(str(results[nextKey]['total'])))
	data.append("")

	line = "\t".join(data)

	return line

def secondline(vMaster, vendorName):
	results = vMaster.resultsForVendor(vendorName)
	data = []
	data.append("fail")

	for key in GlobalCategories().keys()[:-1]:
		nVar = str(results[key]['fail'])
		data.append(formattedValue(nVar))

	data.append("")

	nextKey = 'totalStatus'
	data.append(formattedValue(str(results[nextKey]['fail'])))
	passNumber = (results[nextKey]['fail']) * 1.0 / (results[nextKey]['total']) * 100
	data.append("{:3.2f}%".format(passNumber))

	line = "\t".join(data)

	return line

def thirdline(vMaster, vendorName):
	results = vMaster.resultsForVendor(vendorName)
	data = []
	data.append("success")

	for key in GlobalCategories().keys()[:-1]:
		nVar = str(results[key]['pass'])
		data.append(formattedValue(nVar))

	nextKey = GlobalCategories().keys()[-1]
	data.append(formattedValue(str(results[nextKey]['pass'])))

	nextKey = 'totalStatus'
	data.append(formattedValue(str(results[nextKey]['pass'])))
	passNumber = (results[nextKey]['pass']) * 1.0 / (results[nextKey]['total']) * 100
	data.append("{:3.2f}%".format(passNumber))

	line = "\t".join(data)
	return line

def lastLine(vMaster):
	data = []
	data.append("Total")

	for key in GlobalCategories().keys()[:-1]:
		amount = 0
		for vendor in vMaster.vendors():
			results = vMaster.resultsForVendor(vendor)
			amount += results[key]['fail']
		data.append(formattedValue(str(amount)))

	amount = 0
	for vendor in vMaster.vendors():
		results = vMaster.resultsForVendor(vendor)
		amount += results['totalStatus']['pass']
	data.append(formattedValue(str(amount)))

	amount = 0
	for vendor in vMaster.vendors():
		results = vMaster.resultsForVendor(vendor)
		amount += results['totalStatus']['total']
	data.append(formattedValue(str(amount)))

	data.append("")

	line = "\t".join(data)
	return line

def tabDelimitedResultsFromDataBaseWithStartAndStopTimes(dbPath, startTime,endTime):
	dataStore = DataStoreReadOnly(dbPath)
	records = dataStore.recordsForDateStartAndDateEnd(startTime, endTime)
	v = VendorMaster()
	v.addRecords(records)
	sepString = "Results for the period of %s through %s" % (startTime, endTime) + "\n"
	sepString += header() + ("\n")
	for vendor in v.vendors():
		sepString += vendorInfo(v, vendor) + ("\n")
	sepString += lastLine(v) + ("\n")
	sepString += ("\n")
	sepString += criteria()
	return sepString

def outputDataWithTitleToFile(data, destPath):
	with open(destPath, 'w') as f:
		f.write(data)

def sendEmailFile(address, recipients, filePath, startDate, endDate):
	msg = MIMEMultipart('alternative')
	s = smtplib.SMTP(address)

	toEmail, fromEmail = ", ".join(recipients), 'bwfweeklyanalysis@bwfnoreply.com'
	print ", ".join(recipients)
	msg['Subject'] = 'BWF Analysis for the dates of %s through %s' % (startDate.strftime("%m-%d-%Y"), endDate.strftime("%m-%d-%Y"))
	msg['From'] = fromEmail
	body = 'BWF Analysis for the dates of %s through %s' % (startDate.strftime("%m-%d-%Y"), endDate.strftime("%m-%d-%Y"))

	#file attachment
	f = file(filePath)
	attachment = MIMEText(f.read())
	f.close()
	attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(filePath))           
	msg.attach(attachment)

	s.sendmail(fromEmail, toEmail, msg.as_string())

def sendWeeklyEmail(config):

	dbPath = config['dataBasePath']

	dateStart = datetime.date.today() - datetime.timedelta(days=7)
	dateEnd = datetime.date.today()

	data = tabDelimitedResultsFromDataBaseWithStartAndStopTimes(dbPath, dateStart.strftime("%Y-%m-%d %H:%M:%S"), dateEnd.strftime("%Y-%m-%d %H:%M:%S"))
	filePathName = "BWFAnalysis_%s_%s.txt" % (dateStart.strftime('%m%d%y'),dateEnd.strftime('%m%d%y'))
	fullPath = os.path.join(os.path.dirname(dbPath), filePathName)
	outputDataWithTitleToFile(data, fullPath)
	sendEmailFile(config['smtpServer'], config['emailRecipients'], fullPath, dateStart, dateEnd)

if __name__ == '__main__':
	
	f = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'weeklyemailconfig.json'), 'r')
	config = json.loads(f.read())
	sendWeeklyEmail(config)