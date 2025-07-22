from flask import Flask
from .config import config_by_name
from .extensions import db, ma
from .routes.stock import stock_bp
# (기존에 등록한 다른 bp들도 함께)

def create_app(config_name='dev'):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # 확장 초기화
    db.init_app(app)
    ma.init_app(app)

    # Blueprint 등록
    app.register_blueprint(stock_bp)
    # app.register_blueprint(other_bp)

    return app
