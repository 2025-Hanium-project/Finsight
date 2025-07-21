from flask import Flask
from .config import Config
from .extensions import db, ma
from .routes import sample_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 확장 초기화
    db.init_app(app)
    ma.init_app(app)

    # Blueprint 등록
    app.register_blueprint(sample_bp)

    return app
