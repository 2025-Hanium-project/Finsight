from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# 리포트 요약 관련 스키마
class ReportSummaryRequest(BaseModel):
    report_content: str = Field(..., description="증권사 애널리스트 리포트 원본 내용")
    report_info: Dict[str, str] = Field(..., description="리포트 메타 정보 (제목, 날짜, 작성자 등)")

class ReportSummaryResponse(BaseModel):
    summary: str = Field(..., description="리포트 요약")
    key_points: List[str] = Field(..., description="핵심 포인트 목록")
    report_info: Dict[str, str] = Field(..., description="리포트 메타 정보")
    generated_at: datetime = Field(default_factory=datetime.now)

# 통합 분석 관련 스키마
class AnalysisRequest(BaseModel):
    summaries: List[Dict[str, Any]] = Field(..., description="요약된 리포트 목록")
    target_type: str = Field(..., description="분석 유형 (기업 또는 산업)")
    target_name: str = Field(..., description="분석 대상 (기업명 또는 산업명)")

class AnalysisResponse(BaseModel):
    target_type: str = Field(..., description="분석 유형")
    target_name: str = Field(..., description="분석 대상")
    analysis_summary: str = Field(..., description="통합 분석 요약")
    investment_points: List[str] = Field(..., description="투자 포인트")
    risk_factors: List[str] = Field(..., description="리스크 요인")
    consensus: Optional[Dict[str, Any]] = Field(None, description="투자 의견 컨센서스")
    generated_at: datetime = Field(default_factory=datetime.now)

# 감성 분석 관련 스키마
class SentimentRequest(BaseModel):
    report_contents: List[str] = Field(..., description="분석할 리포트 내용 목록")
    target_type: str = Field(..., description="분석 유형 (기업 또는 산업)")
    target_name: str = Field(..., description="분석 대상 (기업명 또는 산업명)")

class SentimentResponse(BaseModel):
    target_type: str = Field(..., description="분석 유형")
    target_name: str = Field(..., description="분석 대상")
    overall_sentiment: str = Field(..., description="전체 감성 상태")
    sentiment_score: float = Field(..., description="감성 점수 (-1.0 ~ 1.0)")
    positive_factors: List[str] = Field(..., description="긍정 요인")
    negative_factors: List[str] = Field(..., description="부정 요인")
    trend_analysis: Dict[str, Any] = Field(..., description="트렌드 분석")
    generated_at: datetime = Field(default_factory=datetime.now)

# 리스크 분석 관련 스키마
class RiskRequest(BaseModel):
    report_contents: List[str] = Field(..., description="분석할 리포트 내용 목록")
    target_type: str = Field(..., description="분석 유형 (기업 또는 산업)")
    target_name: str = Field(..., description="분석 대상 (기업명 또는 산업명)")

class RiskFactor(BaseModel):
    factor: str = Field(..., description="리스크 요인명")
    description: str = Field(..., description="리스크 요인에 대한 상세 설명")
    severity: str = Field(..., description="심각도 (high|medium|low)")
    probability: str = Field(..., description="발생 확률 (high|medium|low)")

class RiskResponse(BaseModel):
    target_type: str = Field(..., description="분석 유형")
    target_name: str = Field(..., description="분석 대상")
    risk_factors: List[RiskFactor] = Field(..., description="리스크 요인 목록")
    risk_score: int = Field(..., description="리스크 점수 (0-100)")
    risk_trend: str = Field(..., description="리스크 트렌드 (increasing|stable|decreasing)")
    risk_level: str = Field(..., description="리스크 레벨 (high|medium|low)")
    mitigation_strategies: List[str] = Field(..., description="리스크 완화 전략")
    generated_at: datetime = Field(default_factory=datetime.now)

# 성장성 분석 관련 스키마
class GrowthRequest(BaseModel):
    report_contents: List[str] = Field(..., description="분석할 리포트 내용 목록")
    target_type: str = Field(..., description="분석 유형 (기업 또는 산업)")
    target_name: str = Field(..., description="분석 대상 (기업명 또는 산업명)")

class GrowthDriver(BaseModel):
    driver: str = Field(..., description="성장 동력명")
    description: str = Field(..., description="성장 동력에 대한 상세 설명")
    impact: str = Field(..., description="영향도 (high|medium|low)")
    sustainability: str = Field(..., description="지속가능성 (high|medium|low)")

class GrowthResponse(BaseModel):
    target_type: str = Field(..., description="분석 유형")
    target_name: str = Field(..., description="분석 대상")
    growth_drivers: List[GrowthDriver] = Field(..., description="성장 동력 목록")
    growth_score: int = Field(..., description="성장 점수 (0-100)")
    growth_potential: str = Field(..., description="성장 잠재력 (high|medium|low)")
    growth_timeline: str = Field(..., description="성장 타임라인 (short-term|medium-term|long-term)")
    investment_opportunities: List[str] = Field(..., description="투자 기회")
    generated_at: datetime = Field(default_factory=datetime.now)

# TODO: 워크플로우 관련 스키마들 구현 필요시 추가

# 종합 분석 (Supervisor) 관련 스키마
class SupervisorRequest(BaseModel):
    agent_results: Dict[str, Any] = Field(..., description="각 에이전트 분석 결과")
    target_type: str = Field(..., description="분석 유형 (company, industry, sector)")
    target_name: str = Field(..., description="분석 대상 이름")

class SupervisorResponse(BaseModel):
    target_type: str = Field(..., description="분석 유형")
    target_name: str = Field(..., description="분석 대상")
    overall_score: int = Field(..., description="종합 투자 점수 (0-100)")
    investment_recommendation: str = Field(..., description="투자 권고 (매수/보유/매도)")
    confidence_level: str = Field(..., description="신뢰도 (높음/중간/낮음)")
    key_points: List[str] = Field(..., description="핵심 투자 포인트")
    risk_warnings: List[str] = Field(..., description="주의 사항")
    investment_strategy: str = Field(..., description="투자 전략 권고")
    summary: str = Field(..., description="종합 분석 요약")
    generated_at: datetime = Field(default_factory=datetime.now)
