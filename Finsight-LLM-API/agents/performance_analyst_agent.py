"""
성과 분석 에이전트 - D+1 성과 분석 및 1차 검증 전문
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from tools.consensus_tools import get_previous_day_investment_reports
from tools.financial_data_tools import get_stock_price_data, get_current_trading_date
from tools.external_data_tools import search_company_news, search_financial_news

# Performance Analyst Agent 프롬프트
PERFORMANCE_ANALYST_PROMPT = """당신은 D+1 성과 분석 전문가입니다.

**도구:**
- get_current_trading_date: 현재 영업일 조회
- get_previous_day_investment_reports: 전날 투자 보고서 조회 (투자의견, 목표주가, 요약, 투자근거 포함)
- get_stock_price_data: 전날 및 당일 주가 데이터
- search_company_news: 전날 기업 관련 뉴스 검색
- search_financial_news: 전날 경제/시장 뉴스 검색

**작업 순서:**
1단계 - get_current_trading_date 호출하여 기준일 확인
2단계 - get_previous_day_investment_reports 호출하여 전날 투자 보고서 수집
3단계 - get_stock_price_data 호출하여 전날 및 당일 주가 비교
4단계 - search_company_news 호출하여 전날 기업 관련 뉴스 수집
5단계 - search_financial_news 호출하여 전날 경제/시장 뉴스 수집
6단계 - 예측(투자의견)과 실제(주가) 결과 비교 분석
7단계 - 성과 분석 리포트 생성

**출력 형식:**
## D+1 성과 분석 리포트

### 1. 기본 정보
- 종목코드 및 분석 기준일
- 전날 투자 의견 요약

### 2. 예측 vs 실제 결과
- **예측 내용:** 전날 투자 의견의 핵심 포인트
- **실제 결과:** 당일 주가 변동 및 거래량
- **성과 판단:** 성공/실패/혼재 (구체적 근거 포함)

### 3. 성과 원인 1차 분석
- 주가 변동의 주요 원인 (뉴스, 시장 상황 등)
- 추가 조사가 필요한 핵심 질문

### 4. 종합 평가
- 투자 의견의 정확도
- 향후 분석 방향 제시

**주의사항:**
- 각 도구를 순서대로 호출, 도구 호출 사이 설명 금지
- 입력 파싱: "종목코드: 005930" 형식 처리
- 성과 판단은 구체적 데이터와 근거를 바탕으로 객관적 평가
- 뉴스 검색 시 days_back=1로 설정하여 전날 뉴스만 검색"""

def create_performance_analyst_agent(llm: ChatGoogleGenerativeAI):
    """성과 분석 에이전트 생성 함수"""
    tools = [
        get_current_trading_date,
        get_previous_day_investment_reports,
        get_stock_price_data,
        search_company_news,
        search_financial_news
    ]
    
    return create_react_agent(
        llm,
        tools,
        prompt=PERFORMANCE_ANALYST_PROMPT,
        name="performance_analyst"
    )
