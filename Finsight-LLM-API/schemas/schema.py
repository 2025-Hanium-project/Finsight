"""
워크플로우별 에이전트 출력 스키마 정의
"""

from pydantic import BaseModel, Field
from typing import List

# =====================================
# 1. 개별 에이전트 출력 스키마
# =====================================

class ConsensusProcessingResult(BaseModel):
    """Consensus Processing Agent 출력"""
    stock_code: str = Field(description="종목코드 (예: 005930)")
    stock_name: str = Field(description="종목명 (예: 삼성전자)")
    report_title: str = Field(description="리포트 제목")
    report_date: str = Field(description="리포트 날짜(YYYY-MM-DD)")
    report_type: str = Field(description="리포트 유형 (기업분석/산업분석)")
    analyst_name: str = Field(description="애널리스트 이름")
    company_name: str = Field(description="증권사명")
    rating: str = Field(description="투자의견 (강력매수/매수/중립/매도/강력매도/없음)")
    opinion_change: str = Field(description="투자의견 변경 (유지/상향/하향)")
    target_price: str = Field(description="목표가 (숫자만, 예: 84000)")
    target_price_change: str = Field(description="목표가 변경 (상향/하향/신규/유지)")
    investment_rationale: str = Field(description="리포트 전체 본문 내용")
    summary: str = Field(description="3-5문장 요약")

class AnalysisResult(BaseModel):
    """분석 에이전트들의 공통 출력"""
    analyst_type: str = Field(description="분석 유형 (corporate/industry/market_context/quantitative/performance)")
    analysis_content: str = Field(description="분석 내용")

# =====================================
# 2. Supervisor → Writer 전달 스키마
# =====================================

class ReportWriterInput(BaseModel):
    """Report Writer에게 전달할 구조화된 데이터"""
    stock_code: str = Field(description="종목코드")
    stock_name: str = Field(description="종목명")
    report_date: str = Field(description="보고서 작성 날짜")
    
    # 컨센서스 종합 분석
    consensus_summary: str = Field(description="컨센서스 데이터 종합 요약")
    average_target_price: str = Field(description="평균 목표주가")
    investment_opinion_distribution: str = Field(description="투자의견 분포")
    
    # 4대 분석 결과
    corporate_analysis: str = Field(description="기업 펀더멘털 분석 결과")
    industry_analysis: str = Field(description="산업 동향 분석 결과")
    market_context_analysis: str = Field(description="거시경제 영향 분석 결과")
    quantitative_analysis: str = Field(description="기술적 지표 분석 결과")
    
    # 최종 결론
    final_investment_opinion: str = Field(description="최종 투자 의견")
    final_conclusion: str = Field(description="종합 결론 및 투자 권고사항")
    key_points: List[str] = Field(description="핵심 포인트 (3-5개)")
    investment_risks: List[str] = Field(description="주요 투자 위험 요소 (3-5개)")

class ReviewWriterInput(BaseModel):
    """Review Writer에게 전달할 구조화된 데이터"""
    stock_code: str = Field(description="종목코드")
    stock_name: str = Field(description="종목명")
    review_date: str = Field(description="리뷰 날짜")
    
    # 예측 vs 실제 비교
    original_prediction_summary: str = Field(description="전날 예측 내용 요약")
    actual_market_performance: str = Field(description="실제 시장 성과")
    performance_assessment: str = Field(description="성과 평가 (성공/부분성공/실패)")
    
    # 4대 관점별 원인 분석
    corporate_cause_analysis: str = Field(description="기업 요인 원인 분석")
    industry_cause_analysis: str = Field(description="산업 요인 원인 분석")
    market_cause_analysis: str = Field(description="거시경제 요인 원인 분석")
    technical_cause_analysis: str = Field(description="기술적 요인 원인 분석")
    
    # 종합 결론
    primary_influence_factors: List[str] = Field(description="주요 영향 요인 (3-5개)")
    unexpected_variables: List[str] = Field(description="예상치 못한 변수 (2-4개)")
    final_cause_conclusion: str = Field(description="종합적인 원인 분석 결론")

# =====================================
# 3. 최종 사용자 출력 스키마 (텍스트)
# =====================================

class ConsensusData(BaseModel):
    """Consensus 워크플로우 최종 출력 (JSON)"""
    stock_code: str = Field(description="종목코드")
    stock_name: str = Field(description="종목명")
    report_title: str = Field(description="리포트 제목")
    report_date: str = Field(description="리포트 날짜(YYYY-MM-DD)")
    report_type: str = Field(description="리포트 유형")
    analyst_name: str = Field(description="애널리스트 이름")
    company_name: str = Field(description="증권사명")
    rating: str = Field(description="투자의견")
    opinion_change: str = Field(description="투자의견 변경")
    target_price: str = Field(description="목표가")
    target_price_change: str = Field(description="목표가 변경")
    investment_rationale: str = Field(description="리포트 전체 본문")
    summary: str = Field(description="요약")

class ReportOutput(BaseModel):
    """Report 워크플로우 최종 출력 (텍스트)"""
    report_content: str = Field(description="완성된 투자 보고서 텍스트")

class ReviewOutput(BaseModel):
    """Review 워크플로우 최종 출력 (텍스트)"""
    review_content: str = Field(description="완성된 성과 분석 리뷰 텍스트")

# =====================================
# 4. Schema Mappings
# =====================================

# 개별 에이전트 출력 스키마
AGENT_SCHEMAS = {
    "consensus_processing": ConsensusProcessingResult,
    "corporate_analyst": AnalysisResult,
    "industry_analyst": AnalysisResult,
    "market_context_analyst": AnalysisResult,
    "quantitative_analyst": AnalysisResult,
    "performance_analyst": AnalysisResult,
}

# Supervisor → Writer 전달 스키마
WRITER_INPUT_SCHEMAS = {
    "report": ReportWriterInput,
    "review": ReviewWriterInput,
}

# 최종 사용자 출력 스키마
FINAL_OUTPUT_SCHEMAS = {
    "consensus": ConsensusData,
    "report": ReportOutput,
    "review": ReviewOutput,
}

def get_agent_schema(agent_name: str) -> BaseModel:
    """에이전트별 출력 스키마 반환"""
    return AGENT_SCHEMAS.get(agent_name)

def get_writer_input_schema(workflow_type: str) -> BaseModel:
    """Writer 입력 스키마 반환"""
    return WRITER_INPUT_SCHEMAS.get(workflow_type)

def get_final_output_schema(workflow_type: str) -> BaseModel:
    """최종 출력 스키마 반환"""
    return FINAL_OUTPUT_SCHEMAS.get(workflow_type) 