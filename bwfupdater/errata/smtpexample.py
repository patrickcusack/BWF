import smtplib

# me == my email address
# you == recipient's email address
me = "patrickcusack@universalpostsound.com"
you = "patrickcusack@mac.com"

# Send the message via local SMTP server.
s = smtplib.SMTP('172.23.200.25')
s.sendmail(me, you, "This is a test")
s.quit()