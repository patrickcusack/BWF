import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from configurationoptions import configurationOptions
from messageformatting import failureHTMLText
from messageformatting import generalfailureHTMLTextMessage

import datetime

def sendAnalysisFailure(resultObject):
  errorDict = failureHTMLText(resultObject)
  text = errorDict['text']
  html = errorDict['html'] 
  sendEmailNotification(configurationOptions().smtpServer, "no.reply@BWFAnalyzer.com", configurationOptions().emailRecipients, "BWF Analysis Error: {}".format(resultObject['fileName']), text, html)

def sendProcessFailureMessage(infoDict):
  subject = infoDict['subject']
  message = infoDict['message']

  errorMessage = generalfailureHTMLTextMessage(message)
  recipients = configurationOptions().serviceErrorRecipients

  text = errorMessage['text']
  html = errorMessage['html'] 
  sendEmailNotification(configurationOptions().smtpServer, "no.reply@BWFAnalyzer.com", recipients, subject, text, html)

def sendPeriodicFailureMessage(message):
  '''send an email with a periodic frequency'''

  errorMessage = generalfailureHTMLTextMessage(message)
  text = errorMessage['text']
  html = errorMessage['html'] 
  recipients = configurationOptions().serviceErrorRecipients

  pathToEmailFile = os.path.join(os.path.dirname(__file__),'emailtimestamp')
  emailfile = None
  tempFile = None

  #does the email file exist? if no then create and send email immedaitely
  if not os.path.exists(pathToEmailFile):
    sendEmailNotification(configurationOptions().smtpServer, "no.reply@BWFAnalyzer.com", recipients, "Periodic Message: There was a process error: %s" % (message), text, html)
    try:
      emailfile = open(pathToEmailFile, 'w+')
      return
    except Exception as e:
      pass

  tempEmailFile = os.path.join(os.path.dirname(__file__),'tempFile')
  try:
    tempFile = open(tempEmailFile, 'w+')
  except Exception as e:
    sendEmailNotification(configurationOptions().smtpServer, "no.reply@BWFAnalyzer.com", recipients, "Periodic Process Error Message: %s" % (message), text, html)
    return

  #if the time last sent is greater than 30, then send
  difference = os.stat(tempEmailFile)[8] -  os.stat(pathToEmailFile)[8]
  print difference

  #send email every 4 hours
  if difference > (60 * 60 * 4):
    print 'sending email'
    sendEmailNotification(configurationOptions().smtpServer, "no.reply@BWFAnalyzer.com", recipients, "Periodic Process Error Message: %s" % (message), text, html)
    emailfile = open(pathToEmailFile, 'w+')
  else:
    print 'not sending email'


def sendEmailNotification(mailServer, sender, recipients, subject, message, html):
  msg = MIMEMultipart('alternative')
  msg['Subject'] = subject
  msg['From'] = sender
  msg['To'] = ", ".join(recipients)

  text = message
  html = html

  # Record the MIME types of both parts - text/plain and text/html.
  part1 = MIMEText(text, 'plain')
  part2 = MIMEText(html, 'html')

  # Attach parts into message container.
  # According to RFC 2046, the last part of a multipart message, in this case
  # the HTML message, is best and preferred.
  msg.attach(part1)
  msg.attach(part2)

  # Send the message via local SMTP server.
  s = smtplib.SMTP(mailServer)
  # sendmail function takes 3 arguments: sender's address, recipient's address
  # and message to send - here it is sent as one string.
  try:
    s.sendmail(sender, recipients, msg.as_string())
  except Exception as e:
    print e.message
  s.quit()

if __name__ == '__main__':

  sendPeriodicFailureMessage("this is a test message at {}".format(datetime.datetime.now().strftime("%m-%d-%Y %H:%M")))

