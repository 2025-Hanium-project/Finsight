"""
설정 관리

기능:
- 환경 변수 관리
- LLM 설정
- 에이전트별 모델 설정
- 협업 시스템 설정
- 성능 최적화 설정
"""

import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# ============================================================================
# API 설정
# ============================================================================

API_HOST = os.getenv('API_HOST', 'localhost')
API_PORT = int(os.getenv('API_PORT', 8000))
API_VERSION = os.getenv('API_VERSION', 'v1')

# ============================================================================
# LLM 설정 (Gemini만 사용)
# ============================================================================

# LLM 제공자 설정 (Gemini만 사용)
LLM_PROVIDER = 'gemini'

# Gemini API 설정
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# 기본 LLM 설정
DEFAULT_GEMINI_MODEL = os.getenv('DEFAULT_GEMINI_MODEL', 'gemini-2.0-flash')
DEFAULT_TEMPERATURE = float(os.getenv('DEFAULT_TEMPERATURE', 0.7))
MAX_TOKENS = int(os.getenv('MAX_TOKENS', 4096))
LLM_TIMEOUT = int(os.getenv('LLM_TIMEOUT', 30))
MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', 3))
RETRY_DELAY = float(os.getenv('RETRY_DELAY', 1.0))

# ============================================================================
# 에이전트별 LLM 모델 설정 (Gemini만 사용)
# ============================================================================

# Gemini 에이전트 모델 설정
AGENT_MODELS = {
    # 데이터 에이전트
    'financial_statement_agent': os.getenv('GEMINI_FINANCIAL_STATEMENT_MODEL', 'gemini-2.0-flash'),
    'news_analysis_agent': os.getenv('GEMINI_NEWS_ANALYSIS_MODEL', 'gemini-2.0-flash'),
    'securities_report_agent': os.getenv('GEMINI_SECURITIES_REPORT_MODEL', 'gemini-2.0-flash'),
    'market_data_agent': os.getenv('GEMINI_MARKET_DATA_MODEL', 'gemini-2.0-flash'),
    
    # 분석 에이전트
    'risk_assessment_agent': os.getenv('GEMINI_RISK_ASSESSMENT_MODEL', 'gemini-2.0-flash'),
    'growth_analysis_agent': os.getenv('GEMINI_GROWTH_ANALYSIS_MODEL', 'gemini-2.0-flash'),
    'valuation_agent': os.getenv('GEMINI_VALUATION_MODEL', 'gemini-2.0-flash'),
    'peer_comparison_agent': os.getenv('GEMINI_PEER_COMPARISON_MODEL', 'gemini-2.0-flash'),
    
    # 리포트 에이전트
    'dday_report_agent': os.getenv('GEMINI_DDAY_REPORT_MODEL', 'gemini-2.0-flash'),
    'dplus1_report_agent': os.getenv('GEMINI_DPLUS1_REPORT_MODEL', 'gemini-2.0-flash'),
    
    # 지원 에이전트
    'supervisor_agent': os.getenv('GEMINI_SUPERVISOR_MODEL', 'gemini-2.0-flash'),
    'data_quality_agent': os.getenv('GEMINI_DATA_QUALITY_MODEL', 'gemini-2.0-flash'),
    'document_processing_agent': os.getenv('GEMINI_DOCUMENT_PROCESSING_MODEL', 'gemini-2.0-flash')
}

# Gemini 에이전트 모델 설정 (동일한 설정을 별도로 유지)
GEMINI_AGENT_MODELS = AGENT_MODELS.copy()

# ============================================================================
# 워크플로우 설정
# ============================================================================

# 워크플로우 실행 설정
WORKFLOW_EXECUTION_ENABLED = os.getenv('WORKFLOW_EXECUTION_ENABLED', 'true').lower() == 'true'

# 워크플로우 설정
WORKFLOW_CONFIGS = {
    "comprehensive": {
        "name": "종합 분석 워크플로우",
        "description": "모든 에이전트를 활용한 종합 분석",
        "steps": [
            {
                "step_id": "data_collection",
                "step_name": "데이터 수집",
                "agent_name": "financial_statement_agent",
                "step_type": "data_collection",
                "dependencies": [],
                "timeout": 60
            },
            {
                "step_id": "news_analysis",
                "step_name": "뉴스 분석",
                "agent_name": "news_analysis_agent",
                "step_type": "analysis",
                "dependencies": ["data_collection"],
                "timeout": 45
            },
            {
                "step_id": "risk_assessment",
                "step_name": "리스크 평가",
                "agent_name": "risk_assessment_agent",
                "step_type": "analysis",
                "dependencies": ["data_collection", "news_analysis"],
                "timeout": 60
            },
            {
                "step_id": "growth_analysis",
                "step_name": "성장성 분석",
                "agent_name": "growth_analysis_agent",
                "step_type": "analysis",
                "dependencies": ["data_collection"],
                "timeout": 45
            },
            {
                "step_id": "valuation",
                "step_name": "밸류에이션",
                "agent_name": "valuation_agent",
                "step_type": "analysis",
                "dependencies": ["data_collection", "risk_assessment", "growth_analysis"],
                "timeout": 60
            },
            {
                "step_id": "peer_comparison",
                "step_name": "동종업계 비교",
                "agent_name": "peer_comparison_agent",
                "step_type": "analysis",
                "dependencies": ["data_collection", "valuation"],
                "timeout": 45
            },
            {
                "step_id": "report_generation",
                "step_name": "리포트 생성",
                "agent_name": "dday_report_agent",
                "step_type": "report_generation",
                "dependencies": ["data_collection", "news_analysis", "risk_assessment", "growth_analysis", "valuation", "peer_comparison"],
                "timeout": 90
            }
        ],
        "timeout": 300,
        "max_retries": 3,
        "parallel_execution": True
    },
    "quick_analysis": {
        "name": "빠른 분석 워크플로우",
        "description": "핵심 분석만 수행하는 빠른 워크플로우",
        "steps": [
            {
                "step_id": "data_collection",
                "step_name": "데이터 수집",
                "agent_name": "financial_statement_agent",
                "step_type": "data_collection",
                "dependencies": [],
                "timeout": 30
            },
            {
                "step_id": "risk_assessment",
                "step_name": "리스크 평가",
                "agent_name": "risk_assessment_agent",
                "step_type": "analysis",
                "dependencies": ["data_collection"],
                "timeout": 30
            },
            {
                "step_id": "report_generation",
                "step_name": "리포트 생성",
                "agent_name": "dplus1_report_agent",
                "step_type": "report_generation",
                "dependencies": ["data_collection", "risk_assessment"],
                "timeout": 45
            }
        ],
        "timeout": 120,
        "max_retries": 2,
        "parallel_execution": False
    },
    "risk_focused": {
        "name": "리스크 중심 분석 워크플로우",
        "description": "리스크 평가에 집중한 워크플로우",
        "steps": [
            {
                "step_id": "data_collection",
                "step_name": "데이터 수집",
                "agent_name": "financial_statement_agent",
                "step_type": "data_collection",
                "dependencies": [],
                "timeout": 45
            },
            {
                "step_id": "news_analysis",
                "step_name": "뉴스 분석",
                "agent_name": "news_analysis_agent",
                "step_type": "analysis",
                "dependencies": ["data_collection"],
                "timeout": 30
            },
            {
                "step_id": "risk_assessment",
                "step_name": "리스크 평가",
                "agent_name": "risk_assessment_agent",
                "step_type": "analysis",
                "dependencies": ["data_collection", "news_analysis"],
                "timeout": 60
            },
            {
                "step_id": "report_generation",
                "step_name": "리포트 생성",
                "agent_name": "dday_report_agent",
                "step_type": "report_generation",
                "dependencies": ["data_collection", "news_analysis", "risk_assessment"],
                "timeout": 60
            }
        ],
        "timeout": 180,
        "max_retries": 3,
        "parallel_execution": True
    }
}

# ============================================================================
# 협업 시스템 설정
# ============================================================================

# 기본 협업 시스템 설정
COLLABORATION_TIMEOUT = int(os.getenv('COLLABORATION_TIMEOUT', 60))
COLLABORATION_MAX_RETRIES = int(os.getenv('COLLABORATION_MAX_RETRIES', 3))
COLLABORATION_RETRY_DELAY = float(os.getenv('COLLABORATION_RETRY_DELAY', 2.0))

# 고급 협업 시스템 설정
ADVANCED_COLLABORATION_ENABLED = os.getenv('ADVANCED_COLLABORATION_ENABLED', 'true').lower() == 'true'
KNOWLEDGE_BASE_SIZE = int(os.getenv('KNOWLEDGE_BASE_SIZE', 1000))
WORKFLOW_EXECUTION_TIMEOUT = int(os.getenv('WORKFLOW_EXECUTION_TIMEOUT', 300))

# 최적화된 협업 시스템 설정
OPTIMIZED_COLLABORATION_ENABLED = os.getenv('OPTIMIZED_COLLABORATION_ENABLED', 'true').lower() == 'true'
PARALLEL_PROCESSING_LIMIT = int(os.getenv('PARALLEL_PROCESSING_LIMIT', 5))
CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # 1시간

# ============================================================================
# 대시보드 설정
# ============================================================================

DASHBOARD_ENABLED = os.getenv('DASHBOARD_ENABLED', 'true').lower() == 'true'
DASHBOARD_UPDATE_INTERVAL = int(os.getenv('DASHBOARD_UPDATE_INTERVAL', 30))  # 30초
DASHBOARD_HISTORY_SIZE = int(os.getenv('DASHBOARD_HISTORY_SIZE', 100))

# ============================================================================
# 성능 최적화 설정
# ============================================================================

# 병렬 처리 설정
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', 10))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
CONNECTION_POOL_SIZE = int(os.getenv('CONNECTION_POOL_SIZE', 20))

# 메모리 관리 설정
MAX_MEMORY_USAGE = int(os.getenv('MAX_MEMORY_USAGE', 1024))  # MB
GARBAGE_COLLECTION_INTERVAL = int(os.getenv('GARBAGE_COLLECTION_INTERVAL', 300))  # 5분

# ============================================================================
# 로깅 설정
# ============================================================================

LOGS_PATH = os.getenv('LOGS_PATH', './logs')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_MAX_SIZE = int(os.getenv('LOG_MAX_SIZE', 10 * 1024 * 1024))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))

# ============================================================================
# 보안 설정
# ============================================================================

# Rate Limiting 설정
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', 100))  # 분당 요청 수
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 60))  # 초

# IP 차단 설정
IP_BLOCKING_ENABLED = os.getenv('IP_BLOCKING_ENABLED', 'true').lower() == 'true'
BLOCKED_IPS = os.getenv('BLOCKED_IPS', '').split(',') if os.getenv('BLOCKED_IPS') else []

# 입력 검증 설정
INPUT_VALIDATION_ENABLED = os.getenv('INPUT_VALIDATION_ENABLED', 'true').lower() == 'true'
MAX_INPUT_SIZE = int(os.getenv('MAX_INPUT_SIZE', 1024 * 1024))  # 1MB

# ============================================================================
# 데이터베이스 설정 (향후 확장용)
# ============================================================================

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./finsight.db')
DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', 10))
DATABASE_MAX_OVERFLOW = int(os.getenv('DATABASE_MAX_OVERFLOW', 20))

# ============================================================================
# 외부 API 설정
# ============================================================================

# 금융 데이터 API 설정
FINANCIAL_API_KEY = os.getenv('FINANCIAL_API_KEY', '')
FINANCIAL_API_BASE_URL = os.getenv('FINANCIAL_API_BASE_URL', '')

# 뉴스 API 설정
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
NEWS_API_BASE_URL = os.getenv('NEWS_API_BASE_URL', '')

# 시장 데이터 API 설정
MARKET_DATA_API_KEY = os.getenv('MARKET_DATA_API_KEY', '')
MARKET_DATA_API_BASE_URL = os.getenv('MARKET_DATA_API_BASE_URL', '')

# ============================================================================
# 유틸리티 함수
# ============================================================================

def get_agent_model(agent_name: str) -> str:
    """에이전트별 모델 반환"""
    return AGENT_MODELS.get(agent_name, DEFAULT_GEMINI_MODEL)

def get_workflow_config(workflow_type: str) -> dict:
    """워크플로우 설정 반환"""
    if workflow_type in WORKFLOW_CONFIGS:
        return WORKFLOW_CONFIGS[workflow_type]
    else:
        return WORKFLOW_CONFIGS.get("comprehensive", {})

def is_feature_enabled(feature_name: str) -> bool:
    """기능 활성화 여부 확인"""
    feature_flags = {
        'dashboard': DASHBOARD_ENABLED,
        'collaboration': ADVANCED_COLLABORATION_ENABLED,
        'optimized_collaboration': OPTIMIZED_COLLABORATION_ENABLED,
        'cache': CACHE_ENABLED,
        'rate_limit': RATE_LIMIT_ENABLED,
        'ip_blocking': IP_BLOCKING_ENABLED,
        'input_validation': INPUT_VALIDATION_ENABLED,
        'workflow': WORKFLOW_EXECUTION_ENABLED
    }
    return feature_flags.get(feature_name, False)

def get_system_config() -> dict:
    """전체 시스템 설정 반환"""
    return {
        'api': {
            'host': API_HOST,
            'port': API_PORT,
            'version': API_VERSION
        },
        'llm': {
            'provider': LLM_PROVIDER,
            'default_model': DEFAULT_GEMINI_MODEL,
            'temperature': DEFAULT_TEMPERATURE,
            'max_tokens': MAX_TOKENS,
            'timeout': LLM_TIMEOUT
        },
        'workflow': {
            'enabled': WORKFLOW_EXECUTION_ENABLED,
            'configs': list(WORKFLOW_CONFIGS.keys()),
            'timeout': WORKFLOW_EXECUTION_TIMEOUT
        },
        'collaboration': {
            'timeout': COLLABORATION_TIMEOUT,
            'max_retries': COLLABORATION_MAX_RETRIES,
            'advanced_enabled': ADVANCED_COLLABORATION_ENABLED,
            'optimized_enabled': OPTIMIZED_COLLABORATION_ENABLED
        },
        'dashboard': {
            'enabled': DASHBOARD_ENABLED,
            'update_interval': DASHBOARD_UPDATE_INTERVAL
        },
        'performance': {
            'max_concurrent_requests': MAX_CONCURRENT_REQUESTS,
            'request_timeout': REQUEST_TIMEOUT,
            'max_memory_usage': MAX_MEMORY_USAGE
        },
        'security': {
            'rate_limit_enabled': RATE_LIMIT_ENABLED,
            'ip_blocking_enabled': IP_BLOCKING_ENABLED,
            'input_validation_enabled': INPUT_VALIDATION_ENABLED
        }
    }
