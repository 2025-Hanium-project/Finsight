"""
성능 모니터링 클래스

실시간으로 시스템 성능을 모니터링하고 분석하는 기능을 제공합니다.
"""

import time
import psutil
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import threading

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """시스템 메트릭 데이터 클래스"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_usage_percent: float
    network_sent: int
    network_recv: int
    active_threads: int
    active_processes: int


@dataclass
class PerformanceMetrics:
    """성능 메트릭 데이터 클래스"""
    timestamp: datetime
    response_time: float
    throughput: float
    error_rate: float
    success_rate: float
    queue_size: int
    active_connections: int


class PerformanceMonitor:
    """성능 모니터링 클래스"""
    
    def __init__(self, 
                 monitoring_interval: float = 1.0,
                 max_history_size: int = 1000,
                 alert_thresholds: Dict[str, float] = None):
        """
        성능 모니터 초기화
        
        Args:
            monitoring_interval: 모니터링 간격 (초)
            max_history_size: 최대 히스토리 크기
            alert_thresholds: 알림 임계값
        """
        self.monitoring_interval = monitoring_interval
        self.max_history_size = max_history_size
        self.alert_thresholds = alert_thresholds or {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'response_time': 5.0,
            'error_rate': 0.1
        }
        
        # 메트릭 히스토리
        self.system_metrics_history = deque(maxlen=max_history_size)
        self.performance_metrics_history = deque(maxlen=max_history_size)
        
        # 모니터링 상태
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 성능 통계
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        
        # 알림 콜백
        self.alert_callbacks = []
        
        logger.info("성능 모니터 초기화 완료")
    
    def start_monitoring(self):
        """모니터링 시작"""
        if self.is_monitoring:
            logger.warning("모니터링이 이미 실행 중입니다")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("성능 모니터링 시작")
    
    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("성능 모니터링 중지")
    
    def _monitor_loop(self):
        """모니터링 루프"""
        while self.is_monitoring:
            try:
                # 시스템 메트릭 수집
                system_metrics = self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)
                
                # 성능 메트릭 수집
                performance_metrics = self._collect_performance_metrics()
                self.performance_metrics_history.append(performance_metrics)
                
                # 알림 체크
                self._check_alerts(system_metrics, performance_metrics)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"모니터링 중 오류 발생: {str(e)}")
                time.sleep(self.monitoring_interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """시스템 메트릭 수집"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used=memory.used,
                memory_total=memory.total,
                disk_usage_percent=disk.percent,
                network_sent=network.bytes_sent,
                network_recv=network.bytes_recv,
                active_threads=threading.active_count(),
                active_processes=len(psutil.pids())
            )
        except Exception as e:
            logger.error(f"시스템 메트릭 수집 실패: {str(e)}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used=0,
                memory_total=0,
                disk_usage_percent=0.0,
                network_sent=0,
                network_recv=0,
                active_threads=0,
                active_processes=0
            )
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """시스템 메트릭 수집 (공개 메서드)"""
        metrics = self._collect_system_metrics()
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "memory_used": metrics.memory_used,
            "memory_total": metrics.memory_total,
            "disk_usage_percent": metrics.disk_usage_percent,
            "network_sent": metrics.network_sent,
            "network_recv": metrics.network_recv,
            "active_threads": metrics.active_threads,
            "active_processes": metrics.active_processes
        }
    
    def _collect_performance_metrics(self) -> PerformanceMetrics:
        """성능 메트릭 수집"""
        try:
            # 응답 시간 계산
            avg_response_time = (
                self.total_response_time / self.total_requests 
                if self.total_requests > 0 else 0.0
            )
            
            # 처리량 계산 (요청/초)
            throughput = self.total_requests / max(1, len(self.performance_metrics_history))
            
            # 에러율 계산
            error_rate = (
                self.failed_requests / self.total_requests 
                if self.total_requests > 0 else 0.0
            )
            
            # 성공율 계산
            success_rate = (
                self.successful_requests / self.total_requests 
                if self.total_requests > 0 else 0.0
            )
            
            return PerformanceMetrics(
                timestamp=datetime.now(),
                response_time=avg_response_time,
                throughput=throughput,
                error_rate=error_rate,
                success_rate=success_rate,
                queue_size=0,  # TODO: 큐 크기 구현
                active_connections=0  # TODO: 활성 연결 수 구현
            )
        except Exception as e:
            logger.error(f"성능 메트릭 수집 실패: {str(e)}")
            return PerformanceMetrics(
                timestamp=datetime.now(),
                response_time=0.0,
                throughput=0.0,
                error_rate=0.0,
                success_rate=0.0,
                queue_size=0,
                active_connections=0
            )
    
    def _check_alerts(self, system_metrics: SystemMetrics, performance_metrics: PerformanceMetrics):
        """알림 체크"""
        alerts = []
        
        # CPU 사용률 체크
        if system_metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts.append({
                'type': 'high_cpu_usage',
                'message': f"CPU 사용률이 높습니다: {system_metrics.cpu_percent:.1f}%",
                'severity': 'warning',
                'timestamp': datetime.now()
            })
        
        # 메모리 사용률 체크
        if system_metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts.append({
                'type': 'high_memory_usage',
                'message': f"메모리 사용률이 높습니다: {system_metrics.memory_percent:.1f}%",
                'severity': 'warning',
                'timestamp': datetime.now()
            })
        
        # 응답 시간 체크
        if performance_metrics.response_time > self.alert_thresholds['response_time']:
            alerts.append({
                'type': 'slow_response_time',
                'message': f"응답 시간이 느립니다: {performance_metrics.response_time:.2f}초",
                'severity': 'warning',
                'timestamp': datetime.now()
            })
        
        # 에러율 체크
        if performance_metrics.error_rate > self.alert_thresholds['error_rate']:
            alerts.append({
                'type': 'high_error_rate',
                'message': f"에러율이 높습니다: {performance_metrics.error_rate:.2%}",
                'severity': 'error',
                'timestamp': datetime.now()
            })
        
        # 알림 콜백 실행
        for alert in alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"알림 콜백 실행 실패: {str(e)}")
    
    def add_request_metrics(self, response_time: float, success: bool):
        """요청 메트릭 추가"""
        self.total_requests += 1
        self.total_response_time += response_time
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
    
    def add_alert_callback(self, callback):
        """알림 콜백 추가"""
        self.alert_callbacks.append(callback)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """현재 메트릭 반환"""
        if not self.system_metrics_history:
            return {}
        
        latest_system = self.system_metrics_history[-1]
        latest_performance = self.performance_metrics_history[-1] if self.performance_metrics_history else None
        
        return {
            'system': {
                'cpu_percent': latest_system.cpu_percent,
                'memory_percent': latest_system.memory_percent,
                'memory_used_mb': latest_system.memory_used // (1024 * 1024),
                'memory_total_mb': latest_system.memory_total // (1024 * 1024),
                'disk_usage_percent': latest_system.disk_usage_percent,
                'active_threads': latest_system.active_threads,
                'active_processes': latest_system.active_processes
            },
            'performance': {
                'response_time': latest_performance.response_time if latest_performance else 0.0,
                'throughput': latest_performance.throughput if latest_performance else 0.0,
                'error_rate': latest_performance.error_rate if latest_performance else 0.0,
                'success_rate': latest_performance.success_rate if latest_performance else 0.0,
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests
            } if latest_performance else {}
        }
    
    def get_metrics_history(self, duration_minutes: int = 60) -> Dict[str, List]:
        """메트릭 히스토리 반환"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        system_history = [
            {
                'timestamp': m.timestamp.isoformat(),
                'cpu_percent': m.cpu_percent,
                'memory_percent': m.memory_percent,
                'disk_usage_percent': m.disk_usage_percent
            }
            for m in self.system_metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        performance_history = [
            {
                'timestamp': m.timestamp.isoformat(),
                'response_time': m.response_time,
                'throughput': m.throughput,
                'error_rate': m.error_rate,
                'success_rate': m.success_rate
            }
            for m in self.performance_metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        return {
            'system': system_history,
            'performance': performance_history
        }
    
    def reset_metrics(self):
        """메트릭 초기화"""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        self.system_metrics_history.clear()
        self.performance_metrics_history.clear()
        logger.info("메트릭 초기화 완료") 