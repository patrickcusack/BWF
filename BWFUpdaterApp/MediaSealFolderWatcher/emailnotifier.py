import os
from configurator import configurationOptions
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utility import DefaultLogger


def sendSuccessEmail(message=""):
	# simpleSuccessEmail(message)
	nMessage = 'Success' + " " +  str(message)
	gmailMessage(nMessage)

def sendFailureEmail(message=""):
	# simpleFailureEmail(message)
	nMessage = 'Failure' + " " +  str(message)
	gmailMessage(nMessage)

def gmailMessage(message=""):
	to = 'patrickcusack@mac.com'
	gmail_user = 'evspatrickcusack@gmail.com'
	gmail_pwd = 'argonaut'
	smtpserver = smtplib.SMTP("smtp.gmail.com",587)
	smtpserver.ehlo()
	smtpserver.starttls()
	smtpserver.ehlo
	smtpserver.login(gmail_user, gmail_pwd)
	header = 'To:' + to + '\n' + 'From: ' + gmail_user + '\n' + 'Subject:testing \n'
	msg = header + '\n' + 'This is a message: ' + message +'\n\n'
	smtpserver.sendmail(gmail_user, to, msg)
	smtpserver.close()

def simpleSuccessEmail(message=""):
	smtpServer = configurationOptions().smtpServer
	recipients = configurationOptions().emailRecipients

	try:
		s = smtplib.SMTP(smtpServer)
		msg = "Subject: %s\n\n%s" % ('MediaSeal Process Complete', message)
		s.sendmail("do.not.reply@msarchiveserver.com", recipients, msg)
		s.quit()
	except Exception as e:
		info = 'There was an Error sending a sendSuccessEmail email:' + message + " :" + e.message
		DefaultLogger().debug(info)

def simpleFailureEmail(message=""):	
	smtpServer = configurationOptions().smtpServer
	recipients = configurationOptions().emailRecipients

	try:
		s = smtplib.SMTP(smtpServer)
		msg = "Subject: %s\n\n%s" % ('MediaSeal Process Error', message)
		s.sendmail("do.not.reply@msarchiveserver.com", recipients, msg)
		s.quit()
	except Exception as e:
		info = 'There was an Error sending a sendSuccessEmail email:' + message + " :" + e.message
		DefaultLogger().debug(info)

def successEmail(message=""):
	smtpServer = configurationOptions().smtpServer
	recipients = configurationOptions().emailRecipients

	try:
		s = smtplib.SMTP(smtpServer)
		msg = MIMEText("""MediaSeal Process Complete""")
		sender = 'do.not.reply@msarchiveserver.com'
		msg['Subject'] = "MediaSeal Process Complete" + "\n" + message
		msg['From'] = sender
		msg['To'] = ", ".join(recipients)
		s.sendmail(sender, recipients, msg.as_string())
		s.quit()
	except Exception as e:
		info = 'There was an Error sending a sendSuccessEmail email:' + message + " :" + e.message
		DefaultLogger().debug(info)

def failureEmail(message=""):
	smtpServer = configurationOptions().smtpServer
	recipients = configurationOptions().emailRecipients

	try:
		s = smtplib.SMTP(smtpServer)
		msg = MIMEText("""MediaSeal Process Error""")
		sender = 'do.not.reply@msarchiveserver.com'
		msg['Subject'] = "MediaSeal Process Error" + "\n" + message
		msg['From'] = sender
		msg['To'] = ", ".join(recipients)
		s.sendmail(sender, recipients, msg.as_string())	
		s.quit()
	except Exception as e:
		info = 'There was an Error sending a sendFailureEmail email:' + message + " :" + e.message
		DefaultLogger().debug(info)

if __name__ == '__main__':
	sendSuccessEmail("This is a success email that is properly spelled.")
