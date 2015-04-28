#!/usr/bin/python
import os
import argparse
from pcwavefile import PCWaveFile
import pctimecode
import tracklayouts
from ixmlupdater import xmlStringForWaveFile, addiXMLToWaveFile
import tracklayouts 
from prettyprintxml import prettyprintxml

def updatebwftimecode():
	parser = argparse.ArgumentParser(description="Set Timecode for a Broadcast Wave File, Optionally write metadata to iXML, and display file information")
	parser.add_argument( "filename", help="the file to process, represented as a path")
	parser.add_argument('-t','--timecode', required=True, dest="timecode", help="the timecode value, displayed as either drop or non drop, wrapped in quotes")
	parser.add_argument('-f', '--framerate', required=True, dest="framerate", help="an string representation of the framerate", choices=['2398', '24', '25', '2997', '2997DF', '30'])
	parser.add_argument('-l','--tracklayout', dest="tracklayout", help="a tracklayout confirguration for the iXML file", choices=tracklayouts.tracklayoutRepresentation())
	parser.add_argument('-x', '--noixml', dest="noixml", help="do not write ixml into file", action="store_true")

	group = parser.add_mutually_exclusive_group()
	group.add_argument('-v', '--verbose', dest="verbose", help="display iXML to screen", action="store_true")
	group.add_argument('-o', '--outputfile', dest="outputfile", help="a path to a file to save information about the wav file you are updating") 
	args = parser.parse_args()

	# bail if the timecode is not properly specified
	if pctimecode.isTimeCodeSafe(args.timecode, args.framerate) == False:
		print "-----------Timcode is invalid-----------"
		return

	useDropFrame = False 
	if args.framerate.find("DF") is not -1:
		useDropFrame = True

	filename = args.filename
	layout = tracklayouts.tracklayouts

	if os.path.exists(filename):
		wavefile = PCWaveFile(filename)

		newTimeReference = 0
		fileSampleRate = wavefile.numberOfSamplesPerSecond()

	# Calculate new timecode information
		if args.framerate == '2398':
			newTimeReference = pctimecode.convertTimeCodeToUnsignedLongLong2398(args.timecode, fileSampleRate)
		elif args.framerate == '24':
			newTimeReference = pctimecode.convertTimeCodeToUnsignedLongLong24(args.timecode, fileSampleRate)
		elif args.framerate == '25':
			newTimeReference = pctimecode.convertTimeCodeToUnsignedLongLong25(args.timecode, fileSampleRate)
		elif args.framerate == '2997':
			if useDropFrame == True:
				newTimeReference = pctimecode.convertTimeCodeToUnsignedLongLong2997DF(args.timecode, fileSampleRate)
			else:
				newTimeReference = pctimecode.convertTimeCodeToUnsignedLongLong2997(args.timecode, fileSampleRate)
		else:
			newTimeReference = pctimecode.convertTimeCodeToUnsignedLongLong30(args.timecode, fileSampleRate)

		wavefile.setTimeReference(newTimeReference)
	
	# Set the layout of the files for the iXML chunk	
		suggestedTrackLayoutDictionary = {}
		if args.tracklayout is not None:
			suggestedTrackLayoutDictionary = {"suggestedTrackNameLayoutArray":layout[args.tracklayout]["trackNames"], "suggestedTrackFunctionLayoutArray":layout[args.tracklayout]["trackFunctions"]}
		
		xmlstring = xmlStringForWaveFile(wavefile, useDropFrame, args.framerate, suggestedTrackLayoutDictionary)
		
	# Check to see if we want to append the iXML to the file
		if args.noixml == False:
			wavefile.clearIXMLChunk()
			addiXMLToWaveFile(wavefile, xmlstring)

	# Write the iXML to stdout or file depending on the option
		if args.verbose == True:
			print "Sample Time Stamp:", newTimeReference
			prettyprintxml(xmlstring)
		elif args.outputfile is not None:
			with open(args.outputfile, 'w+') as f:
				f.write(xmlstring)

	else:
		print "file does not exist:", filename

if __name__ == '__main__':

	updatebwftimecode()
	