"""
컨센서스 데이터 구조 정의
"""

from pydantic import BaseModel, Field
from typing import Optional

class ConsensusData(BaseModel):
    """컨센서스 리포트 데이터 스키마
    
    Structured output을 위한 Pydantic 모델
    """
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