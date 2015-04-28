import requests
import json
import types
import re
from emailnotifier import sendSuccessEmail
from emailnotifier import sendFailureEmail

def getDaisyNumber(filePath):
	if 'DA' not in filePath:
		return None
	if '_' not in filePath:
		return None
	try:
		daisyPattern = re.compile(r"""(.*?)(DA[0-9]{0,12})(\_)(.+?$)""")
		match = daisyPattern.match(filePath)
		if match == None:
			print 'No Match'
			return None
		if match.groups < 2:
			print 'Not enough Matches'
			return None
		return match.group(2)
	except Exception as e:
		print e.message
		return None

def daisyAccesTest():
	daisyLookup = DaisyMetadataLookup("DA000446098")
	if daisyLookup.isValid == True:
		checksum =  daisyLookup.checksumForFile('DA000446098_31359_FTR_133_SM_ENG_audio_01.mxf')
		if checksum is not None:
			print checksum
		else:
			print "No checksum FOR GOOD FILE"

		checksum =  daisyLookup.checksumForFile('FILE_DOES_NOT_EXIST.mxf')
		if checksum is not None:
			print checksum
		else:
			print "No checksum for BAD FILE"

def mock_DA_Numbers():
	return ['DA000068853', 'DA000068853','DA000128318','DA000513729','DA000057907','DA000557041','DA000478228','DA000427688']

def mock_files():
	return ["DropSquad_DA000068853_05457_FTR_Theatrical_2398_16x9FF_178_ENG_HD_ProResHQ_220M.mov", 
			"InGodWeTrust_DA000128318_02122_FTR_Theatrical_2997_4x3FF_133_LAS_NTSC_ProResHQ_60M.mov",
			"InGodWeTrust_DA000513729_02122_FTR_TheatricalTexted_2398_16x9FF_133_ENG_HD_ProResHQ_220M.mov", 
			"K9_DA000057907_05380_FTR_Theatrical_2398_16x9FF_178_ENG_HD_ProResHQ_220M.mov", 
			"LawForTombstone_DA000557041_UW044_FTR_Theatrical_2997_4x3FF_133_ENG_NTSC_ProResHQ_60M.mov", 
			"LawlessBreedThe_DA000478228_UF820_FTR_Theatrical_2398_16x9SM_133_ENG_HD_ProResHQ_220M.mov", 
			"Traffic_DA000427688_09647_FTR_TheatricalTexted_2398_16x9FF_178_ENG_HD_ProResHQ_220M.mov"]

class DaisyMetadataLookup():

	def __init__(self, numberString, isDevMode=True):
		self.isDevMode = isDevMode
		self.number = numberString
		self.metadataObject = json.loads(self.metaDataStringForNumber(numberString))
		self.isValid = self.isMetaDataObjectValid(self.metadataObject)

	def metaDataStringForNumber(self, numberString):
		if self.isDevMode == True:
			return self.mockDataAsString(numberString)
		try:
			# address = 'http://daisy.inbcu.com/daisy/asset/metadata/' + str(numberString)
			address = "http://qa.daisy.nbcuni.ge.com/daisy/asset/metadata/" + str(numberString)
			r = requests.get(address)
			if r.status_code == 200:
				return r.text
		except Exception as e:
			print e.message
			errorString = 'Unable to retrive daisy asset metadata for ' +  str(numberString) + "."
			errorString = errorString + " " + "Additional information: " + str(e.message)
			sendFailureEmail(errorString)
		return '[]'

	def assetFiles(self):
		if 'assetFiles' not in self.metadataObject.keys():
			return None
		if len(self.metadataObject['assetFiles']) == 0:
			return None
		return self.metadataObject['assetFiles']

	def checksumForFile(self, fileName):
		for assetFile in self.assetFiles():
			if 'filename' not in assetFile.keys() and 'checksum' not in assetFile.keys():
				continue
			else:
				if assetFile['filename'] == fileName:
					return assetFile['checksum']
		return None

	def fileSizeForFile(self, fileName):
		for assetFile in self.assetFiles():
			if 'fileSizeDetails' not in assetFile.keys():
				continue
			else:
				if assetFile['filename'] == fileName:
					return assetFile['fileSizeDetails']
		return None

	def isMetaDataObjectValid(self, metadataObject):
		if metadataObject == None:
			return False
		if type(metadataObject) != types.DictType:
			return False
		return True

	def mockDataAsString(self, daNumber):
		try:
			data = {"DA000068853":'''{"timecodeType": "NDFTC", "closedCaptionType": "Closed Captioning-None", "videoBitrate": "220 Mbit/s", "mediaAssetLevel": "Mezzanine ProRes", "frameRate": "23.98", "audioBitDepth": "24 bit", "vendor": "UDS - TVD", "primaryLanguage": "English", "dueDate": null, "assetType": "Asset", "textedLanguage": null, "runTime": null, "title": "DROP SQUAD Theatrical (05457) 84 min 1994", "createDate": 1292227200000, "videoScanType": "progressive segmented frame", "productionNumberId": null, "storageCategory": "Archive DR", "closedCaptionLanguage": "Unspecified", "trackingId": "DA000068853", "audioFormat": "Stereo", "channelCapacity": "4", "assetCollection": "N/A", "displayAspectRatio": "16x9", "audioCodec": "Not Applicable", "location": null, "status": "Available", "contentType": "Full Feature", "parentTrackingId": null, "standard": "HD", "originalPONumber": "66785", "versionId": "360", "assetCategory": "audiovideo", "packages": [{"packageType": "Package", "frameRate": "Not Applicable", "packageId": "PKG526283"}], "setId": "SET303171", "subtitles": [], "assetFiles": [{"status": "Available", "fileLocation": "FPD ARCHIVE", "encrypted": false, "createDate": null, "filename": "DropSquad_DA000068853_05457_FTR_Theatrical_2398_16x9FF_178_ENG_HD_ProResHQ_220M.mov", "encryptedChecksum": null, "encryptedEndDate": null, "fileSizeDetails": "null", "fileSize": "0 bytes", "trackingId": null, "checksum": "E18EBE47C811CE1EF57E02E71E324342", "fileExtension": "MOV File Extension", "encryptedStartDate": null, "fileFormat": "Unknown", "encryptedType": ""}], "videoCodec": "Apple Pro Res", "texted": "Texted", "contentItems": null, "children": [], "productionNumber": "05457", "sampleRate": "48 kHz", "audioChannels": [{"channelLanguage": "English", "channelNumber": "1", "channelConfiguration": "Stereo LT +12db"}, {"channelLanguage": "English", "channelNumber": "2", "channelConfiguration": "Stereo RT +12db"}, {"channelLanguage": "Not Applicable", "channelNumber": "3", "channelConfiguration": "Stereo LT M&E +12db"}, {"channelLanguage": "Not Applicable", "channelNumber": "4", "channelConfiguration": "Stereo RT M&E +12db"}], "externalLink": "http://daisy.inbcu.com/daisy/app/assetLink?barcode=DA000068853", "aspectRatio": "1.78:1", "videoFormat": "Full Frame"}''',
					"DA000128318":'''{"timecodeType": "DFTC", "closedCaptionType": null, "videoBitrate": "60 Mbit/s", "mediaAssetLevel": "Mezzanine ProRes", "frameRate": "29.97", "audioBitDepth": "Blank", "vendor": "Universal Digital Video ", "primaryLanguage": "Latin American Spanish", "dueDate": 1361557411000, "assetType": "Asset", "textedLanguage": null, "runTime": null, "title": "IN GOD WE TRUST Theatrical (02122) 97 min 1980", "createDate": 1361556904000, "videoScanType": "interlaced", "productionNumberId": null, "storageCategory": "Archive DR", "closedCaptionLanguage": null, "trackingId": "DA000128318", "audioFormat": "Blank", "channelCapacity": "4", "assetCollection": "N/A", "displayAspectRatio": "4x3", "audioCodec": "Linear Pulse Code Modulation", "location": null, "status": "Available", "contentType": "Full Feature", "parentTrackingId": null, "standard": "NTSC", "originalPONumber": "16289-1", "versionId": "19948", "assetCategory": "audiovideo", "packages": [], "setId": null, "subtitles": [], "assetFiles": [{"status": "Available", "fileLocation": "FPD ARCHIVE", "encrypted": false, "createDate": null, "filename": "InGodWeTrust_DA000128318_02122_FTR_Theatrical_2997_4x3FF_133_LAS_NTSC_ProResHQ_60M.mov", "encryptedChecksum": null, "encryptedEndDate": null, "fileSizeDetails": "null", "fileSize": "0 bytes", "trackingId": null, "checksum": "dd9c2437da7e66cdba05e6dd2e6b679a", "fileExtension": "MOV File Extension", "encryptedStartDate": null, "fileFormat": "Blank", "encryptedType": ""}], "videoCodec": "Apple Pro Res", "texted": "Texted", "contentItems": null, "children": [], "productionNumber": "02122", "sampleRate": "48 kHz", "audioChannels": [{"channelLanguage": "English", "channelNumber": "1", "channelConfiguration": "Mono Combine +12db"}, {"channelLanguage": "English", "channelNumber": "2", "channelConfiguration": "Mono Combine +12db"}, {"channelLanguage": "Latin American Spanish", "channelNumber": "3", "channelConfiguration": "Mono Combine +12db"}, {"channelLanguage": "Latin American Spanish", "channelNumber": "4", "channelConfiguration": "Mono Combine +12db"}], "externalLink": "http://daisy.inbcu.com/daisy/app/assetLink?barcode=DA000128318", "aspectRatio": "1.33:1", "videoFormat": "Full Frame"}''',
					"DA000513729":'''{"timecodeType": "23.98", "closedCaptionType": "Closed Captioning-None", "videoBitrate": "220 Mbit/s", "mediaAssetLevel": "Mezzanine ProRes", "frameRate": "23.98", "audioBitDepth": "Blank", "vendor": "Universal Digital Servic", "primaryLanguage": "English", "dueDate": 1403040530000, "assetType": "Asset", "textedLanguage": null, "runTime": "0:00", "title": "IN GOD WE TRUST Theatrical (02122) 97 min 1980", "createDate": 1402433011000, "videoScanType": "progressive", "productionNumberId": null, "storageCategory": "Archive DR", "closedCaptionLanguage": "Blank", "trackingId": "DA000513729", "audioFormat": "Mono", "channelCapacity": "4", "assetCollection": "N/A", "displayAspectRatio": "16x9", "audioCodec": "Linear Pulse Code Modulation", "location": null, "status": "Available", "contentType": "Full Feature", "parentTrackingId": "DA000081959", "standard": "HD", "originalPONumber": "151733-1", "versionId": "19948", "assetCategory": "audiovideo", "packages": [{"packageType": "Master Package", "frameRate": "23.98", "packageId": "PKG600789"}], "setId": null, "subtitles": [], "assetFiles": [{"status": "Available", "fileLocation": "FPD ARCHIVE", "encrypted": false, "createDate": null, "filename": "InGodWeTrust_DA000513729_02122_FTR_TheatricalTexted_2398_16x9FF_133_ENG_HD_ProResHQ_220M.mov", "encryptedChecksum": null, "encryptedEndDate": null, "fileSizeDetails": "134904315904", "fileSize": "125 GB", "trackingId": null, "checksum": "9d157b21e9b85c4293e0440d446bcb6d", "fileExtension": "MOV File Extension", "encryptedStartDate": null, "fileFormat": "Unknown", "encryptedType": ""}], "videoCodec": "Apple Pro Res", "texted": "Texted Full Show", "contentItems": null, "children": [], "productionNumber": "02122", "sampleRate": "48 kHz", "audioChannels": [{"channelLanguage": "English", "channelNumber": "1", "channelConfiguration": "Mono Combine +12db"}, {"channelLanguage": "English", "channelNumber": "2", "channelConfiguration": "Mono Combine +12db"}, {"channelLanguage": "English", "channelNumber": "3", "channelConfiguration": "Mono M&E +12db"}, {"channelLanguage": "English", "channelNumber": "4", "channelConfiguration": "Mono M&E +12db"}], "externalLink": "http://daisy.inbcu.com/daisy/app/assetLink?barcode=DA000513729", "aspectRatio": "1.33:1", "videoFormat": "Full Frame"}''',
					"DA000057907":'''{"timecodeType": "NDFTC", "closedCaptionType": "Closed Captioning-None", "videoBitrate": "220 Mbit/s", "mediaAssetLevel": "Mezzanine ProRes", "frameRate": "23.98", "audioBitDepth": "24 bit", "vendor": "UDS - TVD", "primaryLanguage": "English", "dueDate": null, "assetType": "Asset", "textedLanguage": null, "runTime": null, "title": "K-9 Theatrical (05380) 102 min 1989", "createDate": 1270241640000, "videoScanType": "progressive segmented frame", "productionNumberId": null, "storageCategory": "Archive DR", "closedCaptionLanguage": "Unspecified", "trackingId": "DA000057907", "audioFormat": "Stereo", "channelCapacity": "4", "assetCollection": "N/A", "displayAspectRatio": "16x9", "audioCodec": "Not Applicable", "location": null, "status": "Available", "contentType": "Full Feature", "parentTrackingId": null, "standard": "HD", "originalPONumber": null, "versionId": "20588", "assetCategory": "audiovideo", "packages": [{"packageType": "Package", "frameRate": "Not Applicable", "packageId": "PKG524159"}], "setId": null, "subtitles": [], "assetFiles": [{"status": "Available", "fileLocation": "FPD ARCHIVE", "encrypted": false, "createDate": null, "filename": "K9_DA000057907_05380_FTR_Theatrical_2398_16x9FF_178_ENG_HD_ProResHQ_220M.mov", "encryptedChecksum": null, "encryptedEndDate": null, "fileSizeDetails": "73807868422", "fileSize": "68 GB", "trackingId": null, "checksum": "ad14406af5956facee9522dbfaeafa9e", "fileExtension": "MOV File Extension", "encryptedStartDate": null, "fileFormat": "Apple Pro Res", "encryptedType": ""}], "videoCodec": "Apple Pro Res", "texted": "Texted", "contentItems": null, "children": [], "productionNumber": "05380", "sampleRate": "48 kHz", "audioChannels": [{"channelLanguage": "English", "channelNumber": "1", "channelConfiguration": "Stereo LT +12db"}, {"channelLanguage": "English", "channelNumber": "2", "channelConfiguration": "Stereo RT +12db"}, {"channelLanguage": "Not Applicable", "channelNumber": "3", "channelConfiguration": "Stereo LT M&E +12db"}, {"channelLanguage": "Not Applicable", "channelNumber": "4", "channelConfiguration": "Stereo RT M&E +12db"}], "externalLink": "http://daisy.inbcu.com/daisy/app/assetLink?barcode=DA000057907", "aspectRatio": "1.78:1", "videoFormat": "Full Frame"}''',
					"DA000557041":'''{"timecodeType": "DFTC", "closedCaptionType": "Closed Captioning-None", "videoBitrate": "60 Mbit/s", "mediaAssetLevel": "Mezzanine ProRes", "frameRate": "29.97", "audioBitDepth": "Blank", "vendor": null, "primaryLanguage": "English", "dueDate": 1415347200000, "assetType": "Asset", "textedLanguage": null, "runTime": "01:36:49", "title": "LAW FOR TOMBSTONE Theatrical (UW044) 59 min 1937", "createDate": 1415219063000, "videoScanType": "interlaced", "productionNumberId": null, "storageCategory": "Archive DR", "closedCaptionLanguage": "Blank", "trackingId": "DA000557041", "audioFormat": "Dolby Surround", "channelCapacity": "4", "assetCollection": "N/A", "displayAspectRatio": "4x3", "audioCodec": "Linear Pulse Code Modulation", "location": null, "status": "Available", "contentType": "Full Feature", "parentTrackingId": "DA000550025", "standard": "NTSC", "originalPONumber": null, "versionId": "14498", "assetCategory": "audiovideo", "packages": [], "setId": null, "subtitles": [], "assetFiles": [{"status": "Available", "fileLocation": "FPD ARCHIVE", "encrypted": false, "createDate": null, "filename": "LawForTombstone_DA000557041_UW044_FTR_Theatrical_2997_4x3FF_133_ENG_NTSC_ProResHQ_60M.mov", "encryptedChecksum": null, "encryptedEndDate": null, "fileSizeDetails": "47934914560", "fileSize": "44 GB", "trackingId": null, "checksum": "0ac0f81bec648ac944e2064c565da51c", "fileExtension": "MOV File Extension", "encryptedStartDate": null, "fileFormat": "Unknown", "encryptedType": ""}], "videoCodec": "Apple Pro Res", "texted": "Texted", "contentItems": null, "children": [], "productionNumber": "UW044", "sampleRate": "48 kHz", "audioChannels": [{"channelLanguage": "English", "channelNumber": "1", "channelConfiguration": "Mono Combine"}, {"channelLanguage": "English", "channelNumber": "2", "channelConfiguration": "Mono Combine"}], "externalLink": "http://daisy.inbcu.com/daisy/app/assetLink?barcode=DA000557041", "aspectRatio": "1.33:1", "videoFormat": "Full Frame"}''',
					"DA000478228":'''{"timecodeType": "23.98", "closedCaptionType": null, "videoBitrate": "220 Mbit/s", "mediaAssetLevel": "Mezzanine ProRes", "frameRate": "23.98", "audioBitDepth": "Blank", "vendor": "Universal Digital Servic", "primaryLanguage": "English", "dueDate": 1393516611000, "assetType": "Asset", "textedLanguage": null, "runTime": "0:00", "title": "THE LAWLESS BREED Theatrical (UF820) 83 min 1953", "createDate": 1393431434000, "videoScanType": "progressive", "productionNumberId": null, "storageCategory": "Archive DR", "closedCaptionLanguage": null, "trackingId": "DA000478228", "audioFormat": "Mono", "channelCapacity": "4", "assetCollection": "N/A", "displayAspectRatio": "16x9", "audioCodec": "Linear Pulse Code Modulation", "location": null, "status": "Available", "contentType": "Full Feature", "parentTrackingId": "DA000081304", "standard": "HD", "originalPONumber": "110296-1", "versionId": "13269", "assetCategory": "audiovideo", "packages": [{"packageType": "Master Package", "frameRate": "23.98", "packageId": "PKG598079"}], "setId": null, "subtitles": [], "assetFiles": [{"status": "Available", "fileLocation": "FPD ARCHIVE", "encrypted": false, "createDate": null, "filename": "LawlessBreedThe_DA000478228_UF820_FTR_Theatrical_2398_16x9SM_133_ENG_HD_ProResHQ_220M.mov", "encryptedChecksum": null, "encryptedEndDate": null, "fileSizeDetails": "114452393984", "fileSize": "106 GB", "trackingId": null, "checksum": "5ea047c4edfca4496426b4f3ec1c6373", "fileExtension": "MOV File Extension", "encryptedStartDate": null, "fileFormat": "Blank", "encryptedType": ""}], "videoCodec": "Apple Pro Res", "texted": "Texted", "contentItems": null, "children": [], "productionNumber": "UF820", "sampleRate": "48 kHz", "audioChannels": [{"channelLanguage": "English", "channelNumber": "1", "channelConfiguration": "Mono Combine +12db"}, {"channelLanguage": "English", "channelNumber": "2", "channelConfiguration": "Mono Combine +12db"}, {"channelLanguage": "Not Applicable", "channelNumber": "3", "channelConfiguration": "Mono M&E +12db"}, {"channelLanguage": "Not Applicable", "channelNumber": "4", "channelConfiguration": "Mono M&E +12db"}], "externalLink": "http://daisy.inbcu.com/daisy/app/assetLink?barcode=DA000478228", "aspectRatio": "1.33:1", "videoFormat": "Side Matted"}''',
					"DA000427688":'''{"timecodeType": "23.98", "closedCaptionType": null, "videoBitrate": "220 Mbit/s", "mediaAssetLevel": "Mezzanine ProRes", "frameRate": "23.98", "audioBitDepth": "Blank", "vendor": "Universal Digital Servic", "primaryLanguage": "English", "dueDate": 1380554756000, "assetType": "Asset", "textedLanguage": null, "runTime": "0:00", "title": "TRAFFIC Theatrical (09647) 147 min 2000", "createDate": 1380036608000, "videoScanType": "progressive", "productionNumberId": null, "storageCategory": "Archive DR", "closedCaptionLanguage": null, "trackingId": "DA000427688", "audioFormat": "5.1 Discrete", "channelCapacity": "10", "assetCollection": "N/A", "displayAspectRatio": "16x9", "audioCodec": "Linear Pulse Code Modulation", "location": null, "status": "Available", "contentType": "Full Feature", "parentTrackingId": "DA000080625", "standard": "HD", "originalPONumber": "43429-1", "versionId": "10091", "assetCategory": "audiovideo", "packages": [{"packageType": "Master Package", "frameRate": "23.98", "packageId": "PKG599316"}], "setId": null, "subtitles": [], "assetFiles": [{"status": "Available", "fileLocation": "FPD ARCHIVE", "encrypted": false, "createDate": null, "filename": "Traffic_DA000427688_09647_FTR_TheatricalTexted_2398_16x9FF_178_ENG_HD_ProResHQ_220M.mov", "encryptedChecksum": null, "encryptedEndDate": null, "fileSizeDetails": "null", "fileSize": "0 bytes", "trackingId": null, "checksum": "13a84da1b5d74c620f06b401b0a193f6", "fileExtension": "MOV File Extension", "encryptedStartDate": null, "fileFormat": "Blank", "encryptedType": ""}], "videoCodec": "Apple Pro Res", "texted": "Texted Full Show", "contentItems": null, "children": [], "productionNumber": "09647", "sampleRate": "48 kHz", "audioChannels": [{"channelLanguage": "English", "channelNumber": "1", "channelConfiguration": "Stereo Left"}, {"channelLanguage": "English", "channelNumber": "2", "channelConfiguration": "Stereo Right"}, {"channelLanguage": "English", "channelNumber": "3", "channelConfiguration": "Stereo Center"}, {"channelLanguage": "English", "channelNumber": "4", "channelConfiguration": "Lower Frequency Effects"}, {"channelLanguage": "English", "channelNumber": "5", "channelConfiguration": "Stereo Left Surround"}, {"channelLanguage": "English", "channelNumber": "6", "channelConfiguration": "Stereo Right Surround"}, {"channelLanguage": "English", "channelNumber": "7", "channelConfiguration": "Stereo LT +12db"}, {"channelLanguage": "English", "channelNumber": "8", "channelConfiguration": "Stereo RT +12db"}, {"channelLanguage": "Not Applicable", "channelNumber": "9", "channelConfiguration": "Stereo LT M&E +12db"}, {"channelLanguage": "Not Applicable", "channelNumber": "10", "channelConfiguration": "Stereo RT M&E +12db"}], "externalLink": "http://daisy.inbcu.com/daisy/app/assetLink?barcode=DA000427688", "aspectRatio": "1.78:1", "videoFormat": "Full Frame"}'''}
			return data[daNumber]
		except Exception as e:
			return None

if __name__ == '__main__':
	# print 'DA000446098_31359_FTR_133_SM_ENG_01', getDaisyNumber('DA000446098_31359_FTR_133_SM_ENG_01')
	# print 'BAD EXAMPLE', getDaisyNumber('BAD EXAMPLE')

	# for number in mock_DA_Numbers():
	# 	print DaisyMetadataLookup(number, True).metadataObject
	# 	print '\n'

	# for fileElement in mock_files():
	# 	dn = getDaisyNumber(fileElement)
	# 	dm = DaisyMetadataLookup(dn)
	# 	print fileElement, dm.checksumForFile(fileElement).upper()

 	print DaisyMetadataLookup('DA000405696').metadataObject


