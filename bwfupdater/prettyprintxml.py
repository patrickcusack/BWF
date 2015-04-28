from xml.dom.minidom import parseString

def prettyprintxml(xml_string):
	xml = parseString(xml_string)
	print xml.toprettyxml()