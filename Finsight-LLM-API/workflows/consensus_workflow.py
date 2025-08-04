from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langsmith import traceable
from schemas.schema import ConsensusData

from agents.consensus_processing_agent import create_consensus_processing_agent
from agents.supervisor_agent import create_supervisor_agent

class ConsensusWorkflow:
    """컨센서스 리포트 처리 워크플로우 메인 클래스"""
    
    def __init__(self, google_api_key: str):
        # 기본 LLM 초기화
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key
        )
        # Structured output용 별도 LLM (최종 결과 변환용)
        self.structured_llm = self.llm.with_structured_output(ConsensusData)
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """워크플로우 그래프 구축"""
        # 에이전트 생성 (기본 LLM 사용)
        consensus_processing_agent = create_consensus_processing_agent(self.llm)
        
        # Supervisor 워크플로우 생성 (기본 LLM 사용)
        supervisor_workflow = create_supervisor_agent(
            self.llm, 
            [consensus_processing_agent]
        )
        
        return supervisor_workflow.compile()
    
    @traceable(name="consensus_workflow")  # LangSmith 추적을 위한 데코레이터
    def process(self, file_path: str):
        """파일 처리 워크플로우 실행"""
        inputs = {"messages": [{"role": "user", "content": f"PDF 파일 {file_path}을 분석해서 컨센서스 정보를 추출해주세요."}]}
        
        # 기본 워크플로우 실행
        for chunk in self.graph.stream(
            inputs,
            config={
                "tags": ["consensus-processing", "supervisor"],
                "metadata": {
                    "file_path": file_path,
                    "workflow_type": "consensus"
                }
            }
        ):
            # 최종 결과 감지 후 structured output으로 변환
            if self._is_final_result(chunk):
                json_content = self._extract_json_from_chunk(chunk)
                if json_content:
                    # JSON을 Pydantic 모델로 변환
                    try:
                        structured_result = self.structured_llm.invoke(
                            f"다음 JSON 데이터를 올바른 형식으로 변환해주세요: {json_content}"
                        )
                        yield structured_result
                    except Exception as e:
                        print(f"Structured output 변환 오류: {e}")
                        yield chunk
                else:
                    yield chunk
            else:
                yield chunk
    
    def _is_final_result(self, chunk):
        """최종 결과인지 확인 (JSON 포함 여부로 판단)"""
        if isinstance(chunk, dict):
            for node_name, node_data in chunk.items():
                if node_name == "supervisor" and isinstance(node_data, dict):
                    messages = node_data.get('messages', [])
                    for message in messages:
                        content = getattr(message, 'content', '') or ''
                        # JSON 형태의 최종 결과 감지
                        if content and (content.startswith('{') or '```json' in content):
                            return True
        return False
    
    def _extract_json_from_chunk(self, chunk):
        """Chunk에서 JSON 내용 추출"""
        import json
        import re
        
        if isinstance(chunk, dict):
            for node_name, node_data in chunk.items():
                if isinstance(node_data, dict) and 'messages' in node_data:
                    messages = node_data['messages']
                    
                    for message in messages:
                        content = getattr(message, 'content', '') or ''
                        
                        if content:
                            # 마크다운 코드블록에서 JSON 추출
                            if '```json' in content:
                                json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
                                if json_match:
                                    return json_match.group(1).strip()
                            
                            # 순수 JSON 형태 추출
                            elif content.startswith('{') and content.endswith('}'):
                                return content
        
        return None