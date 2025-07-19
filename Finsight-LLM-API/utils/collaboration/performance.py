"""
협업 성능 최적화

에이전트 협업의 성능을 모니터링하고 최적화하는 기능을 제공합니다.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PerformanceMetric(Enum):
    """성능 메트릭"""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    COLLABORATION_EFFICIENCY = "collaboration_efficiency"
    RESOURCE_UTILIZATION = "resource_utilization"


@dataclass
class PerformanceData:
    """성능 데이터"""
    metric: PerformanceMetric
    value: float
    timestamp: datetime
    agent_id: str = None
    workflow_id: str = None
    metadata: Dict[str, Any] = None


class CollaborationPerformance:
    """협업 성능 최적화 클래스"""
    
    def __init__(self, langgraph_manager=None):
        """
        협업 성능 최적화 초기화
        
        Args:
            langgraph_manager: LangGraphManager 인스턴스
        """
        self.langgraph_manager = langgraph_manager
        self.performance_data = []
        self.optimization_history = []
        
        logger.info("협업 성능 최적화 초기화 완료")
    
    def record_performance(self, metric: PerformanceMetric, value: float, 
                          agent_id: str = None, workflow_id: str = None, 
                          metadata: Dict[str, Any] = None):
        """성능 데이터 기록"""
        try:
            performance_data = PerformanceData(
                metric=metric,
                value=value,
                timestamp=datetime.now(),
                agent_id=agent_id,
                workflow_id=workflow_id,
                metadata=metadata or {}
            )
            
            self.performance_data.append(performance_data)
            logger.debug(f"성능 데이터 기록: {metric.value} = {value}")
            
        except Exception as e:
            logger.error(f"성능 데이터 기록 실패: {str(e)}")
    
    def analyze_collaboration_performance(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """협업 성능 분석"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
            recent_data = [d for d in self.performance_data if d.timestamp >= cutoff_time]
            
            if not recent_data:
                return {'message': '분석할 데이터가 없습니다'}
            
            # 메트릭별 분석
            analysis = {}
            for metric in PerformanceMetric:
                metric_data = [d for d in recent_data if d.metric == metric]
                if metric_data:
                    values = [d.value for d in metric_data]
                    analysis[metric.value] = {
                        'count': len(values),
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'latest': values[-1] if values else 0
                    }
            
            # 협업 효율성 분석
            collaboration_efficiency = self._calculate_collaboration_efficiency(recent_data)
            
            # 성능 권장사항
            recommendations = self._generate_performance_recommendations(analysis)
            
            return {
                'analysis_period_minutes': duration_minutes,
                'total_data_points': len(recent_data),
                'metric_analysis': analysis,
                'collaboration_efficiency': collaboration_efficiency,
                'recommendations': recommendations,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"협업 성능 분석 실패: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_collaboration_efficiency(self, data: List[PerformanceData]) -> Dict[str, Any]:
        """협업 효율성 계산"""
        try:
            # 응답 시간 효율성
            response_time_data = [d for d in data if d.metric == PerformanceMetric.RESPONSE_TIME]
            avg_response_time = sum([d.value for d in response_time_data]) / len(response_time_data) if response_time_data else 0
            
            # 처리량 효율성
            throughput_data = [d for d in data if d.metric == PerformanceMetric.THROUGHPUT]
            avg_throughput = sum([d.value for d in throughput_data]) / len(throughput_data) if throughput_data else 0
            
            # 에러율 효율성
            error_rate_data = [d for d in data if d.metric == PerformanceMetric.ERROR_RATE]
            avg_error_rate = sum([d.value for d in error_rate_data]) / len(error_rate_data) if error_rate_data else 0
            
            # 효율성 점수 계산 (0-100)
            response_efficiency = max(0, 100 - (avg_response_time * 10))  # 응답시간이 낮을수록 높은 점수
            throughput_efficiency = min(100, avg_throughput * 10)  # 처리량이 높을수록 높은 점수
            error_efficiency = max(0, 100 - (avg_error_rate * 100))  # 에러율이 낮을수록 높은 점수
            
            overall_efficiency = (response_efficiency + throughput_efficiency + error_efficiency) / 3
            
            return {
                'overall_efficiency': overall_efficiency,
                'response_efficiency': response_efficiency,
                'throughput_efficiency': throughput_efficiency,
                'error_efficiency': error_efficiency,
                'avg_response_time': avg_response_time,
                'avg_throughput': avg_throughput,
                'avg_error_rate': avg_error_rate
            }
            
        except Exception as e:
            logger.error(f"협업 효율성 계산 실패: {str(e)}")
            return {'error': str(e)}
    
    def _generate_performance_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """성능 권장사항 생성"""
        recommendations = []
        
        try:
            # 응답 시간 권장사항
            if 'response_time' in analysis:
                avg_response_time = analysis['response_time']['avg']
                if avg_response_time > 3.0:
                    recommendations.append({
                        'type': 'response_time',
                        'priority': 'high' if avg_response_time > 5.0 else 'medium',
                        'issue': f"평균 응답 시간이 {avg_response_time:.2f}초로 느립니다",
                        'recommendation': "비동기 처리 도입 및 캐싱 시스템 강화",
                        'expected_improvement': "응답 시간 30-50% 단축"
                    })
            
            # 처리량 권장사항
            if 'throughput' in analysis:
                avg_throughput = analysis['throughput']['avg']
                if avg_throughput < 10:
                    recommendations.append({
                        'type': 'throughput',
                        'priority': 'medium',
                        'issue': f"평균 처리량이 {avg_throughput:.1f} req/s로 낮습니다",
                        'recommendation': "병렬 처리 확대 및 리소스 최적화",
                        'expected_improvement': "처리량 2-3배 향상"
                    })
            
            # 에러율 권장사항
            if 'error_rate' in analysis:
                avg_error_rate = analysis['error_rate']['avg']
                if avg_error_rate > 0.05:
                    recommendations.append({
                        'type': 'error_rate',
                        'priority': 'high' if avg_error_rate > 0.1 else 'medium',
                        'issue': f"평균 에러율이 {avg_error_rate:.2%}로 높습니다",
                        'recommendation': "에러 처리 개선 및 재시도 메커니즘 구현",
                        'expected_improvement': "에러율 50-80% 감소"
                    })
            
            # 협업 효율성 권장사항
            if 'collaboration_efficiency' in analysis:
                efficiency = analysis['collaboration_efficiency']['avg']
                if efficiency < 70:
                    recommendations.append({
                        'type': 'collaboration_efficiency',
                        'priority': 'medium',
                        'issue': f"협업 효율성이 {efficiency:.1f}%로 낮습니다",
                        'recommendation': "에이전트 간 통신 최적화 및 의존성 개선",
                        'expected_improvement': "협업 효율성 20-30% 향상"
                    })
            
        except Exception as e:
            logger.error(f"성능 권장사항 생성 실패: {str(e)}")
        
        return recommendations
    
    def get_agent_performance_summary(self, agent_id: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """에이전트 성능 요약"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
            agent_data = [d for d in self.performance_data 
                         if d.agent_id == agent_id and d.timestamp >= cutoff_time]
            
            if not agent_data:
                return {'message': '에이전트 성능 데이터가 없습니다'}
            
            # 메트릭별 요약
            summary = {}
            for metric in PerformanceMetric:
                metric_data = [d for d in agent_data if d.metric == metric]
                if metric_data:
                    values = [d.value for d in metric_data]
                    summary[metric.value] = {
                        'count': len(values),
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'latest': values[-1]
                    }
            
            return {
                'agent_id': agent_id,
                'analysis_period_minutes': duration_minutes,
                'total_data_points': len(agent_data),
                'metric_summary': summary,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"에이전트 성능 요약 생성 실패: {str(e)}")
            return {'error': str(e)}
    
    def get_workflow_performance_summary(self, workflow_id: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """워크플로우 성능 요약"""
        try:
            cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
            workflow_data = [d for d in self.performance_data 
                           if d.workflow_id == workflow_id and d.timestamp >= cutoff_time]
            
            if not workflow_data:
                return {'message': '워크플로우 성능 데이터가 없습니다'}
            
            # 메트릭별 요약
            summary = {}
            for metric in PerformanceMetric:
                metric_data = [d for d in workflow_data if d.metric == metric]
                if metric_data:
                    values = [d.value for d in metric_data]
                    summary[metric.value] = {
                        'count': len(values),
                        'min': min(values),
                        'max': max(values),
                        'avg': sum(values) / len(values),
                        'latest': values[-1]
                    }
            
            return {
                'workflow_id': workflow_id,
                'analysis_period_minutes': duration_minutes,
                'total_data_points': len(workflow_data),
                'metric_summary': summary,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"워크플로우 성능 요약 생성 실패: {str(e)}")
            return {'error': str(e)}
    
    def apply_optimization(self, optimization_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """성능 최적화 적용"""
        try:
            optimization_result = {
                'type': optimization_type,
                'parameters': parameters,
                'applied_at': datetime.now().isoformat(),
                'status': 'simulated',
                'expected_improvement': '성능 개선 예상'
            }
            
            # 최적화 히스토리에 추가
            self.optimization_history.append(optimization_result)
            
            logger.info(f"성능 최적화 적용: {optimization_type}")
            return optimization_result
            
        except Exception as e:
            logger.error(f"성능 최적화 적용 실패: {str(e)}")
            return {
                'type': optimization_type,
                'status': 'failed',
                'error': str(e)
            }
    
    def get_optimization_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최적화 히스토리 조회"""
        return self.optimization_history[-limit:] if self.optimization_history else []
    
    def clear_performance_data(self):
        """성능 데이터 초기화"""
        self.performance_data.clear()
        logger.info("성능 데이터 초기화 완료")


# 전역 인스턴스
_collaboration_performance = None

def get_collaboration_performance() -> CollaborationPerformance:
    """협업 성능 인스턴스 반환"""
    global _collaboration_performance
    if _collaboration_performance is None:
        _collaboration_performance = CollaborationPerformance()
    return _collaboration_performance


def get_optimized_collaboration_manager():
    """최적화된 협업 매니저 반환"""
    from .base import CollaborationManager
    
    # 최적화된 협업 매니저 생성
    manager = CollaborationManager()
    
    # 성능 모니터링 설정
    performance = get_collaboration_performance()
    
    # 성능 최적화 설정
    manager.performance_monitor = performance
    
    return manager 