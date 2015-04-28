import argparse
import os
import sys

from pcwavefile import PCWaveFile
import pctimecode
from ixmlupdater import xmlStringForWaveFile, addiXMLToWaveFile
import tracklayouts 

def trackLayoutTest():

	parser = argparse.ArgumentParser(description="Set Timecode for a Broadcast Wave File")
	parser.add_argument( "filename", help="the file to process, represented as a path")
	parser.add_argument('-l','--tracklayout', dest="tracklayout", help="a tracklayout confirguration for the iXML file", choices=tracklayouts.tracklayoutRepresentation())
	args = parser.parse_args()

	filename = args.filename
	layout = tracklayouts.tracklayouts

	if os.path.exists(filename):
		wavefile 	= PCWaveFile(filename)

		suggestedTrackLayoutDictionary = {}
		if args.tracklayout is not None:
			suggestedTrackLayoutDictionary = {"suggestedTrackNameLayoutArray":layout[args.tracklayout]["trackNames"], "suggestedTrackFunctionLayoutArray":layout[args.tracklayout]["trackFunctions"]}


		xmlstring 	= xmlStringForWaveFile(wavefile, True, "2997", suggestedTrackLayoutDictionary)
		# addiXMLToWaveFile(wavefile, xmlstring)
		print xmlstring
	else:
		print "file does not exist:", filename



if __name__ == '__main__':

	trackLayoutTest()

