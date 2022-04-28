#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import os
from dotenv import load_dotenv


def request_weather(latitude, longitude):
  load_dotenv()
  weather_api = os.getenv('WEATHER_API')
  weather = {
    "temperature": None,
    "humidity": None,
    "description": None
  }
  
  url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={weather_api}"
  response = requests.request(method='GET', url=url)
  if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")
    data_json = json.loads(str(soup))
    try:
      weather['temperature'] = int(data_json['main']['temp'])
      weather['humidity'] = int(data_json['main']['humidity'])
      weather['description'] = data_json['weather'][0]['description'].title()
    except Exception as e:
      print(f"request_weather. Coords: {latitude}, {longitude}. Exception: {e}")
  return weather


def request_elevation(latitude, longitude):
  load_dotenv()
  mapquest_api = os.getenv('MAPQUEST_API')
  elevation = None 
  
  url = f"http://open.mapquestapi.com/elevation/v1/profile?key={mapquest_api}&shapeFormat=raw&latLngCollection={latitude},{longitude}"
  response = requests.request(method='GET', url=url)
  if response.status_code == 200:
    soup = BeautifulSoup(str(response.content.decode("utf-8")), "html.parser")
    data_json = json.loads(str(soup))
    try:
      elevation = int(data_json['elevationProfile'][0]['height'])
    except Exception as e:
      print(f"request_elevation. Coords: {latitude}, {longitude}. Exception: {e}")
  return elevation


def request_air_quality(latitude, longitude):
  load_dotenv()
  weather_api = os.getenv('WEATHER_API')
  aqi_descriptions = {
    "1": "Good",
    "2": "Fair",
    "3": "Moderate",
    "4": "Poor",
    "5": "Very Poor"
  }
  air_quality = None
  
  url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={latitude}&lon={longitude}&appid={weather_api}"
  response = requests.request(method='GET', url=url)
  if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")
    aqi_json = json.loads(str(soup))
    try:
      aqi_num = (aqi_json['list'][0]['main']['aqi'])
      aqi_desc = aqi_descriptions[str(aqi_num)]
      air_quality = f"{aqi_num} - {aqi_desc}"
    except Exception as e:
      print(f"request_air_quality. Coords: {latitude}, {longitude}. Exception: {e}")
  return air_quality