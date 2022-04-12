#!/usr/bin/env python3

from datetime import datetime
import re
from . import db, gmailservice, emailfunctions
from .models import User, Marker, Trail
from dateutil import parser



def main():
  _path = "/home/noel/python_projects/map_app/"
  
  # Connects to google gmail service
  CLIENT_SECRET_FILE = _path + "client_secret.json"
  API_NAME = 'gmail'
  API_VERSION = 'v1'
  SCOPES = ['https://mail.google.com/']
  service = gmailservice.Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

  
  #  Checks for and retrieves unread messages with attachments
  message_info_list = emailfunctions.Get_Unread_Messages(service, 'me')
  if len(message_info_list) > 0:
    for message in message_info_list:
      info = emailfunctions.Get_Message_Info(service, 'me', message)

      ID = info['ID']
      sender= info['sender']
      date= info["date"]
      #message_id = info["message_id"]
      message_body = info["message_body"]
      
      # Match sender to user table
      checkincontact = None
      # Email Parse
      if "<" in sender:
        test_reg = re.search(r"<(\S*)>", sender)
        if test_reg:
          checkincontact = test_reg.group(1)
        else:
          print("No Email Match")
      # Phone Number Parse
      else:
        test_reg = re.search(r"(\d{10})@", sender)
        if test_reg:
          checkincontact = test_reg.group(1)
        else:
          print("No Phone Number Match")
          
      
      if checkincontact:
        # User Check
        user_match = User.query.filter_by(checkincontact=checkincontact).first()
        if user_match:
          # User Current Trail Check
          user_trail = Trail.query.join(User, Trail.user_id==user_match.id).filter(Trail.id==user_match.current_trail).first()
          if user_trail:
            pass
          else:
            print("No Trail Match")
            
          # Coordinates Parse
          coordinates = {
            "latitude": None,
            "longitude": None
          }
          # Latitude
          latitude = None
          lat_parse = re.search(r"^[\s\S]*?(\-?\d{2}\.\d{4})[^a-zA-Z]*([a-zA-z])?", message_body)
          if lat_parse:
            if lat_parse.group(1):
              latitude = lat_parse.group(1)
              if lat_parse.group(2):
                direction = ""
                if "s" in direction:
                  latitude = "-" + lat_parse.group(1)
          coordinates['latitude'] = latitude

          # Longitude
          longitude = None
          lon_parse = re.search(r"^[\s\S]*?(\-?\d{3}\.\d{4})[^a-zA-Z]*([a-zA-z])?", message_body)
          if lon_parse:
            if lon_parse.group(1):
              longitude = lon_parse.group(1)
              if lon_parse.group(2):
                direction = ""
                if "w" in direction:
                  longitude = "-" + lon_parse.group(1)
          coordinates['longitude'] = longitude

          #print(coordinates)
      else:
        print("Unable to parse sender info")
        
        
      # Convert Email date/time to datetime
      datetime_object = parser.parse(date)
      #print(datetime_object)
      
      
      # Search Weather API
      
      
      
      
      # Add Data to Current Route
      # marker = Marker{
      #   "datetime": str(datetime_object),
      #   "lat": coordinates['latitude'],
      #   "lon": coordinates['longitude'],
      #   "elevation": None,
      #   "tempF": None,
      #   "humidity": None,
      #   "airquality": None,
      #   "weather": None,
      #   "trail_id": user_match.current_trail
      # }
      # db.session.add(marker)
      # db.session.commit()
      
      # Delete Message
      #emailfunctions.Delete_Message(service, userID, ID)
  else:
    print("No messages to process")

if __name__ == "__main__":
  main()