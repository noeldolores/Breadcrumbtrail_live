from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate



db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
DB_NAME = "noeldolores$breadcrumbtrail"


def create_app():
  app = Flask(__name__)
  app.config.from_object("config.ProductionConfig")
  db.init_app(app)
  migrate.init_app(app, db)
  mail.init_app(app)

  from .views import views
  from .auth import auth

  app.register_blueprint(views, url_prefix='/')
  app.register_blueprint(auth, url_prefix='/')

  from .models import User, Marker, Trail

  login_manager = LoginManager()
  login_manager.login_view = 'auth.login'
  login_manager.init_app(app)

  @login_manager.user_loader
  def load_user(id):
    return User.query.get(int(id))

  return app

def create_database(app):
  db.create_all(app=app)


app = create_app()
app.app_context().push()
#create_database(app)