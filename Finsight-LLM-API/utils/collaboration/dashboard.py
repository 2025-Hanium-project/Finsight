"""
협업 대시보드

에이전트 협업 상태를 시각화하고 모니터링하는 대시보드를 제공합니다.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class DashboardConfig:
    """대시보드 설정"""
    refresh_interval: float = 5.0
    max_history_size: int = 100
    enable_real_time: bool = True
    enable_export: bool = True


class CollaborationDashboard:
    """협업 대시보드 클래스"""
    
    def __init__(self, langgraph_manager=None, config: DashboardConfig = None):
        """
        협업 대시보드 초기화
        
        Args:
            langgraph_manager: LangGraphManager 인스턴스
            config: 대시보드 설정
        """
        self.langgraph_manager = langgraph_manager
        self.config = config or DashboardConfig()
        
        # 대시보드 상태
        self.is_active = False
        self.last_update = None
        self.dashboard_history = []
        
        logger.info("협업 대시보드 초기화 완료")
    
    def start_dashboard(self):
        """대시보드 시작"""
        self.is_active = True
        self.last_update = datetime.now()
        logger.info("협업 대시보드 시작")
    
    def stop_dashboard(self):
        """대시보드 중지"""
        self.is_active = False
        logger.info("협업 대시보드 중지")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """대시보드 데이터 반환"""
        try:
            # 협업 그래프 정보
            collaboration_graph = self.langgraph_manager.get_collaboration_graph() if self.langgraph_manager else {}
            
            # 워크플로우 상태
            workflow_statuses = self._get_workflow_statuses()
            
            # 에이전트 상태
            agent_statuses = self._get_agent_statuses()
            
            # 협업 통계
            collaboration_stats = self._get_collaboration_stats()
            
            # 실행 히스토리
            execution_history = self.langgraph_manager.get_execution_history(10) if self.langgraph_manager else []
            
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'collaboration_graph': collaboration_graph,
                'workflow_statuses': workflow_statuses,
                'agent_statuses': agent_statuses,
                'collaboration_stats': collaboration_stats,
                'execution_history': execution_history,
                'last_update': self.last_update.isoformat() if self.last_update else None
            }
            
            # 히스토리에 추가
            self.dashboard_history.append({
                'timestamp': datetime.now(),
                'data': dashboard_data
            })
            
            # 히스토리 크기 제한
            if len(self.dashboard_history) > self.config.max_history_size:
                self.dashboard_history = self.dashboard_history[-self.config.max_history_size:]
            
            self.last_update = datetime.now()
            return dashboard_data
            
        except Exception as e:
            logger.error(f"대시보드 데이터 생성 실패: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_workflow_statuses(self) -> List[Dict[str, Any]]:
        """워크플로우 상태 목록"""
        if not self.langgraph_manager:
            return []
        
        statuses = []
        for workflow_id in self.langgraph_manager.workflows.keys():
            status = self.langgraph_manager.get_workflow_status(workflow_id)
            statuses.append(status)
        
        return statuses
    
    def _get_agent_statuses(self) -> List[Dict[str, Any]]:
        """에이전트 상태 목록"""
        if not self.langgraph_manager:
            return []
        
        statuses = []
        for agent_id, node in self.langgraph_manager.nodes.items():
            status = {
                'agent_id': agent_id,
                'agent_type': node.agent_type,
                'capabilities': node.capabilities,
                'dependencies': node.dependencies,
                'priority': node.priority,
                'is_active': node.is_active,
                'status': 'active' if node.is_active else 'inactive'
            }
            statuses.append(status)
        
        return statuses
    
    def _get_collaboration_stats(self) -> Dict[str, Any]:
        """협업 통계"""
        if not self.langgraph_manager:
            return {}
        
        total_agents = len(self.langgraph_manager.nodes)
        active_agents = len([node for node in self.langgraph_manager.nodes.values() if node.is_active])
        total_workflows = len(self.langgraph_manager.workflows)
        completed_workflows = len([w for w in self.langgraph_manager.workflows.values() if w.get('status') == 'completed'])
        
        # 협업 타입별 통계
        collaboration_types = {}
        for edge in self.langgraph_manager.edges:
            collab_type = edge.collaboration_type.value
            collaboration_types[collab_type] = collaboration_types.get(collab_type, 0) + 1
        
        return {
            'total_agents': total_agents,
            'active_agents': active_agents,
            'inactive_agents': total_agents - active_agents,
            'total_workflows': total_workflows,
            'completed_workflows': completed_workflows,
            'running_workflows': len([w for w in self.langgraph_manager.workflows.values() if w.get('status') == 'executing']),
            'collaboration_types': collaboration_types,
            'total_edges': len(self.langgraph_manager.edges)
        }
    
    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """에이전트 성능 정보"""
        if not self.langgraph_manager or agent_id not in self.langgraph_manager.nodes:
            return {'error': '에이전트를 찾을 수 없습니다'}
        
        node = self.langgraph_manager.nodes[agent_id]
        
        # 관련 워크플로우 찾기
        related_workflows = []
        for workflow_id, workflow in self.langgraph_manager.workflows.items():
            if agent_id in workflow['nodes']:
                related_workflows.append({
                    'workflow_id': workflow_id,
                    'status': workflow['status']
                })
        
        # 의존성 정보
        dependencies = self.langgraph_manager.get_agent_dependencies(agent_id)
        
        return {
            'agent_id': agent_id,
            'agent_type': node.agent_type,
            'capabilities': node.capabilities,
            'priority': node.priority,
            'is_active': node.is_active,
            'dependencies': dependencies,
            'related_workflows': related_workflows,
            'total_workflows': len(related_workflows)
        }
    
    def get_workflow_details(self, workflow_id: str) -> Dict[str, Any]:
        """워크플로우 상세 정보"""
        if not self.langgraph_manager or workflow_id not in self.langgraph_manager.workflows:
            return {'error': '워크플로우를 찾을 수 없습니다'}
        
        workflow = self.langgraph_manager.workflows[workflow_id]
        
        # 워크플로우 노드 정보
        nodes_info = []
        for node_id in workflow['nodes']:
            if node_id in self.langgraph_manager.nodes:
                node = self.langgraph_manager.nodes[node_id]
                nodes_info.append({
                    'agent_id': node_id,
                    'agent_type': node.agent_type,
                    'capabilities': node.capabilities,
                    'priority': node.priority,
                    'is_active': node.is_active
                })
        
        # 유효성 검사
        validation = self.langgraph_manager.validate_workflow(workflow_id)
        
        return {
            'workflow_id': workflow_id,
            'status': workflow['status'],
            'nodes': nodes_info,
            'edges': workflow['edges'],
            'created_at': workflow['created_at'].isoformat(),
            'started_at': workflow.get('started_at', {}).isoformat() if workflow.get('started_at') else None,
            'completed_at': workflow.get('completed_at', {}).isoformat() if workflow.get('completed_at') else None,
            'validation': validation
        }
    
    def export_dashboard_data(self, format_type: str = 'json') -> str:
        """대시보드 데이터 내보내기"""
        try:
            dashboard_data = self.get_dashboard_data()
            
            if format_type.lower() == 'json':
                return json.dumps(dashboard_data, indent=2, ensure_ascii=False)
            else:
                return f"지원하지 않는 형식: {format_type}"
                
        except Exception as e:
            logger.error(f"대시보드 데이터 내보내기 실패: {str(e)}")
            return f"내보내기 실패: {str(e)}"
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """대시보드 요약 정보"""
        try:
            dashboard_data = self.get_dashboard_data()
            
            collaboration_stats = dashboard_data.get('collaboration_stats', {})
            workflow_statuses = dashboard_data.get('workflow_statuses', [])
            
            # 워크플로우 상태별 개수
            workflow_status_counts = {}
            for status in workflow_statuses:
                status_name = status.get('status', 'unknown')
                workflow_status_counts[status_name] = workflow_status_counts.get(status_name, 0) + 1
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_agents': collaboration_stats.get('total_agents', 0),
                'active_agents': collaboration_stats.get('active_agents', 0),
                'total_workflows': collaboration_stats.get('total_workflows', 0),
                'completed_workflows': collaboration_stats.get('completed_workflows', 0),
                'workflow_status_distribution': workflow_status_counts,
                'total_collaborations': collaboration_stats.get('total_edges', 0)
            }
            
        except Exception as e:
            logger.error(f"대시보드 요약 생성 실패: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_summary(self) -> Dict[str, Any]:
        """대시보드 요약 (별칭)"""
        return self.get_dashboard_summary()
    
    def get_agent_details(self, agent_id: str) -> Dict[str, Any]:
        """에이전트 상세 정보"""
        return self.get_agent_performance(agent_id)
    
    def get_system_alerts(self) -> List[Dict[str, Any]]:
        """시스템 알림"""
        alerts = []
        
        try:
            dashboard_data = self.get_dashboard_data()
            stats = dashboard_data.get('collaboration_stats', {})
            
            # 에이전트 비활성화 알림
            if stats.get('inactive_agents', 0) > 0:
                alerts.append({
                    'type': 'warning',
                    'message': f"{stats.get('inactive_agents', 0)}개의 에이전트가 비활성화 상태입니다",
                    'timestamp': datetime.now().isoformat()
                })
            
            # 워크플로우 실패 알림
            failed_workflows = stats.get('total_workflows', 0) - stats.get('completed_workflows', 0)
            if failed_workflows > 0:
                alerts.append({
                    'type': 'error',
                    'message': f"{failed_workflows}개의 워크플로우가 실패했습니다",
                    'timestamp': datetime.now().isoformat()
                })
            
            # 성능 알림
            if stats.get('total_agents', 0) > 10:
                alerts.append({
                    'type': 'info',
                    'message': "시스템에 많은 에이전트가 등록되어 있습니다",
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            alerts.append({
                'type': 'error',
                'message': f"알림 생성 중 오류: {str(e)}",
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """시각화 데이터"""
        try:
            dashboard_data = self.get_dashboard_data()
            
            # 차트용 데이터
            chart_data = {
                'agent_status': {
                    'labels': ['활성', '비활성'],
                    'data': [
                        dashboard_data.get('collaboration_stats', {}).get('active_agents', 0),
                        dashboard_data.get('collaboration_stats', {}).get('inactive_agents', 0)
                    ]
                },
                'workflow_status': {
                    'labels': ['완료', '실행중', '실패'],
                    'data': [
                        dashboard_data.get('collaboration_stats', {}).get('completed_workflows', 0),
                        dashboard_data.get('collaboration_stats', {}).get('running_workflows', 0),
                        dashboard_data.get('collaboration_stats', {}).get('total_workflows', 0) - 
                        dashboard_data.get('collaboration_stats', {}).get('completed_workflows', 0)
                    ]
                },
                'collaboration_types': dashboard_data.get('collaboration_stats', {}).get('collaboration_types', {})
            }
            
            return {
                'timestamp': dashboard_data.get('timestamp'),
                'chart_data': chart_data,
                'collaboration_graph': dashboard_data.get('collaboration_graph', {})
            }
            
        except Exception as e:
            logger.error(f"시각화 데이터 생성 실패: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_dashboard_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """대시보드 히스토리 조회"""
        return [
            {
                'timestamp': history['timestamp'].isoformat(),
                'summary': history['data'].get('collaboration_stats', {})
            }
            for history in self.dashboard_history[-limit:]
        ]


# 전역 인스턴스
_collaboration_dashboard = None

def get_collaboration_dashboard():
    """협업 대시보드 인스턴스 반환"""
    global _collaboration_dashboard
    if _collaboration_dashboard is None:
        _collaboration_dashboard = CollaborationDashboard()
    return _collaboration_dashboard 