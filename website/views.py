from flask import Blueprint, request, flash, session, render_template, redirect, url_for, escape
from flask_login import current_user, login_required, login_user
from datetime import datetime
import json
import sys
from sqlalchemy.orm import query
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, Marker, Trail
import time
import pytz
from sqlalchemy import desc, select
import re
from . import email_bot
from config import Config


views = Blueprint('views', __name__)


def init_user_settings():
  if not current_user.is_authenticated:
    user_settings = {
      'timezone':'UTC',
      'unitmeasure':'metric'
    }
  elif current_user.settings is not None:
    user_settings = json.loads(current_user.settings)
    current_user.settings = json.dumps(user_settings)
    db.session.commit()
  return user_settings


def user_search():
  if 'search' in request.form:
    user_mapId_query = str(request.form['search']).lower()
    user_match = User.query.filter_by(mapId=user_mapId_query).first()

    return user_match
  else:
    return None


def trail_checkIn():
  if 'save_location' in request.form:
    
    return "Location Check-In"
  else:
    return "No Check-In Initiated"


def create_trail():
  if 'create_trail' in request.form:
    trail_name = str(request.form['new_trail_name'])
    
    user = User.query.filter_by(email=current_user.email).first()
    current_trails_sql = Trail.query.join(User, Trail.user_id==current_user.id).all()
    current_trail_names = []
    for trail in current_trails_sql:
      current_trail_names.append(trail.name)
    
    if trail_name not in current_trail_names:
      utc_now = pytz.utc.localize(datetime.utcnow())
      trail = Trail(
        name=trail_name,
        datetime=utc_now,
        user=user
      )
      db.session.add(trail)
      db.session.commit()
      return trail
    else:
      flash('Trail Name Already In Use', category='error')
  return None
  

def select_trail():
  if 'select_trail' in request.form:
    selected_trail = str(request.form['select_trail'])
    return selected_trail
  return None


def list_from_marker_class(markers):
  marker_list = []
  if len(markers) > 0:
    for marker in markers:
      marker_list.append(
        {
          "date":marker.datetime.strftime("%m/%d/%Y"),
          "time":marker.datetime.strftime("%-I:%M%p"),
          "lat":float("{0:.4f}".format(marker.lat)),
          "lon":float("{0:.4f}".format(marker.lon)),
          "elevation":marker.elevation,
          "temp":marker.temp,
          "humidity":marker.humidity,
          "airquality":marker.airquality,
          "weather":marker.weather,
          'popup': marker.datetime.strftime("%m/%d/%Y %-I:%M%p")
        }
      )
    
    return marker_list[::-1]
  return None


def load_active_trail(trail):
  markers = list_from_marker_class(trail.markers)
  active_trail = {
    "id": trail.id,
    "name":trail.name,
    "date":"",
    "time":"",
    "markers": markers
  }
  
  if markers:
    active_trail['date'] = markers[0]['date']
    active_trail['time'] = markers[0]['time']
  
  return active_trail


@views.route('/')
def redirect_to_home():
  if current_user.is_authenticated:
    return redirect(url_for('views.user_trail',user_mapId=current_user.mapId))
  return redirect(url_for('views.home'))


@views.route('/home', methods=['GET', 'POST'])
def home():
  if request.method == 'POST':
    user_match = user_search()
    if user_match:
      return redirect(url_for('views.user_trail',user_mapId=user_match.mapId))
    
  user_trails = None

  return render_template('user_map.html', user=current_user, user_trails=user_trails)


@views.route('/<user_mapId>', methods=['GET', 'POST'])
def user_trail(user_mapId):
  user_match = User.query.filter_by(mapId=user_mapId).first()
  
  if user_match:
    if current_user.is_authenticated:
      user_trails = Trail.query.join(User, Trail.user_id==current_user.id).all()
      
      if current_user.current_trail:
        active_trail_match = Trail.query.join(User, Trail.user_id==current_user.id).filter(Trail.id==current_user.current_trail).first()
        active_trail = load_active_trail(active_trail_match)
        
      elif len(user_trails) == 1:
        active_trail_match = user_trails[0]
        active_trail = load_active_trail(active_trail_match)
      else:
        active_trail = None
      
      if request.method == 'POST':
        user_match = user_search()
        if user_match:
          return redirect(url_for('views.user_trail',user_mapId=user_match.mapId))
        
        trail_checkIn()
        
        createTrail_request = create_trail()
        if createTrail_request:
          active_trail_match = createTrail_request
          current_user.current_trail = active_trail_match.id
          active_trail = load_active_trail(active_trail_match)
          db.session.commit()
          return redirect(url_for('views.user_trail',user_mapId=current_user.mapId))
          
        selected_trail = select_trail()
        if selected_trail:
          current_user.current_trail = selected_trail
          db.session.commit()
          active_trail_match = Trail.query.join(User, Trail.user_id==current_user.id).filter(Trail.id==selected_trail).first()
          active_trail = load_active_trail(active_trail_match)
          
        if "test_button" in request.form:
          email_bot.main()
          return redirect(url_for('views.user_trail',user_mapId=current_user.mapId)) 
          
      settings = json.loads(current_user.settings)
    else:
      user_trails = []
      sql_trails = user_match.trails
      for trail in sql_trails:
        user_trails.append(
          {
            "id": trail.id,
            "name": trail.name,
            "date":trail.datetime.strftime("%b %d, %Y"),
            "time":trail.datetime.strftime("%-I:%M%p"),
            "markers": list_from_marker_class(trail.markers)
          }
        )
        
      active_trail_match = Trail.query.join(User, Trail.user_id==user_match.id).filter(Trail.id==user_match.current_trail).first() 
      active_trail = load_active_trail(active_trail_match)
      
      if request.method == 'POST':
        user_mapId_search = user_search()
        if user_mapId_search:
          return redirect(url_for('views.user_trail',user_mapId=user_mapId_search.mapId))
        
        selected_trail = select_trail()
        if selected_trail:
          active_trail_match = Trail.query.join(User, Trail.user_id==user_match.id).filter(Trail.id==selected_trail).first()
          active_trail = load_active_trail(active_trail_match)
      settings = {'unitmeasure':'Metric'}
    
    mapbox_api = Config.MAPBOX_API
    return render_template('user_map.html', user=current_user, user_trails=user_trails, active_trail=active_trail, unitmeasure=settings['unitmeasure'], mapbox_api=mapbox_api)
  else:
    return redirect(url_for('views.home'))


@views.route('/usersettings', methods=['GET', 'POST'])
@login_required
def usersettings():
  if request.method == 'POST':
    search_request = user_search()
    if search_request is None:
      print("user not found")
      
  if current_user.is_authenticated:
    user_settings = init_user_settings()

    if request.method == 'POST':
      changes = []
      timezone = str((request.form.get('timezone')))
      unitmeasure = str((request.form.get('unitmeasure')))

      if current_user.role != "guest":
        firstName = str((request.form.get('firstName')))
        lastName = str((request.form.get('lastName')))
        email = str((request.form.get('email')))
        password1 = str((request.form.get('password1')))
        password2 = str((request.form.get('password2')))

        if len(firstName) == 0:
          pass
        elif len(firstName) < 2:
          flash('Name must be at least 2 characters', category='error')
        elif current_user.firstName == firstName:
          flash(f'Name is already {firstName}', category='error')
        else:
          current_user.firstName = firstName
          changes.append("First Name")
          
        if len(lastName) == 0:
          pass
        elif len(lastName) < 2:
          flash('Name must be at least 2 characters', category='error')
        elif current_user.lastName == lastName:
          flash(f'Name is already {lastName}', category='error')
        else:
          current_user.lastName = lastName
          changes.append("Last Name")
          
        if len(email) == 0:
          pass
        elif len(email) < 4:
          flash('Email must be greater than 4 characters', category='error')
        else:
          email_exists = User.query.filter_by(email=email).first()
          if email_exists:
            flash('Email already exists.', category='error')
          else:
            current_user.email = email
            changes.append("Email")

        if len(password1) == 0:
          pass
        elif password1 != password2:
          flash('Passwords do not match', category='error')
        elif len(password1) < 7:
          flash('Password must be at least 7 characters', category='error')
        elif check_password_hash(current_user.password, password1):
          flash('New password must be different than current password.', category='error')
        else:
          current_user.password=generate_password_hash(password1, method='sha256')
          changes.append("Password")

      if timezone != "None":
        if timezone != user_settings['timezone']:
          user_settings['timezone'] = timezone
          changes.append('Timezone')
      elif user_settings['timezone'] == "None":
        user_settings['timezone'] = "UTC"
        changes.append('Timezone')
        
      if unitmeasure != "None":
        if unitmeasure != user_settings['unitmeasure']:
          user_settings['unitmeasure'] = unitmeasure
          changes.append('Units')
      elif user_settings['unitmeasure'] == "None":
          user_settings['unitmeasure'] = "Metric"
          changes.append('Units')

      if current_user.role != "guest":
        if 'delete' in request.form:
          return redirect(url_for('views.deleteaccount'))

      if len(changes) > 0:
        current_user.settings = json.dumps(user_settings)
        db.session.commit()
        user_settings = json.loads(current_user.settings)
        flash(f'Settings Saved: {", ".join(changes)}', category='success')

    return render_template('usersettings.html', user=current_user, lastName=current_user.lastName, firstName=current_user.firstName, email=current_user.email, settings=user_settings, priv_key=current_user.private_key)