import smtplib
 
to = 'patrickcusack@mac.com'
gmail_user = 'evspatrickcusack@gmail.com'
gmail_pwd = 'argonaut'
smtpserver = smtplib.SMTP("smtp.gmail.com",587)
smtpserver.ehlo()
smtpserver.starttls()
smtpserver.ehlo
smtpserver.login(gmail_user, gmail_pwd)
header = 'To:' + to + '\n' + 'From: ' + gmail_user + '\n' + 'Subject:testing \n'
print header
msg = header + '\n this is test msg from patrick cusack\n\n'
smtpserver.sendmail(gmail_user, to, msg)
print 'done!'
smtpserver.close()