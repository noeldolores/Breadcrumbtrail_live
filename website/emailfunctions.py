#!/usr/bin/env python3

from config import Config
from imap_tools import MailBox



def connect_to_mail():
  server = Config.MAIL_SERVER
  username = Config.MAIL_USERNAME
  password = Config.MAIL_PASSWORD
  mailbox = MailBox(server).login(username, password)
  return mailbox
  
  
def get_unread_message_info(mailbox):
  unread_mail = mailbox.fetch(mark_seen=False)
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