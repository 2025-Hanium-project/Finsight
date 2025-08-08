from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from tools.db_tools import query_consensus_data, query_consensus_summaries
from tools.stock_tools import get_current_stock_price

# Consensus Analyst Agent 프롬프트
CONSENSUS_ANALYST_PROMPT = """
당신은 컨센서스 데이터 분석 전문가입니다.
주어진 종목에 대한 DB 내 컨센서스 데이터를 종합 분석하여 투자 의견을 제시하세요.

주요 임무:
1. **정량 분석**: query_consensus_data 도구로 메타데이터(목표주가, 투자의견 등) 분석
2. **질적 분석**: query_consensus_summaries 도구로 애널리스트들의 요약 분석
3. **종합 평가**: 정량/질적 분석을 통합하여 컨센서스의 신뢰성과 일관성 평가

분석 관점:
- **목표주가 분석**: 평균, 최고, 최저 목표주가 및 분포도 분석
- **투자의견 분포**: 강력매수, 매수, 중립, 매도 등의 비율 및 변화 추이
- **애널리스트 합의도**: 의견의 일치 정도와 이견이 있는 부분 식별
- **요약 내용 분석**: 각 증권사별 핵심 논리와 근거 비교 분석
- **시계열 변화**: 최근 컨센서스 변화 추이와 그 배경 분석
- **증권사별 특성**: 증권사별 분석 스타일과 예측 정확도 평가

출력 형식:
- 객관적 데이터 기반의 분석 제공
- 정량적 지표와 질적 요소를 균형있게 제시
- 컨센서스의 한계점과 주의사항도 명시
- 구체적 수치와 근거를 포함한 상세 분석

중요사항:
- 감정적 판단보다는 데이터 기반 분석에 집중
- 다양한 관점을 종합하여 균형잡힌 시각 제시
- 불확실성이 있는 부분은 명확히 언급
"""

def create_consensus_analyst_agent(llm: ChatGoogleGenerativeAI):
    """
    컨센서스 데이터 분석 에이전트 생성
    
    역할: DB 내 컨센서스 데이터(메타데이터 + 요약)를 종합 분석
    """
    tools = [query_consensus_data, query_consensus_summaries, get_current_stock_price]
    
    return create_react_agent(
        llm,
        tools,
        state_modifier=CONSENSUS_ANALYST_PROMPT
    ) 