"""
데이터 흐름 표준화를 위한 공통 데이터 클래스
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum


class AgentType(Enum):
    """에이전트 타입 열거형"""
    SUMMARY = "summary"
    SENTIMENT = "sentiment"
    RISK = "risk"
    GROWTH = "growth"
    ANALYSIS = "analysis"
    SUPERVISOR = "supervisor"


class ProcessingStatus(Enum):
    """처리 상태 열거형"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class StandardInput(BaseModel):
    """모든 에이전트가 공통으로 사용하는 입력 데이터 구조"""
    
    # 기본 정보
    target_type: str = Field(..., description="분석 대상 타입 (company, industry, sector)")
    target_name: str = Field(..., description="분석 대상 이름")
    symbol: Optional[str] = Field(None, description="종목 코드")
    
    # 리포트 데이터
    reports: List[Dict[str, Any]] = Field(default_factory=list, description="리포트 데이터 목록")
    
    # 메타데이터
    request_id: Optional[str] = Field(None, description="요청 고유 ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="요청 시각")
    
    # 설정
    temperature: float = Field(0.7, description="LLM 온도 설정")
    max_tokens: int = Field(4096, description="최대 토큰 수")
    
    # 추가 설정
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트 정보")
    
    @validator('target_type')
    def validate_target_type(cls, v):
        valid_types = ['company', 'industry', 'sector']
        if v.lower() not in valid_types:
            raise ValueError(f"target_type은 다음 중 하나여야 합니다: {valid_types}")
        return v.lower()
    
    @validator('reports')
    def validate_reports(cls, v):
        if not v:
            return v
        
        for report in v:
            if not isinstance(report, dict):
                raise ValueError("리포트는 딕셔너리 형태여야 합니다")
            if 'content' not in report:
                raise ValueError("리포트에 'content' 필드가 필요합니다")
        
        return v


class StandardOutput(BaseModel):
    """모든 에이전트가 공통으로 사용하는 출력 데이터 구조"""
    
    # 기본 정보
    agent_type: AgentType = Field(..., description="에이전트 타입")
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    symbol: Optional[str] = Field(None, description="종목 코드")
    
    # 처리 상태
    status: ProcessingStatus = Field(..., description="처리 상태")
    success: bool = Field(..., description="성공 여부")
    
    # 결과 데이터
    result: Dict[str, Any] = Field(default_factory=dict, description="분석 결과")
    
    # 메타데이터
    request_id: Optional[str] = Field(None, description="요청 고유 ID")
    processing_time: Optional[float] = Field(None, description="처리 시간 (초)")
    generated_at: datetime = Field(default_factory=datetime.now, description="생성 시각")
    
    # 에러 정보
    error: Optional[Dict[str, Any]] = Field(None, description="에러 정보")
    warnings: List[str] = Field(default_factory=list, description="경고 메시지")
    
    # 품질 메트릭
    confidence_score: Optional[float] = Field(None, description="신뢰도 점수 (0-1)")
    quality_metrics: Dict[str, Any] = Field(default_factory=dict, description="품질 메트릭")


class ReportData(BaseModel):
    """표준화된 리포트 데이터 구조"""
    
    content: str = Field(..., description="리포트 내용")
    info: Dict[str, Any] = Field(default_factory=dict, description="리포트 메타정보")
    
    # 추가 필드
    source: Optional[str] = Field(None, description="리포트 출처")
    date: Optional[datetime] = Field(None, description="리포트 날짜")
    author: Optional[str] = Field(None, description="작성자")
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("리포트 내용이 비어있습니다")
        return v.strip()


class AgentConfig(BaseModel):
    """에이전트 설정 구조"""
    
    model_config = {"protected_namespaces": ()}  # Pydantic 경고 해결
    
    agent_type: AgentType = Field(..., description="에이전트 타입")
    llm_model: str = Field(..., description="사용할 LLM 모델명")
    temperature: float = Field(0.7, description="온도 설정")
    max_tokens: int = Field(4096, description="최대 토큰 수")
    timeout: int = Field(300, description="타임아웃 (초)")
    max_retries: int = Field(3, description="최대 재시도 횟수")
    
    # 에이전트별 특수 설정
    special_params: Dict[str, Any] = Field(default_factory=dict, description="에이전트별 특수 파라미터")


# TODO: 워크플로우 상태 관리 기능 구현 필요시 추가


def convert_to_standard_input(
    target_type: str,
    target_name: str,
    reports: List[Dict[str, Any]],
    symbol: Optional[str] = None,
    **kwargs
) -> StandardInput:
    """기존 데이터를 StandardInput으로 변환"""
    
    # 리포트 데이터 변환
    standard_reports = []
    for report in reports:
        if isinstance(report, dict):
            standard_reports.append(report)
        else:
            # 문자열인 경우 content로 변환
            standard_reports.append({"content": str(report)})
    
    return StandardInput(
        target_type=target_type,
        target_name=target_name,
        symbol=symbol,
        reports=standard_reports,
        **kwargs
    )


def create_agent_result(
    agent_type: AgentType,
    target_type: str,
    target_name: str,
    result: Dict[str, Any],
    success: bool = True,
    symbol: Optional[str] = None,
    **kwargs
) -> StandardOutput:
    """에이전트 결과 생성 헬퍼"""
    
    status = ProcessingStatus.COMPLETED if success else ProcessingStatus.FAILED
    
    return StandardOutput(
        agent_type=agent_type,
        target_type=target_type,
        target_name=target_name,
        symbol=symbol,
        status=status,
        success=success,
        result=result,
        **kwargs
    ) 