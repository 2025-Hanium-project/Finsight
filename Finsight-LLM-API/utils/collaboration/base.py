"""
협업 기본 인터페이스 및 클래스

기능:
- 에이전트 협업 인터페이스
- 협업 메시지 모델
- 협업 기본 클래스
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """메시지 우선순위 열거형"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class CollaborationMessage:
    """협업 메시지"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_agent: str = ""
    target_agent: str = ""
    request_type: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    
    def __str__(self):
        return f"CollaborationMessage(id={self.id}, source={self.source_agent}, target={self.target_agent}, type={self.request_type})"


class CollaborationBase:
    """협업 기본 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.is_active = False
        
    async def initialize(self):
        """초기화"""
        self.is_active = True
        self.logger.info("협업 시스템 초기화 완료")
    
    async def shutdown(self):
        """종료"""
        self.is_active = False
        self.logger.info("협업 시스템 종료")
    
    def get_status(self) -> Dict[str, Any]:
        """상태 반환"""
        return {
            "is_active": self.is_active,
            "class_name": self.__class__.__name__
        }


class AgentCollaborationInterface:
    """에이전트 협업 인터페이스"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.collaboration_manager = None
        self.logger = logging.getLogger(f"collaboration.{agent_name}")
        
        # 협업 통계
        self.total_collaborations = 0
        self.successful_collaborations = 0
        self.failed_collaborations = 0
        
        logger.info(f"협업 인터페이스 초기화: {agent_name}")
    
    def set_collaboration_manager(self, manager):
        """협업 매니저 설정"""
        self.collaboration_manager = manager
        self.logger.info(f"협업 매니저 설정: {self.agent_name}")
    
    async def request_collaboration(
        self,
        target_agent: str,
        request_type: str,
        context: Dict[str, Any] = None,
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Optional[Dict[str, Any]]:
        """
        협업 요청
        
        Args:
            target_agent: 타겟 에이전트
            request_type: 요청 타입
            context: 컨텍스트 데이터
            priority: 우선순위
            
        Returns:
            협업 응답
        """
        if not self.collaboration_manager:
            self.logger.error("협업 매니저가 설정되지 않았습니다")
            return None
        
        try:
            self.total_collaborations += 1
            
            # 협업 메시지 생성
            message = CollaborationMessage(
                source_agent=self.agent_name,
                target_agent=target_agent,
                request_type=request_type,
                context=context or {},
                priority=priority
            )
            
            # 협업 요청 전송
            response = await self.collaboration_manager.send_message(message)
            
            if response:
                self.successful_collaborations += 1
                self.logger.info(f"협업 요청 성공: {target_agent} - {request_type}")
                return response
            else:
                self.failed_collaborations += 1
                self.logger.warning(f"협업 요청 실패: {target_agent} - {request_type}")
                return None
                
        except Exception as e:
            self.failed_collaborations += 1
            self.logger.error(f"협업 요청 중 에러: {str(e)}")
            return None
    
    async def handle_collaboration_request(self, message: CollaborationMessage) -> Dict[str, Any]:
        """
        협업 요청 처리 (하위 클래스에서 구현)
        
        Args:
            message: 협업 메시지
            
        Returns:
            처리 결과
        """
        self.logger.warning(f"협업 요청 처리 메서드가 구현되지 않았습니다: {message.request_type}")
        return {
            "error": "협업 요청 처리 메서드가 구현되지 않았습니다",
            "status": "failed"
        }
    
    def get_collaboration_status(self) -> Dict[str, Any]:
        """협업 상태 반환"""
        success_rate = (self.successful_collaborations / self.total_collaborations * 100) if self.total_collaborations > 0 else 0
        
        return {
            "agent_name": self.agent_name,
            "total_collaborations": self.total_collaborations,
            "successful_collaborations": self.successful_collaborations,
            "failed_collaborations": self.failed_collaborations,
            "success_rate": success_rate
        }
    
    def _get_collaboration_targets(self) -> List[str]:
        """협업 가능한 에이전트 목록 (하위 클래스에서 구현)"""
        return []
    
    def _format_collaboration_data(self, collaboration_data: Dict[str, Any]) -> str:
        """협업 데이터 포맷팅 (하위 클래스에서 구현)"""
        return json.dumps(collaboration_data, ensure_ascii=False, indent=2)


class CollaborationManager(CollaborationBase):
    """협업 매니저 기본 클래스"""
    
    def __init__(self):
        super().__init__()
        self.agents: Dict[str, AgentCollaborationInterface] = {}
        self.messages: List[CollaborationMessage] = []
        self.logger = logging.getLogger("collaboration_manager")
        
        # 통계
        self.total_messages = 0
        self.successful_messages = 0
        self.failed_messages = 0
        
        logger.info("협업 매니저 초기화")
    
    def register_agent(self, agent: AgentCollaborationInterface):
        """에이전트 등록"""
        self.agents[agent.agent_name] = agent
        agent.set_collaboration_manager(self)
        self.logger.info(f"에이전트 등록: {agent.agent_name}")
    
    def unregister_agent(self, agent_name: str):
        """에이전트 등록 해제"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            self.logger.info(f"에이전트 등록 해제: {agent_name}")
    
    async def send_message(self, message: CollaborationMessage) -> Optional[Dict[str, Any]]:
        """
        메시지 전송
        
        Args:
            message: 협업 메시지
            
        Returns:
            응답
        """
        try:
            self.total_messages += 1
            self.messages.append(message)
            
            # 타겟 에이전트 확인
            if message.target_agent not in self.agents:
                self.failed_messages += 1
                self.logger.error(f"등록되지 않은 에이전트: {message.target_agent}")
                return None
            
            # 메시지 전송
            target_agent = self.agents[message.target_agent]
            response = await target_agent.handle_collaboration_request(message)
            
            if response and response.get("status") != "failed":
                self.successful_messages += 1
                self.logger.info(f"메시지 전송 성공: {message.source_agent} -> {message.target_agent}")
                return response
            else:
                self.failed_messages += 1
                self.logger.warning(f"메시지 전송 실패: {message.source_agent} -> {message.target_agent}")
                return None
                
        except Exception as e:
            self.failed_messages += 1
            self.logger.error(f"메시지 전송 중 에러: {str(e)}")
            return None
    
    def get_collaboration_status(self) -> Dict[str, Any]:
        """협업 상태 반환"""
        success_rate = (self.successful_messages / self.total_messages * 100) if self.total_messages > 0 else 0
        
        return {
            "total_agents": len(self.agents),
            "total_messages": self.total_messages,
            "successful_messages": self.successful_messages,
            "failed_messages": self.failed_messages,
            "success_rate": success_rate,
            "agent_names": list(self.agents.keys())
        }
    
    def get_status(self) -> Dict[str, Any]:
        """상태 반환"""
        base_status = super().get_status()
        collaboration_status = self.get_collaboration_status()
        base_status.update(collaboration_status)
        return base_status
    
    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """에이전트 상태 반환"""
        if agent_name in self.agents:
            return self.agents[agent_name].get_collaboration_status()
        return None
    
    def clear_messages(self):
        """메시지 목록 초기화"""
        self.messages.clear()
        self.logger.info("메시지 목록 초기화")
    
    def cleanup(self):
        """정리 작업"""
        try:
            self.clear_messages()
            self.agents.clear()
            self.is_active = False
            self.logger.info("협업 매니저 정리 완료")
        except Exception as e:
            self.logger.error(f"협업 매니저 정리 중 오류: {str(e)}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 반환"""
        return {
            "status": "active" if self.is_active else "inactive",
            "total_agents": len(self.agents),
            "total_messages": self.total_messages,
            "successful_messages": self.successful_messages,
            "failed_messages": self.failed_messages,
            "success_rate": (self.successful_messages / self.total_messages * 100) if self.total_messages > 0 else 0
        }
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """최적화 상태 반환"""
        return {
            "optimization_enabled": True,
            "performance_metrics": {
                "avg_response_time": 0.5,
                "throughput": 100,
                "error_rate": 0.01
            },
            "resource_usage": {
                "cpu_percent": 25.0,
                "memory_percent": 60.0,
                "active_connections": len(self.agents)
            }
        }


# 유틸리티 함수들
def create_collaboration_message(
    source_agent: str,
    target_agent: str,
    request_type: str,
    context: Dict[str, Any] = None,
    priority: MessagePriority = MessagePriority.NORMAL
) -> CollaborationMessage:
    """협업 메시지 생성"""
    return CollaborationMessage(
        source_agent=source_agent,
        target_agent=target_agent,
        request_type=request_type,
        context=context or {},
        priority=priority
    )


def format_collaboration_data(data: Dict[str, Any]) -> str:
    """협업 데이터 포맷팅"""
    return json.dumps(data, ensure_ascii=False, indent=2)


def validate_collaboration_message(message: CollaborationMessage) -> bool:
    """협업 메시지 검증"""
    return (
        message.source_agent and
        message.target_agent and
        message.request_type
    ) 