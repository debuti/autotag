#!/usr/bin/env python
###############################################################################################
#  Author:
_author = '<a href="mailto:debuti@gmail.com">Borja Garcia</a>'
# Program:
_name = 'generalutils'
# Descrip:
_description = '''Library for uncataloged utilities.'''
# Version:
_version = '0.0.2'
#    Date: 
_date = '2010-11-05'
# License: This script doesn't require any license since it's not intended to be redistributed.
#          In such case, unless stated otherwise, the purpose of the author is to follow GPLv3.
# History:
#          0.0.1 (2010-11-05)
#            -Initial release
###############################################################################################

import os
import time
import shellutils
import socket
import platform

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders


def osName():
    '''This function returns the os name
    '''
    if (platform.system() == 'Linux'):
        (distname,version,id) = platform.linux_distribution()
        return distname
    return platform.system()


def osVersion():
    '''This function returns the os version
    '''
    if (platform.system() == 'Linux'):
        #platform.linux_distribution() output will be something like this ('Ubuntu', '12.04', 'precise')
        return platform.linux_distribution()[1]
    if (platform.system() == 'Windows'):
        return platform.system()
    return None

    return platform.release()


def systemName():
    '''This function returns the system name
    '''
    return socket.gethostname()
    

def now():
    '''This function returns the current time
    '''
    return time.strftime("%Y-%m-%d:%H:%M:%S")


def isInCron(line):
    '''This method checks if crontab contains one line 
    '''
    code, output, error = shellutils.run(["crontab", "-l"])
     
    if len(error) != 0 or shellutils.grep(line, output) == None:
        return False
        
    else:
        return True


def setCron(line):
    '''This method add a line to crontab
    '''
    TEMP_FILE="/tmp/crontab.edit.tmp"
    
    code, output, error = shellutils.run(["crontab", "-l"])
    if len(error) == 0:
        file_out = open(TEMP_FILE, 'w')
        file_out.write(output + "\n" + line + "\n")
        file_out.close()
        code, output, error = shellutils.run(["crontab", TEMP_FILE])
        if len(error) == 0:
            return 0
        else:
            return None
    else:
        return None


def mail(gmailUser, gmailPwd, to, subject, text, attach=None):
    '''This procedure sends an email to a list of recipients
    '''
    msg = MIMEMultipart()

    msg['From'] = gmailUser
    msg['To'] = to
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    if attach != None:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(open(attach, 'rb').read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition',
           'attachment; filename="%s"' % os.path.basename(attach))
        msg.attach(part)

    mailServer = smtplib.SMTP("smtp.gmail.com", 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(gmailUser, gmailPwd)
    mailServer.sendmail(to, to, msg.as_string())
    # Should be mailServer.quit(), but that crashes...
    mailServer.close()


def notifyPushover(appId, userId, message, title="Python app"):
    '''This function is for sending push notifications
    '''
    import httplib, urllib
    conn = httplib.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
      urllib.urlencode({
        "token": appId,
        "user": userId,
        "message": message,
		"title": title,
      }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()
