import sys
import os
from pymongo import MongoClient
import datetime

# http://altons.github.io/python/2013/01/21/gentle-introduction-to-mongodb-using-pymongo/

def currentDBName():
	return 'fileDatabase2'

def testObject():
	return {"author": "Mike", "text": "My first blog post!", "tags": ["mongodb", "python", "pymongo"], "date": datetime.datetime.utcnow()}

def main():
	try:
		client = MongoClient('localhost', 27017)
		db = client[currentDBName()]
		records = db.records
		recordId = records.insert(testObject())
		print recordId 
	except Exception:
		print 'unable to connect'

def showAllRecords():
	try:
		client = MongoClient('localhost', 27017)
		db = client[currentDBName()]
		records = db.records
		print records.count()
	except Exception:
		print 'unable to connect'

def recordForFilePath(filePath):
	return {"filePath": filePath, "processed":False, "created_at":datetime.datetime.utcnow(), "modified_at":datetime.datetime.utcnow(), "result":""}

def addFilePathToDataBase(filePath):
	try:
		client = MongoClient('localhost', 27017)
		db = client[currentDBName()]
		db.records.insert(recordForFilePath(filePath))
	except Exception:
		print 'unable to connect'

def findUnProcessedRecords():
	try:
		client = MongoClient('localhost', 27017)
		db = client[currentDBName()]
		for r in db.records.find():
			# db.records.update({"_id":r['_id']},{"$set":{"next":"new addition"}})
			print r
	except Exception as e:
		print e.message, 'unable to connect'

def walkPathAndCreateRecords(filePath):
	if os.path.isdir(filePath):
		for path, dirs, files in os.walk(filePath):
		    for name in files:
		    	fullpath = os.path.join(path, name)
		    	addFilePathToDataBase(fullpath)
	else:
		addFilePathToDataBase(filePath)

def main():
	try:	
		walkPathAndCreateRecords(sys.argv[1])
	except Exception:
		print 'path not defined'	

if __name__ == '__main__':
	findUnProcessedRecords()
	# main()