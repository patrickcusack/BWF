		print channel
			print 'tone runs'
			for run in self.contiguousRuns(runs):
				start = convertUnsignedLongLongToTimeCode(run['start'], self.timeCodeSampleRate, self.timeBase)
				stop = convertUnsignedLongLongToTimeCode(run['start']+ (run['length']*self.timeCodeSampleRate), self.timeCodeSampleRate, self.timeBase)
				print start, "to", stop, (run['length']*self.timeCodeSampleRate)

			#is one these runs a tone run? ie does it start and end between the proper time and at least 55-ish seconds?
			#check the freq at 00:59:58:00
			#must answer - is pop clean?

			#is there an error at the margins? if so ok, otherwise is the error is more than length 1 then we a problem 
			print 'error runs'
			for run in self.contiguousRuns(errorRuns):
				start = convertUnsignedLongLongToTimeCode(run['start'], self.timeCodeSampleRate, self.timeBase)
				stop = convertUnsignedLongLongToTimeCode(run['start']+ (run['length']*self.timeCodeSampleRate), self.timeCodeSampleRate, self.timeBase)
				print start, "to", stop, (run['length']*self.timeCodeSampleRate)

			#is one these runs a silence run? ie does it start and end between the proper time?
			print 'silence runs'
			for run in self.contiguousRuns(silenceRuns):
				start = convertUnsignedLongLongToTimeCode(run['start'], self.timeCodeSampleRate, self.timeBase)
				stop = convertUnsignedLongLongToTimeCode(run['start']+ (run['length']*self.timeCodeSampleRate), self.timeCodeSampleRate, self.timeBase)
				print start, "to", stop, (run['length']*self.timeCodeSampleRate)