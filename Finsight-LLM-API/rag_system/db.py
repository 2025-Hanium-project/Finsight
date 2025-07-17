import psycopg2
from contextlib import contextmanager
from typing import Generator
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': 35000,  
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

@contextmanager
def get_conn() -> Generator[psycopg2.extensions.connection, None, None]:
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()
