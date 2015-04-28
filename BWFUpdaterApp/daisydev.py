import requests
import json

def updateStatus(daNumber):
	url = 'http://qa.daisy.nbcuni.ge.com/daisy/assetupdate/updateField/'
	payload = {'classname':'AssetStatus', 'fieldDescription':'Available'}
	headers = {'content-type':'application/x-www-form-urlencoded'}
	r = rquests.put('{}{}'.format(url, daNumber), payload=payload, headers=headers)
