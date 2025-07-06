from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional, Union, List
import logging
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import re
import hashlib
import secrets

logger = logging.getLogger(__name__)

# ================================
# 에러 타입 및 예외 클래스들 (기존 exceptions.py)
# ================================

class ErrorType(Enum):
    """에러 타입 분류"""
    VALIDATION_ERROR = "validation_error"
    LLM_ERROR = "llm_error"
    AGENT_ERROR = "agent_error"
    # TODO: 워크플로우 에러 타입 구현 필요시 추가
    TIMEOUT_ERROR = "timeout_error"
    NETWORK_ERROR = "network_error"
    PARSING_ERROR = "parsing_error"
    CONFIGURATION_ERROR = "configuration_error"


class BaseAnalysisError(Exception):
    """기본 분석 에러 클래스"""
    
    def __init__(
        self,
        message: str,
        error_type: ErrorType,
        details: Optional[Dict[str, Any]] = None,
        agent_name: Optional[str] = None,
        retry_possible: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        self.agent_name = agent_name
        self.retry_possible = retry_possible
        
        # 에러 로깅
        logger.error(
            f"[{error_type.value}] {agent_name or 'Unknown'}: {message}",
            extra={"details": details}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """에러 정보를 딕셔너리로 변환"""
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "agent_name": self.agent_name,
            "details": self.details,
            "retry_possible": self.retry_possible
        }


class AgentError(BaseAnalysisError):
    """에이전트 실행 중 발생하는 에러"""
    
    def __init__(
        self,
        agent_name: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retry_possible: bool = True
    ):
        super().__init__(
            message=message,
            error_type=ErrorType.AGENT_ERROR,
            details=details,
            agent_name=agent_name,
            retry_possible=retry_possible
        )


class LLMError(BaseAnalysisError):
    """LLM 호출 중 발생하는 에러"""
    
    def __init__(
        self,
        message: str,
        llm_model: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if llm_model:
            details["llm_model"] = llm_model
        if status_code:
            details["status_code"] = status_code
            
        super().__init__(
            message=message,
            error_type=ErrorType.LLM_ERROR,
            details=details,
            retry_possible=status_code != 400 if status_code else True
        )


class ValidationError(BaseAnalysisError):
    """데이터 검증 에러"""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        invalid_value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if field_name:
            details["field_name"] = field_name
        if invalid_value is not None:
            details["invalid_value"] = str(invalid_value)
            
        super().__init__(
            message=message,
            error_type=ErrorType.VALIDATION_ERROR,
            details=details,
            retry_possible=False
        )


# TODO: 워크플로우 에러 클래스 구현 필요시 추가


class TimeoutError(BaseAnalysisError):
    """타임아웃 에러"""
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[int] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_type=ErrorType.TIMEOUT_ERROR,
            details=details,
            retry_possible=True
        )


class ParsingError(BaseAnalysisError):
    """응답 파싱 에러"""
    
    def __init__(
        self,
        message: str,
        raw_response: Optional[str] = None,
        expected_schema: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if raw_response:
            details["raw_response"] = raw_response[:1000]  # 첫 1000자만 저장
        if expected_schema:
            details["expected_schema"] = expected_schema
            
        super().__init__(
            message=message,
            error_type=ErrorType.PARSING_ERROR,
            details=details,
            retry_possible=True
        )


# ================================
# 보안 관리자 클래스들 (기존 security.py)
# ================================

class SecurityManager:
    """보안 관리자"""
    
    def __init__(self):
        self.rate_limit_store = defaultdict(list)
        self.blocked_ips = set()
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS 패턴
            r'javascript:',
            r'vbscript:',
            r'on\w+\s*=',  # 이벤트 핸들러
            r'eval\s*\(',
            r'exec\s*\(',
            r'(union|select|insert|update|delete|drop|create|alter)\s+',  # SQL 주입 패턴
            r'\.\./',  # 디렉토리 탐색
            r'<iframe[^>]*>',  # iframe 태그
            r'<object[^>]*>',  # object 태그
            r'<embed[^>]*>',   # embed 태그
            # LLM 프롬프트에서 정상적으로 사용되는 특수문자는 제외
        ]
    
    def sanitize_input(self, input_data: Union[str, Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        """입력 데이터 sanitization"""
        if isinstance(input_data, str):
            return self._sanitize_string(input_data)
        elif isinstance(input_data, dict):
            return {key: self.sanitize_input(value) for key, value in input_data.items()}
        elif isinstance(input_data, list):
            return [self.sanitize_input(item) for item in input_data]
        return input_data
    
    def _sanitize_string(self, text: str) -> str:
        """문자열 sanitization"""
        if not text:
            return ""
        
        # 최대 길이 제한
        if len(text) > 50000:  # 50KB 제한
            text = text[:50000]
        
        # 위험한 패턴 감지
        for pattern in self.suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"의심스러운 패턴 감지: {pattern}")
                # 위험한 패턴을 안전한 문자로 교체
                text = re.sub(pattern, '[FILTERED]', text, flags=re.IGNORECASE)
        
        # HTML 엔티티 이스케이프
        text = (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
        
        return text
    
    def sanitize_error_message(self, error_msg: str) -> str:
        """에러 메시지 sanitization"""
        if not error_msg:
            return "알 수 없는 오류가 발생했습니다"
        
        # 민감한 정보 패턴 마스킹
        sensitive_patterns = [
            r'password[=:]\s*\w+',
            r'token[=:]\s*\w+',
            r'key[=:]\s*\w+',
            r'secret[=:]\s*\w+',
            r'api[_-]?key[=:]\s*\w+',
            r'localhost:\d+',
            r'127\.0\.0\.1:\d+',
            r'file:///\S+',
            r'[a-zA-Z]:\\[\\\w\s]+',  # Windows 경로
            r'/[/\w\s]+',  # Unix 경로
        ]
        
        for pattern in sensitive_patterns:
            error_msg = re.sub(pattern, '[REDACTED]', error_msg, flags=re.IGNORECASE)
        
        # 길이 제한
        if len(error_msg) > 500:
            error_msg = error_msg[:500] + "..."
        
        return error_msg
    
    def check_rate_limit(self, client_ip: str, endpoint: str, limit: int = 60, window: int = 60) -> bool:
        """요청 빈도 제한 확인"""
        now = datetime.now()
        key = f"{client_ip}:{endpoint}"
        
        # 윈도우 시간 내의 요청만 유지
        self.rate_limit_store[key] = [
            req_time for req_time in self.rate_limit_store[key]
            if now - req_time < timedelta(seconds=window)
        ]
        
        # 현재 요청 추가
        self.rate_limit_store[key].append(now)
        
        # 제한 확인
        if len(self.rate_limit_store[key]) > limit:
            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
            return False
        
        return True
    
    def is_ip_blocked(self, client_ip: str) -> bool:
        """IP 차단 확인"""
        return client_ip in self.blocked_ips
    
    def block_ip(self, client_ip: str, reason: str = "Suspicious activity"):
        """IP 차단"""
        self.blocked_ips.add(client_ip)
        logger.warning(f"IP {client_ip} blocked: {reason}")
    
    def generate_request_id(self) -> str:
        """안전한 요청 ID 생성"""
        return secrets.token_hex(16)
    
    def hash_data(self, data: str) -> str:
        """데이터 해싱"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def validate_content_type(self, content_type: str) -> bool:
        """컨텐츠 타입 검증"""
        allowed_types = [
            'application/json',
            'application/x-www-form-urlencoded',
            'multipart/form-data'
        ]
        
        if not content_type:
            return False
        
        return any(allowed_type in content_type for allowed_type in allowed_types)
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """보안 이벤트 로깅"""
        logger.warning(f"SECURITY EVENT: {event_type}", extra={
            'event_type': event_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })


class InputValidator:
    """입력 검증기"""
    
    @staticmethod
    def validate_target_type(target_type: str) -> bool:
        """분석 대상 타입 검증"""
        allowed_types = ['company', 'industry', 'sector']
        return target_type and target_type.lower() in allowed_types
    
    @staticmethod
    def validate_target_name(target_name: str) -> bool:
        """분석 대상명 검증"""
        if not target_name or not target_name.strip():
            return False
        
        # 길이 제한
        if len(target_name) > 100:
            return False
        
        # 기본 문자만 허용 (한글, 영문, 숫자, 공백, 하이픈)
        pattern = r'^[가-힣a-zA-Z0-9\s\-\.]+$'
        return bool(re.match(pattern, target_name))
    
    @staticmethod
    def validate_symbol(symbol: Optional[str]) -> bool:
        """종목 코드 검증"""
        if not symbol:
            return True  # 옵션 필드
        
        # 길이 제한
        if len(symbol) > 20:
            return False
        
        # 영문, 숫자만 허용
        pattern = r'^[A-Za-z0-9]+$'
        return bool(re.match(pattern, symbol))
    
    @staticmethod
    def validate_report_content(content: str) -> bool:
        """리포트 내용 검증"""
        if not content or not content.strip():
            return False
        
        # 길이 제한
        if len(content) > 100000:  # 100KB 제한
            return False
        
        return True


# ================================
# 전역 인스턴스
# ================================

security_manager = SecurityManager()
input_validator = InputValidator()


# ================================
# 기존 에러 핸들러 관련 코드
# ================================

class LLMRequestError(BaseAnalysisError):
    """LLM 요청 관련 오류"""
    pass

class InvalidRequestError(BaseAnalysisError):
    """요청 형식이 올바르지 않을 때 발생하는 예외"""
    pass

# 오류 응답 포맷 함수
def format_error_response(error_code: int, error_msg: str, request: Request) -> Dict[str, Any]:
    """보안 처리된 오류 응답 포맷"""
    # 에러 메시지 sanitization
    safe_error_msg = security_manager.sanitize_error_message(error_msg)
    
    return {
        "status": "error",
        "error_code": error_code,
        "message": safe_error_msg,
        "timestamp": datetime.now().isoformat(),
        "path": request.url.path,
        "request_id": security_manager.generate_request_id()
    }

# 예외 핸들러 설정 함수
def setup_exception_handlers(app: FastAPI) -> None:
    """애플리케이션에 예외 핸들러 등록"""

    @app.exception_handler(LLMRequestError)
    async def llm_request_error_handler(request: Request, exc: LLMRequestError):
        """LLM 요청 오류 핸들러"""
        client_ip = request.client.host
        
        # 보안 이벤트 로깅
        security_manager.log_security_event("llm_request_error", {
            "client_ip": client_ip,
            "path": request.url.path,
            "error_type": "LLMRequestError"
        })
        
        return JSONResponse(
            status_code=503,
            content=format_error_response(503, "LLM 서비스 일시적 장애", request)
        )

    @app.exception_handler(InvalidRequestError)
    async def invalid_request_handler(request: Request, exc: InvalidRequestError):
        """잘못된 요청 핸들러"""
        client_ip = request.client.host
        
        # 보안 이벤트 로깅
        security_manager.log_security_event("invalid_request", {
            "client_ip": client_ip,
            "path": request.url.path,
            "error_type": "InvalidRequestError"
        })
        
        return JSONResponse(
            status_code=400,
            content=format_error_response(400, "잘못된 요청 형식", request)
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP 예외 핸들러"""
        client_ip = request.client.host
        
        # 보안 이벤트 로깅 (4xx, 5xx 에러만)
        if exc.status_code >= 400:
            security_manager.log_security_event("http_exception", {
                "client_ip": client_ip,
                "path": request.url.path,
                "status_code": exc.status_code,
                "error_type": "HTTPException"
            })
        
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(exc.status_code, exc.detail, request)
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """일반 예외 핸들러"""
        client_ip = request.client.host
        
        # 디버그를 위한 로그 추가 (에러 메시지는 sanitization)
        safe_error_msg = security_manager.sanitize_error_message(str(exc))
        logger.error(f"처리되지 않은 예외 발생: {safe_error_msg}", exc_info=True)
        
        # 보안 이벤트 로깅
        security_manager.log_security_event("unhandled_exception", {
            "client_ip": client_ip,
            "path": request.url.path,
            "error_type": type(exc).__name__
        })
        
        return JSONResponse(
            status_code=500,
            content=format_error_response(500, "서버 내부 오류가 발생했습니다", request)
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: Exception):
        """검증 오류 핸들러"""
        client_ip = request.client.host
        
        # 보안 이벤트 로깅
        security_manager.log_security_event("validation_error", {
            "client_ip": client_ip,
            "path": request.url.path,
            "error_type": "ValidationError"
        })
        
        return JSONResponse(
            status_code=422,
            content=format_error_response(422, "입력 데이터 검증 실패", request)
        )


# ================================
# 유틸리티 함수들
# ================================

def handle_agent_error(
    func_name: str,
    agent_name: str,
    error: Exception
) -> BaseAnalysisError:
    """에이전트 에러 처리"""
    if isinstance(error, BaseAnalysisError):
        return error
    
    # 일반 예외를 AgentError로 변환
    return AgentError(
        agent_name=agent_name,
        message=f"{func_name} 실행 중 오류: {str(error)}"
    )


def create_error_response(error: BaseAnalysisError) -> Dict[str, Any]:
    """에러 응답 생성"""
    return {
        "success": False,
        "error": error.to_dict(),
        "timestamp": datetime.now().isoformat()
    }


def get_security_manager() -> SecurityManager:
    """보안 관리자 인스턴스 반환"""
    return security_manager


def get_input_validator() -> InputValidator:
    """입력 검증기 인스턴스 반환"""
    return input_validator


# 추가 보안 예외 클래스들
class SecurityError(BaseAnalysisError):
    """보안 관련 오류"""
    pass

class RateLimitError(SecurityError):
    """요청 빈도 제한 오류"""
    pass

class BlockedIPError(SecurityError):
    """차단된 IP 오류"""
    pass
