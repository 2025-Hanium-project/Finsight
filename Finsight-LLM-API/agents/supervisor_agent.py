from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph_supervisor import create_supervisor

# Supervisor Agent 프롬프트
SUPERVISOR_PROMPT = """
당신은 컨센서스 처리 워크플로우의 감독자입니다.

역할:
1. **라우팅**: 요청에 따라 적절한 에이전트로 작업을 전달
2. **검증**: 에이전트 결과를 검토하고 품질을 확인
3. **피드백**: 문제가 있을 경우 수정 요청 및 피드백 제공
4. **최종 승인**: 검증 완료 후 structured output 형식으로 반환

작업 흐름:
1. 요청이 오면 consensus_processing_agent로 전달
2. 에이전트가 JSON 결과를 반환하면 다음을 검토:
   - 필수 필드가 모두 있는지 확인
   - investment_rationale이 리포트 본문을 충분히 포함하고 있는지 검증
   - 텍스트에 줄바꿈 문자가 없는지 확인
   - target_price가 숫자 형태인지 확인
   - 원본 텍스트와 추출된 정보의 일치성 검증

3. **검증 실패 시**: 구체적인 피드백과 함께 에이전트에게 재작업 요청
4. **검증 성공 시**: structured output 형식으로 최종 데이터 반환

**중요**: 
- 최종 응답은 structured output으로 자동 처리되므로 JSON 형식을 명시적으로 작성할 필요가 없습니다.
- 품질 보장을 위해 철저한 검증을 수행하세요.
- 피드백은 구체적이고 실행 가능한 내용으로 제공하세요.
"""

def create_supervisor_agent(llm: ChatGoogleGenerativeAI, agents: list):
    """
    Supervisor agent 생성
    
    역할: 
    - 에이전트 라우팅 및 작업 분배
    - 결과 검증 및 품질 관리
    - 피드백 루프를 통한 결과 개선
    
    Args:
        llm: ChatGoogleGenerativeAI 모델
        agents: 관리할 에이전트들의 리스트
    
    Returns:
        StateGraph: 컴파일된 워크플로우 그래프
    """
    # create_supervisor를 사용해 자동 라우팅 및 검증 설정
    workflow = create_supervisor(
        agents=agents,
        model=llm, 
        prompt=SUPERVISOR_PROMPT
    )
    
    return workflow