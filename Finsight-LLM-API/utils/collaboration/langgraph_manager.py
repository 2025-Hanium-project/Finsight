"""
LangGraph 기반 협업 관리자

LangGraph를 사용한 고급 에이전트 협업 시스템을 제공합니다.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CollaborationType(Enum):
    """협업 타입"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HIERARCHICAL = "hierarchical"
    ADAPTIVE = "adaptive"


@dataclass
class CollaborationNode:
    """협업 노드"""
    agent_id: str
    agent_type: str
    capabilities: List[str]
    dependencies: List[str] = None
    priority: int = 1
    is_active: bool = True


@dataclass
class CollaborationEdge:
    """협업 엣지"""
    from_agent: str
    to_agent: str
    collaboration_type: CollaborationType
    weight: float = 1.0
    conditions: Dict[str, Any] = None


class LangGraphManager:
    """LangGraph 기반 협업 관리자"""
    
    def __init__(self):
        """LangGraph 관리자 초기화"""
        self.nodes = {}
        self.edges = []
        self.workflows = {}
        self.execution_history = []
        
        logger.info("LangGraph 관리자 초기화 완료")
    
    def add_agent_node(self, agent_id: str, agent_type: str, capabilities: List[str], 
                       dependencies: List[str] = None, priority: int = 1):
        """에이전트 노드 추가"""
        try:
            node = CollaborationNode(
                agent_id=agent_id,
                agent_type=agent_type,
                capabilities=capabilities,
                dependencies=dependencies or [],
                priority=priority
            )
            
            self.nodes[agent_id] = node
            logger.info(f"에이전트 노드 추가: {agent_id}")
            
        except Exception as e:
            logger.error(f"에이전트 노드 추가 실패: {str(e)}")
    
    def add_collaboration_edge(self, from_agent: str, to_agent: str, 
                              collaboration_type: CollaborationType, weight: float = 1.0,
                              conditions: Dict[str, Any] = None):
        """협업 엣지 추가"""
        try:
            edge = CollaborationEdge(
                from_agent=from_agent,
                to_agent=to_agent,
                collaboration_type=collaboration_type,
                weight=weight,
                conditions=conditions or {}
            )
            
            self.edges.append(edge)
            logger.info(f"협업 엣지 추가: {from_agent} -> {to_agent}")
            
        except Exception as e:
            logger.error(f"협업 엣지 추가 실패: {str(e)}")
    
    def create_workflow(self, workflow_id: str, nodes: List[str], edges: List[tuple]):
        """워크플로우 생성"""
        try:
            workflow = {
                'id': workflow_id,
                'nodes': nodes,
                'edges': edges,
                'created_at': datetime.now(),
                'status': 'created'
            }
            
            self.workflows[workflow_id] = workflow
            logger.info(f"워크플로우 생성: {workflow_id}")
            
        except Exception as e:
            logger.error(f"워크플로우 생성 실패: {str(e)}")
    
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """워크플로우 실행"""
        try:
            if workflow_id not in self.workflows:
                raise ValueError(f"워크플로우를 찾을 수 없습니다: {workflow_id}")
            
            workflow = self.workflows[workflow_id]
            workflow['status'] = 'executing'
            workflow['started_at'] = datetime.now()
            
            # 실행 로직 (시뮬레이션)
            result = {
                'workflow_id': workflow_id,
                'status': 'completed',
                'input_data': input_data,
                'output_data': {},
                'execution_time': 0.0,
                'completed_at': datetime.now()
            }
            
            # 실행 히스토리에 추가
            self.execution_history.append({
                'workflow_id': workflow_id,
                'execution_time': datetime.now(),
                'result': result
            })
            
            workflow['status'] = 'completed'
            workflow['completed_at'] = datetime.now()
            
            logger.info(f"워크플로우 실행 완료: {workflow_id}")
            return result
            
        except Exception as e:
            logger.error(f"워크플로우 실행 실패: {str(e)}")
            return {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e)
            }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """워크플로우 상태 조회"""
        if workflow_id not in self.workflows:
            return {'status': 'not_found'}
        
        workflow = self.workflows[workflow_id]
        return {
            'id': workflow_id,
            'status': workflow['status'],
            'created_at': workflow['created_at'].isoformat(),
            'started_at': workflow.get('started_at', {}).isoformat() if workflow.get('started_at') else None,
            'completed_at': workflow.get('completed_at', {}).isoformat() if workflow.get('completed_at') else None
        }
    
    def get_collaboration_graph(self) -> Dict[str, Any]:
        """협업 그래프 정보"""
        return {
            'nodes': [
                {
                    'id': node.agent_id,
                    'type': node.agent_type,
                    'capabilities': node.capabilities,
                    'dependencies': node.dependencies,
                    'priority': node.priority,
                    'is_active': node.is_active
                }
                for node in self.nodes.values()
            ],
            'edges': [
                {
                    'from': edge.from_agent,
                    'to': edge.to_agent,
                    'type': edge.collaboration_type.value,
                    'weight': edge.weight,
                    'conditions': edge.conditions
                }
                for edge in self.edges
            ],
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges)
        }
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """실행 히스토리 조회"""
        return [
            {
                'workflow_id': history['workflow_id'],
                'execution_time': history['execution_time'].isoformat(),
                'result': history['result']
            }
            for history in self.execution_history[-limit:]
        ]
    
    def remove_agent_node(self, agent_id: str):
        """에이전트 노드 제거"""
        if agent_id in self.nodes:
            del self.nodes[agent_id]
            # 관련 엣지도 제거
            self.edges = [edge for edge in self.edges 
                         if edge.from_agent != agent_id and edge.to_agent != agent_id]
            logger.info(f"에이전트 노드 제거: {agent_id}")
    
    def update_agent_priority(self, agent_id: str, priority: int):
        """에이전트 우선순위 업데이트"""
        if agent_id in self.nodes:
            self.nodes[agent_id].priority = priority
            logger.info(f"에이전트 우선순위 업데이트: {agent_id} -> {priority}")
    
    def get_agent_dependencies(self, agent_id: str) -> List[str]:
        """에이전트 의존성 조회"""
        if agent_id not in self.nodes:
            return []
        
        return self.nodes[agent_id].dependencies
    
    def validate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """워크플로우 유효성 검사"""
        if workflow_id not in self.workflows:
            return {'valid': False, 'error': '워크플로우를 찾을 수 없습니다'}
        
        workflow = self.workflows[workflow_id]
        issues = []
        
        # 노드 존재 여부 확인
        for node_id in workflow['nodes']:
            if node_id not in self.nodes:
                issues.append(f"노드를 찾을 수 없습니다: {node_id}")
        
        # 의존성 확인
        for node_id in workflow['nodes']:
            if node_id in self.nodes:
                dependencies = self.nodes[node_id].dependencies
                for dep in dependencies:
                    if dep not in workflow['nodes']:
                        issues.append(f"의존성 누락: {node_id} -> {dep}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'workflow_id': workflow_id
        } 