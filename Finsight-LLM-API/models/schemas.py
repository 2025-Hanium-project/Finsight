"""
API 스키마 정의

현재 사용:
- utils/data_models.py의 StandardInput/StandardOutput이 기본 데이터 모델로 사용됨
- 이 파일은 세부 API 엔드포인트별 특화 스키마용

향후 계획:
- 각 에이전트별 특화 요청/응답 스키마
- 워크플로우 상태 관리 스키마
- 협업 시스템 통신 프로토콜 스키마
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

# ============================================================================
# 에이전트별 요청/응답 스키마
# ============================================================================

# 데이터 에이전트 스키마
class FinancialStatementRequest(BaseModel):
    """재무제표 분석 요청"""
    target_type: str = Field(..., description="분석 대상 타입 (company, industry, sector)")
    target_name: str = Field(..., description="분석 대상 이름")
    symbol: Optional[str] = Field(None, description="종목 코드")
    financial_data: Dict[str, Any] = Field(..., description="재무 데이터")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class FinancialStatementResponse(BaseModel):
    """재무제표 분석 응답"""
    financial_health: str = Field(..., description="재무 건전성 평가")
    key_ratios: Dict[str, float] = Field(..., description="주요 재무비율")
    risk_factors: List[str] = Field(..., description="재무 리스크 요인")
    status: str = Field(..., description="처리 상태")
    generated_at: datetime = Field(default_factory=datetime.now)

class NewsAnalysisRequest(BaseModel):
    """뉴스 분석 요청"""
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    news_contents: List[str] = Field(..., description="뉴스 내용 목록")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class NewsAnalysisResponse(BaseModel):
    """뉴스 분석 응답"""
    sentiment_score: float = Field(..., description="감정 점수")
    negative_news_count: int = Field(..., description="부정적 뉴스 수")
    overall_sentiment: str = Field(..., description="전체 감정 상태")
    risk_implications: List[str] = Field(..., description="리스크 함의")
    status: str = Field(..., description="처리 상태")
    generated_at: datetime = Field(default_factory=datetime.now)

class SecuritiesReportRequest(BaseModel):
    """증권사 리포트 분석 요청"""
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    report_content: str = Field(..., description="리포트 내용")
    report_info: Dict[str, str] = Field(..., description="리포트 메타 정보")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class SecuritiesReportResponse(BaseModel):
    """증권사 리포트 분석 응답"""
    summary: str = Field(..., description="리포트 요약")
    key_points: List[str] = Field(..., description="핵심 포인트")
    report_info: Dict[str, str] = Field(..., description="리포트 메타 정보")
    status: str = Field(..., description="처리 상태")
    generated_at: datetime = Field(default_factory=datetime.now)

class MarketDataRequest(BaseModel):
    """시장 데이터 분석 요청"""
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    market_data: Dict[str, Any] = Field(..., description="시장 데이터")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class MarketDataResponse(BaseModel):
    """시장 데이터 분석 응답"""
    market_volatility: float = Field(..., description="시장 변동성")
    risk_level: str = Field(..., description="리스크 레벨")
    recommendation: str = Field(..., description="투자 권고")
    market_trend: str = Field(..., description="시장 트렌드")
    status: str = Field(..., description="처리 상태")
    generated_at: datetime = Field(default_factory=datetime.now)

# 분석 에이전트 스키마
class RiskAssessmentRequest(BaseModel):
    """리스크 평가 요청"""
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    analysis_data: Dict[str, Any] = Field(..., description="분석 데이터")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class RiskAssessmentResponse(BaseModel):
    """리스크 평가 응답"""
    risk_level: str = Field(..., description="리스크 레벨")
    financial_risks: str = Field(..., description="재무 리스크")
    market_risks: str = Field(..., description="시장 리스크")
    operational_risks: str = Field(..., description="운영 리스크")
    regulatory_risks: str = Field(..., description="규제 리스크")
    credit_risks: str = Field(..., description="신용 리스크")
    liquidity_risks: str = Field(..., description="유동성 리스크")
    risk_mitigation: str = Field(..., description="리스크 완화 방안")
    confidence_score: str = Field(..., description="신뢰도 점수")
    agent_name: str = Field(..., description="에이전트 이름")
    agent_type: str = Field(..., description="에이전트 타입")
    generated_at: datetime = Field(default_factory=datetime.now)
    collaboration_data: List[str] = Field(..., description="협업 데이터")

class GrowthAnalysisRequest(BaseModel):
    """성장성 분석 요청"""
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    growth_data: Dict[str, Any] = Field(..., description="성장 데이터")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class GrowthAnalysisResponse(BaseModel):
    """성장성 분석 응답"""
    growth_score: int = Field(..., description="성장 점수")
    growth_potential: str = Field(..., description="성장 잠재력")
    growth_drivers: List[Dict[str, str]] = Field(..., description="성장 동력")
    investment_opportunities: List[str] = Field(..., description="투자 기회")
    status: str = Field(..., description="처리 상태")
    generated_at: datetime = Field(default_factory=datetime.now)

class ValuationRequest(BaseModel):
    """밸류에이션 분석 요청"""
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    valuation_data: Dict[str, Any] = Field(..., description="밸류에이션 데이터")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class ValuationResponse(BaseModel):
    """밸류에이션 분석 응답"""
    fair_value: float = Field(..., description="공정가치")
    valuation_methods: Dict[str, float] = Field(..., description="밸류에이션 방법별 가치")
    recommendation: str = Field(..., description="투자 권고")
    status: str = Field(..., description="처리 상태")
    generated_at: datetime = Field(default_factory=datetime.now)

class PeerComparisonRequest(BaseModel):
    """동종업계 비교 요청"""
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    peer_data: Dict[str, Any] = Field(..., description="동종업계 데이터")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class PeerComparisonResponse(BaseModel):
    """동종업계 비교 응답"""
    competitive_position: str = Field(..., description="경쟁 위치")
    relative_performance: Dict[str, float] = Field(..., description="상대적 성과")
    competitive_advantages: List[str] = Field(..., description="경쟁 우위")
    status: str = Field(..., description="처리 상태")
    generated_at: datetime = Field(default_factory=datetime.now)

# 리포트 에이전트 스키마
class DDayReportRequest(BaseModel):
    """D-day 리포트 요청"""
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    agent_results: Dict[str, Any] = Field(..., description="에이전트 분석 결과")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class DDayReportResponse(BaseModel):
    """D-day 리포트 응답"""
    investment_summary: str = Field(..., description="투자 요약")
    key_recommendations: List[str] = Field(..., description="핵심 권고사항")
    risk_assessment: str = Field(..., description="리스크 평가")
    market_outlook: str = Field(..., description="시장 전망")
    status: str = Field(..., description="처리 상태")
    generated_at: datetime = Field(default_factory=datetime.now)

class DPlus1ReportRequest(BaseModel):
    """D+1 리포트 요청"""
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    dday_results: Dict[str, Any] = Field(..., description="D-day 결과")
    market_updates: Dict[str, Any] = Field(..., description="시장 업데이트")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class DPlus1ReportResponse(BaseModel):
    """D+1 리포트 응답"""
    follow_up_analysis: str = Field(..., description="후속 분석")
    updated_recommendations: List[str] = Field(..., description="업데이트된 권고")
    market_reaction: str = Field(..., description="시장 반응")
    next_steps: List[str] = Field(..., description="다음 단계")
    status: str = Field(..., description="처리 상태")
    generated_at: datetime = Field(default_factory=datetime.now)

# 지원 에이전트 스키마
class DocumentProcessingRequest(BaseModel):
    """문서 처리 요청"""
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    document_content: str = Field(..., description="문서 내용")
    document_type: str = Field(..., description="문서 타입")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class DocumentProcessingResponse(BaseModel):
    """문서 처리 응답"""
    processed_content: str = Field(..., description="처리된 내용")
    extracted_data: Dict[str, Any] = Field(..., description="추출된 데이터")
    quality_score: float = Field(..., description="품질 점수")
    status: str = Field(..., description="처리 상태")
    generated_at: datetime = Field(default_factory=datetime.now)

class DataQualityRequest(BaseModel):
    """데이터 품질 평가 요청"""
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    data_quality_metrics: Dict[str, Any] = Field(..., description="데이터 품질 메트릭")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class DataQualityResponse(BaseModel):
    """데이터 품질 평가 응답"""
    overall_quality: str = Field(..., description="전체 품질")
    completeness_score: float = Field(..., description="완성도 점수")
    accuracy_score: float = Field(..., description="정확도 점수")
    consistency_score: float = Field(..., description="일관성 점수")
    recommendations: List[str] = Field(..., description="개선 권고")
    status: str = Field(..., description="처리 상태")
    generated_at: datetime = Field(default_factory=datetime.now)

class SupervisorRequest(BaseModel):
    """Supervisor 에이전트 요청"""
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    agent_results: Dict[str, Any] = Field(..., description="에이전트 분석 결과")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class SupervisorResponse(BaseModel):
    """Supervisor 에이전트 응답"""
    overall_score: int = Field(..., description="종합 투자 점수")
    investment_recommendation: str = Field(..., description="투자 권고")
    confidence_level: str = Field(..., description="신뢰도")
    key_points: List[str] = Field(..., description="핵심 투자 포인트")
    risk_warnings: List[str] = Field(..., description="주의 사항")
    investment_strategy: str = Field(..., description="투자 전략")
    summary: str = Field(..., description="종합 분석 요약")
    status: str = Field(..., description="처리 상태")
    generated_at: datetime = Field(default_factory=datetime.now)

# ============================================================================
# 협업 시스템 스키마
# ============================================================================

class CollaborationRequest(BaseModel):
    """협업 요청"""
    source_agent: str = Field(..., description="요청 에이전트")
    target_agent: str = Field(..., description="대상 에이전트")
    request_type: str = Field(..., description="요청 타입")
    context: Dict[str, Any] = Field(..., description="요청 컨텍스트")
    data: Dict[str, Any] = Field(default_factory=dict, description="요청 데이터")

class CollaborationResponse(BaseModel):
    """협업 응답"""
    success: bool = Field(..., description="성공 여부")
    result: Dict[str, Any] = Field(..., description="응답 결과")
    collaboration_id: str = Field(..., description="협업 ID")
    timestamp: datetime = Field(default_factory=datetime.now)

# ============================================================================
# 워크플로우 스키마
# ============================================================================

class WorkflowRequest(BaseModel):
    """워크플로우 요청"""
    workflow_type: str = Field(..., description="워크플로우 타입")
    target_type: str = Field(..., description="분석 대상 타입")
    target_name: str = Field(..., description="분석 대상 이름")
    input_data: Dict[str, Any] = Field(..., description="입력 데이터")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")

class WorkflowResponse(BaseModel):
    """워크플로우 응답"""
    workflow_id: str = Field(..., description="워크플로우 ID")
    status: str = Field(..., description="워크플로우 상태")
    results: Dict[str, Any] = Field(..., description="워크플로우 결과")
    execution_time: float = Field(..., description="실행 시간")
    generated_at: datetime = Field(default_factory=datetime.now)

# ============================================================================
# 대시보드 스키마
# ============================================================================

class DashboardMetrics(BaseModel):
    """대시보드 메트릭"""
    active_messages: int = Field(..., description="활성 메시지 수")
    total_collaborations: int = Field(..., description="총 협업 수")
    registered_agents: int = Field(..., description="등록된 에이전트 수")
    feedback_loop_count: int = Field(..., description="피드백 루프 수")
    resolution_queue_count: int = Field(..., description="해결 대기 큐 수")
    total_errors: int = Field(..., description="총 에러 수")
    timestamp: datetime = Field(default_factory=datetime.now)

class SystemStatus(BaseModel):
    """시스템 상태"""
    health_score: float = Field(..., description="시스템 건강도 점수")
    health_status: str = Field(..., description="시스템 건강도 상태")
    active_agents: int = Field(..., description="활성 에이전트 수")
    system_uptime: str = Field(..., description="시스템 가동 시간")
    last_update: datetime = Field(default_factory=datetime.now)

class DashboardResponse(BaseModel):
    """대시보드 응답"""
    timestamp: datetime = Field(default_factory=datetime.now)
    metrics: List[DashboardMetrics] = Field(..., description="메트릭 목록")
    events: List[Dict[str, Any]] = Field(..., description="이벤트 목록")
    agent_activity: Dict[str, Any] = Field(..., description="에이전트 활동")
    error_summary: Dict[str, Any] = Field(..., description="에러 요약")
    system_status: SystemStatus = Field(..., description="시스템 상태")
