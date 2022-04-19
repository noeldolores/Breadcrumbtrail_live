#!/usr/bin/env python3

from imap_tools import MailBox, AND
import os
from dotenv import load_dotenv



def connect_to_mail():
  load_dotenv()
  server = os.getenv('MAIL_SERVER_IMAP')
  username = os.getenv('MAIL_USERNAME')
  password = os.getenv('MAIL_PASSWORD')
  mailbox = MailBox(server).login(username, password)
  return mailbox


def get_unread_message_info(mailbox):
  unread_mail = mailbox.fetch(AND(seen=False))
  mail_list = []
  for mail in unread_mail:
    mail_list.append(
      {
        "ID": mail.uid,
        "sender": mail.from_,
        "date": mail.date,
        "message_body": mail.text.replace('\r\n', ' ')
      }
    )
  return mail_list


def delete_processed_email(mailbox, email_id):
  mailbox.delete(email_id)