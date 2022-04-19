#!/usr/bin/env python3

import re
from . import db, emailfunctions
from .models import User, Marker, Trail
from config import Config
import requests
from bs4 import BeautifulSoup
import json
import decimal
import os
from dotenv import load_dotenv



def main():
  mailbox = emailfunctions.connect_to_mail()
  message_info_list = emailfunctions.get_unread_message_info(mailbox)

  if len(message_info_list) > 0:
    for message in message_info_list:
      ID = message['ID']
      date= message["date"]
      message_body = message["message_body"]

      # Match sender to user table
      priv_key_match = None
      priv_key_search = re.search(r"([a-z]{2}#[0-9]{4})", message_body.lower())
      if priv_key_search:
        priv_key_match = priv_key_search.group(1).upper()
      else:
        print("No match found")

      if priv_key_match is not None:
        # User Check
        user_match = User.query.filter_by(private_key=priv_key_match).first()
        if user_match:
          # User Current Trail Check
          user_trail = Trail.query.join(User, Trail.user_id==user_match.id).filter(Trail.id==user_match.current_trail).first()

          # Marker number
          marker_num = len(user_trail.markers) + 1

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
        else:
          user_trail = None
          coordinates = {
            "latitude": -1,
            "longitude": -1
          }


        # Note Parse
        note = ""
        note_parse = re.search(r"message:[\"|\']([\s\S]*)[\"|\']", message_body)
        if note_parse:
          full_note = note_parse.group(1)
          if len(full_note) > 300:
            note = full_note[:300]
          else:
            note = full_note


        # Search Weather API
        load_dotenv()
        weather_api = os.getenv('WEATHER_API')
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={coordinates['latitude']}&lon={coordinates['longitude']}&appid={weather_api}"
        response = requests.request(method='GET', url=url)
        if response.status_code == 200:
          soup = BeautifulSoup(response.content, "html.parser")
          data_json = json.loads(str(soup))
        else:
          print(f"Error with Weather API. Coords: {coordinates['latitude']}, {coordinates['longitude']}")
          data_json = {
            'main': {
              'temp': -1,
              'humidity': -1
            },
            'weather': [
              {
                'description': -1
              }
            ]
          }
        # Grab Elevation from Open-Elevation API
        mapquest_api = os.getenv('MAPQUEST_API')
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
          marker_num = marker_num,
          datetime= date,
          lat= decimal.Decimal(coordinates['latitude']),
          lon= decimal.Decimal(coordinates['longitude']),
          elevation= int(elevation_json['elevationProfile'][0]['height']),
          temp= int(data_json['main']['temp']),
          humidity= int(data_json['main']['humidity']),
          airquality= f"{aqi_num} - {aqi_desc}",
          weather= data_json['weather'][0]['description'].title(),
          note = note,
          trail = user_trail
          )

        db.session.add(marker)
        db.session.commit()

        # Delete Message
        emailfunctions.delete_processed_email(mailbox, ID)

      else:
        print("Unable to parse sender info")

  else:
    print("No messages to process")

if __name__ == "__main__":
  main()