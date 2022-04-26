from flask import Blueprint, request, flash, render_template, redirect, url_for, escape
from flask_login import current_user, login_required
from datetime import datetime
import json
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, Marker, Trail
import pytz
from . import email_bot
import os
from dotenv import load_dotenv

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


def change_user_settings_request(user_settings):
  changes = []
  timezone = str(escape(request.form.get('timezone')))
  unitmeasure = str(escape(request.form.get('unitmeasure')))
  firstName = str(escape(request.form.get('firstName')))
  lastName = str(escape(request.form.get('lastName')))
  email = str(escape(request.form.get('email')))
  password1 = str(escape(request.form.get('password1')))
  password2 = str(escape(request.form.get('password2')))

  if len(firstName) == 0:
    pass
  elif len(firstName) < 2:
    flash(f'First Name must be at least 2 letters: "{firstName}"', category='error')
    return None
  elif current_user.firstName == firstName:
    flash(f'First Name is already "{firstName}"', category='error')
    return None
  else:
    current_user.firstName = firstName
    changes.append("First Name")

  if len(lastName) == 0:
    pass
  elif len(lastName) < 1:
    flash(f'Last Name must be at least 1 letter: "{lastName}"', category='error')
    return None
  elif current_user.lastName == lastName:
    flash(f'Last Name is already {lastName}', category='error')
    return None
  else:
    current_user.lastName = lastName
    changes.append("Last Name")

  if len(email) == 0:
    pass
  elif len(email) < 4:
    flash(f'Email must be greater than 4 characters: "{email}"', category='error')
    return None
  else:
    email_exists = User.query.filter_by(email=email).first()
    if email_exists:
      flash('Email already exists.', category='error')
      return None
    else:
      current_user.email = email
      changes.append("Email")

  if len(password1) == 0:
    pass
  elif password1 != password2:
    flash('Passwords do not match', category='error')
    return None
  elif len(password1) < 7:
    flash('Password must be at least 7 characters', category='error')
    return None
  elif check_password_hash(current_user.password, password1):
    flash('New password must be different than current password.', category='error')
    return None
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


def user_search():
  if request.form.keys() >= {'search'}:
    user_mapId_query = str(escape(request.form.get('search'))).lower()
    user_match = User.query.filter_by(mapId=user_mapId_query).first()

    return user_match
  return None


def trail_checkIn():
  if 'save_location' in request.form:

    return "Location Check-In"
  else:
    return "No Check-In Initiated"


def create_trail():
  if request.form.keys() >= {'create_trail'}:
    trail_name = str(escape(request.form.get('new_trail_name')))

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
        hidden=False,
        user=user
      )
      db.session.add(trail)
      db.session.commit()
      return trail
    else:
      flash('Trail Name Already In Use', category='error')
  return None


def select_trail():
  if request.form.keys() >= {'select_trail'}:
    selected_trail = str(escape(request.form.get('select_trail')))
    return selected_trail
  return None


def delete_trail():
  if request.form.keys() >= {'delete_trail'}:
    selected_trail = str(escape(request.form.get('delete_trail')))
    return selected_trail
  return None


def hide_trail():
  if request.form.keys() >= {'hide_trail'}:
    _ = str(escape(request.form.get('hide_trail')))
    trail_match = Trail.query.filter_by(id=_).first()
    return trail_match
  return None


def list_from_marker_class(markers):
  marker_list = []
  if len(markers) > 0:
    for marker in markers:
      marker_list.append(
        {
          "marker_num": marker.marker_num,
          "date":marker.datetime.strftime("%m/%d/%Y"),
          "time":marker.datetime.strftime("%-I:%M%p"),
          "lat":float("{0:.4f}".format(marker.lat)),
          "lon":float("{0:.4f}".format(marker.lon)),
          "elevation":marker.elevation,
          "temp":marker.temp,
          "humidity":marker.humidity,
          "airquality":marker.airquality,
          "weather":marker.weather,
          "note":marker.note,
          "popup": marker.datetime.strftime("%m/%d/%Y %-I:%M%p")
        }
      )

    return marker_list[::-1]
  return None


def load_active_trail(trail):
  try:
    markers = list_from_marker_class(trail.markers)
    active_trail = {
      "id": trail.id,
      "name":trail.name,
      "hidden": trail.hidden,
      "date":"",
      "time":"",
      "markers": markers
    }

    if markers:
      active_trail['date'] = markers[0]['date']
      active_trail['time'] = markers[0]['time']

    return active_trail
  except:
    return None


def load_user_trails(sql_trails):
  user_trails = []
  for trail in sql_trails:
    user_trails.append(
      {
        "id": trail.id,
        "name": trail.name,
        "hidden": trail.hidden,
        "date":trail.datetime.strftime("%b %d, %Y"),
        "time":trail.datetime.strftime("%-I:%M%p"),
        "markers": list_from_marker_class(trail.markers)
      }
    )
  return user_trails


@views.route('/', methods=['GET', 'POST'])
def redirect_to_home():
  if current_user.is_authenticated:
    return redirect(url_for('views.user_trail',user_mapId=current_user.mapId))

  if request.method == 'POST':
    if request.form.keys() >= {'search_button'}:
      user_match = user_search()
      if user_match:
        return redirect(url_for('views.user_trail',user_mapId=user_match.mapId))
  return render_template('home.html')


@views.route('/home', methods=['GET', 'POST'])
def home():
  if request.method == 'POST':
    if request.form.keys() >= {'search_button'}:
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
      user_trails = Trail.query.join(User, Trail.user_id==user_match.id).all()

      if user_match.current_trail:
        active_trail_match = Trail.query.join(User, Trail.user_id==user_match.id).filter(Trail.id==user_match.current_trail).first()
        active_trail = load_active_trail(active_trail_match)

      elif len(user_trails) == 1:
        active_trail_match = user_trails[0]
        if active_trail_match.hidden:
          active_trail = None
        else:
          active_trail = load_active_trail(active_trail_match)
      else:
        active_trail = None

      if request.method == 'POST':
        if request.form.keys() >= {'search_button'}:
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
          if current_user.id == user_match.id:
            current_user.current_trail = selected_trail
            db.session.commit()
          active_trail_match = Trail.query.join(User, Trail.user_id==user_match.id).filter(Trail.id==selected_trail).first()
          active_trail = load_active_trail(active_trail_match)


        if "test_button" in request.form:
          email_bot.main()
          return redirect(url_for('views.user_trail',user_mapId=current_user.mapId))

      settings = json.loads(current_user.settings)
    else:
      sql_trails = user_match.trails
      user_trails = load_user_trails(sql_trails)

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

    load_dotenv()
    mapbox_api = os.getenv('MAPBOX_API')
    return render_template('user_map.html', user=current_user, match=user_match, user_trails=user_trails, active_trail=active_trail, unitmeasure=settings['unitmeasure'], mapbox_api=mapbox_api)
  else:
    return redirect(url_for('views.home'))


@views.route('/manage', methods=['GET', 'POST'])
@login_required
def manage_trails():
  if current_user.is_authenticated:
    user_trails = Trail.query.join(User, Trail.user_id==current_user.id).all()
    trail_list = load_user_trails(user_trails)

    if request.method == 'POST':
      if request.form.keys() >= {'search_button'}:
        user_match = user_search()
        if user_match:
          return redirect(url_for('views.user_trail',user_mapId=user_match.mapId))

      delete_trail_request = delete_trail()
      if delete_trail_request:
        if str(current_user.current_trail) == str(delete_trail_request):
          _ = [i for i in user_trails if not (str(i.id) == str(delete_trail_request))]
          if len(_) > 0:
            current_user.current_trail = int(_[0].id)
          else:
            current_user.current_trail = None
          db.session.commit()

        Marker.query.filter_by(trail_id=delete_trail_request).delete()
        Trail.query.filter_by(id=delete_trail_request).delete()
        db.session.commit()

        user_trails = Trail.query.join(User, Trail.user_id==current_user.id).all()
        trail_list = load_user_trails(user_trails)
        return render_template('manage_trails.html', user=current_user, user_trails=trail_list)

      hide_trail_request = hide_trail()
      if hide_trail_request:
        if hide_trail_request.hidden == False:
          hide_trail_request.hidden = True
        else:
          hide_trail_request.hidden = False
          if current_user.current_trail is None:
            current_user.current_trail = hide_trail_request.id

        user_trails = Trail.query.join(User, Trail.user_id==current_user.id).all()
        trail_list = load_user_trails(user_trails)

        if current_user.current_trail == hide_trail_request.id:
          active_trail_match = Trail.query.join(User, Trail.user_id==current_user.id).filter(Trail.id==current_user.current_trail).first()
          if active_trail_match.hidden:
            _ = [i for i in trail_list if not i['hidden']]
            if len(_) > 0:
              current_user.current_trail = int(_[0]['id'])
            else:
              current_user.current_trail = None

        db.session.commit()
        return render_template('manage_trails.html', user=current_user, user_trails=trail_list)

    return render_template('manage_trails.html', user=current_user, user_trails=trail_list)
  else:
    return redirect(url_for('views.home'))


@views.route('/usersettings', methods=['GET', 'POST'])
def usersettings():
  if current_user.is_authenticated:
    user_settings = init_user_settings()

    if request.method == 'POST':
      if request.form.keys() >= {'search_button'}:
        user_match = user_search()
        if user_match:
          return redirect(url_for('views.user_trail',user_mapId=user_match.mapId))

      if request.form.keys() >= {'delete'}:
        return redirect(url_for('views.deleteaccount'))

      if request.form.keys() >= {'save'}:
        settings_changes = change_user_settings_request(user_settings)
        if settings_changes:
          current_user.settings = json.dumps(settings_changes[1])
          db.session.commit()
          user_settings = json.loads(current_user.settings)
          flash(f'Settings Saved: {", ".join(settings_changes[0])}', category='success')

    return render_template('usersettings.html', user=current_user, lastName=current_user.lastName, firstName=current_user.firstName, email=current_user.email, settings=user_settings, priv_key=current_user.private_key)
  else:
    return redirect(url_for('views.home'))


@views.route('/deleteaccount', methods=['GET', 'POST'])
def deleteaccount():
  if current_user.is_authenticated:
    if request.method == 'POST':
      if request.form.keys() >= {'search_button'}:
        user_match = user_search()
        if user_match:
          return redirect(url_for('views.user_trail',user_mapId=user_match.mapId))

      if request.form.keys() >= {'delete'}:
        email = str(escape(request.form.get('email')))
        password1 = str(escape(request.form.get('password1')))

        if current_user.email == email:
          if check_password_hash(current_user.password, password1):
            db.session.delete(current_user)
            db.session.commit()
            return redirect(url_for('views.home'))
          else:
            flash('Incorrect Password, please try again.', category='error')
        else:
          flash('Incorrect Email, please try again.', category='error')

    return render_template('deleteaccount.html', user=current_user)
  else:
    return redirect(url_for('views.home'))