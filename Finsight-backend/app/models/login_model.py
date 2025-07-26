from flask_login import UserMixin
from ..extensions import db, bcrypt


# UserMixin = get_id, is_authenticated, is_active, is_anonymous 등 기본 구현 제공
# 필요시 오버라이드해서 추가 기능 구현 가능
class User(db.Model, UserMixin):
    __tablename__ = 'user'

    user_id = db.Column(db.String(36), primary_key=True)
    user_name = db.Column(db.Text, nullable=False)
    password = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.current_timestamp())

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)
    def get_id(self):
        return str(self.user_id)