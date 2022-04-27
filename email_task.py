import os
from dotenv import load_dotenv
from imap_tools import MailBox
from website import email_bot
import time


def main():
    time.sleep(60)
    try:
      load_dotenv()
      server = os.getenv('MAIL_SERVER_IMAP')
      username = os.getenv('MAIL_USERNAME')
      password = os.getenv('MAIL_PASSWORD')
      with MailBox(server).login(username, password) as mailbox:
        email_bot.main(mailbox)
    except Exception as e:
      print(f"Error connecting to mailbox: {e}")


if __name__ == "__main__":
    main()