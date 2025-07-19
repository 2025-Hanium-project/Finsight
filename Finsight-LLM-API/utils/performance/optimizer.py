"""
성능 최적화 클래스

시스템 성능을 분석하고 최적화 방안을 제안하는 기능을 제공합니다.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """최적화 타입"""
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    CONCURRENCY = "concurrency"


@dataclass
class OptimizationRecommendation:
    """최적화 권장사항"""
    type: OptimizationType
    title: str
    description: str
    priority: str  # low, medium, high, critical
    estimated_impact: str
    implementation_difficulty: str
    cost: str
    steps: List[str]
    metrics_to_monitor: List[str]


class PerformanceOptimizer:
    """성능 최적화 클래스"""
    
    def __init__(self, monitor=None):
        """
        성능 최적화 초기화
        
        Args:
            monitor: PerformanceMonitor 인스턴스
        """
        self.monitor = monitor
        self.optimization_history = []
        self.recommendations_cache = {}
        
        logger.info("성능 최적화 초기화 완료")
    
    def analyze_performance(self, metrics: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """성능 분석 및 최적화 권장사항 생성"""
        recommendations = []
        
        try:
            # 시스템 메트릭 분석
            if 'system' in metrics:
                system_recs = self._analyze_system_metrics(metrics['system'])
                recommendations.extend(system_recs)
            
            # 성능 메트릭 분석
            if 'performance' in metrics:
                perf_recs = self._analyze_performance_metrics(metrics['performance'])
                recommendations.extend(perf_recs)
            
            # 캐시에 저장
            cache_key = datetime.now().strftime("%Y%m%d_%H%M")
            self.recommendations_cache[cache_key] = recommendations
            
            # 히스토리에 추가
            self.optimization_history.append({
                'timestamp': datetime.now(),
                'recommendations': recommendations,
                'metrics': metrics
            })
            
            logger.info(f"성능 분석 완료: {len(recommendations)}개 권장사항 생성")
            return recommendations
            
        except Exception as e:
            logger.error(f"성능 분석 실패: {str(e)}")
            return []
    
    def _analyze_system_metrics(self, system_metrics: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """시스템 메트릭 분석"""
        recommendations = []
        
        # CPU 사용률 분석
        cpu_percent = system_metrics.get('cpu_percent', 0)
        if cpu_percent > 80:
            recommendations.append(OptimizationRecommendation(
                type=OptimizationType.CPU,
                title="CPU 사용률 최적화",
                description=f"CPU 사용률이 {cpu_percent:.1f}%로 높습니다. 작업 분산이 필요합니다.",
                priority="high" if cpu_percent > 90 else "medium",
                estimated_impact="CPU 사용률 20-30% 감소",
                implementation_difficulty="medium",
                cost="낮음",
                steps=[
                    "비동기 처리 도입",
                    "작업 큐 시스템 구현",
                    "불필요한 프로세스 종료",
                    "CPU 집약적 작업 최적화"
                ],
                metrics_to_monitor=["cpu_percent", "response_time", "throughput"]
            ))
        
        # 메모리 사용률 분석
        memory_percent = system_metrics.get('memory_percent', 0)
        if memory_percent > 85:
            recommendations.append(OptimizationRecommendation(
                type=OptimizationType.MEMORY,
                title="메모리 사용률 최적화",
                description=f"메모리 사용률이 {memory_percent:.1f}%로 높습니다. 메모리 누수 가능성이 있습니다.",
                priority="high" if memory_percent > 95 else "medium",
                estimated_impact="메모리 사용률 15-25% 감소",
                implementation_difficulty="medium",
                cost="낮음",
                steps=[
                    "메모리 누수 검사",
                    "객체 풀링 도입",
                    "불필요한 데이터 캐시 정리",
                    "메모리 사용량 모니터링 강화"
                ],
                metrics_to_monitor=["memory_percent", "memory_used_mb", "response_time"]
            ))
        
        # 디스크 사용률 분석
        disk_usage = system_metrics.get('disk_usage_percent', 0)
        if disk_usage > 90:
            recommendations.append(OptimizationRecommendation(
                type=OptimizationType.DATABASE,
                title="디스크 공간 최적화",
                description=f"디스크 사용률이 {disk_usage:.1f}%로 높습니다. 공간 정리가 필요합니다.",
                priority="critical" if disk_usage > 95 else "high",
                estimated_impact="디스크 공간 확보",
                implementation_difficulty="low",
                cost="없음",
                steps=[
                    "로그 파일 정리",
                    "임시 파일 삭제",
                    "오래된 데이터 아카이빙",
                    "디스크 사용량 모니터링"
                ],
                metrics_to_monitor=["disk_usage_percent", "response_time"]
            ))
        
        return recommendations
    
    def _analyze_performance_metrics(self, perf_metrics: Dict[str, Any]) -> List[OptimizationRecommendation]:
        """성능 메트릭 분석"""
        recommendations = []
        
        # 응답 시간 분석
        response_time = perf_metrics.get('response_time', 0)
        if response_time > 3.0:
            recommendations.append(OptimizationRecommendation(
                type=OptimizationType.CONCURRENCY,
                title="응답 시간 최적화",
                description=f"평균 응답 시간이 {response_time:.2f}초로 느립니다. 성능 개선이 필요합니다.",
                priority="high" if response_time > 5.0 else "medium",
                estimated_impact="응답 시간 30-50% 단축",
                implementation_difficulty="medium",
                cost="중간",
                steps=[
                    "데이터베이스 쿼리 최적화",
                    "캐싱 시스템 도입",
                    "비동기 처리 확대",
                    "로드 밸런싱 구현"
                ],
                metrics_to_monitor=["response_time", "throughput", "error_rate"]
            ))
        
        # 에러율 분석
        error_rate = perf_metrics.get('error_rate', 0)
        if error_rate > 0.05:  # 5%
            recommendations.append(OptimizationRecommendation(
                type=OptimizationType.CONCURRENCY,
                title="에러율 개선",
                description=f"에러율이 {error_rate:.2%}로 높습니다. 안정성 개선이 필요합니다.",
                priority="high" if error_rate > 0.1 else "medium",
                estimated_impact="에러율 50-80% 감소",
                implementation_difficulty="medium",
                cost="중간",
                steps=[
                    "에러 로깅 강화",
                    "예외 처리 개선",
                    "재시도 메커니즘 구현",
                    "서킷 브레이커 패턴 도입"
                ],
                metrics_to_monitor=["error_rate", "success_rate", "response_time"]
            ))
        
        # 처리량 분석
        throughput = perf_metrics.get('throughput', 0)
        if throughput < 10:  # 초당 10개 요청 미만
            recommendations.append(OptimizationRecommendation(
                type=OptimizationType.CONCURRENCY,
                title="처리량 향상",
                description=f"처리량이 {throughput:.1f} req/s로 낮습니다. 병렬 처리 개선이 필요합니다.",
                priority="medium",
                estimated_impact="처리량 2-3배 향상",
                implementation_difficulty="high",
                cost="높음",
                steps=[
                    "멀티스레딩 구현",
                    "비동기 I/O 최적화",
                    "데이터베이스 커넥션 풀 확대",
                    "캐시 전략 개선"
                ],
                metrics_to_monitor=["throughput", "response_time", "cpu_percent"]
            ))
        
        return recommendations
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """최적화 요약 정보"""
        if not self.optimization_history:
            return {"message": "최적화 히스토리가 없습니다"}
        
        latest_analysis = self.optimization_history[-1]
        recommendations = latest_analysis['recommendations']
        
        # 우선순위별 분류
        priority_counts = {
            'critical': len([r for r in recommendations if r.priority == 'critical']),
            'high': len([r for r in recommendations if r.priority == 'high']),
            'medium': len([r for r in recommendations if r.priority == 'medium']),
            'low': len([r for r in recommendations if r.priority == 'low'])
        }
        
        # 타입별 분류
        type_counts = {}
        for rec in recommendations:
            type_counts[rec.type.value] = type_counts.get(rec.type.value, 0) + 1
        
        return {
            'total_recommendations': len(recommendations),
            'priority_distribution': priority_counts,
            'type_distribution': type_counts,
            'latest_analysis_time': latest_analysis['timestamp'].isoformat(),
            'critical_issues': len([r for r in recommendations if r.priority == 'critical']),
            'high_priority_issues': len([r for r in recommendations if r.priority == 'high'])
        }
    
    def get_recommendations_by_priority(self, priority: str) -> List[OptimizationRecommendation]:
        """우선순위별 권장사항 조회"""
        if not self.optimization_history:
            return []
        
        latest_recommendations = self.optimization_history[-1]['recommendations']
        return [r for r in latest_recommendations if r.priority == priority]
    
    def get_recommendations_by_type(self, optimization_type: OptimizationType) -> List[OptimizationRecommendation]:
        """타입별 권장사항 조회"""
        if not self.optimization_history:
            return []
        
        latest_recommendations = self.optimization_history[-1]['recommendations']
        return [r for r in latest_recommendations if r.type == optimization_type]
    
    def apply_optimization(self, recommendation: OptimizationRecommendation) -> Dict[str, Any]:
        """최적화 적용 (시뮬레이션)"""
        try:
            # 실제 적용은 구현에 따라 달라질 수 있음
            # 여기서는 시뮬레이션 결과를 반환
            result = {
                'recommendation_title': recommendation.title,
                'applied_at': datetime.now().isoformat(),
                'status': 'simulated',
                'estimated_impact': recommendation.estimated_impact,
                'implementation_steps': recommendation.steps,
                'monitoring_metrics': recommendation.metrics_to_monitor
            }
            
            logger.info(f"최적화 적용 시뮬레이션: {recommendation.title}")
            return result
            
        except Exception as e:
            logger.error(f"최적화 적용 실패: {str(e)}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """최적화 리포트 생성"""
        if not self.optimization_history:
            return {"message": "분석 데이터가 없습니다"}
        
        latest_analysis = self.optimization_history[-1]
        recommendations = latest_analysis['recommendations']
        
        # 통계 계산
        total_recs = len(recommendations)
        critical_recs = len([r for r in recommendations if r.priority == 'critical'])
        high_recs = len([r for r in recommendations if r.priority == 'high'])
        
        # 타입별 분석
        type_analysis = {}
        for rec in recommendations:
            if rec.type.value not in type_analysis:
                type_analysis[rec.type.value] = []
            type_analysis[rec.type.value].append({
                'title': rec.title,
                'priority': rec.priority,
                'impact': rec.estimated_impact
            })
        
        return {
            'report_generated_at': datetime.now().isoformat(),
            'total_recommendations': total_recs,
            'critical_issues': critical_recs,
            'high_priority_issues': high_recs,
            'priority_distribution': {
                'critical': critical_recs,
                'high': high_recs,
                'medium': len([r for r in recommendations if r.priority == 'medium']),
                'low': len([r for r in recommendations if r.priority == 'low'])
            },
            'type_analysis': type_analysis,
            'recommendations': [
                {
                    'title': r.title,
                    'type': r.type.value,
                    'priority': r.priority,
                    'description': r.description,
                    'impact': r.estimated_impact,
                    'difficulty': r.implementation_difficulty,
                    'cost': r.cost
                }
                for r in recommendations
            ]
        } 