from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask_login import UserMixin
from sqlalchemy.dialects.mysql import JSON, DECIMAL
from sqlalchemy.orm import backref
from datetime import datetime
from . import db
from flask import current_app as app


class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  role = db.Column(db.String(150))
  email = db.Column(db.String(150), unique=True)
  password = db.Column(db.String(150))
  firstName = db.Column(db.String(150))
  lastName = db.Column(db.String(150))
  mapId = db.Column(db.String(150), unique=True)
  private_key = db.Column(db.String(150), unique=True)
  settings = db.Column(JSON)
  current_trail = db.Column(db.Integer)
  trails = db.relationship('Trail', backref=db.backref('user'))

  def get_reset_token(self, expires_sec=1800):
    s = Serializer(app.config['SECRET_KEY'], expires_sec)
    return s.dumps({'user_id':self.id}).decode('utf-8')

  @staticmethod
  def verify_reset_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
      user_id = s.loads(token)['user_id']
    except:
      return None
    return User.query.get(user_id)


class Trail(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(150))
  datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  hidden = db.Column(db.Boolean)
  markers = db.relationship('Marker', backref=db.backref('trail'))
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  
  
class Marker(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  marker_num = db.Column(db.Integer)
  datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  lat = db.Column(DECIMAL(8,6))
  lon = db.Column(DECIMAL(9,6))
  elevation = db.Column(db.Integer)
  temp = db.Column(db.Integer)
  humidity = db.Column(db.Integer)
  airquality = db.Column(db.String(150))
  weather = db.Column(db.String(150))
  note = db.Column(db.String(300))
  trail_id = db.Column(db.Integer, db.ForeignKey(Trail.id))