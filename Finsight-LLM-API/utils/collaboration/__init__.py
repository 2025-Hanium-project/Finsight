"""
협업 시스템 모듈

에이전트 간 협업을 위한 다양한 기능을 제공합니다.

주요 구성:
- base: 기본 협업 인터페이스
- langgraph_manager: LangGraph 기반 협업 관리
- dashboard: 협업 대시보드
- performance: 협업 성능 최적화
"""

from .base import CollaborationBase, CollaborationManager
from .langgraph_manager import LangGraphManager
from .dashboard import CollaborationDashboard
from .performance import CollaborationPerformance

# 별칭 추가
SimpleCollaborationManager = CollaborationManager

__all__ = [
    'CollaborationBase',
    'CollaborationManager',
    'SimpleCollaborationManager',  # 별칭 추가
    'LangGraphManager',
    'CollaborationDashboard',
    'CollaborationPerformance'
] 