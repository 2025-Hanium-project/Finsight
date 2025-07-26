from flask import Flask
from .config import config_by_name
from .extensions import db, ma, swagger
from flasgger import LazyJSONEncoder
from .routes.stock import stock_bp
from .routes.stock_direct import direct_bp
from flask_cors import CORS
from .extensions import db, ma, swagger, bcrypt, login_manager
from .routes.auth import auth_bp 
import os
from dotenv import load_dotenv

# (기존에 등록한 다른 bp들도 함께)

def create_app(config_name='dev'):

    app = Flask(__name__)
    app.json_ecncoder = LazyJSONEncoder  # JSON 직렬화 시 LazyJSONEncoder 사용
    app.config.from_object(config_by_name[config_name])
    # 세션 보안 관련 설정
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = False  # 개발 환경에서는 False, 배포 시 True

    CORS(app)  # CORS 설정 추가
    app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')  # 환경변수에서 SECRET_KEY 가져오기
    # 확장 초기화
    db.init_app(app)
    ma.init_app(app)
    swagger.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # 로그인 필요시 이동할 라우트명
    # Blueprint 등록
    app.register_blueprint(stock_bp)
    app.register_blueprint(direct_bp)
    app.register_blueprint(auth_bp)

    return app

@login_manager.user_loader
def load_user(user_id):
    from .models.login_model import User
    return User.query.get(user_id)
