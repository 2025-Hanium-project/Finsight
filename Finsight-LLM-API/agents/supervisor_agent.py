"""
Supervisor Agent - 워크플로우별 전용 프롬프트와 라우팅 관리
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph_supervisor import create_supervisor

# 공통 Supervisor Agent 프롬프트 (간결)
BASE_SUPERVISOR_PROMPT = """당신은 금융 분석 워크플로우의 총괄 감독자입니다.

**역할:**
1. 라우팅: 적절한 전문 에이전트로 작업 전달
2. 검증: 결과 검토 및 품질 확인
3. 피드백: 구체적 수정 요청 및 피드백 제공
4. 조정: 에이전트 간 작업 조정 및 순서 관리
5. 최종 승인: 검증 완료 후 적절한 형식으로 반환

**원칙:**
- 품질 보장을 위한 철저한 검증
- 구체적이고 실행 가능한 피드백
- 에이전트 간 의존성 고려한 순차 처리 관리"""

# Workflow 1: Consensus 처리 전용 프롬프트 (간결)
CONSENSUS_WORKFLOW_PROMPT = """현재 워크플로우: Consensus 처리

**작업 흐름:**
1단계 - 분석: 파일 경로를 받아 consensus_processing_agent로 전달
2단계 - 검증: JSON 결과 검토 (필수 필드, 본문 포함, 줄바꿈 없음, 숫자 형태, 원본 일치)
3단계 - 피드백 루프: 검증 실패 시 구체적 피드백과 재작업 요청
4단계 - 최종 응답: 검증 성공 시 JSON 형식으로 반환"""

# Workflow 2: D-day Report 전용 프롬프트 (간결)
REPORT_WORKFLOW_PROMPT = """현재 워크플로우: D-day Report 생성

**작업 흐름:**
1단계 - 컨센서스 분석: consensus_analyst에게 지시
2단계 - 심층 분석 : corporate_analyst, industry_analyst, market_context_analyst, quantitative_analyst에게 지시
3단계 - 종합 및 결론 : report_writer에게 지시

**최종 처리:**
- Report Writer 보고서 검토 후 최종 승인
- 순수한 보고서 텍스트만 반환 (JSON 변환 없음)
- 중간 과정 메시지나 메타데이터 제외

**완료 조건:**
모든 에이전트 분석 완료 후 Report Writer 보고서를 최종 검토하여 제공"""

# Workflow 3: D+1 Review 전용 프롬프트 (간결)
REVIEW_WORKFLOW_PROMPT = """현재 워크플로우: D+1 Review 분석

**작업 흐름:**
1단계 - 성과 분석: performance_analyst_agent에게 지시
2단계 - 원인 규명 심층 분석: corporate_analyst, industry_analyst, market_context_analyst, technical_analyst에게 지시
3단계 - 종합 및 결론: report_writer_agent에게 지시

**최종 처리:**
- Report Writer 보고서 검토 후 최종 승인
- 순수한 보고서 텍스트만 반환 (JSON 변환 없음)
- 중간 과정 메시지나 메타데이터 제외

**완료 조건:**
모든 에이전트 분석 완료 후 Report Writer 보고서를 최종 검토하여 제공"""

def create_supervisor_agent(
    llm: ChatGoogleGenerativeAI,
    agents: list,
    request_type: str
):
    """워크플로우별 특화된 Supervisor Agent 생성"""
    
    # 기본 프롬프트에 워크플로우별 프롬프트 추가
    full_prompt = BASE_SUPERVISOR_PROMPT
    
    if request_type == "consensus":
        full_prompt += CONSENSUS_WORKFLOW_PROMPT
    elif request_type == "report":
        full_prompt += REPORT_WORKFLOW_PROMPT
    elif request_type == "review":
        full_prompt += REVIEW_WORKFLOW_PROMPT

    # create_supervisor를 사용해 자동 라우팅 및 검증 설정
    workflow = create_supervisor(
        agents=agents,
        model=llm, 
        prompt=full_prompt
    )
    
    return workflow