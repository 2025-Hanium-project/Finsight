"""
에러 처리 시스템

기능:
- 커스텀 예외 클래스
- 에러 핸들링
- 보안 관리
- 입력 검증
- 로깅 및 모니터링
"""

import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import json
import re
import hashlib
import time
from collections import defaultdict, deque
import threading
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# ============================================================================
# 커스텀 예외 클래스
# ============================================================================

class BaseAnalysisError(Exception):
    """기본 분석 에러 클래스"""
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "ANALYSIS_ERROR"
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)

class AgentError(BaseAnalysisError):
    """에이전트 관련 에러"""
    def __init__(self, message: str, agent_name: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "AGENT_ERROR", details)
        self.agent_name = agent_name

class CollaborationError(BaseAnalysisError):
    """협업 시스템 관련 에러"""
    def __init__(self, message: str, collaboration_type: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "COLLABORATION_ERROR", details)
        self.collaboration_type = collaboration_type

class WorkflowError(BaseAnalysisError):
    """워크플로우 관련 에러"""
    def __init__(self, message: str, workflow_type: str = None, step: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "WORKFLOW_ERROR", details)
        self.workflow_type = workflow_type
        self.step = step

class LLMError(BaseAnalysisError):
    """LLM 관련 에러"""
    def __init__(self, message: str, provider: str = None, model: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "LLM_ERROR", details)
        self.provider = provider
        self.model = model

class ParsingError(BaseAnalysisError):
    """파싱 관련 에러"""
    def __init__(self, message: str, content_type: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "PARSING_ERROR", details)
        self.content_type = content_type

class ValidationError(BaseAnalysisError):
    """검증 관련 에러"""
    def __init__(self, message: str, field: str = None, value: Any = None, details: Dict[str, Any] = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field
        self.value = value

class TimeoutError(BaseAnalysisError):
    """타임아웃 관련 에러"""
    def __init__(self, message: str, operation: str = None, timeout: float = None, details: Dict[str, Any] = None):
        super().__init__(message, "TIMEOUT_ERROR", details)
        self.operation = operation
        self.timeout = timeout

class SecurityError(BaseAnalysisError):
    """보안 관련 에러"""
    def __init__(self, message: str, security_type: str = None, details: Dict[str, Any] = None):
        super().__init__(message, "SECURITY_ERROR", details)
        self.security_type = security_type

# ============================================================================
# 보안 관리자
# ============================================================================

class SecurityManager:
    """보안 관리자"""
    
    def __init__(self):
        self.blocked_ips = set()
        self.rate_limit_data = defaultdict(lambda: deque(maxlen=100))
        self.security_events = deque(maxlen=1000)
        self.request_ids = set()
        self.lock = threading.Lock()
        
    def generate_request_id(self) -> str:
        """요청 ID 생성"""
        timestamp = str(int(time.time() * 1000000))
        random_part = hashlib.md5(f"{timestamp}{time.time()}".encode()).hexdigest()[:8]
        request_id = f"req_{timestamp}_{random_part}"
        
        with self.lock:
            self.request_ids.add(request_id)
        return request_id
    
    def is_ip_blocked(self, ip: str) -> bool:
        """IP 차단 여부 확인"""
        return ip in self.blocked_ips
    
    def block_ip(self, ip: str, reason: str = "Manual block"):
        """IP 차단"""
        with self.lock:
            self.blocked_ips.add(ip)
        self.log_security_event("ip_blocked", {"ip": ip, "reason": reason})
    
    def unblock_ip(self, ip: str):
        """IP 차단 해제"""
        with self.lock:
            self.blocked_ips.discard(ip)
        self.log_security_event("ip_unblocked", {"ip": ip})
    
    def check_rate_limit(self, ip: str, endpoint: str) -> bool:
        """Rate limiting 확인"""
        current_time = time.time()
        key = f"{ip}:{endpoint}"
        
        with self.lock:
            # 1분 이내 요청 수 확인
            recent_requests = [req_time for req_time in self.rate_limit_data[key] 
                             if current_time - req_time < 60]
            
            if len(recent_requests) >= 100:  # 분당 100회 제한
                self.log_security_event("rate_limit_exceeded", {
                    "ip": ip, "endpoint": endpoint, "count": len(recent_requests)
                })
            return False
        
            self.rate_limit_data[key].append(current_time)
        return True
    
    def validate_content_type(self, content_type: str) -> bool:
        """Content-Type 검증"""
        allowed_types = [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data"
        ]
        return any(allowed_type in content_type for allowed_type in allowed_types)
    
    def sanitize_error_message(self, message: str) -> str:
        """에러 메시지 sanitization"""
        # 민감한 정보 제거
        sanitized = re.sub(r'password["\']?\s*[:=]\s*["\'][^"\']*["\']', 'password="***"', message)
        sanitized = re.sub(r'api_key["\']?\s*[:=]\s*["\'][^"\']*["\']', 'api_key="***"', sanitized)
        sanitized = re.sub(r'token["\']?\s*[:=]\s*["\'][^"\']*["\']', 'token="***"', sanitized)
        
        # 파일 경로 정보 제거
        sanitized = re.sub(r'[A-Za-z]:\\[^\s]+', '[FILE_PATH]', sanitized)
        sanitized = re.sub(r'/[^\s]+', '[FILE_PATH]', sanitized)
        
        return sanitized
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """보안 이벤트 로깅"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        with self.lock:
            self.security_events.append(event)
        
        logger.warning(f"보안 이벤트: {event_type} - {details}")
    
    def get_security_status(self) -> Dict[str, Any]:
        """보안 상태 반환"""
        with self.lock:
            return {
                "blocked_ips_count": len(self.blocked_ips),
                "blocked_ips": list(self.blocked_ips),
                "recent_security_events": list(self.security_events)[-10:],
                "rate_limit_data": {k: len(v) for k, v in self.rate_limit_data.items()}
            }

# ============================================================================
# 입력 검증기
# ============================================================================

class InputValidator:
    """입력 검증기"""
    
    def __init__(self):
        self.max_input_size = 1024 * 1024  # 1MB
        self.max_reports_per_request = 10
        self.allowed_target_types = ['company', 'industry', 'sector']
        
    def validate_standard_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """StandardInput 검증"""
        errors = []
        
        # 필수 필드 검증
        if 'target_type' not in data:
            errors.append("target_type 필드가 필요합니다")
        elif data['target_type'] not in self.allowed_target_types:
            errors.append(f"target_type은 다음 중 하나여야 합니다: {self.allowed_target_types}")
        
        if 'target_name' not in data:
            errors.append("target_name 필드가 필요합니다")
        elif not isinstance(data['target_name'], str) or len(data['target_name'].strip()) == 0:
            errors.append("target_name은 비어있지 않은 문자열이어야 합니다")
        
        # 선택적 필드 검증
        if 'symbol' in data and data['symbol']:
            if not isinstance(data['symbol'], str):
                errors.append("symbol은 문자열이어야 합니다")
        
        if 'reports' in data:
            if not isinstance(data['reports'], list):
                errors.append("reports는 리스트여야 합니다")
            elif len(data['reports']) > self.max_reports_per_request:
                errors.append(f"reports는 최대 {self.max_reports_per_request}개까지 허용됩니다")
        
        if 'context' in data and not isinstance(data['context'], dict):
            errors.append("context는 딕셔너리여야 합니다")
        
        if errors:
            raise ValidationError(
                message="입력 검증 실패",
                details={"errors": errors, "input_data": data}
            )
        
        return data
    
    def validate_agent_request(self, agent_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 요청 검증"""
        # 기본 검증
        validated_data = self.validate_standard_input(data)
        
        # 에이전트별 특화 검증
        if agent_name in ['financial_statement_agent', 'market_data_agent']:
            if 'symbol' not in data or not data['symbol']:
                raise ValidationError(
                    message=f"{agent_name}는 symbol 필드가 필요합니다",
                    field="symbol"
                )
        
        if agent_name in ['securities_report_agent']:
            if 'reports' not in data or not data['reports']:
                raise ValidationError(
                    message=f"{agent_name}는 reports 필드가 필요합니다",
                    field="reports"
                )
        
        return validated_data
    
    def sanitize_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """입력 데이터 sanitization"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # XSS 방지
                sanitized_value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE)
                sanitized_value = re.sub(r'<[^>]*>', '', sanitized_value)
                sanitized[key] = sanitized_value
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_input(value)
            elif isinstance(value, list):
                sanitized[key] = [self.sanitize_input(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value
        
        return sanitized

# ============================================================================
# 에러 핸들러
# ============================================================================

def handle_agent_error(error: Exception, agent_name: str = None) -> Dict[str, Any]:
    """에이전트 에러 처리"""
    error_info = {
        "error_type": type(error).__name__,
        "message": str(error),
        "timestamp": datetime.now().isoformat(),
        "agent_name": agent_name
    }
    
    if isinstance(error, AgentError):
        error_info.update({
            "error_code": error.error_code,
            "details": error.details
        })
    elif isinstance(error, LLMError):
        error_info.update({
            "provider": error.provider,
            "model": error.model
        })
    elif isinstance(error, TimeoutError):
        error_info.update({
            "operation": error.operation,
            "timeout": error.timeout
        })
    
    logger.error(f"에이전트 에러: {error_info}")
    return error_info

def handle_collaboration_error(error: Exception, collaboration_type: str = None) -> Dict[str, Any]:
    """협업 시스템 에러 처리"""
    error_info = {
        "error_type": type(error).__name__,
        "message": str(error),
        "timestamp": datetime.now().isoformat(),
        "collaboration_type": collaboration_type
    }
    
    if isinstance(error, CollaborationError):
        error_info.update({
            "error_code": error.error_code,
            "details": error.details
        })
    
    logger.error(f"협업 시스템 에러: {error_info}")
    return error_info

def handle_workflow_error(error: Exception, workflow_type: str = None, step: str = None) -> Dict[str, Any]:
    """워크플로우 에러 처리"""
    error_info = {
        "error_type": type(error).__name__,
        "message": str(error),
        "timestamp": datetime.now().isoformat(),
        "workflow_type": workflow_type,
        "step": step
    }
    
    if isinstance(error, WorkflowError):
        error_info.update({
            "error_code": error.error_code,
            "details": error.details
        })
    
    logger.error(f"워크플로우 에러: {error_info}")
    return error_info

# ============================================================================
# FastAPI 예외 핸들러 설정
# ============================================================================

def setup_exception_handlers(app):
    """FastAPI 예외 핸들러 설정"""
    
    @app.exception_handler(BaseAnalysisError)
    async def analysis_error_handler(request: Request, exc: BaseAnalysisError):
        """분석 에러 핸들러"""
        error_response = {
            "error": exc.error_code,
            "message": exc.message,
            "timestamp": exc.timestamp.isoformat(),
            "details": exc.details
        }
        
        logger.error(f"분석 에러: {error_response}")
        return JSONResponse(status_code=500, content=error_response)
    
    @app.exception_handler(AgentError)
    async def agent_error_handler(request: Request, exc: AgentError):
        """에이전트 에러 핸들러"""
        error_response = {
            "error": "AGENT_ERROR",
            "message": exc.message,
            "agent_name": exc.agent_name,
            "timestamp": exc.timestamp.isoformat(),
            "details": exc.details
        }
        
        logger.error(f"에이전트 에러: {error_response}")
        return JSONResponse(status_code=500, content=error_response)
    
    @app.exception_handler(CollaborationError)
    async def collaboration_error_handler(request: Request, exc: CollaborationError):
        """협업 에러 핸들러"""
        error_response = {
            "error": "COLLABORATION_ERROR",
            "message": exc.message,
            "collaboration_type": exc.collaboration_type,
            "timestamp": exc.timestamp.isoformat(),
            "details": exc.details
        }
        
        logger.error(f"협업 에러: {error_response}")
        return JSONResponse(status_code=500, content=error_response)
    
    @app.exception_handler(WorkflowError)
    async def workflow_error_handler(request: Request, exc: WorkflowError):
        """워크플로우 에러 핸들러"""
        error_response = {
            "error": "WORKFLOW_ERROR",
            "message": exc.message,
            "workflow_type": exc.workflow_type,
            "step": exc.step,
            "timestamp": exc.timestamp.isoformat(),
            "details": exc.details
        }
        
        logger.error(f"워크플로우 에러: {error_response}")
        return JSONResponse(status_code=500, content=error_response)
    
    @app.exception_handler(LLMError)
    async def llm_error_handler(request: Request, exc: LLMError):
        """LLM 에러 핸들러"""
        error_response = {
            "error": "LLM_ERROR",
            "message": exc.message,
            "provider": exc.provider,
            "model": exc.model,
            "timestamp": exc.timestamp.isoformat(),
            "details": exc.details
        }
        
        logger.error(f"LLM 에러: {error_response}")
        return JSONResponse(status_code=500, content=error_response)
    
    @app.exception_handler(TimeoutError)
    async def timeout_error_handler(request: Request, exc: TimeoutError):
        """타임아웃 에러 핸들러"""
        error_response = {
            "error": "TIMEOUT_ERROR",
            "message": exc.message,
            "operation": exc.operation,
            "timeout": exc.timeout,
            "timestamp": exc.timestamp.isoformat(),
            "details": exc.details
        }
        
        logger.error(f"타임아웃 에러: {error_response}")
        return JSONResponse(status_code=408, content=error_response)

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        """검증 에러 핸들러"""
        error_response = {
            "error": "VALIDATION_ERROR",
            "message": exc.message,
            "field": exc.field,
            "value": str(exc.value) if exc.value else None,
            "timestamp": exc.timestamp.isoformat(),
            "details": exc.details
        }
        
        logger.error(f"검증 에러: {error_response}")
        return JSONResponse(status_code=400, content=error_response)
    
    @app.exception_handler(SecurityError)
    async def security_error_handler(request: Request, exc: SecurityError):
        """보안 에러 핸들러"""
        error_response = {
            "error": "SECURITY_ERROR",
            "message": "보안 위반이 감지되었습니다",
            "security_type": exc.security_type,
            "timestamp": exc.timestamp.isoformat()
        }
        
        logger.error(f"보안 에러: {error_response}")
        return JSONResponse(status_code=403, content=error_response)

# ============================================================================
# 전역 인스턴스
# ============================================================================

_security_manager = None
_input_validator = None

def get_security_manager() -> SecurityManager:
    """보안 관리자 인스턴스 반환"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager

def get_input_validator() -> InputValidator:
    """입력 검증기 인스턴스 반환"""
    global _input_validator
    if _input_validator is None:
        _input_validator = InputValidator()
    return _input_validator

# ============================================================================
# 유틸리티 함수
# ============================================================================

def log_error_with_context(error: Exception, context: Dict[str, Any] = None):
    """컨텍스트와 함께 에러 로깅"""
    error_info = {
        "error_type": type(error).__name__,
        "message": str(error),
        "timestamp": datetime.now().isoformat(),
        "traceback": traceback.format_exc(),
        "context": context or {}
    }
    
    logger.error(f"에러 발생: {json.dumps(error_info, indent=2, default=str)}")
    return error_info

def create_error_response(error: Exception, include_traceback: bool = False) -> Dict[str, Any]:
    """에러 응답 생성"""
    response = {
        "error": type(error).__name__,
        "message": str(error),
        "timestamp": datetime.now().isoformat()
    }
    
    if include_traceback:
        response["traceback"] = traceback.format_exc()
    
    return response
