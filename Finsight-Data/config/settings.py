import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class Settings:
    # --- Project Directories ---
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

    # --- API Keys ---
    KRX_API_KEY = os.getenv('KRX_API_KEY', '')
    DART_API_KEY = os.getenv('DART_API_KEY', '')
    FRED_API_KEY = os.getenv('FRED_API_KEY', '')
    ECOS_API_KEY = os.getenv('ECOS_API_KEY', '')  # 한국은행 경제통계시스템 API 키
    KOSIS_API_KEY = os.getenv('KOSIS_API_KEY', '')  # 통계청 KOSIS API 키
    NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID', '')  # 네이버 API 클라이언트 ID
    NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET', '')  # 네이버 API 클라이언트 시크릿

    # --- Data Collection Settings ---
    COLLECTION_INTERVAL = int(os.getenv('COLLECTION_INTERVAL', 60))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    TIMEOUT = int(os.getenv('TIMEOUT', 30))
    
    KOREA_INDICES = {
        'KOSPI': '1001',
        'KOSDAQ': '2001',
        'KOSPI200': '1028',
    }
    GLOBAL_INDICES = {
        'S&P500': '^GSPC', 'NASDAQ': '^IXIC', 'DOW': '^DJI', 
        'NIKKEI': '^N225', 'HANG_SENG': '^HSI'
    }
    CURRENCIES = {'USD': 'USDKRW=X', 'EUR': 'EURKRW=X', 'JPY': 'JPYKRW=X'}
    
    # --- Fallback Settings ---
    TOP_STOCKS_FALLBACK = [
        '005930', '000660', '207940', '373220', '012450',  # 삼성전자, SK하이닉스, 삼성바이오로직스, LG에너지솔루션, 한화에어로스페이스
        '005380', '035420', '105560', '005935', '329180',  # 현대차, NAVER, KB금융, 삼성전자우, HD현대중공업
        '000270', '034020', '068270', '035720', '055550',  # 기아, 두산에너빌리티, 셀트리온, 카카오, 신한지주
        '028260', '042660', '012330', '009540', '032830'   # 삼성물산, 한화오션, 현대모비스, HD한국조선해양, 삼성생명
    ]

    # --- Run Mode ---
    RUN_MODE = os.getenv('RUN_MODE', "once")
    SCHEDULE_TIME = os.getenv('SCHEDULE_TIME', "08:00")

    # --- Logging ---
    LOG_LEVEL = os.getenv('LOG_LEVEL', "INFO")
    LOG_FILE_PATH = os.path.join(LOGS_DIR, "data_collector.log")
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))

# 전역 설정 객체
settings = Settings() 