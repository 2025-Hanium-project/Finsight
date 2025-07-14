import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# API 설정
API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = int(os.getenv('API_PORT', 8000))
API_VERSION = os.getenv('API_VERSION', 'v1')

# Ollama API 설정
OLLAMA_API_BASE_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434')
OLLAMA_API_GENERATE_URL = f"{OLLAMA_API_BASE_URL}/api/generate"

# Gemini API 설정
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# LLM 제공자 설정
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'ollama').lower()  # 'ollama' 또는 'gemini'

# 로그 설정
LOGS_PATH = os.getenv('LOGS_PATH', './logs')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', 10 * 1024 * 1024))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))

# Agent별 LLM 모델 설정
AGENT_MODELS = {
    'summary_agent': os.getenv('SUMMARY_MODEL', 'llama3'),
    'analysis_agent': os.getenv('ANALYSIS_MODEL', 'llama3:8b'),
    'sentiment_agent': os.getenv('SENTIMENT_MODEL', 'llama3'),
    'risk_agent': os.getenv('RISK_MODEL', 'llama3'),
    'growth_agent': os.getenv('GROWTH_MODEL', 'llama3'),
    'supervisor_agent': os.getenv('SUPERVISOR_MODEL', 'llama3'),
    'supervisor_validator': os.getenv('SUPERVISOR_VALIDATOR_MODEL', 'llama3'),
}

# Gemini용 Agent별 모델 설정
GEMINI_AGENT_MODELS = {
    'summary_agent': os.getenv('GEMINI_SUMMARY_MODEL', 'gemini-2.0-flash'),
    'analysis_agent': os.getenv('GEMINI_ANALYSIS_MODEL', 'gemini-2.0-flash'),
    'sentiment_agent': os.getenv('GEMINI_SENTIMENT_MODEL', 'gemini-2.0-flash'),
    'risk_agent': os.getenv('GEMINI_RISK_MODEL', 'gemini-2.0-flash'),
    'growth_agent': os.getenv('GEMINI_GROWTH_MODEL', 'gemini-2.0-flash'),
    'supervisor_agent': os.getenv('GEMINI_SUPERVISOR_MODEL', 'gemini-2.0-flash'),
    'supervisor_validator': os.getenv('GEMINI_SUPERVISOR_VALIDATOR_MODEL', 'gemini-2.0-flash'),
}

DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'llama3')
DEFAULT_GEMINI_MODEL = os.getenv('DEFAULT_GEMINI_MODEL', 'gemini-2.0-flash')

# 워크플로우 설정
# TODO: 워크플로우 타임아웃 설정 구현 필요시 추가
AGENT_TIMEOUT = int(os.getenv('AGENT_TIMEOUT', 400))  # 개별 에이전트 타임아웃 6분 40초
MAX_PARALLEL_AGENTS = int(os.getenv('MAX_PARALLEL_AGENTS', 4))
ENABLE_PARALLEL_EXECUTION = os.getenv('ENABLE_PARALLEL_EXECUTION', 'true').lower() == 'true'

# 재시도 설정
MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', 3))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', 1))  # 초

# LLM 호출 설정
LLM_TIMEOUT = int(os.getenv('LLM_TIMEOUT', 300))  # 5분
DEFAULT_TEMPERATURE = float(os.getenv('DEFAULT_TEMPERATURE', 0.7))
MAX_TOKENS = int(os.getenv('MAX_TOKENS', 4096))

# 데이터 처리 설정
MAX_REPORT_SIZE = int(os.getenv('MAX_REPORT_SIZE', 50000))  # 50KB
MAX_REPORTS_PER_REQUEST = int(os.getenv('MAX_REPORTS_PER_REQUEST', 10))

# 캐싱 설정 (향후 사용)
ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'false').lower() == 'true'
CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # 1시간

# 성능 모니터링 설정
ENABLE_PERFORMANCE_MONITORING = os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
SLOW_REQUEST_THRESHOLD = float(os.getenv('SLOW_REQUEST_THRESHOLD', 10.0))  # 10초
