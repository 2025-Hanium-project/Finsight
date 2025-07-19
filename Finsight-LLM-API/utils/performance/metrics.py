"""
성능 메트릭 클래스

성능 데이터를 수집하고 분석하는 기능을 제공합니다.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """메트릭 데이터 포인트"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """메트릭 요약 정보"""
    name: str
    count: int
    min_value: float
    max_value: float
    mean_value: float
    median_value: float
    std_dev: float
    p95: float
    p99: float
    last_value: float
    first_timestamp: datetime
    last_timestamp: datetime


class PerformanceMetrics:
    """성능 메트릭 클래스"""
    
    def __init__(self, max_history_size: int = 1000):
        """
        성능 메트릭 초기화
        
        Args:
            max_history_size: 최대 히스토리 크기
        """
        self.max_history_size = max_history_size
        self.metrics = defaultdict(lambda: deque(maxlen=max_history_size))
        self.metric_callbacks = defaultdict(list)
        
        logger.info("성능 메트릭 초기화 완료")
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """메트릭 기록"""
        try:
            metric_point = MetricPoint(
                timestamp=datetime.now(),
                value=value,
                tags=tags or {},
                metadata=metadata or {}
            )
            
            self.metrics[name].append(metric_point)
            
            # 콜백 실행
            for callback in self.metric_callbacks[name]:
                try:
                    callback(metric_point)
                except Exception as e:
                    logger.error(f"메트릭 콜백 실행 실패: {str(e)}")
            
        except Exception as e:
            logger.error(f"메트릭 기록 실패: {str(e)}")
    
    def get_metric_summary(self, name: str, duration_minutes: int = None) -> Optional[MetricSummary]:
        """메트릭 요약 정보 반환"""
        try:
            if name not in self.metrics:
                return None
            
            metric_data = list(self.metrics[name])
            
            # 기간 필터링
            if duration_minutes:
                cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
                metric_data = [m for m in metric_data if m.timestamp >= cutoff_time]
            
            if not metric_data:
                return None
            
            values = [m.value for m in metric_data]
            timestamps = [m.timestamp for m in metric_data]
            
            return MetricSummary(
                name=name,
                count=len(values),
                min_value=min(values),
                max_value=max(values),
                mean_value=statistics.mean(values),
                median_value=statistics.median(values),
                std_dev=statistics.stdev(values) if len(values) > 1 else 0.0,
                p95=statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
                p99=statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values),
                last_value=values[-1],
                first_timestamp=min(timestamps),
                last_timestamp=max(timestamps)
            )
            
        except Exception as e:
            logger.error(f"메트릭 요약 생성 실패: {str(e)}")
            return None
    
    def get_metric_history(self, name: str, duration_minutes: int = None) -> List[MetricPoint]:
        """메트릭 히스토리 반환"""
        try:
            if name not in self.metrics:
                return []
            
            metric_data = list(self.metrics[name])
            
            # 기간 필터링
            if duration_minutes:
                cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
                metric_data = [m for m in metric_data if m.timestamp >= cutoff_time]
            
            return metric_data
            
        except Exception as e:
            logger.error(f"메트릭 히스토리 조회 실패: {str(e)}")
            return []
    
    def get_all_metrics_summary(self, duration_minutes: int = None) -> Dict[str, MetricSummary]:
        """모든 메트릭 요약 정보"""
        summaries = {}
        
        for metric_name in self.metrics.keys():
            summary = self.get_metric_summary(metric_name, duration_minutes)
            if summary:
                summaries[metric_name] = summary
        
        return summaries
    
    def add_metric_callback(self, metric_name: str, callback: Callable[[MetricPoint], None]):
        """메트릭 콜백 추가"""
        self.metric_callbacks[metric_name].append(callback)
    
    def remove_metric_callback(self, metric_name: str, callback: Callable[[MetricPoint], None]):
        """메트릭 콜백 제거"""
        if metric_name in self.metric_callbacks:
            try:
                self.metric_callbacks[metric_name].remove(callback)
            except ValueError:
                logger.warning(f"콜백을 찾을 수 없습니다: {metric_name}")
    
    def get_metric_names(self) -> List[str]:
        """등록된 메트릭 이름 목록"""
        return list(self.metrics.keys())
    
    def clear_metric(self, name: str):
        """특정 메트릭 데이터 삭제"""
        if name in self.metrics:
            self.metrics[name].clear()
            logger.info(f"메트릭 데이터 삭제: {name}")
    
    def clear_all_metrics(self):
        """모든 메트릭 데이터 삭제"""
        self.metrics.clear()
        logger.info("모든 메트릭 데이터 삭제")
    
    def get_metric_statistics(self, name: str, duration_minutes: int = None) -> Dict[str, Any]:
        """메트릭 통계 정보"""
        summary = self.get_metric_summary(name, duration_minutes)
        
        if not summary:
            return {}
        
        return {
            'name': summary.name,
            'count': summary.count,
            'min': summary.min_value,
            'max': summary.max_value,
            'mean': summary.mean_value,
            'median': summary.median_value,
            'std_dev': summary.std_dev,
            'p95': summary.p95,
            'p99': summary.p99,
            'last_value': summary.last_value,
            'first_timestamp': summary.first_timestamp.isoformat(),
            'last_timestamp': summary.last_timestamp.isoformat(),
            'duration_minutes': duration_minutes
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """모든 메트릭 요약 정보"""
        summaries = {}
        
        for metric_name in self.metrics.keys():
            summary = self.get_metric_summary(metric_name)
            if summary:
                summaries[metric_name] = {
                    'count': summary.count,
                    'min': summary.min_value,
                    'max': summary.max_value,
                    'mean': summary.mean_value,
                    'median': summary.median_value,
                    'std_dev': summary.std_dev,
                    'last_value': summary.last_value,
                    'last_timestamp': summary.last_timestamp.isoformat()
                }
        
        return {
            'total_metrics': len(summaries),
            'metrics': summaries,
            'timestamp': datetime.now().isoformat()
        }
    
    def detect_anomalies(self, name: str, threshold_std: float = 2.0, duration_minutes: int = None) -> List[MetricPoint]:
        """이상치 감지"""
        try:
            summary = self.get_metric_summary(name, duration_minutes)
            if not summary:
                return []
            
            metric_data = self.get_metric_history(name, duration_minutes)
            anomalies = []
            
            upper_threshold = summary.mean_value + (threshold_std * summary.std_dev)
            lower_threshold = summary.mean_value - (threshold_std * summary.std_dev)
            
            for point in metric_data:
                if point.value > upper_threshold or point.value < lower_threshold:
                    anomalies.append(point)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"이상치 감지 실패: {str(e)}")
            return []
    
    def get_trend_analysis(self, name: str, duration_minutes: int = None) -> Dict[str, Any]:
        """트렌드 분석"""
        try:
            summary = self.get_metric_summary(name, duration_minutes)
            if not summary:
                return {}
            
            # 간단한 트렌드 분석
            recent_data = self.get_metric_history(name, duration_minutes)
            if len(recent_data) < 2:
                return {'trend': 'insufficient_data'}
            
            # 최근 20% 데이터와 이전 20% 데이터 비교
            split_point = len(recent_data) // 5
            recent_values = [p.value for p in recent_data[-split_point:]]
            earlier_values = [p.value for p in recent_data[:split_point]]
            
            recent_avg = statistics.mean(recent_values)
            earlier_avg = statistics.mean(earlier_values)
            
            change_percent = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg != 0 else 0
            
            if change_percent > 10:
                trend = 'increasing'
            elif change_percent < -10:
                trend = 'decreasing'
            else:
                trend = 'stable'
            
            return {
                'trend': trend,
                'change_percent': change_percent,
                'recent_average': recent_avg,
                'earlier_average': earlier_avg,
                'metric_name': name
            }
            
        except Exception as e:
            logger.error(f"트렌드 분석 실패: {str(e)}")
            return {'trend': 'analysis_failed', 'error': str(e)}
    
    def export_metrics(self, format_type: str = 'json') -> str:
        """메트릭 데이터 내보내기"""
        try:
            export_data = {}
            
            for metric_name in self.metrics.keys():
                summary = self.get_metric_summary(metric_name)
                if summary:
                    export_data[metric_name] = {
                        'summary': {
                            'count': summary.count,
                            'min': summary.min_value,
                            'max': summary.max_value,
                            'mean': summary.mean_value,
                            'median': summary.median_value,
                            'std_dev': summary.std_dev,
                            'p95': summary.p95,
                            'p99': summary.p99
                        },
                        'history': [
                            {
                                'timestamp': point.timestamp.isoformat(),
                                'value': point.value,
                                'tags': point.tags,
                                'metadata': point.metadata
                            }
                            for point in self.get_metric_history(metric_name)
                        ]
                    }
            
            if format_type.lower() == 'json':
                import json
                return json.dumps(export_data, indent=2, ensure_ascii=False)
            else:
                return f"지원하지 않는 형식: {format_type}"
                
        except Exception as e:
            logger.error(f"메트릭 내보내기 실패: {str(e)}")
            return f"내보내기 실패: {str(e)}" 