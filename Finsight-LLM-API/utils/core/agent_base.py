"""
에이전트 기본 클래스 및 인터페이스

기능:
- 에이전트 기본 클래스 정의
- 에이전트 타입 및 설정 관리
- 에이전트 팩토리 패턴 구현
- 에이전트 등록 및 관리 시스템
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from utils.llm.llm_client import generate_response
from config import AGENT_MODELS, GEMINI_API_KEY

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """에이전트 타입 열거형"""
    FINANCIAL_STATEMENT = "financial_statement"
    NEWS_ANALYSIS = "news_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    GROWTH_ANALYSIS = "growth_analysis"
    VALUATION = "valuation"
    PEER_COMPARISON = "peer_comparison"
    SUPERVISOR = "supervisor"
    MARKET_DATA = "market_data"
    SECURITIES_REPORT = "securities_report"
    DDAY_REPORT = "dday_report"
    DPLUS1_REPORT = "dplus1_report"
    DATA_QUALITY = "data_quality"
    DOCUMENT_PROCESSING = "document_processing"
    FINANCIAL_STATEMENT_AGENT = "financial_statement_agent"
    NEWS_ANALYSIS_AGENT = "news_analysis_agent"
    RISK_ASSESSMENT_AGENT = "risk_assessment_agent"
    GROWTH_ANALYSIS_AGENT = "growth_analysis_agent"
    VALUATION_AGENT = "valuation_agent"
    PEER_COMPARISON_AGENT = "peer_comparison_agent"
    SUPERVISOR_AGENT = "supervisor_agent"
    MARKET_DATA_AGENT = "market_data_agent"
    SECURITIES_REPORT_AGENT = "securities_report_agent"


class AgentCapability(Enum):
    """에이전트 능력 열거형"""
    FINANCIAL_ANALYSIS = "financial_analysis"
    NEWS_ANALYSIS = "news_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    GROWTH_ANALYSIS = "growth_analysis"
    VALUATION = "valuation"
    PEER_COMPARISON = "peer_comparison"
    SUPERVISION = "supervision"
    MARKET_DATA = "market_data"
    DOCUMENT_PROCESSING = "document_processing"
    COLLABORATION = "collaboration"


@dataclass
class AgentConfig:
    """에이전트 설정"""
    name: str
    agent_type: AgentType
    model_name: str = "gemini-2.0-flash"
    temperature: float = 0.7
    max_tokens: int = 4096
    capabilities: List[AgentCapability] = field(default_factory=list)
    is_active: bool = True
    collaboration_enabled: bool = True
    max_retries: int = 3
    timeout: int = 30
    
    def __post_init__(self):
        """초기화 후 처리"""
        if not self.capabilities:
            self.capabilities = [self._get_default_capability()]
    
    def _get_default_capability(self) -> AgentCapability:
        """기본 능력 반환"""
        capability_map = {
            AgentType.FINANCIAL_STATEMENT: AgentCapability.FINANCIAL_ANALYSIS,
            AgentType.NEWS_ANALYSIS: AgentCapability.NEWS_ANALYSIS,
            AgentType.RISK_ASSESSMENT: AgentCapability.RISK_ASSESSMENT,
            AgentType.GROWTH_ANALYSIS: AgentCapability.GROWTH_ANALYSIS,
            AgentType.VALUATION: AgentCapability.VALUATION,
            AgentType.PEER_COMPARISON: AgentCapability.PEER_COMPARISON,
            AgentType.SUPERVISOR: AgentCapability.SUPERVISION,
            AgentType.MARKET_DATA: AgentCapability.MARKET_DATA,
            AgentType.SECURITIES_REPORT: AgentCapability.DOCUMENT_PROCESSING,
            AgentType.DDAY_REPORT: AgentCapability.DOCUMENT_PROCESSING,
            AgentType.DPLUS1_REPORT: AgentCapability.DOCUMENT_PROCESSING,
            AgentType.DATA_QUALITY: AgentCapability.DOCUMENT_PROCESSING,
            AgentType.DOCUMENT_PROCESSING: AgentCapability.DOCUMENT_PROCESSING,
        }
        return capability_map.get(self.agent_type, AgentCapability.COLLABORATION)
    
    def update_config(self, **kwargs):
        """설정 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        logger.info(f"에이전트 설정 업데이트: {self.name} - {kwargs}")


class AnalysisAgent(ABC):
    """분석 에이전트 기본 클래스"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.name = config.name
        self.agent_type = config.agent_type
        self.model_name = config.model_name
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.capabilities = config.capabilities
        self.is_active = config.is_active
        self.collaboration_enabled = config.collaboration_enabled
        self.max_retries = config.max_retries
        self.timeout = config.timeout
        
        # 로깅 설정
        self.logger = logging.getLogger(f"agent.{self.name}")
        
        # 성능 통계
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0
        
        logger.info(f"에이전트 초기화: {self.name} ({self.agent_type.value})")
    
    @abstractmethod
    async def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """분석 수행 (추상 메서드)"""
        pass
    
    @abstractmethod
    def _create_prompt(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any] = None) -> str:
        """프롬프트 생성 (추상 메서드)"""
        pass
    
    async def _execute_analysis(self, input_data: Dict[str, Any], collaboration_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """분석 실행"""
        try:
            start_time = datetime.now()
            self.total_requests += 1
            
            # 프롬프트 생성
            prompt = self._create_prompt(input_data, collaboration_data)
            
            # LLM 호출
            response = await generate_response(
                prompt=prompt,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # 응답 파싱
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트 응답으로 처리
                result = {
                    "analysis_type": self.agent_type.value,
                    "analysis_result": response,
                    "agent_name": self.name,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 성능 통계 업데이트
            execution_time = (datetime.now() - start_time).total_seconds()
            self.successful_requests += 1
            if self.total_requests > 0:
                self.average_response_time = (
                    (self.average_response_time * (self.total_requests - 1) + execution_time) 
                    / self.total_requests
                )
            
            # 결과에 메타데이터 추가
            result.update({
                "agent_name": self.name,
                "agent_type": self.agent_type.value,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            })
            
            self.logger.info(f"분석 완료: {self.name} (소요시간: {execution_time:.2f}초)")
            return result
            
        except Exception as e:
            self.failed_requests += 1
            self.logger.error(f"분석 실패: {self.name} - {str(e)}")
            return {
                "error": str(e),
                "agent_name": self.name,
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """에이전트 건강 상태 반환"""
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            "name": self.name,
            "agent_type": self.agent_type.value,
            "is_active": self.is_active,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "average_response_time": self.average_response_time,
            "capabilities": [cap.value for cap in self.capabilities],
            "model_name": self.model_name,
            "collaboration_enabled": self.collaboration_enabled
        }
    
    def update_config(self, **kwargs):
        """설정 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                setattr(self, key, value)
        
        self.logger.info(f"설정 업데이트: {self.name} - {kwargs}")
    
    def reset_statistics(self):
        """통계 초기화"""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.average_response_time = 0.0
        self.logger.info(f"통계 초기화: {self.name}")


# 에이전트 팩토리 및 등록 시스템
class AgentRegistry:
    """에이전트 등록 시스템"""
    
    def __init__(self):
        self.agents: Dict[str, AnalysisAgent] = {}
        self.agent_factories: Dict[AgentType, Callable] = {}
        self.logger = logging.getLogger("agent_registry")
    
    def register_agent(self, agent: AnalysisAgent):
        """에이전트 등록"""
        self.agents[agent.name] = agent
        self.logger.info(f"에이전트 등록: {agent.name}")
    
    def register_factory(self, agent_type: AgentType, factory_func: Callable):
        """에이전트 팩토리 등록"""
        self.agent_factories[agent_type] = factory_func
        self.logger.info(f"에이전트 팩토리 등록: {agent_type.value}")
    
    def create_agent(self, agent_type: AgentType, config: AgentConfig) -> Optional[AnalysisAgent]:
        """에이전트 생성"""
        if agent_type in self.agent_factories:
            try:
                agent = self.agent_factories[agent_type](config)
                self.register_agent(agent)
                return agent
            except Exception as e:
                self.logger.error(f"에이전트 생성 실패: {agent_type.value} - {str(e)}")
                return None
        else:
            self.logger.error(f"등록되지 않은 에이전트 타입: {agent_type.value}")
            return None
    
    def get_agent(self, name: str) -> Optional[AnalysisAgent]:
        """에이전트 조회"""
        return self.agents.get(name)
    
    def get_all_agents(self) -> List[AnalysisAgent]:
        """모든 에이전트 조회"""
        return list(self.agents.values())
    
    def get_active_agents(self) -> List[AnalysisAgent]:
        """활성 에이전트 조회"""
        return [agent for agent in self.agents.values() if agent.is_active]
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[AnalysisAgent]:
        """타입별 에이전트 조회"""
        return [agent for agent in self.agents.values() if agent.agent_type == agent_type]
    
    def remove_agent(self, name: str):
        """에이전트 제거"""
        if name in self.agents:
            del self.agents[name]
            self.logger.info(f"에이전트 제거: {name}")
    
    def get_registry_status(self) -> Dict[str, Any]:
        """등록 시스템 상태 반환"""
        return {
            "total_agents": len(self.agents),
            "active_agents": len(self.get_active_agents()),
            "registered_types": [agent_type.value for agent_type in self.agent_factories.keys()],
            "agent_names": list(self.agents.keys())
        }


# 전역 에이전트 레지스트리
_agent_registry = AgentRegistry()

def get_agent_registry() -> AgentRegistry:
    """에이전트 레지스트리 인스턴스 반환"""
    return _agent_registry


# 유틸리티 함수들
def create_standard_prompt_template(
    agent_name: str = "",
    task_description: str = "",
    output_schema: Dict[str, str] = None,
    collaboration_info: str = ""
) -> str:
    """표준 프롬프트 템플릿 생성"""
    
    # 기본 출력 스키마
    if output_schema is None:
        output_schema = {
            "analysis_result": "분석 결과",
            "confidence_score": "신뢰도 (0-100)"
        }
    
    # 스키마를 JSON 형식으로 변환
    schema_json = "{\n"
    for key, description in output_schema.items():
        schema_json += f'  "{key}": "{description}",\n'
    schema_json = schema_json.rstrip(",\n") + "\n}"
    
    # 협업 정보 포맷팅
    collaboration_section = ""
    if collaboration_info:
        collaboration_section = f"\n\n협업 데이터:\n{collaboration_info}"
    
    # 프롬프트 템플릿 생성
    template = f"""당신은 {agent_name}입니다.

{task_description}

분석해야 할 데이터:
{{input_data}}

{collaboration_section}

분석 결과를 다음 JSON 형식으로 제공해주세요:
{schema_json}

중요: 제공된 데이터를 기반으로 구체적이고 실용적인 분석을 제공하세요."""
    
    return template


def get_agent_health_report() -> Dict[str, Any]:
    """에이전트 건강 상태 리포트"""
    registry = get_agent_registry()
    agents = registry.get_all_agents()
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_agents": len(agents),
        "active_agents": len([a for a in agents if a.is_active]),
        "agents": []
    }
    
    for agent in agents:
        agent_status = agent.get_health_status()
        report["agents"].append(agent_status)
    
    return report 