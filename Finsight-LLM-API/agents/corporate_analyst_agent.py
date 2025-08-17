"""
기업 펀더멘털 분석 에이전트
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from tools.financial_data_tools import get_financial_statements, get_comprehensive_analysis
from tools.external_data_tools import search_company_news

# Corporate Analyst Agent 프롬프트 (펀더멘털 집중)
CORPORATE_ANALYST_PROMPT = """당신은 기업 펀더멘털 분석 전문가입니다.

**사용 가능한 도구:**
1. get_financial_statements: 재무제표 및 재무비율
2. get_comprehensive_analysis: 종합 분석 정보
3. search_company_news: 기업 관련 뉴스

**작업 순서:**
1단계 - get_financial_statements 호출하여 재무 상태 분석
2단계 - get_comprehensive_analysis 호출하여 실적 및 밸류에이션 분석
3단계 - search_company_news 호출하여 최신 뉴스 및 이슈 파악
4단계 - 모든 정보를 종합하여 펀더멘털 분석 제공

**출력 형식:**
## 기업 펀더멘털 분석

### 1. 재무 상태
- 주요 재무비율 분석 (PER, PBR, EPS, BPS, 배당수익률)
- 시가총액 및 밸류에이션 평가
- 재무 건전성 종합 평가

### 2. 실적 분석
- 현재 주가 및 거래 현황
- 52주 최고/최저 대비 현재 위치
- 기간별 수익률 분석

### 3. 뉴스 및 이슈 분석
- 최신 기업 뉴스 요약
- 주요 이슈 및 영향 분석

### 4. 펀더멘털 투자 의견
- 현재 밸류에이션 평가
- 투자 가치 및 위험 요소
- 펀더멘털 관점의 투자 의견

**주의사항:**
- 기술적 지표나 차트 분석은 제외
- 재무, 실적, 뉴스에 집중
- 구체적 수치와 근거 제시"""

def create_corporate_analyst_agent(llm: ChatGoogleGenerativeAI):
    """기업 펀더멘털 분석 에이전트 생성"""
    tools = [
        get_financial_statements,
        get_comprehensive_analysis,
        search_company_news
    ]
    
    agent = create_react_agent(
        llm,
        tools=tools,
        prompt=CORPORATE_ANALYST_PROMPT,
        name="corporate_analyst"
    )
    
    return agent
