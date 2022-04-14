#!/usr/bin/env python3

from datetime import datetime
import re
from . import db, gmailservice, emailfunctions
from .models import User, Marker, Trail
from dateutil import parser
from dotenv import dotenv_values
from config import Config
import requests
from bs4 import BeautifulSoup
import json
import decimal



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
          
      if checkincontact is not None:
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
          direction = ""
          lat_parse = re.search(r"^[\s\S]*?(\-?\d{2}\.\d{4})[^a-zA-Z]*([a-zA-z])?", message_body)
          if lat_parse:
            if lat_parse.group(1):
              latitude = lat_parse.group(1)
              if lat_parse.group(2):
                if "s" in lat_parse.group(2).lower():
                  direction = "-"
          coordinates['latitude'] = direction + latitude
          # Longitude
          longitude = None
          direction = ""
          lon_parse = re.search(r"^[\s\S]*?(\-?\d{3}\.\d{4})[^a-zA-Z]*([a-zA-z])?", message_body)
          if lon_parse:
            if lon_parse.group(1):
              longitude = lon_parse.group(1)
              if lon_parse.group(2):
                if "w" in lon_parse.group(2).lower():
                  direction = "-"
          coordinates['longitude'] = direction + longitude
      
      
        # Convert Email date/time to datetime
        datetime_object = parser.parse(date)
        
        
        # Search Weather API
        weather_api = Config.WEATHER_API
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={coordinates['latitude']}&lon={coordinates['longitude']}&appid={weather_api}"
        response = requests.request(method='GET', url=url)
        if response.status_code == 200:
          soup = BeautifulSoup(response.content, "html.parser")
          data_json = json.loads(str(soup))
        else:
          print(f"Error with Weather API. Coords: {coordinates['latitude']}, {coordinates['longitude']}")
          data_json['main']['temp'] = -1
          data_json['main']['humidity'] = -1
          data_json['weather'][0]['description'] = -1
          
        
        # Grab Elevation from Open-Elevation API
        mapquest_api = Config.MAPQUEST_API
        url = f"http://open.mapquestapi.com/elevation/v1/profile?key={mapquest_api}&shapeFormat=raw&latLngCollection={coordinates['latitude']},{coordinates['longitude']}"
        response = requests.request(method='GET', url=url)
        if response.status_code == 200:
          soup = BeautifulSoup(str(response.content.decode("utf-8")), "html.parser")
          elevation_json = json.loads(str(soup))
        else:
          print(f"Error with Elevation API. Coords: {coordinates['latitude']}, {coordinates['longitude']}")
          elevation_json['elevationProfile'][0]['height'] = -1
        
        
        # Grab Air Quality 1(good) - 5(very poor)
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={coordinates['latitude']}&lon={coordinates['longitude']}&appid={weather_api}"
        response = requests.request(method='GET', url=url)
        if response.status_code == 200:
          soup = BeautifulSoup(response.content, "html.parser")
          aqi_json = json.loads(str(soup))
          aqi_num = (aqi_json['list'][0]['main']['aqi'])
        else:
          print(f"Error with Air Quality API. Coords: {coordinates['latitude']}, {coordinates['longitude']}")
          aqi_num = -1
          
        aqi_descriptions = {
          "-1": "Error",
          "1": "Good",
          "2": "Fair",
          "3": "Moderate",
          "4": "Poor",
          "5": "Very Poor"
        }
        try:
          aqi_desc = aqi_descriptions[str(aqi_num)]
        except:
          aqi_desc = ""
        
        
        # Add Data to Current Route
        marker = Marker(
          datetime= datetime_object,
          lat= decimal.Decimal(coordinates['latitude']),
          lon= decimal.Decimal(coordinates['longitude']),
          elevation= int(elevation_json['elevationProfile'][0]['height']),
          temp= int(data_json['main']['temp']),
          humidity= int(data_json['main']['humidity']),
          airquality= f"{aqi_num} - {aqi_desc}",
          weather= data_json['weather'][0]['description'],
          trail = user_trail
          )

        db.session.add(marker)
        db.session.commit()
        
        # Delete Message
        #emailfunctions.Delete_Message(service, userID, ID)
        
      else:
        print("Unable to parse sender info")
  else:
    print("No messages to process")

if __name__ == "__main__":
  main()