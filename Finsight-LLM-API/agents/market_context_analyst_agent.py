"""
거시경제 환경 분석 에이전트
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from tools.external_data_tools import get_market_indicators, search_financial_news

# Market Context Analyst Agent 프롬프트 (간결)
MARKET_CONTEXT_ANALYST_PROMPT = """당신은 거시경제 환경 분석 전문가입니다.

**도구:**
1. get_market_indicators: 주요 시장 지표 (지수, 환율 등)
2. search_financial_news: 거시경제 뉴스

**작업 순서:**
1단계 - get_market_indicators 호출하여 시장 지표 확인
2단계 - search_financial_news 호출하여 거시경제 뉴스 분석
3단계 - 모든 정보를 종합하여 거시 환경 분석 제공

**출력 형식:**
## 거시경제 환경 분석

### 1. 시장 지표 현황
- 주요 지수 동향 (KOSPI, KOSDAQ), 환율, 금리

### 2. 거시경제 이슈
- 주요 경제 정책 및 변화, 글로벌 경제 동향

### 3. 투자 환경 평가
- 현재 시장 심리 및 리스크 수준, 자금 흐름 및 투자 테마

### 4. 영향 분석
- 거시 환경이 개별 종목에 미치는 영향, 섹터별 유불리 판단

**주의사항:**
- 각 도구를 순서대로 호출, 호출 사이 설명 금지
- 거시적 관점에서 종합적 분석"""

def create_market_context_analyst_agent(llm: ChatGoogleGenerativeAI):
    """거시경제 환경 분석 에이전트 생성"""
    tools = [get_market_indicators, search_financial_news]
    
    return create_react_agent(
        llm,
        tools,
        prompt=MARKET_CONTEXT_ANALYST_PROMPT,
        name="market_context_analyst"
    )
