from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph_supervisor import create_supervisor
from .prompts import SUPERVISOR_PROMPT

def create_supervisor_agent(llm: ChatGoogleGenerativeAI, agents: list):
    """
    Supervisor agent 생성 (기본 LLM 사용)
    
    역할: 에이전트 라우팅 및 결과 검토
    Args:
        llm: ChatGoogleGenerativeAI 모델
        agents: 관리할 에이전트들의 리스트
    
    Returns:
        StateGraph: 컴파일된 워크플로우 그래프
    """
    # create_supervisor를 사용해 자동 라우팅 설정
    workflow = create_supervisor(
        agents=agents,
        model=llm,  # 기본 LLM 사용 (도구 바인딩 호환성 위해)
        prompt=SUPERVISOR_PROMPT
    )
    
    return workflow