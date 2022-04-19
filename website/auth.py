from flask import Blueprint, render_template, request, flash, redirect, url_for, escape
from flask_login import login_user, login_required, logout_user, current_user
import json
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from .views import user_search
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
  count = 0
  while existing_mapId is not None:
    count += 1
    num = generate_fourdigits()
    mapId = str(firstname) + "#" + str(num)
    existing_mapId = User.query.filter_by(mapId=mapId).first()
    if count > 9000:
      return None
  else:
    return mapId


def generate_private_key(firstname, lastname):
  num = generate_fourdigits()
  priv_key = str(firstname[0]) + str(lastname[0]) + "#" + str(num)
  existing_priv_key= User.query.filter_by(private_key=priv_key).first()
  count = 0
  while existing_priv_key is not None:
    num = generate_fourdigits()
    priv_key = str(firstname[0]) + str(lastname[0]) + "#" + str(num)
    existing_priv_key = User.query.filter_by(private_key=priv_key).first()
    if count > 9000:
      return None
  else:
    return priv_key


def signup_request():
  if request.form.keys() >= {'email','firstName','lastName','password1','password2'}:
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

      if mapId and priv_key:
        new_user = User(email=email, firstName=firstName, lastName=lastName, mapId=mapId, private_key=priv_key, password=generate_password_hash(password1, method='sha256'), role="basic",
                      settings=json.dumps(user_settings))
        return new_user
  return None


def login_request():
  if request.form.keys() >= {'email', 'password'}:
    email = str(escape(request.form.get('email'))).lower()
    password = str(escape(request.form.get('password')))

    user = User.query.filter_by(email=email).first()
    if user:
      if check_password_hash(user.password, password):
        return user
  return None



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



@auth.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    return redirect(url_for('views.home'))

  if request.method == 'POST':
    if request.form.keys() >= {'search_button'}:
      user_match = user_search()
      if user_match:
        return redirect(url_for('views.user_trail',user_mapId=user_match.mapId))

    if request.form.keys() >= {'login_button'}:
      login_check = login_request()
      if login_check:
        login_user(login_check, remember=True)
        return redirect(url_for('views.user_trail',user_mapId=login_check.mapId))
      flash('Incorrect email or password, try again!', category='error')

  return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect(url_for('auth.login'))


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
  if current_user.is_authenticated:
    return redirect(url_for('views.home'))

  if request.method == 'POST':
    user_match = user_search()
    if user_match:
      return redirect(url_for('views.user_trail',user_mapId=user_match.mapId))

    if request.form.keys() >= {'signup_button'}:
      signup_check = signup_request()
      if signup_check:
        db.session.add(signup_check)
        db.session.commit()
        login_user(signup_check, remember=True)
        return redirect(url_for('views.user_trail',user_mapId=signup_check.mapId))
      flash('A limit error has occured. Please try again later.', category='error')

  return render_template("signup.html", user=current_user)


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