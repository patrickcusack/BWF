import hashlib
import sys

def hashfile(afile, hasher, blocksize=65536):
    buf = afile.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = afile.read(blocksize)
    return hasher.digest()

def hashForFile(aFile):
    return ''.join(x.encode('hex') for x in hashfile(aFile, hashlib.md5()))    

def hashForFilePath(path):
	with open(path, 'rb') as f:	
		return ''.join(x.encode('hex') for x in hashfile(f, hashlib.md5()))

if __name__ == '__main__':
	print hashForFilePath(sys.argv[1])
