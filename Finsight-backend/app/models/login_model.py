from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    user_id = db.Column(db.String(36), primary_key=True)
    user_name = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)
