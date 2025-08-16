from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langsmith import traceable
from schemas.schema import ConsensusData
from typing import Dict, Any
import json
import re
from langchain_core.messages import HumanMessage

from agents.consensus_processing_agent import create_consensus_processing_agent
from agents.supervisor_agent import create_supervisor_agent

class ConsensusWorkflow:
    """컨센서스 리포트 처리 워크플로우 메인 클래스"""
    
    def __init__(self, google_api_key: str, request_type: str = "consensus"):
        """워크플로우 초기화
        
        Args:
            google_api_key: Google API 키
            request_type: 요청 타입 (consensus, report, review)
        """
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0
        )
        self.request_type = request_type
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """워크플로우 그래프 구축"""
        # 컨센서스 처리 에이전트 생성
        consensus_processing_agent = create_consensus_processing_agent(self.llm)
        
        # Supervisor 워크플로우 생성
        supervisor_workflow = create_supervisor_agent(
            self.llm, 
            [consensus_processing_agent],
            self.request_type
        )
        
        return supervisor_workflow.compile()
    
    @traceable(name="consensus_workflow")  # LangSmith 추적
    def run(self, inputs: Dict[str, Any]):
        """워크플로우 실행
        
        Args:
            inputs: 입력 데이터 (file_path 포함)
            
        Yields:
            처리 결과 또는 중간 chunk
        """
        print(f"워크플로우 실행: {inputs}")
    
        final_result = None
        
        # 스트리밍 실행
        for chunk in self.graph.stream(
            {
                "messages": [HumanMessage(content=inputs.get("file_path", ""))],
                "workflow_config": {
                    "workflow_type": "consensus"
                }
            }
        ):
            # supervisor에서 최종 JSON 결과가 나오면 저장
            if self._is_final_json_result(chunk):
                json_content = self._extract_json_from_chunk(chunk)
                if json_content:
                    try:
                        final_result = json.loads(json_content)
                        print(f"최종 결과 추출 완료: {final_result.get('stock_code', 'Unknown')}")
                        break  # 최종 결과를 찾으면 중단
                    except json.JSONDecodeError as e:
                        print(f"JSON 파싱 오류: {e}")
                        final_result = {"error": "JSON 파싱 실패", "raw_content": json_content}
                        break
        
        # 최종 결과가 없으면 에러 반환
        if final_result is None:
            final_result = {"error": "최종 결과를 찾을 수 없습니다"}
        
        return final_result
    
    def _is_final_json_result(self, chunk):
        """supervisor에서 나온 최종 JSON 결과인지 확인"""
        if isinstance(chunk, dict):
            for node_name, node_data in chunk.items():
                if node_name == "supervisor" and isinstance(node_data, dict):
                    messages = node_data.get('messages', [])
                    for message in messages:
                        content = getattr(message, 'content', '') or ''
                        # 완전한 JSON 구조 확인 (stock_code와 summary 필드로 판단)
                        if content and ('"stock_code"' in content and '"summary"' in content):
                            return True
        return False
    
    def _extract_json_from_chunk(self, chunk):
        """Chunk에서 JSON 내용 추출"""
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
                            
                            # 순수 JSON 형태 추출 (stock_code가 포함된 완전한 JSON만)
                            elif content.startswith('{') and content.endswith('}') and '"stock_code"' in content:
                                return content
        
        return None