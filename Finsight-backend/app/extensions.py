from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flasgger import Swagger
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

db = SQLAlchemy()
ma = Marshmallow()
swagger = Swagger()
bcrypt = Bcrypt()
login_manager = LoginManager()