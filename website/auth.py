import imp
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, escape
from flask_login import login_user, login_required, logout_user, current_user
import json
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db, mail
import random
from flask_mail import Message

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
  
  
def generate_private_key(firstname, lastname):
  num = generate_fourdigits()
  priv_key = str(firstname[0]) + str(lastname[0]) + "#" + str(num)
  existing_priv_key= User.query.filter_by(private_key=priv_key).first()
  while existing_priv_key is not None:
    num = generate_fourdigits()
    priv_key = str(firstname[0]) + str(lastname[0]) + "#" + str(num)
    existing_priv_key = User.query.filter_by(private_key=priv_key).first()
    if not existing_priv_key:
      break
  else:
    return priv_key
  

@auth.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    return redirect(url_for('views.home'))

  if request.method == 'POST':
    email = str(escape(request.form.get('email'))).lower()
    password = str(escape(request.form.get('password')))

    user = User.query.filter_by(email=email).first()
    if user:
      if check_password_hash(user.password, password):
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
  logout_user()
  return redirect(url_for('views.home'))


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
  if current_user.is_authenticated:
    return redirect(url_for('views.home'))

  if request.method == 'POST':
    email = str(escape(request.form.get('email'))).lower()
    firstName = str(escape(request.form.get('firstName')))
    lastName = str(escape(request.form.get('lastName')))
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
      
      mapId = generate_user_mapId(firstName.lower())
      priv_key = generate_private_key(firstName, lastName)
      
      new_user = User(email=email, firstName=firstName, lastName=lastName, mapId=mapId, private_key= priv_key, password=generate_password_hash(password1, method='sha256'), role="basic",
                      settings=json.dumps(user_settings))
      db.session.add(new_user)
      db.session.commit()
      login_user(new_user, remember=True)
      return redirect(url_for('views.user_trail',user_mapId=mapId))

  return render_template("signup.html", user=current_user)


def send_reset_email(user):
  token = user.get_reset_token()
  msg = Message('Password Reset Request',
                sender="no-reply@breadcrumbtrail.app",
                recipients=[user.email])
  msg.body= f'''To reset your password, visit the following link:
{url_for('auth.reset_token', token=token, _external=True)}

If you did not make this request, you can ignore this email and no changes will be made.
  '''
  mail.send(msg)


@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
  if current_user.is_authenticated:
    return redirect(url_for('views.home'))

  if request.method == 'POST':
    if 'email' in request.form:
      email = str(escape(request.form.get('email'))).lower()
      user = User.query.filter_by(email=email).first()
      if user:
        send_reset_email(user)
        flash(f'Password reset link sent to {email}.', category='success')

      return redirect(url_for('auth.login'))
  form = "request"
  return render_template("accountrecovery.html", user=current_user, form=form)


@auth.route('/accountrecovery/<token>', methods=['GET', 'POST'])
def reset_token(token):
  if current_user.is_authenticated:
    return redirect(url_for('views.user_trail',user_mapId=current_user.mapId))

  user = User.verify_reset_token(token)
  if not user:
    flash('Invalid or Expired token', category='error')
    return redirect(url_for('auth.reset_request'))
  form = "reset"

  if request.method == 'POST':
    password1 = str(escape(request.form.get('password1')))
    password2 = str(escape(request.form.get('password2')))
    if password1 != password2:
      flash('Passwords do not match', category='error')
    elif len(password1) < 7:
      flash('Password must be at least 7 characters', category='error')
    else:
      hashed_password = generate_password_hash(password1, method='sha256')
      user.password = hashed_password
      db.session.commit()
      login_user(user, remember=True)
      flash('Password Reset!', category='success')
      return redirect(url_for('views.user_trail',user_mapId=current_user.mapId))

  return render_template("accountrecovery.html", user=current_user, form=form)