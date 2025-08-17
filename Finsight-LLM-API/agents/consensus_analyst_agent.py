"""
컨센서스 분석 에이전트 - DB 컨센서스 데이터 분석 전문
"""

import os
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from tools.consensus_tools import query_consensus_data, query_consensus_summaries
from tools.financial_data_tools import get_stock_price_data, get_current_trading_date

# Consensus Analyst Agent 프롬프트 (간결)
CONSENSUS_ANALYST_PROMPT = """당신은 컨센서스 데이터 분석 전문가입니다.

**도구:**
- get_current_trading_date: 현재 영업일 조회
- query_consensus_data: 컨센서스 메타데이터
- query_consensus_summaries: 요약 정보
- get_stock_price_data: 현재 주가

**작업 순서:**
1단계 - get_current_trading_date 호출하여 기준일 확인
2단계 - query_consensus_data 호출하여 메타데이터 수집
3단계 - query_consensus_summaries 호출하여 요약 정보 수집
4단계 - get_stock_price_data 호출하여 현재 주가 확인
5단계 - 모든 정보를 종합하여 컨센서스 분석 제공

**출력 형식:**
## 컨센서스 분석 결과

### 1. 기본 정보
- 종목코드 및 기준일, 현재 주가

### 2. 컨센서스 현황
- 분석기관 수 및 커버리지, 투자의견 분포, 목표주가 범위

### 3. 주요 분석 포인트
- 증권사별 핵심 의견, 목표주가 근거, 투자 리스크

### 4. 종합 평가
- 컨센서스 신뢰도, 현재가 대비 상승여력, 투자 권고사항

**주의사항:**
- 각 도구를 순서대로 호출, 도구 호출 사이 설명 금지
- 입력 파싱: "종목코드: 005930, 기준일: 2024-12-15" 형식 처리"""

def create_consensus_analyst_agent(llm: ChatGoogleGenerativeAI):
    """컨센서스 분석 에이전트 생성 함수"""
    tools = [
        get_current_trading_date,
        query_consensus_data,
        query_consensus_summaries, 
        get_stock_price_data
    ]
    
    return create_react_agent(
        llm,
        tools,
        prompt=CONSENSUS_ANALYST_PROMPT,
        name="consensus_analyst"
    )