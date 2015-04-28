import numpy as np
import math

def main():
	runningAnalysis = [0,0,0,0,0,0,0,0,0,0,0,0]
	length = len(runningAnalysis)
	rms = math.sqrt(np.sum(runningAnalysis)/(48048*length))
	print rms

if __name__ == '__main__':
	main()
