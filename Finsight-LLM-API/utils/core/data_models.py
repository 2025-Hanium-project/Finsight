"""
데이터 모델 및 스키마 정의

기능:
- Pydantic 모델 정의
- API 요청/응답 스키마
- 협업 메시지 모델
- 워크플로우 모델
"""

import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field, validator


class ProcessingStatus(Enum):
    """처리 상태 열거형"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(Enum):
    """에이전트 타입 열거형"""
    RISK_ASSESSMENT = "risk_assessment"
    FINANCIAL_STATEMENT = "financial_statement"
    NEWS_ANALYSIS = "news_analysis"
    MARKET_DATA = "market_data"
    GROWTH_ANALYSIS = "growth_analysis"
    PEER_COMPARISON = "peer_comparison"
    VALUATION = "valuation"
    SUPERVISOR = "supervisor"


class CollaborationType(Enum):
    """협업 타입 열거형"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    PEER_TO_PEER = "peer_to_peer"


class MessagePriority(Enum):
    """메시지 우선순위 열거형"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class KnowledgeType(Enum):
    """지식 타입 열거형"""
    FINANCIAL_INSIGHT = "financial_insight"
    MARKET_ANALYSIS = "market_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    NEWS_SENTIMENT = "news_sentiment"
    TECHNICAL_INDICATOR = "technical_indicator"
    FUNDAMENTAL_DATA = "fundamental_data"


# 표준 입력/출력 모델
class StandardInput(BaseModel):
    """표준 입력 모델"""
    target_type: str = Field(..., description="타겟 타입 (company, sector, market)")
    target_name: str = Field(..., description="타겟 이름")
    symbol: Optional[str] = Field(default=None, description="심볼")
    reports: List[Dict[str, Any]] = Field(default_factory=list, description="리포트 목록")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StandardOutput(BaseModel):
    """표준 출력 모델"""
    agent_type: AgentType = Field(..., description="에이전트 타입")
    target_type: str = Field(..., description="타겟 타입")
    target_name: str = Field(..., description="타겟 이름")
    symbol: Optional[str] = Field(default=None, description="심볼")
    status: ProcessingStatus = Field(..., description="처리 상태")
    success: bool = Field(..., description="성공 여부")
    result: Dict[str, Any] = Field(..., description="처리 결과")
    execution_time: float = Field(..., description="실행 시간 (초)")
    timestamp: datetime = Field(default_factory=datetime.now, description="타임스탬프")
    error_message: Optional[str] = Field(default=None, description="에러 메시지")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 협업 메시지 모델
class CollaborationMessage(BaseModel):
    """협업 메시지 모델"""
    id: str = Field(..., description="메시지 고유 ID")
    source_agent: str = Field(..., description="소스 에이전트")
    target_agent: str = Field(..., description="타겟 에이전트")
    message_type: str = Field(..., description="메시지 타입")
    content: Dict[str, Any] = Field(default_factory=dict, description="메시지 내용")
    priority: MessagePriority = Field(default=MessagePriority.NORMAL, description="우선순위")
    timestamp: datetime = Field(default_factory=datetime.now, description="타임스탬프")
    status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="처리 상태")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 지식 공유 모델
class KnowledgeShare(BaseModel):
    """지식 공유 모델"""
    id: str = Field(..., description="지식 고유 ID")
    agent: str = Field(..., description="에이전트 이름")
    knowledge_type: KnowledgeType = Field(..., description="지식 타입")
    content: Dict[str, Any] = Field(..., description="지식 내용")
    confidence: float = Field(..., ge=0.0, le=1.0, description="신뢰도")
    timestamp: datetime = Field(default_factory=datetime.now, description="타임스탬프")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 워크플로우 모델
class WorkflowStep(BaseModel):
    """워크플로우 단계 모델"""
    step_name: str = Field(..., description="단계 이름")
    agent_name: str = Field(..., description="에이전트 이름")
    input_mapping: Dict[str, str] = Field(default_factory=dict, description="입력 매핑")
    output_mapping: Dict[str, str] = Field(default_factory=dict, description="출력 매핑")
    timeout: int = Field(default=30, description="타임아웃 (초)")
    retry_count: int = Field(default=3, description="재시도 횟수")
    is_required: bool = Field(default=True, description="필수 단계 여부")
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v < 1:
            raise ValueError('타임아웃은 1초 이상이어야 합니다')
        return v
    
    @validator('retry_count')
    def validate_retry_count(cls, v):
        if v < 0:
            raise ValueError('재시도 횟수는 0 이상이어야 합니다')
        return v


class WorkflowConfig(BaseModel):
    """워크플로우 설정 모델"""
    workflow_name: str = Field(..., description="워크플로우 이름")
    description: str = Field(default="", description="워크플로우 설명")
    steps: List[WorkflowStep] = Field(..., description="워크플로우 단계들")
    collaboration_type: CollaborationType = Field(default=CollaborationType.SEQUENTIAL, description="협업 타입")
    max_execution_time: int = Field(default=300, description="최대 실행 시간 (초)")
    error_handling: str = Field(default="continue", description="에러 처리 방식")
    
    @validator('max_execution_time')
    def validate_max_execution_time(cls, v):
        if v < 10:
            raise ValueError('최대 실행 시간은 10초 이상이어야 합니다')
        return v


# API 요청/응답 모델
class AgentRequest(BaseModel):
    """에이전트 요청 모델"""
    agent_name: str = Field(..., description="에이전트 이름")
    input_data: Dict[str, Any] = Field(..., description="입력 데이터")
    collaboration_data: Dict[str, Any] = Field(default_factory=dict, description="협업 데이터")
    priority: MessagePriority = Field(default=MessagePriority.NORMAL, description="우선순위")
    timeout: int = Field(default=30, description="타임아웃 (초)")
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v < 1:
            raise ValueError('타임아웃은 1초 이상이어야 합니다')
        return v


class AgentResponse(BaseModel):
    """에이전트 응답 모델"""
    agent_name: str = Field(..., description="에이전트 이름")
    status: ProcessingStatus = Field(..., description="처리 상태")
    result: Dict[str, Any] = Field(..., description="처리 결과")
    execution_time: float = Field(..., description="실행 시간 (초)")
    timestamp: datetime = Field(default_factory=datetime.now, description="타임스탬프")
    error_message: Optional[str] = Field(default=None, description="에러 메시지")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CollaborationRequest(BaseModel):
    """협업 요청 모델"""
    workflow_id: str = Field(..., description="워크플로우 ID")
    workflow_config: WorkflowConfig = Field(..., description="워크플로우 설정")
    input_data: Dict[str, Any] = Field(..., description="입력 데이터")
    priority: MessagePriority = Field(default=MessagePriority.NORMAL, description="우선순위")
    timeout: int = Field(default=300, description="타임아웃 (초)")
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v < 10:
            raise ValueError('타임아웃은 10초 이상이어야 합니다')
        return v


class CollaborationResponse(BaseModel):
    """협업 응답 모델"""
    workflow_id: str = Field(..., description="워크플로우 ID")
    status: ProcessingStatus = Field(..., description="처리 상태")
    results: Dict[str, AgentResponse] = Field(..., description="에이전트별 결과")
    total_execution_time: float = Field(..., description="총 실행 시간 (초)")
    timestamp: datetime = Field(default_factory=datetime.now, description="타임스탬프")
    error_messages: List[str] = Field(default_factory=list, description="에러 메시지들")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 대시보드 모델
class DashboardMetric(BaseModel):
    """대시보드 메트릭 모델"""
    name: str = Field(..., description="메트릭 이름")
    value: Union[int, float, str] = Field(..., description="메트릭 값")
    unit: str = Field(default="", description="단위")
    category: str = Field(..., description="카테고리")
    description: str = Field(default="", description="설명")
    timestamp: datetime = Field(default_factory=datetime.now, description="타임스탬프")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardEvent(BaseModel):
    """대시보드 이벤트 모델"""
    event_type: str = Field(..., description="이벤트 타입")
    message: str = Field(..., description="이벤트 메시지")
    severity: str = Field(default="info", description="심각도")
    timestamp: datetime = Field(default_factory=datetime.now, description="타임스탬프")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SystemStatus(BaseModel):
    """시스템 상태 모델"""
    health_score: float = Field(..., ge=0.0, le=100.0, description="건강 점수")
    health_status: str = Field(..., description="건강 상태")
    active_agents: int = Field(..., description="활성 에이전트 수")
    system_uptime: str = Field(..., description="시스템 가동 시간")
    last_update: datetime = Field(default_factory=datetime.now, description="마지막 업데이트")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardSummary(BaseModel):
    """대시보드 요약 모델"""
    timestamp: datetime = Field(default_factory=datetime.now, description="타임스탬프")
    metrics: List[DashboardMetric] = Field(..., description="메트릭들")
    events: List[DashboardEvent] = Field(default_factory=list, description="이벤트들")
    agent_activity: Dict[str, Any] = Field(default_factory=dict, description="에이전트 활동")
    error_summary: Dict[str, Any] = Field(default_factory=dict, description="에러 요약")
    system_status: SystemStatus = Field(..., description="시스템 상태")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 성능 모니터링 모델
class PerformanceMetrics(BaseModel):
    """성능 메트릭 모델"""
    total_requests: int = Field(..., description="총 요청 수")
    successful_requests: int = Field(..., description="성공한 요청 수")
    failed_requests: int = Field(..., description="실패한 요청 수")
    average_response_time: float = Field(..., description="평균 응답 시간")
    success_rate: float = Field(..., description="성공률")
    timestamp: datetime = Field(default_factory=datetime.now, description="타임스탬프")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TestResponse(BaseModel):
    """테스트 응답 모델"""
    company: str = Field(..., description="회사명")
    analysis: str = Field(..., description="분석 내용")
    score: float = Field(..., ge=0.0, le=10.0, description="점수")
    
    @validator('score')
    def validate_score(cls, v):
        if v < 0 or v > 10:
            raise ValueError('점수는 0-10 사이여야 합니다')
        return v


# 유틸리티 함수들
def create_collaboration_message(
    source_agent: str,
    target_agent: str,
    message_type: str,
    content: Dict[str, Any] = None,
    priority: MessagePriority = MessagePriority.NORMAL
) -> CollaborationMessage:
    """협업 메시지 생성"""
    import uuid
    
    return CollaborationMessage(
        id=str(uuid.uuid4()),
        source_agent=source_agent,
        target_agent=target_agent,
        message_type=message_type,
        content=content or {},
        priority=priority
    )


def create_knowledge_share(
    agent: str,
    knowledge_type: KnowledgeType,
    content: Dict[str, Any],
    confidence: float
) -> KnowledgeShare:
    """지식 공유 생성"""
    import uuid
    
    return KnowledgeShare(
        id=str(uuid.uuid4()),
        agent=agent,
        knowledge_type=knowledge_type,
        content=content,
        confidence=confidence
    )


def create_dashboard_metric(
    name: str,
    value: Union[int, float, str],
    unit: str = "",
    category: str = "general",
    description: str = ""
) -> DashboardMetric:
    """대시보드 메트릭 생성"""
    return DashboardMetric(
        name=name,
        value=value,
        unit=unit,
        category=category,
        description=description
    )


def create_system_status(
    health_score: float,
    health_status: str,
    active_agents: int,
    system_uptime: str
) -> SystemStatus:
    """시스템 상태 생성"""
    return SystemStatus(
        health_score=health_score,
        health_status=health_status,
        active_agents=active_agents,
        system_uptime=system_uptime
    ) 