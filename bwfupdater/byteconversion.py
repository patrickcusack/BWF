import struct

def les24toles32Value(fileDataAsString):
	if len(fileDataAsString) != 3:
		print "error"

	return struct.unpack('<i', fileDataAsString + ('\xff' if ord(fileDataAsString[2]) & 0x80 else '\0'))[0]