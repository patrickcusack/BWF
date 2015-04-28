def formatErrorsHTML(errors):
	html = '<div>'
	for error in errors:
		html += '<p style="color:red">' + error + '</p>'
	html += '</div>'
	return html

def formatErrorsText(errors):
	html = ''
	for error in errors:
		html += error + '\n'
	return html

def generalfailureHTMLTextMessage(message):
	message = "Process Error: " + message 
	return {'html':generalfailureHTMLMessage(message), 'text':generalfailureTextMessage(message)}	

def generalfailureHTMLMessage(message):
	return 	'<div><p>' + message + '</p></div>'

def generalfailureTextMessage(message):
	return 	message

def failureHTMLText(resultObject):
	return {'html':failureMessageWithFileHTML(resultObject), 'text':failureMessageWithFileText(resultObject)}

def failureMessageWithFileHTML(resultObject):
	errorMessage = '<div><p>The file ' + resultObject['fileName'] + ' has the following <span style="color:red">errors</span>:</p></div>'
	errorMessage += formatErrorsHTML(resultObject['errors'])
	errorMessage += '<div></div>'

	passingHeader = '<div><p>The file ' + resultObject['fileName'] + ' <span style="color:green">passed</span> in the following areas:</p></div>'
	passingInfo = ''
	if resultObject['bitDepth'] == 24:
		passingInfo += '<p style="color:green">The file bit depth is 24 bits.</p>'
	if resultObject['sampleRate'] == 48000:
		passingInfo += '<p style="color:green">The file has a sample rate of 48kHz.</p>'
	if resultObject['bextChunk'] == True:
		passingInfo += '<p style="color:green">The file has a BEXT Chunk and is a Broadcast WAV File.</p>'
	if resultObject['fileLevels']['layout'] in ['SMPTE', 'STEREO']:
		passingInfo += '<p style="color:green">The file layout is ' + resultObject['fileLevels']['layout'] + '.</p>'
	if resultObject['pops']['status'] == 'pass':
		passingInfo += '<p style="color:green">The file has proper pops on its tracks.</p>'
	if resultObject['headTones']['status'] == 'pass':
		passingInfo += '<p style="color:green">The file has proper head tones - 1kHz frequency at -20db Peak.</p>'

	if passingInfo != '':
		errorMessage += passingHeader + passingInfo

	return errorMessage

def failureMessageWithFileText(resultObject):
	errorMessage = 'The following file: ' + resultObject['fileName'] + ' has the following errors:'
	errorMessage += '\n'
	errorMessage += formatErrorsText(resultObject['errors'])
	errorMessage += '\n'

	passingHeader = 'The file, ' + resultObject['fileName'] + ', passed in the following areas:'
	passingInfo = ''
	if resultObject['bitDepth'] == 24:
		passingInfo += 'The file is 24 bits.\n'
	if resultObject['sampleRate'] == 48000:
		passingInfo += 'The file is 48kHz.\n'
	if resultObject['bextChunk'] == True:
		passingInfo += 'The file is a Broadcast WAV File.\n'
	if resultObject['fileLevels']['status'] == 'pass':
		passingInfo += 'The file is ' + resultObject['fileLevels']['layout'] + '.\n'
	if resultObject['pops']['status'] == 'pass':
		passingInfo += 'The file has proper pops on its tracks.\n'
	if resultObject['headTones']['status'] == 'pass':
		passingInfo += 'The file has proper head tones - 1kHz frequency at -20db Peak.\n'

	if passingInfo != '':
		errorMessage += passingHeader + passingInfo
		
	return errorMessage

