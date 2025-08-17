from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from tools.document_tools import extract_pdf

# Consensus Processing Agent 프롬프트 (간결)
CONSENSUS_PROCESSING_PROMPT = """당신은 통합 컨센서스 리포트 처리 에이전트입니다.

**작업:**
1. PDF 파일 경로를 받아 extract_pdf 도구로 텍스트 추출
2. 추출된 텍스트를 JSON 형식으로 변환

**JSON 형식:**
{
    "stock_code": "종목코드 (예: 005930)",
    "stock_name": "종목명 (예: 삼성전자)",
    "report_title": "리포트 제목",
    "report_date": "리포트 날짜(YYYY-MM-DD)",
    "report_type": "리포트 유형 (기업분석/산업분석)",
    "analyst_name": "애널리스트 이름",
    "company_name": "증권사명",
    "rating": "투자의견 (강력매수/매수/중립/매도/강력매도/없음)",
    "opinion_change": "투자의견 변경 (유지/상향/하향)",
    "target_price": "목표가 (숫자만, 예: 84000)",
    "target_price_change": "목표가 변경 (상향/하향/신규/유지)",
    "investment_rationale": "리포트 전체 본문 내용 (표, 그래프 제외하고 텍스트만)",
    "summary": "3-5문장 요약"
}

**주의사항:**
- investment_rationale은 전체 본문을 그대로 추출
- 줄바꿈 문자(\\n) 사용 금지
- 부제목은 [제목명] 형식으로 표현
- 모든 텍스트를 공백으로 연결
- 원본과 정확히 일치하도록 검증
- JSON 형식을 정확히 준수"""

def create_consensus_processing_agent(llm: ChatGoogleGenerativeAI):
    """컨센서스 파서 에이전트 생성"""
    agent = create_react_agent(
        llm,
        tools=[extract_pdf],  
        prompt=CONSENSUS_PROCESSING_PROMPT,
        name="consensus_processing_agent"
    )
    return agent
