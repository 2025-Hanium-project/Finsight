"""
Utils 모듈

기능:
- 핵심 유틸리티 클래스들
- 협업 시스템
- 성능 모니터링
- LLM 클라이언트
"""

# Core 모듈들
from utils.core.agent_base import (
    AnalysisAgent, AgentConfig, AgentType, AgentCapability,
    AgentRegistry, create_standard_prompt_template, get_agent_registry
)
from utils.core.data_models import (
    StandardInput, StandardOutput, ProcessingStatus, CollaborationMessage,
    MessagePriority, CollaborationType, KnowledgeType, AgentRequest,
    AgentResponse, CollaborationRequest, CollaborationResponse,
    WorkflowConfig, WorkflowStep, DashboardMetric, DashboardEvent,
    SystemStatus, DashboardSummary, PerformanceMetrics, TestResponse
)

# Collaboration 모듈들
from utils.collaboration.base import (
    CollaborationBase, CollaborationManager, AgentCollaborationInterface,
    create_collaboration_message, format_collaboration_data, validate_collaboration_message
)
from utils.collaboration.langgraph_manager import LangGraphManager
from utils.collaboration.dashboard import CollaborationDashboard
from utils.collaboration.performance import CollaborationPerformance

# Performance 모듈들
from utils.performance.monitor import PerformanceMonitor
from utils.performance.metrics import PerformanceMetrics
from utils.performance.alerts import PerformanceAlert
from utils.performance.dashboard import PerformanceDashboard
from utils.performance.optimizer import PerformanceOptimizer

# LLM 모듈들
from utils.llm.llm_client import generate_response, generate_multimodal_response, LLMClient

# Image Processing 모듈들 (securities_report_agent에서 통합됨)
# 순환 import 방지를 위해 lazy import 사용

# Backward compatibility
__all__ = [
    # Core
    'AnalysisAgent', 'AgentConfig', 'AgentType', 'AgentCapability',
    'AgentRegistry', 'create_standard_prompt_template', 'get_agent_registry',
    'StandardInput', 'StandardOutput', 'ProcessingStatus', 'CollaborationMessage',
    'MessagePriority', 'CollaborationType', 'KnowledgeType', 'AgentRequest',
    'AgentResponse', 'CollaborationRequest', 'CollaborationResponse',
    'WorkflowConfig', 'WorkflowStep', 'DashboardMetric', 'DashboardEvent',
    'SystemStatus', 'DashboardSummary', 'PerformanceMetrics', 'TestResponse',
    
    # Collaboration
    'CollaborationBase', 'CollaborationManager', 'AgentCollaborationInterface',
    'create_collaboration_message', 'format_collaboration_data', 'validate_collaboration_message',
    'LangGraphManager', 'CollaborationDashboard', 'CollaborationPerformance',
    
    # Performance
    'PerformanceMonitor', 'PerformanceMetrics', 'PerformanceAlert', 
    'PerformanceDashboard', 'PerformanceOptimizer',
    
    # LLM
    'generate_response', 'generate_multimodal_response', 'LLMClient',
    
    # Image Processing (lazy import)
    # 'ImageProcessor', 'SecuritiesReportOCR', 'BatchImageProcessor',
    # 'ImageProcessingResult', 'OCRResult', 'ImageFormat', 'ImageQuality'
]

# 버전 정보
__version__ = "2.0.0"
__author__ = "FinsightAI Team"
__description__ = "FinsightAI Utils - AI 에이전트 시스템을 위한 유틸리티 모듈"
