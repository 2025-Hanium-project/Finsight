"""
협업 기반 에이전트 기본 클래스
"""
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from utils.llm_client import generate_response
from error_handlers import AgentError, ParsingError, get_security_manager

logger = logging.getLogger(__name__)
security_manager = get_security_manager()


class AgentType(Enum):
    """에이전트 타입 정의"""
    # 데이터 소스별 에이전트
    FINANCIAL_STATEMENT = "financial_statement"
    NEWS_ANALYSIS = "news_analysis"
    SECURITIES_REPORT = "securities_report"
    MARKET_DATA = "market_data"
    
    # 분석 유형별 에이전트
    RISK_ASSESSMENT = "risk_assessment"
    GROWTH_ANALYSIS = "growth_analysis"
    VALUATION = "valuation"
    PEER_COMPARISON = "peer_comparison"
    
    # 보고서 작성 에이전트
    DDAY_REPORT = "dday_report"
    DPLUS1_REPORT = "dplus1_report"
    
    # 지원 에이전트
    DOCUMENT_PROCESSING = "document_processing"
    DATA_QUALITY = "data_quality"
    SUPERVISOR = "supervisor"


@dataclass
class AgentRequest:
    """에이전트 간 요청 데이터"""
    source_agent: str
    target_agent: str
    request_type: str
    data: Dict[str, Any]
    priority: int = 1
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class AgentResponse:
    """에이전트 간 응답 데이터"""
    source_agent: str
    target_agent: str
    response_type: str
    data: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CollaborationManager:
    """에이전트 간 협업 관리"""
    
    def __init__(self):
        self.agents: Dict[str, 'BaseAgent'] = {}
        self.request_queue: List[AgentRequest] = []
        self.response_cache: Dict[str, AgentResponse] = {}
        self.logger = logging.getLogger("collaboration_manager")
    
    def register_agent(self, agent: 'BaseAgent'):
        """에이전트 등록"""
        self.agents[agent.agent_name] = agent
        self.logger.info(f"에이전트 등록: {agent.agent_name}")
    
    async def request_data(self, request: AgentRequest) -> Optional[AgentResponse]:
        """다른 에이전트에게 데이터 요청"""
        if request.target_agent not in self.agents:
            self.logger.error(f"존재하지 않는 에이전트: {request.target_agent}")
            return None
        
        target_agent = self.agents[request.target_agent]
        
        try:
            # 캐시된 응답 확인
            cache_key = f"{request.target_agent}_{request.request_type}_{hash(str(request.data))}"
            if cache_key in self.response_cache:
                cached_response = self.response_cache[cache_key]
                if (datetime.now() - cached_response.timestamp).seconds < 300:  # 5분 캐시
                    return cached_response
            
            # 에이전트 실행
            result = await target_agent.execute({
                "request_type": request.request_type,
                **request.data
            })
            
            response = AgentResponse(
                source_agent=request.target_agent,
                target_agent=request.source_agent,
                response_type=request.request_type,
                data=result,
                success=True
            )
            
            # 캐시에 저장
            self.response_cache[cache_key] = response
            
            return response
            
        except Exception as e:
            self.logger.error(f"에이전트 요청 실패: {str(e)}")
            return AgentResponse(
                source_agent=request.target_agent,
                target_agent=request.source_agent,
                response_type=request.request_type,
                data={},
                success=False,
                error_message=str(e)
            )
    
    async def broadcast_request(self, source_agent: str, request_type: str, data: Dict[str, Any]) -> List[AgentResponse]:
        """모든 에이전트에게 브로드캐스트 요청"""
        responses = []
        
        for agent_name, agent in self.agents.items():
            if agent_name != source_agent:
                request = AgentRequest(
                    source_agent=source_agent,
                    target_agent=agent_name,
                    request_type=request_type,
                    data=data
                )
                
                response = await self.request_data(request)
                if response:
                    responses.append(response)
        
        return responses


class BaseAgent:
    """협업 기반 에이전트 기본 클래스"""
    
    def __init__(self, agent_name: str, agent_type: AgentType):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.collaboration_manager: Optional[CollaborationManager] = None
        self.logger = logging.getLogger(f"agent.{agent_name}")
        
        # 에이전트별 설정
        self.temperature = 0.7
        self.max_retries = 3
        self.timeout = 30
        
        # 협업 가능한 에이전트 목록
        self.collaboration_targets = self._get_collaboration_targets()
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록 반환 (하위 클래스에서 구현)"""
        return []
    
    def set_collaboration_manager(self, manager: CollaborationManager):
        """협업 매니저 설정"""
        self.collaboration_manager = manager
        manager.register_agent(self)
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 실행"""
        self.logger.info(f"{self.agent_name} 에이전트 시작")
        start_time = datetime.now()
        
        try:
            # 입력 검증
            self._validate_input(input_data)
            
            # 보안 처리
            safe_input = security_manager.sanitize_input(input_data)
            
            # 협업 데이터 수집
            collaboration_data = await self._gather_collaboration_data(safe_input)
            
            # 프롬프트 생성
            prompt = self._create_prompt(safe_input, collaboration_data)
            
            # LLM 호출
            response = await generate_response(
                prompt=prompt,
                agent_type=self.agent_name,
                temperature=self.temperature
            )
            
            # 응답 파싱
            result = self._parse_response(response)
            
            # 후처리
            final_result = self._post_process(result, safe_input, collaboration_data)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"{self.agent_name} 완료: {processing_time:.3f}s")
            
            return final_result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"{self.agent_name} 실패: {str(e)} ({processing_time:.3f}s)")
            raise AgentError(
                agent_name=self.agent_name,
                message=f"{self.agent_name} 에이전트 실행 실패: {str(e)}"
            )
    
    async def _gather_collaboration_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """협업 데이터 수집"""
        if not self.collaboration_manager or not self.collaboration_targets:
            return {}
        
        collaboration_data = {}
        
        for target_agent in self.collaboration_targets:
            try:
                request = AgentRequest(
                    source_agent=self.agent_name,
                    target_agent=target_agent,
                    request_type="data_request",
                    data=input_data
                )
                
                response = await self.collaboration_manager.request_data(request)
                if response and response.success:
                    collaboration_data[target_agent] = response.data
                
            except Exception as e:
                self.logger.warning(f"협업 데이터 수집 실패 ({target_agent}): {str(e)}")
        
        return collaboration_data
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """입력 데이터 검증 (하위 클래스에서 구현)"""
        if not input_data:
            raise AgentError(
                agent_name=self.agent_name,
                message="입력 데이터가 비어있습니다"
            )
    
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> str:
        """프롬프트 생성 (하위 클래스에서 구현)"""
        raise NotImplementedError("하위 클래스에서 구현해야 합니다")
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """LLM 응답 파싱"""
        try:
            # JSON 응답 파싱
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError as e:
            # JSON 파싱 실패 시 텍스트에서 JSON 추출 시도
            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return parsed
            except:
                pass
            
            raise ParsingError(
                message=f"{self.agent_name} 응답 파싱 실패",
                raw_response=response[:500],
                expected_schema="JSON"
            )
    
    def _post_process(self, result: Dict[str, Any], input_data: Dict[str, Any], collaboration_data: Dict[str, Any]) -> Dict[str, Any]:
        """결과 후처리"""
        # 기본 메타데이터 추가
        result.update({
            "agent_name": self.agent_name,
            "agent_type": self.agent_type.value,
            "generated_at": datetime.now().isoformat(),
            "collaboration_data": list(collaboration_data.keys()) if collaboration_data else []
        })
        return result


class DataSourceAgent(BaseAgent):
    """데이터 소스별 에이전트 기본 클래스"""
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        super()._validate_input(input_data)
        
        if "data_source" not in input_data:
            raise AgentError(
                agent_name=self.agent_name,
                message="데이터 소스 정보가 필요합니다"
            )


class AnalysisAgent(BaseAgent):
    """분석 유형별 에이전트 기본 클래스"""
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        super()._validate_input(input_data)
        
        # 다양한 키 이름 지원
        analysis_target_keys = ["analysis_target", "target_type", "target_name", "data_source"]
        has_valid_key = any(key in input_data for key in analysis_target_keys)
        
        if not has_valid_key:
            raise AgentError(
                agent_name=self.agent_name,
                message="분석 대상 정보가 필요합니다"
            )


class ReportAgent(BaseAgent):
    """보고서 작성 에이전트 기본 클래스"""
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        super()._validate_input(input_data)
        
        if "report_type" not in input_data:
            raise AgentError(
                agent_name=self.agent_name,
                message="보고서 타입 정보가 필요합니다"
            )


class SupportAgent(BaseAgent):
    """지원 에이전트 기본 클래스"""
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        super()._validate_input(input_data)
        
        if "task_type" not in input_data:
            raise AgentError(
                agent_name=self.agent_name,
                message="작업 타입 정보가 필요합니다"
            )


# 전역 협업 매니저 인스턴스
collaboration_manager = CollaborationManager()


def get_collaboration_manager() -> CollaborationManager:
    """전역 협업 매니저 반환"""
    return collaboration_manager


def create_standard_prompt_template(
    agent_name: str,
    task_description: str,
    output_schema: Dict[str, str],
    collaboration_info: str = ""
) -> str:
    """표준 프롬프트 템플릿 생성"""
    
    schema_description = "\n".join([
        f'  "{field}": "{description}"'
        for field, description in output_schema.items()
    ])
    
    collaboration_section = ""
    if collaboration_info:
        collaboration_section = f"""
**협업 데이터**:
{collaboration_info}
"""
    
    # 문자열 포맷팅 충돌을 피하기 위해 다른 방식 사용
    template = f"""
당신은 전문적인 {agent_name}입니다.

**작업**: {task_description}

**분석 대상**: {{target_type}} - {{target_name}}

**입력 데이터**:
{{input_data}}

{collaboration_section}
**출력 형식** (반드시 JSON 형식으로):
{{
{schema_description}
}}

**중요 사항**:
1. 모든 응답은 한국어로 작성
2. JSON 형식만 반환 (설명 불필요)
3. 객관적이고 전문적인 분석 제공
4. 근거가 불충분한 경우 "정보 부족"으로 표시
5. 협업 데이터가 있는 경우 이를 참고하여 분석
"""
    
    return template


def format_agent_response(
    agent_name: str,
    result: Dict[str, Any],
    target_type: str = "",
    target_name: str = ""
) -> Dict[str, Any]:
    """에이전트 응답 표준 형식"""
    return {
        "agent_type": agent_name,
        "target_type": target_type,
        "target_name": target_name,
        "success": True,
        "result": result,
        "generated_at": datetime.now().isoformat(),
        "processing_time": 0.0
    } 