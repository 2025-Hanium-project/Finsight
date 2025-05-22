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
    report_contents: List[Dict[str, Any]] = Field(..., description="분석할 리포트 목록")
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
