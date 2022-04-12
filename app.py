#!/usr/bin/env python3
from website import create_app


app = create_app()


if __name__ == '__main__':
  app.run(debug=True)
  
""" Functions and Flow
* User who wants to create a custom map must create an account
* User attaches a phone number or email from which they can update their map remotely
1) Website has an email address to which users send their coordinates
2) Bot scrapes email every interval, checking for new messages.
3) If a new message is found, the sender phone/email is matched to a user account, and their map is updated with the sent coords
* User can also update their coords on the website directly  
* Users are assigned a name id that can be shared for others to view their map
- Likely First Name + Last Name first letter + 4 digits (similar to discord), eg AustinM1234
2) Find a friend's map by using a direct url: www.breadcrumbtrail.app/austinm1234

def emailchecker()
* Login and check for new messages every few minutes or so (depends on usage pull)
* Match sender email/phone to a user in the database.
* If match is found, update_user_table()

def update_user_table()
* Fed from emailchecker: latitude, longitude, time, date
* Use openweathermap.org API to grab weather info (temperature, humidity, aqi, condition, elevation) at the coords on the time and date
* Add entries to table 

def show_user_map(username)
* User goes to www.breadcrumbtrail.app/austinm1234
* username = austinm1234
* Trigger search_db_username(austinm1234). If match, continue
* Use the user_records list to add markers to a map, and populate info for each marker
* Display map

def search_db_username:
* Seach db for user table matching the queried username. If match, continue
* Add all records to a list of dictionaries:
user_records = [
    {
        "date": str,
        "time": str,
        "lat": int,
        "lon": int,
        "elevation": int,
        "tempF": int,
        "tempC": int,
        "humidity": int,
        "AQI": int,
        "condition": str
    },
    {
        ...
    }
]
* Add items to the top of the list during table record iteration, so that it is in chronological order
* Return list
"""