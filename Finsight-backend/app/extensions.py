from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flasgger import Swagger

db = SQLAlchemy()
ma = Marshmallow()
swagger = Swagger()
