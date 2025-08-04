from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from .prompts import CONSENSUS_PROCESSING_PROMPT
from tools.document_tools import extract_pdf

def create_consensus_processing_agent(llm: ChatGoogleGenerativeAI):
    """컨센서스 파서 에이전트 생성
    
    PDF 추출 → JSON 파싱 작업을 담당하는 에이전트
    """
    agent = create_react_agent(
        llm,
        tools=[extract_pdf],  
        prompt=CONSENSUS_PROCESSING_PROMPT,
        name='consensus_processing_agent'
    )
    return agent
