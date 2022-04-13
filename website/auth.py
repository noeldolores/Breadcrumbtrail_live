import imp
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, escape
from flask_login import login_user, login_required, logout_user, current_user
import json
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db
import random


auth = Blueprint('auth', __name__)


def generate_fourdigits():
  num = random.randint(1000,9999)
  return num


def generate_user_mapId(firstname):
  num = generate_fourdigits()
  mapId = str(firstname) + "#" + str(num)
  existing_mapId= User.query.filter_by(mapId=mapId).first()
  while existing_mapId is not None:
    num = generate_fourdigits()
    mapId = str(firstname) + "#" + str(num)
    existing_mapId= User.query.filter_by(mapId=mapId).first()
  else:
    return mapId
  
  

@auth.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    session.pop('_flashes', None)
    return redirect(url_for('views.home'))
  else:
    if 'reset' in session:
      session.pop('reset', None)

  if request.method == 'POST':
    email = str(escape(request.form.get('email'))).lower()
    password = str(escape(request.form.get('password')))

    user = User.query.filter_by(email=email).first()
    if user:
      if check_password_hash(user.password, password):
        session.pop('_flashes', None)
        #flash('Logged in successfuly!', category='success')
        login_user(user, remember=True)
        return redirect(url_for('views.user_trail',user_mapId=user.mapId))
      else:
        flash('Incorrect password, try again!', category='error')
    else:
        flash('Email does not exist.', category='error')

  return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
  session.clear()
  logout_user()
  return redirect(url_for('views.home'))


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
  if current_user.is_authenticated:
    session.pop('_flashes', None)
    return redirect(url_for('views.home'))
  else:
    session.pop('_flashes', None)
    pass

  if request.method == 'POST':
    email = str(escape(request.form.get('email'))).lower()
    firstName = str(escape(request.form.get('firstName')))
    password1 = str(escape(request.form.get('password1')))
    password2 = str(escape(request.form.get('password2')))

    user = User.query.filter_by(email=email).first()
    if user:
      flash('Email already exists.', category='error')
    elif len(email) < 4:
      flash('Email must be greater than 4 characters', category='error')
    elif len(firstName) < 2:
      flash('Name must be at least 1 character', category='error')
    elif password1 != password2:
      flash('Passwords do not match', category='error')
    elif len(password1) < 7:
      flash('Password must be at least 7 characters', category='error')
    else:
      user_settings = {
        'timezone':'UTC',
        'unitmeasure':'Metric'
      }
      
      checkincontact = email
      mapId = generate_user_mapId(firstName.lower())
      
      new_user = User(email=email, firstName=firstName, mapId=mapId, checkincontact= checkincontact, password=generate_password_hash(password1, method='sha256'), role="basic",
                      settings=json.dumps(user_settings))
      db.session.add(new_user)
      db.session.commit()
      login_user(new_user, remember=True)
      session.pop('_flashes', None)
      #flash('Account Created!', category='success')
      return redirect(url_for('views.user_trail',user_mapId=mapId))

  return render_template("signup.html", user=current_user)