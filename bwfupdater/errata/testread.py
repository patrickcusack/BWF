import os
import sys

def testRead(filePath):
	with open(filePath, 'r') as f:
		f.seek(1024)
		data = f.read(3456000)
		print len(data)
		
def main():
	filePath = None
	try:
		filePath = sys.argv[1]
	except Exception:
		print "No file specified"
		return

	testRead(filePath)

if __name__ == '__main__':
	main()
