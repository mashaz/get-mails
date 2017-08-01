# -*- coding: utf-8 -*-

import re
import datetime
import email
import imaplib
import mailbox
from pymongo import MongoClient

ALLOWED_SENDER = 'sender_you_want_to_recieve'
EMAIL_ACCOUNT = 'your_email_account'
with open('you_password_address', 'r') as p:
    PASSWORD = p.read().split()[0]

def decode_mime_words(s):
    return u''.join(
        word.decode(encoding or 'utf8') if isinstance(word, bytes) else word
        for word, encoding in email.header.decode_header(s))

client = MongoClient('127.0.0.1',27017)
mail_content = client['mails']['content']

mail = imaplib.IMAP4_SSL("imap.example.com")
mail.login(EMAIL_ACCOUNT, PASSWORD)
mail.list()
mail.select('inbox')
result, data = mail.uid('search', None, "ALL") # (ALL/UNSEEN)
i = len(data[0].split())
new_mail = 0
for x in range(i):
    latest_email_uid = data[0].split()[x]
    result, email_data = mail.uid('fetch', latest_email_uid, '(RFC822)')
    raw_email = email_data[0][1]
    raw_email_string = raw_email.decode('utf-8')

    email_message = email.message_from_string(raw_email_string.encode('utf-8'))
    # Header Details
    date_tuple = email.utils.parsedate_tz(email_message['Date'])
    now_time = datetime.datetime.now()
    if date_tuple:
        local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        local_message_date = "%s" %(str(local_date.strftime("%a, %d %b %Y %H:%M:%S")))
    else:
        local_message_date = re.findall(r'\r\n[\s\S]{30,50}\+0800', raw_email_string)[0].strip('\n').strip()
    email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
    email_to = str(email.header.make_header(email.header.decode_header(email_message['To'])))
    subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))#.lstrip('').rstrip('?=').replace('=2','.')
    # Body details
    body = ''
    subject = decode_mime_words(subject)
    email_from = decode_mime_words(email_from)
    email_to = decode_mime_words(email_to)
    for part in email_message.walk():
        if part.get_content_type() == "text/plain":
            body = body + part.get_payload(decode=True)
        else:
            continue
    if not ALLOWED_SENDER in email_from:
        print('Illegal sender.{}'.format(x+1))
        continue
    mail_exists = mail_content.find_one({'date':local_message_date,'body':body})
    if mail_exists != None :
        print('old mail {}'.format(x+1))
        continue
    print(local_message_date)
    mail_content.insert_one({
        'sender':email_from,
        'subject':subject,
        'date':local_message_date,
        'body':body,
        'status':'unseen'
        })
    new_mail += 1
print('Recieved {} new mails this time.'.format(new_mail))
