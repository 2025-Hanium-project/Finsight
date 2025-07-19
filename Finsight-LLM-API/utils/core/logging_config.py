"""
로깅 설정 및 관리

기능:
- 로깅 설정 구성
- 로그 레벨 관리
- 로그 포맷터 설정
- 로그 핸들러 관리
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """컬러 로그 포맷터"""
    
    # 색상 코드
    COLORS = {
        'DEBUG': '\033[36m',    # 청록색
        'INFO': '\033[32m',     # 초록색
        'WARNING': '\033[33m',  # 노란색
        'ERROR': '\033[31m',    # 빨간색
        'CRITICAL': '\033[35m', # 자주색
        'RESET': '\033[0m'      # 리셋
    }
    
    def format(self, record):
        # 로그 레벨에 따른 색상 적용
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """구조화된 로그 포맷터"""
    
    def format(self, record):
        # 구조화된 로그 포맷
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 예외 정보 추가
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # 추가 필드들
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 
                          'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    use_colors: bool = True,
    structured_logging: bool = False
) -> None:
    """
    로깅 설정
    
    Args:
        log_level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 로그 파일 경로 (None이면 파일 로깅 비활성화)
        max_bytes: 로그 파일 최대 크기
        backup_count: 백업 파일 개수
        use_colors: 컬러 로그 사용 여부
        structured_logging: 구조화된 로깅 사용 여부
    """
    import json
    
    # 로그 레벨 설정
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    
    if structured_logging:
        console_formatter = StructuredFormatter()
    else:
        if use_colors:
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 설정 (선택적)
    if log_file:
        # 로그 디렉토리 생성
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 로테이팅 파일 핸들러
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        
        if structured_logging:
            file_formatter = StructuredFormatter()
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # 특정 로거들의 레벨 설정
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    
    logging.info(f"로깅 설정 완료 - 레벨: {log_level}, 파일: {log_file or '없음'}")


def get_logger(name: str) -> logging.Logger:
    """
    로거 인스턴스 반환
    
    Args:
        name: 로거 이름
        
    Returns:
        로거 인스턴스
    """
    return logging.getLogger(name)


def set_log_level(logger_name: str, level: str) -> None:
    """
    특정 로거의 레벨 설정
    
    Args:
        logger_name: 로거 이름
        level: 로그 레벨
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger(logger_name).setLevel(numeric_level)


def add_log_context(logger: logging.Logger, context: Dict[str, Any]) -> None:
    """
    로그 컨텍스트 추가
    
    Args:
        logger: 로거 인스턴스
        context: 컨텍스트 정보
    """
    for key, value in context.items():
        setattr(logger, key, value)


class LogContext:
    """로그 컨텍스트 관리자"""
    
    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context
        self.original_attributes = {}
    
    def __enter__(self):
        # 기존 속성 저장
        for key in self.context.keys():
            if hasattr(self.logger, key):
                self.original_attributes[key] = getattr(self.logger, key)
        
        # 새 컨텍스트 설정
        for key, value in self.context.items():
            setattr(self.logger, key, value)
        
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 원래 속성 복원
        for key, value in self.original_attributes.items():
            setattr(self.logger, key, value)
        
        # 새로 추가된 속성 제거
        for key in self.context.keys():
            if key not in self.original_attributes and hasattr(self.logger, key):
                delattr(self.logger, key)


def create_log_context(logger: logging.Logger, **context) -> LogContext:
    """
    로그 컨텍스트 생성
    
    Args:
        logger: 로거 인스턴스
        **context: 컨텍스트 정보
        
    Returns:
        로그 컨텍스트 관리자
    """
    return LogContext(logger, context)


# 성능 로깅 유틸리티
class PerformanceLogger:
    """성능 로깅 유틸리티"""
    
    def __init__(self, logger: logging.Logger, operation_name: str):
        self.logger = logger
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"{self.operation_name} 시작")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            if exc_type:
                self.logger.error(f"{self.operation_name} 실패 (소요시간: {duration:.2f}초)")
            else:
                self.logger.info(f"{self.operation_name} 완료 (소요시간: {duration:.2f}초)")


def log_performance(logger: logging.Logger, operation_name: str):
    """
    성능 로깅 데코레이터
    
    Args:
        logger: 로거 인스턴스
        operation_name: 작업 이름
        
    Returns:
        성능 로깅 컨텍스트 관리자
    """
    return PerformanceLogger(logger, operation_name)


# 에러 로깅 유틸리티
def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """
    에러 로깅
    
    Args:
        logger: 로거 인스턴스
        error: 발생한 예외
        context: 추가 컨텍스트 정보
    """
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'error_traceback': getattr(error, '__traceback__', None)
    }
    
    if context:
        error_info.update(context)
    
    logger.error(f"에러 발생: {error_info}")


# 구조화된 로깅 유틸리티
def log_structured(logger: logging.Logger, level: str, message: str, **kwargs):
    """
    구조화된 로깅
    
    Args:
        logger: 로거 인스턴스
        level: 로그 레벨
        message: 로그 메시지
        **kwargs: 추가 필드들
    """
    log_data = {
        'message': message,
        'timestamp': datetime.now().isoformat(),
        **kwargs
    }
    
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(json.dumps(log_data, ensure_ascii=False))


# 로그 필터
class AgentLogFilter(logging.Filter):
    """에이전트 로그 필터"""
    
    def __init__(self, agent_name: str):
        super().__init__()
        self.agent_name = agent_name
    
    def filter(self, record):
        return self.agent_name in record.name


class CollaborationLogFilter(logging.Filter):
    """협업 로그 필터"""
    
    def __init__(self):
        super().__init__()
    
    def filter(self, record):
        return 'collaboration' in record.name.lower() or 'workflow' in record.name.lower()


# 로그 통계
class LogStatistics:
    """로그 통계 관리"""
    
    def __init__(self):
        self.total_logs = 0
        self.log_counts = {
            'DEBUG': 0,
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0
        }
        self.error_logs = []
    
    def add_log(self, level: str, message: str, error: Exception = None):
        """로그 추가"""
        self.total_logs += 1
        self.log_counts[level] += 1
        
        if error:
            self.error_logs.append({
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': message,
                'error': str(error)
            })
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 반환"""
        return {
            'total_logs': self.total_logs,
            'log_counts': self.log_counts,
            'error_count': len(self.error_logs),
            'recent_errors': self.error_logs[-10:] if self.error_logs else []
        }


# 전역 로그 통계 인스턴스
_log_statistics = LogStatistics()

def get_log_statistics() -> LogStatistics:
    """로그 통계 인스턴스 반환"""
    return _log_statistics 