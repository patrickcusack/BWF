import os
import json

def prettyPrintJSON(data):
	return json.dumps(data, sort_keys = True, indent=4, separators=(',', ': '))

def writeDataToFile(path, data):
	with open(path, 'w') as f:
		f.write(data)

def main():
	mydict = {"a":"1", "b":"2"}
	destination = os.path.expanduser('~/Desktop/test.txt')
	writeDataToFile(destination, prettyPrintJSON(mydict))

if __name__ == '__main__':
	main()