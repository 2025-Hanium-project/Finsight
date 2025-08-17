"""
D-day Report 워크플로우 - 간단한 최종 결과 반환
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langsmith import traceable
from typing import Dict, Any

from agents.consensus_analyst_agent import create_consensus_analyst_agent
from agents.corporate_analyst_agent import create_corporate_analyst_agent
from agents.industry_analyst_agent import create_industry_analyst_agent
from agents.market_context_analyst_agent import create_market_context_analyst_agent
from agents.quantitative_analyst_agent import create_quantitative_analyst_agent
from agents.report_writer_agent import create_report_writer_agent
from agents.supervisor_agent import create_supervisor_agent

class ReportWorkflow:
    """D-day 리포트 처리 워크플로우 - 간단한 최종 결과 반환"""
    
    def __init__(self, google_api_key: str, request_type: str = "report"):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=0
        )
        self.request_type = request_type
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """워크플로우 그래프 구축"""
        # 6개 분석 에이전트 생성
        consensus_analyst = create_consensus_analyst_agent(self.llm)
        corporate_analyst = create_corporate_analyst_agent(self.llm)
        industry_analyst = create_industry_analyst_agent(self.llm)
        market_context_analyst = create_market_context_analyst_agent(self.llm)
        quantitative_analyst = create_quantitative_analyst_agent(self.llm)
        report_writer = create_report_writer_agent(self.llm)
        
        agents = [
            consensus_analyst,
            corporate_analyst, 
            industry_analyst,
            market_context_analyst,
            quantitative_analyst,
            report_writer
        ]
        
        supervisor_workflow = create_supervisor_agent(
            llm=self.llm,
            agents=agents,
            request_type=self.request_type
        )
        
        return supervisor_workflow.compile(checkpointer=None)
    
    @traceable(name="report_workflow")
    def run(self, inputs: Dict[str, Any]):
        """워크플로우 실행 - 간단한 최종 결과 반환"""
        stock_code = inputs.get("stock_code", "005930")
        
        print(f"🚀 워크플로우 시작: {stock_code}")
        
        input_message = f"종목코드: {stock_code}"
        
        final_state = None
        all_chunks = []
        
        # 스트리밍 실행으로 모든 chunk 수집
        for chunk in self.graph.stream({
            "messages": [HumanMessage(content=input_message)],
            "workflow_config": {
                "workflow_type": "report", 
                "stock_code": stock_code
            }
        }):
            all_chunks.append(chunk)
            final_state = chunk  # 마지막 chunk가 최종 상태
        
        print(f"📊 총 {len(all_chunks)}개의 chunk 수집됨")
        
        # 디버깅을 위한 chunk 구조 출력
        if all_chunks:
            print(f"🔍 첫 번째 chunk 구조: {type(all_chunks[0])}")
            if isinstance(all_chunks[0], dict):
                print(f"🔍 첫 번째 chunk 키: {list(all_chunks[0].keys())}")
        
        # 최종 상태에서 마지막 메시지 추출 (간단한 버전)
        if final_state:
            # supervisor 키가 있으면 그 안에서 messages 찾기
            if isinstance(final_state, dict) and 'supervisor' in final_state:
                supervisor_data = final_state['supervisor']
                if isinstance(supervisor_data, dict) and 'messages' in supervisor_data:
                    messages = supervisor_data['messages']
                    if messages:
                        last_message = messages[-1]
                        if hasattr(last_message, 'content'):
                            final_content = last_message.content
                            if final_content and len(final_content.strip()) > 100:
                                print("✅ supervisor.messages에서 최종 보고서 추출 완료")
                                return final_content
            
            # 방법 2: messages 키에서 직접 추출 (기존)
            if isinstance(final_state, dict) and 'messages' in final_state:
                messages = final_state['messages']
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        final_content = last_message.content
                        if final_content and len(final_content.strip()) > 100:
                            print("✅ messages에서 최종 보고서 추출 완료")
                            return final_content
            
            # 방법 3: 직접 content 키 확인
            if isinstance(final_state, dict) and 'content' in final_state:
                final_content = final_state['content']
                if final_content and len(final_content.strip()) > 100:
                    print("✅ content에서 최종 보고서 추출 완료")
                    return final_content
            
            # 방법 4: supervisor 내부 구조 상세 분석
            if isinstance(final_state, dict) and 'supervisor' in final_state:
                supervisor_data = final_state['supervisor']
                print(f"🔍 supervisor 구조 분석:")
                print(f"  타입: {type(supervisor_data)}")
                if isinstance(supervisor_data, dict):
                    print(f"  키: {list(supervisor_data.keys())}")
                    
                    # supervisor 내부의 모든 키에서 content 찾기
                    for key, value in supervisor_data.items():
                        if key == 'messages' and isinstance(value, list) and value:
                            last_msg = value[-1]
                            if hasattr(last_msg, 'content'):
                                content = last_msg.content
                                if content and len(content.strip()) > 100:
                                    print(f"✅ supervisor.{key}에서 최종 보고서 추출 완료")
                                    return content
                        elif key == 'content' and isinstance(value, str) and len(value.strip()) > 100:
                            print(f"✅ supervisor.{key}에서 최종 보고서 추출 완료")
                            return value
            
            # 방법 5: 마지막 chunk에서 supervisor 구조 확인
            for chunk in reversed(all_chunks):
                if isinstance(chunk, dict) and 'supervisor' in chunk:
                    supervisor_data = chunk['supervisor']
                    if isinstance(supervisor_data, dict) and 'messages' in supervisor_data:
                        messages = supervisor_data['messages']
                        if messages:
                            last_msg = messages[-1]
                            if hasattr(last_msg, 'content'):
                                content = last_msg.content
                                if content and len(content.strip()) > 100:
                                    print("✅ 마지막 chunk의 supervisor.messages에서 최종 보고서 추출 완료")
                                    return content
        
        # 디버깅 정보 출력 (수정된 버전)
        print(f"❌ 최종 결과 추출 실패")
        print(f"🔍 final_state 타입: {type(final_state)}")
        if isinstance(final_state, dict):
            print(f"🔍 final_state 키: {list(final_state.keys())}")
            for key, value in final_state.items():
                print(f" {key}: {type(value)} - {str(value)[:200]}...")
                
                # supervisor 키가 있으면 상세 분석
                if key == 'supervisor' and isinstance(value, dict):
                    print(f"  🔍 supervisor 내부 구조:")
                    print(f"    키: {list(value.keys())}")
                    if 'messages' in value:
                        messages = value['messages']
                        print(f"    messages 개수: {len(messages)}")
                        if messages:
                            last_msg = messages[-1]
                            print(f"    마지막 메시지 타입: {type(last_msg)}")
                            if hasattr(last_msg, 'content'):
                                content = last_msg.content
                                print(f"    마지막 메시지 내용 길이: {len(content) if content else 0}")
        
        # 예외: 최종 결과가 없으면 에러 메시지
        return f"❌ {stock_code} 리포트 생성 실패 - 최종 결과를 찾을 수 없습니다."
