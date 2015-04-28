import os
from xml.dom.minidom import Document

def xmlObjectDefinitionRepresentation(fileName, fileHash):
	doc = Document()
	dvObjectDefinition = doc.createElement('DIVAObjectDefinition')
	doc.appendChild(dvObjectDefinition)

	nextObject = doc.createElement('objectName')
	nextObject.appendChild(doc.createTextNode(fileName))
	dvObjectDefinition.appendChild(nextObject)

	nextObject = doc.createElement('categoryName')
	nextObject.appendChild(doc.createTextNode('ARCHIVE_DR'))
	dvObjectDefinition.appendChild(nextObject)

	nextObject = doc.createElement('comments')
	nextObject.appendChild(doc.createTextNode('MEDIASEALED FILE {}'.format(fileHash)))
	dvObjectDefinition.appendChild(nextObject)

	fileListObject = doc.createElement('fileList')
	dvObjectDefinition.appendChild(fileListObject)

	nextObject = doc.createElement('file')
	nextObject.appendChild(doc.createTextNode(fileName))
	nextObject.setAttribute('checksumType', 'MD5')
	nextObject.setAttribute('checksumValue', fileHash)	

	fileListObject.appendChild(nextObject)

	return ''.join(node.toprettyxml() for node in doc.childNodes)

def writeXmlObjectDefinitionRepresentationToFilePath(filePath, fileName, fileHash):
	xmlObjectString = xmlObjectDefinitionRepresentation(fileName, fileHash)
	with open(filePath, 'w') as f:
		f.write(xmlObjectString)

def main():
	fileName = os.path.basename('/Volumes/DriveA/TestFileName.mov')
	fileHash = '8bcee99959124e497147e3c40216848a'
	print xmlObjectDefinitionRepresentation(fileName, fileHash)
	writeXmlObjectDefinitionRepresentationToFilePath((os.path.join(os.path.expanduser('~/Desktop/'), fileName)) + ".xml", fileName, fileHash)

if __name__ == '__main__':
	main()


'''
<DIVAObjectDefinition>
<objectName>__FILENAME__</objectName>
<categoryName>ARCHIVE_DR</categoryName>
<comments>MEDIASEALED FILE %HASH%</comments>
<fileList>
	<file checksumType="MD5" checksumValue="%HASH%">__FILENAME__</file>
</fileList>
</DIVAObjectDefinition>

'''