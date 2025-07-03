import os

# Private Cloud 환경 설정
BASE_DOWNLOAD_PATH = "/nfs/consensus-data/downloads"
LOG_DIR = "/nfs/consensus-data/logs"
PARSED_DATA_DIR = "/nfs/consensus-data/parsed_data"

# 기본 설정
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DEFAULT_TIMEOUT = 30

# Chrome 옵션 (Headless 환경용)
CHROME_OPTIONS = [
    "--headless",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--window-size=1920,1080",
    "--disable-extensions",
    "--disable-plugins",
    "--disable-images",
    "--user-agent=" + USER_AGENT
]

# 데이터베이스 연결 설정 (Private Cloud)
DB_CONFIG = {
    'host': 'finsight.kro.kr',
    'port': 2503,
    'user': 'etluser',
    'password': 'data123!',
    'database': 'consensus_db'
}

# Kafka 설정 (Private Cloud)
KAFKA_CONFIG = {
    'bootstrap_servers': [
        'finsight.kro.kr:31992',
        'finsight.kro.kr:32992', 
        'finsight.kro.kr:33992'
    ],
    'topic': 'consensus-data'
}

# 디렉토리 생성
os.makedirs(BASE_DOWNLOAD_PATH, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(PARSED_DATA_DIR, exist_ok=True)
