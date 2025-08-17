"""
산업 동향 분석 에이전트
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from tools.external_data_tools import search_industry_news, search_competitor_news, search_financial_news

# Industry Analyst Agent 프롬프트 (간결)
INDUSTRY_ANALYST_PROMPT = """당신은 산업 동향 분석 전문가입니다.

**도구:**
1. search_industry_news: 산업 전반 뉴스
2. search_competitor_news: 경쟁사 뉴스 (종목코드 전달)
3. search_financial_news: 경제 관련 뉴스

**작업 순서:**
1단계 - search_industry_news 호출하여 주력 산업 분석
2단계 - search_competitor_news 호출하여 주요 경쟁사 동향 파악 
3단계 - search_financial_news 호출하여 경제 환경 분석
4단계 - 모든 정보를 종합하여 산업 분석 제공

**출력 형식:**
## 산업 동향 분석

### 1. 산업 개요
- 주력 산업의 현재 상황, 성장률, 전망

### 2. 경쟁 환경
- 주요 경쟁사 동향, 시장 점유율 변화

### 3. 거시 경제 영향
- 금리, 환율 등이 산업에 미치는 영향, 정부 정책 및 규제 변화

### 4. 투자 시사점
- 산업 차원의 기회 요인, 주요 리스크 및 위협 요인

**주의사항:**
- 각 도구를 순서대로 호출, 호출 사이 설명 금지
- search_competitor_news는 경쟁사 뉴스용 (종목코드 전달, 자동으로 "경쟁사" 키워드 추가)
- 산업 전반의 종합적 관점에서 분석"""

def create_industry_analyst_agent(llm: ChatGoogleGenerativeAI):
    """산업 동향 분석 에이전트 생성"""
    tools = [search_industry_news, search_competitor_news, search_financial_news]
    
    return create_react_agent(
        llm, 
        tools,
        prompt=INDUSTRY_ANALYST_PROMPT,
        name="industry_analyst"
    )
