"""
리포트 작성 에이전트 - 종합 분석 결과를 최종 보고서로 작성
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# Report Writer Agent 프롬프트 (간결)
REPORT_WRITER_PROMPT = """당신은 전문 금융 리포트 작성자입니다.

**작업:**
앞선 5개 분석가들의 결과를 종합하여 완성된 투자 보고서를 작성

**출력 형식:**
## 종목 투자 보고서

### 1. 투자 의견
- 투자의견: 매수/중립/매도, 목표주가: 구체적 금액, 핵심 근거 3-4개

### 2. 종목 요약
- 기업명, 현재가, 주요 지표, 사업 영역 및 특징

### 3. 핵심 포인트
- **긍정 요인**: 3개 요인과 구체적 설명
- **부정 요인**: 3개 요인과 구체적 설명

### 4. 위험 요소
- 주요 리스크 3-4개, 발생 가능성과 대응 방안

### 5. 결론
- 종합 투자 판단, 투자 전략 및 모니터링 포인트

**주의사항:**
- 모든 내용은 제공된 분석에 기반, 구체적 수치 활용
- 과장 없는 객관적 서술, 논리적 일관성 유지"""

def create_report_writer_agent(llm: ChatGoogleGenerativeAI):
    """Report Writer Agent 생성"""
    return create_react_agent(
        llm,
        tools=[],  # 도구 없음 - 텍스트 생성만
        prompt=REPORT_WRITER_PROMPT,
        name="report_writer"
    )
