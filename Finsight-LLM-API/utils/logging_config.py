"""
통합 로깅 시스템
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import json

from config import (
    LOGS_PATH, LOG_LEVEL, LOG_FORMAT, LOG_MAX_SIZE, LOG_BACKUP_COUNT,
    ENABLE_PERFORMANCE_MONITORING, SLOW_REQUEST_THRESHOLD
)


class CustomFormatter(logging.Formatter):
    """커스텀 포맷터 - 색상 및 구조화된 로깅"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # 청록색
        'INFO': '\033[32m',     # 녹색
        'WARNING': '\033[33m',  # 노란색
        'ERROR': '\033[31m',    # 빨간색
        'CRITICAL': '\033[35m', # 자주색
        'RESET': '\033[0m'      # 리셋
    }
    
    def format(self, record):
        # 색상 추가 (콘솔 출력용)
        if hasattr(record, 'color') and record.color:
            color = self.COLORS.get(record.levelname, '')
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        
        # 구조화된 정보 추가
        if hasattr(record, 'agent_name'):
            record.msg = f"[{record.agent_name}] {record.msg}"
        
        if hasattr(record, 'processing_time'):
            record.msg = f"{record.msg} (처리시간: {record.processing_time:.3f}s)"
        
        return super().format(record)


class PerformanceLogger:
    """성능 모니터링 로거"""
    
    def __init__(self, logger_name: str = "performance"):
        self.logger = logging.getLogger(logger_name)
        self.slow_requests = []
    
    def log_request(self, 
                   method: str, 
                   path: str, 
                   status_code: int, 
                   processing_time: float,
                   agent_name: Optional[str] = None):
        """요청 성능 로깅"""
        
        log_data = {
            'method': method,
            'path': path,
            'status_code': status_code,
            'processing_time': processing_time,
            'agent_name': agent_name,
            'timestamp': datetime.now().isoformat()
        }
        
        if processing_time > SLOW_REQUEST_THRESHOLD:
            self.logger.warning(
                f"느린 요청 감지: {method} {path} - {processing_time:.3f}s",
                extra=log_data
            )
            self.slow_requests.append(log_data)
        else:
            self.logger.info(
                f"요청 완료: {method} {path} - {processing_time:.3f}s",
                extra=log_data
            )
    
    def log_agent_performance(self, 
                            agent_name: str, 
                            operation: str, 
                            processing_time: float,
                            success: bool = True):
        """에이전트 성능 로깅"""
        
        log_data = {
            'agent_name': agent_name,
            'operation': operation,
            'processing_time': processing_time,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        if processing_time > 30:  # 30초 이상
            self.logger.warning(
                f"에이전트 느린 처리: {agent_name}.{operation} - {processing_time:.3f}s",
                extra=log_data
            )
        else:
            self.logger.info(
                f"에이전트 완료: {agent_name}.{operation} - {processing_time:.3f}s",
                extra=log_data
            )
    
    def get_slow_requests(self) -> List[Dict[str, Any]]:
        """느린 요청 목록 반환"""
        return self.slow_requests.copy()


class AgentLogger:
    """에이전트 전용 로거"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")
        
        # 성능 로거
        self.perf_logger = PerformanceLogger(f"performance.{agent_name}")
    
    def info(self, message: str, **kwargs):
        """정보 로깅"""
        self.logger.info(message, extra={'agent_name': self.agent_name, **kwargs})
    
    def warning(self, message: str, **kwargs):
        """경고 로깅"""
        self.logger.warning(message, extra={'agent_name': self.agent_name, **kwargs})
    
    def error(self, message: str, **kwargs):
        """에러 로깅"""
        self.logger.error(message, extra={'agent_name': self.agent_name, **kwargs})
    
    def debug(self, message: str, **kwargs):
        """디버그 로깅"""
        self.logger.debug(message, extra={'agent_name': self.agent_name, **kwargs})
    
    def log_start(self, operation: str, **kwargs):
        """작업 시작 로깅"""
        self.info(f"{operation} 시작", **kwargs)
    
    def log_completion(self, operation: str, processing_time: float, **kwargs):
        """작업 완료 로깅"""
        self.info(f"{operation} 완료", processing_time=processing_time, **kwargs)
        
        if ENABLE_PERFORMANCE_MONITORING:
            self.perf_logger.log_agent_performance(
                self.agent_name, operation, processing_time, True
            )
    
    def log_error(self, operation: str, error: Exception, **kwargs):
        """에러 로깅"""
        self.error(f"{operation} 실패: {str(error)}", **kwargs)
        
        if ENABLE_PERFORMANCE_MONITORING:
            self.perf_logger.log_agent_performance(
                self.agent_name, operation, 0, False
            )


def setup_logging():
    """로깅 시스템 초기화"""
    
    # 로그 디렉토리 생성
    os.makedirs(LOGS_PATH, exist_ok=True)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # 기존 핸들러 정리
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    console_formatter = CustomFormatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 (일반 로그)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=Path(LOGS_PATH) / "app.log",
        maxBytes=LOG_MAX_SIZE,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # 에러 전용 핸들러
    error_handler = logging.handlers.RotatingFileHandler(
        filename=Path(LOGS_PATH) / "error.log",
        maxBytes=LOG_MAX_SIZE,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # 성능 로그 핸들러
    if ENABLE_PERFORMANCE_MONITORING:
        perf_handler = logging.handlers.RotatingFileHandler(
            filename=Path(LOGS_PATH) / "performance.log",
            maxBytes=LOG_MAX_SIZE,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(file_formatter)
        
        # 성능 로거에만 추가
        perf_logger = logging.getLogger("performance")
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)
    
    # 외부 라이브러리 로깅 레벨 조정
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("통합 로깅 시스템 초기화 완료")


def get_agent_logger(agent_name: str) -> AgentLogger:
    """에이전트 로거 생성"""
    return AgentLogger(agent_name)


def get_performance_logger() -> PerformanceLogger:
    """성능 로거 생성"""
    return PerformanceLogger()


# TODO: 워크플로우 이벤트 로깅 기능 구현 필요시 추가


def log_llm_request(llm_model: str, prompt_length: int, response_length: int, processing_time: float):
    """LLM 요청 로깅"""
    logger = logging.getLogger("llm")
    logger.info(
        f"LLM 요청 완료: {llm_model}",
        extra={
            'llm_model': llm_model,
            'prompt_length': prompt_length,
            'response_length': response_length,
            'processing_time': processing_time
        }
    )


# 모듈 로드 시 로깅 시스템 초기화
setup_logging() 