import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# API 설정
API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = int(os.getenv('API_PORT', 8000))
API_VERSION = os.getenv('API_VERSION', 'v1')

# Ollama API 설정
OLLAMA_API_BASE_URL = os.getenv('OLLAMA_API_URL', '<http://localhost:11434>')
OLLAMA_API_GENERATE_URL = f"{OLLAMA_API_BASE_URL}/api/generate"

# 로그 설정
LOGS_PATH = os.getenv('LOGS_PATH', './logs')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Agent별 LLM 모델 설정
AGENT_MODELS = {
    'summary_agent': os.getenv('SUMMARY_MODEL', 'llama3'),  # 요약에 적합한 모델
    'analysis_agent': os.getenv('ANALYSIS_MODEL', 'llama3:8b'), # 분석 및 추론에 적합한 모델
    'sentiment_agent': os.getenv('SENTIMENT_MODEL', 'llama3'),  # 감성 분석에 적합한 모델
}

DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'llama3')

# TO DO: Supervisor Agent에서 사용할 모델 설정
# TO DO: RAG를 위한 벡터 DB 설정
# TO DO: ReRanker 설정
# TO DO: Function Calling 파라미터 설정
