#!/usr/bin/env python3

# import base64
# import os
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from email.mime.base import MIMEBase
# from email import encoders
# import mimetypes


def Get_Unread_Messages(service, userId):
  """Retrieves all unread messages, returns list of message ids.
        Args:
            service: Authorized Gmail API service instance.
            userId: User's email address. The special value "me".
                can be used to indicate the authenticated user.
    """
  message_list = []
  message_ids = service.users().messages().list(userId=userId, labelIds='INBOX', alt="json", q='is:unread').execute()
  
  if message_ids['resultSizeEstimate'] > 0:
    for message in message_ids['messages']:
      message_list.append(message['id'])

  return message_list


def Get_Message_Info(service, userId, message_id):
  """Retrieves received message info, returns tuple.
        Args:
            service: Authorized Gmail API service instance.
            userId: User's email address. The special value "me".
                can be used to indicate the authenticated user.
            message_id: Identifies specific message to interact with.
    """
  message_info = service.users().messages().get(userId=userId, id=message_id).execute()

  #print(message_info)
  ID = message_info['id']
  message_body = message_info['snippet']
  header_info = message_info['payload']['headers']
  for header in header_info:
    if header['name']=='Message-ID':
      message_id=header['value']
    if header['name']=='From':
      sender=header['value']
    if header['name']=='Date':
      date=header['value']

  info = {"ID": ID,
          "sender": sender, 
          "date": date, 
          "message_body": message_body}
  return info


def Delete_Message(service, userId, message_id):
  """Permanently delete message.
        Args:
            service: Authorized Gmail API service instance.
            userId: User's email address. The special value "me".
                can be used to indicate the authenticated user.
            message_id: Identifies specific message to interact with.
    """
  service.users().messages().delete(userId=userId, id=message_id).execute()
  

# def Get_Attachments(service, userId, msg_id, store_dir):
#     """Get and store attachment from Message with given id.
#         Args:
#             service: Authorized Gmail API service instance.
#             userId: User's email address. The special value "me"
#                 can be used to indicate the authenticated user.
#             msg_id: ID of Message containing attachment.
#             store_dir: The directory used to store attachments.
#     """
#     try:
#         message = service.users().messages().get(userId=userId, id=msg_id).execute()
#         parts = [message['payload']]
#         while parts:
#             part = parts.pop()
#             if part.get('parts'):
#                 parts.extend(part['parts'])
#             if part.get('filename'):
#                 if 'data' in part['body']:
#                     file_data = base64.urlsafe_b64decode(part['body']['data'].encode('UTF-8'))
#                     #self.stdout.write('FileData for %s, %s found! size: %s' % (message['id'], part['filename'], part['size']))
#                 elif 'attachmentId' in part['body']:
#                     attachment = service.users().messages().attachments().get(
#                         userId=userId, messageId=message['id'], id=part['body']['attachmentId']
#                     ).execute()
#                     file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
#                     #self.stdout.write('FileData for %s, %s found! size: %s' % (message['id'], part['filename'], attachment['size']))
#                 else:
#                     file_data = None
#                 if file_data:
#                     #do some staff, e.g.
#                     path = ''.join([store_dir, part['filename']])
#                     with open(path, 'wb') as f:
#                         f.write(file_data)
#     except errors.HttpError as error:
#         print('An error occurred: %s' % error)

# def Reply_With_Attchment(service, userId, receiver, subject, message, attachments, threadId, message_id):
#   """Reply to message with the new pdf attached.
#         Args:
#             service: Authorized Gmail API service instance.
#             userId: User's email address. The special value "me".
#                 can be used to indicate the authenticated user.
#             receiver: Email address of who to send to.
#             subject: Email subject.
#             message: Email message, plain text
#             attachments: 'new_pdf.pdf' Name can be changed in pdf.combine_pdfs
#             threadId: Used to match reply with message thread
#             message_id: Identifies specific message to interact with.
#     """
#   # Create email message
#   emailMsg = message
#   mimeMessage = MIMEMultipart()
#   mimeMessage['to'] = receiver
#   mimeMessage['subject'] = subject
#   mimeMessage['threadId'] = threadId
#   mimeMessage['In-Reply-To'] = message_id
#   mimeMessage['References'] = message_id
#   mimeMessage.attach(MIMEText(emailMsg, 'plain'))
  
#   # Attach files
#   if attachments != None:
#     attachment = attachments
#     content_type = mimetypes.guess_type(attachment)
#     main_type, sub_type = content_type[0].split('/', 1)
#     file_name = os.path.basename(attachment)

#     f = open(attachment, 'rb')

#     myFile = MIMEBase(main_type, sub_type)
#     myFile.set_payload(f.read())
#     myFile.add_header('Content-Disposition', 'attachment', filename=file_name)
#     encoders.encode_base64(myFile)

#     f.close()

#     mimeMessage.attach(myFile)
  
#   raw_string = {'raw':base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()}
#   raw_string['threadId']=threadId
  
#   message = service.users().messages().send(userId=userId, body=raw_string).execute()