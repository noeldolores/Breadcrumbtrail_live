#!/usr/bin/env python3
import re
from . import db, api_functions
from .models import User, Marker, Trail
from imap_tools import AND
import decimal
import pytz


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
  try:
    mailbox.delete(email_id)
    return email_id
  except:
    return None


def match_user_private_key(string_to_check):
  priv_key_search = re.search(r"([a-z]{2}#[0-9]{4})", string_to_check.lower())
  if priv_key_search:
    priv_key_match = priv_key_search.group(1).upper()
    user_match = User.query.filter_by(private_key=priv_key_match).first()
    if user_match:
      return user_match
  print("match_user_private_key: user not found")
  return None


def match_lattitude(string_to_check):
  direction = ""
  lat_parse = re.search(r"^[\s\S]*?(\-?\d{2}\.\d{4})[^a-zA-Z]*([a-zA-z])?", string_to_check)
  if lat_parse:
    if lat_parse.group(1):
      latitude = lat_parse.group(1)
      if lat_parse.group(2):
        if "s" in lat_parse.group(2).lower() and not "-" in latitude:
          direction = "-"
    return direction + latitude
  return None


def match_longitude(string_to_check):
  direction = ""
  lon_parse = re.search(r"^[\s\S]*?(\-?\d{3}\.\d{4})[^a-zA-Z]*([a-zA-z])?", string_to_check)
  if lon_parse:
    if lon_parse.group(1):
      longitude = lon_parse.group(1)
      if lon_parse.group(2):
        if "w" in lon_parse.group(2).lower() and not "-" in longitude:
          direction = "-"
    return direction + longitude
  return None

  
def match_note(string_to_check):
  note_parse = re.search(r"message:\s?[\"|\“|\”|\'|\‘|\’|\`]([\s\S]*)[\"|\“|\”|\'|\‘|\’|\`]", string_to_check)
  if note_parse:
    note = note_parse.group(1)
    if len(note) > 300:
      return note[:300]
    else:
      return note
  return None


def main(mailbox):
  message_info_list = get_unread_message_info(mailbox)

  if len(message_info_list) > 0:
    for message in message_info_list:
      ID = message['ID']
      date = message["date"].astimezone(pytz.utc)
      message_body = message["message_body"]

      user_match = match_user_private_key(message_body)
      if user_match:
        user_trail = Trail.query.join(User, Trail.user_id==user_match.id).filter(Trail.id==user_match.current_trail).first()

        if user_trail.markers:
          marker_num = len(user_trail.markers) + 1
        else:
          marker_num = 1

        latitude = match_lattitude(message_body)
        longitude =  match_longitude(message_body)
        note = match_note(message_body)
        elevation = api_functions.request_elevation(latitude, longitude)
        weather = api_functions.request_weather(latitude, longitude)
        air_quality = api_functions.request_air_quality(latitude, longitude)
        
        
        marker = Marker(
          datetime = date,
          trail = user_trail,
          marker_num = marker_num,
          lat = decimal.Decimal(latitude),
          lon = decimal.Decimal(longitude),
          elevation = elevation,
          temp = weather['temperature'],
          humidity = weather['humidity'],
          weather = weather['description'],
          airquality = air_quality,
          note = note)

        db.session.add(marker)
        db.session.commit()

        # Delete Message
        deleted = delete_processed_email(mailbox, ID)
        if deleted:
          print(f"{deleted} was successfully deleted.")
        else:
          print(f"{deleted} was not deleted.")

      else:
        print("Unable to find matching user")
        
  else:
    print("No messages to process")


if __name__ == "__main__":
  main()