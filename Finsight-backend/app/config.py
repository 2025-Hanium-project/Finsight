# app/config.py

import os

class BaseConfig:
    # SQLAlchemy 일반 옵션
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_PRE_PING = True         # 끊긴 커넥션 방지용
    SQLALCHEMY_POOL_RECYCLE = 280           # 타임아웃 방지용

class DevelopmentConfig(BaseConfig):
    # 개발용 데이터베이스 (aia 계정)
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://{user}:{pw}@{host}:{port}/{db}"
        "?charset=utf8mb4"
    ).format(
        user="aia",
        pw="aia123!",
        host="finsight.kro.kr",
        port=32503,
        db="finsight_database"   # 실제 사용할 DB 이름으로 변경
    )

class TestingConfig(BaseConfig):
    # 테스트용 ETL 계정 등 별도 DB를 쓰신다면 여기에 작성
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://{user}:{pw}@{host}:{port}/{db}"
        "?charset=utf8mb4"
    ).format(
        user="etluser",
        pw="data123!",
        host="finsight.kro.kr",
        port=32503,
        db="your_test_db"
    )

class ProductionConfig(BaseConfig):
    # 운영 환경도 보통은 aia 계정 사용
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://{user}:{pw}@{host}:{port}/{db}?charset=utf8mb4"
        .format(
            user="aia",
            pw="aia123!",
            host="finsight.kro.kr",
            port=32503,
            db="your_database_name"
        )
    )

config_by_name = {
    "dev": DevelopmentConfig,
    "test": TestingConfig,
    "prod": ProductionConfig,
}
