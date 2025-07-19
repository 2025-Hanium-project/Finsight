"""
성능 대시보드 클래스

실시간 성능 모니터링 대시보드를 제공합니다.
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
    refresh_interval: float = 5.0  # 초
    max_data_points: int = 100
    enable_alerts: bool = True
    enable_charts: bool = True
    enable_export: bool = True


class PerformanceDashboard:
    """성능 대시보드 클래스"""
    
    def __init__(self, monitor=None, optimizer=None, config: DashboardConfig = None):
        """
        성능 대시보드 초기화
        
        Args:
            monitor: PerformanceMonitor 인스턴스
            optimizer: PerformanceOptimizer 인스턴스
            config: 대시보드 설정
        """
        self.monitor = monitor
        self.optimizer = optimizer
        self.config = config or DashboardConfig()
        
        # 대시보드 상태
        self.is_active = False
        self.last_update = None
        
        logger.info("성능 대시보드 초기화 완료")
    
    def start_dashboard(self):
        """대시보드 시작"""
        self.is_active = True
        self.last_update = datetime.now()
        logger.info("성능 대시보드 시작")
    
    def stop_dashboard(self):
        """대시보드 중지"""
        self.is_active = False
        logger.info("성능 대시보드 중지")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """대시보드 데이터 반환"""
        try:
            # 현재 메트릭
            current_metrics = self.monitor.get_current_metrics() if self.monitor else {}
            
            # 최적화 요약
            optimization_summary = self.optimizer.get_optimization_summary() if self.optimizer else {}
            
            # 시스템 상태
            system_status = self._get_system_status(current_metrics)
            
            # 성능 지표
            performance_indicators = self._get_performance_indicators(current_metrics)
            
            # 알림 정보
            alerts = self._get_active_alerts(current_metrics)
            
            # 차트 데이터
            chart_data = self._get_chart_data()
            
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'system_status': system_status,
                'performance_indicators': performance_indicators,
                'alerts': alerts,
                'optimization_summary': optimization_summary,
                'chart_data': chart_data,
                'last_update': self.last_update.isoformat() if self.last_update else None
            }
            
            self.last_update = datetime.now()
            return dashboard_data
            
        except Exception as e:
            logger.error(f"대시보드 데이터 생성 실패: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_system_status(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """시스템 상태 정보"""
        if not metrics or 'system' not in metrics:
            return {'status': 'unknown', 'message': '메트릭 데이터 없음'}
        
        system = metrics['system']
        
        # CPU 상태
        cpu_percent = system.get('cpu_percent', 0)
        if cpu_percent > 90:
            cpu_status = 'critical'
        elif cpu_percent > 80:
            cpu_status = 'warning'
        elif cpu_percent > 60:
            cpu_status = 'attention'
        else:
            cpu_status = 'normal'
        
        # 메모리 상태
        memory_percent = system.get('memory_percent', 0)
        if memory_percent > 95:
            memory_status = 'critical'
        elif memory_percent > 85:
            memory_status = 'warning'
        elif memory_percent > 70:
            memory_status = 'attention'
        else:
            memory_status = 'normal'
        
        # 디스크 상태
        disk_percent = system.get('disk_usage_percent', 0)
        if disk_percent > 95:
            disk_status = 'critical'
        elif disk_percent > 90:
            disk_status = 'warning'
        elif disk_percent > 80:
            disk_status = 'attention'
        else:
            disk_status = 'normal'
        
        # 전체 상태
        if any(status == 'critical' for status in [cpu_status, memory_status, disk_status]):
            overall_status = 'critical'
        elif any(status == 'warning' for status in [cpu_status, memory_status, disk_status]):
            overall_status = 'warning'
        elif any(status == 'attention' for status in [cpu_status, memory_status, disk_status]):
            overall_status = 'attention'
        else:
            overall_status = 'normal'
        
        return {
            'overall_status': overall_status,
            'cpu': {
                'status': cpu_status,
                'percent': cpu_percent,
                'description': f"CPU 사용률: {cpu_percent:.1f}%"
            },
            'memory': {
                'status': memory_status,
                'percent': memory_percent,
                'used_mb': system.get('memory_used_mb', 0),
                'total_mb': system.get('memory_total_mb', 0),
                'description': f"메모리 사용률: {memory_percent:.1f}%"
            },
            'disk': {
                'status': disk_status,
                'percent': disk_percent,
                'description': f"디스크 사용률: {disk_percent:.1f}%"
            },
            'processes': {
                'active_threads': system.get('active_threads', 0),
                'active_processes': system.get('active_processes', 0)
            }
        }
    
    def _get_performance_indicators(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """성능 지표"""
        if not metrics or 'performance' not in metrics:
            return {'message': '성능 데이터 없음'}
        
        perf = metrics['performance']
        
        # 응답 시간 상태
        response_time = perf.get('response_time', 0)
        if response_time > 5.0:
            response_status = 'critical'
        elif response_time > 3.0:
            response_status = 'warning'
        elif response_time > 1.0:
            response_status = 'attention'
        else:
            response_status = 'normal'
        
        # 에러율 상태
        error_rate = perf.get('error_rate', 0)
        if error_rate > 0.1:
            error_status = 'critical'
        elif error_rate > 0.05:
            error_status = 'warning'
        elif error_rate > 0.01:
            error_status = 'attention'
        else:
            error_status = 'normal'
        
        # 처리량 상태
        throughput = perf.get('throughput', 0)
        if throughput < 5:
            throughput_status = 'critical'
        elif throughput < 10:
            throughput_status = 'warning'
        elif throughput < 20:
            throughput_status = 'attention'
        else:
            throughput_status = 'normal'
        
        return {
            'response_time': {
                'status': response_status,
                'value': response_time,
                'unit': '초',
                'description': f"평균 응답 시간: {response_time:.2f}초"
            },
            'error_rate': {
                'status': error_status,
                'value': error_rate,
                'unit': '%',
                'description': f"에러율: {error_rate:.2%}"
            },
            'throughput': {
                'status': throughput_status,
                'value': throughput,
                'unit': 'req/s',
                'description': f"처리량: {throughput:.1f} req/s"
            },
            'success_rate': {
                'value': perf.get('success_rate', 0),
                'unit': '%',
                'description': f"성공율: {perf.get('success_rate', 0):.1%}"
            },
            'total_requests': perf.get('total_requests', 0),
            'successful_requests': perf.get('successful_requests', 0),
            'failed_requests': perf.get('failed_requests', 0)
        }
    
    def _get_active_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """활성 알림 목록"""
        alerts = []
        
        if not metrics:
            return alerts
        
        # 시스템 알림
        if 'system' in metrics:
            system = metrics['system']
            
            if system.get('cpu_percent', 0) > 80:
                alerts.append({
                    'type': 'system',
                    'severity': 'warning' if system['cpu_percent'] <= 90 else 'critical',
                    'message': f"CPU 사용률이 높습니다: {system['cpu_percent']:.1f}%",
                    'timestamp': datetime.now().isoformat()
                })
            
            if system.get('memory_percent', 0) > 85:
                alerts.append({
                    'type': 'system',
                    'severity': 'warning' if system['memory_percent'] <= 95 else 'critical',
                    'message': f"메모리 사용률이 높습니다: {system['memory_percent']:.1f}%",
                    'timestamp': datetime.now().isoformat()
                })
        
        # 성능 알림
        if 'performance' in metrics:
            perf = metrics['performance']
            
            if perf.get('response_time', 0) > 3.0:
                alerts.append({
                    'type': 'performance',
                    'severity': 'warning' if perf['response_time'] <= 5.0 else 'critical',
                    'message': f"응답 시간이 느립니다: {perf['response_time']:.2f}초",
                    'timestamp': datetime.now().isoformat()
                })
            
            if perf.get('error_rate', 0) > 0.05:
                alerts.append({
                    'type': 'performance',
                    'severity': 'warning' if perf['error_rate'] <= 0.1 else 'critical',
                    'message': f"에러율이 높습니다: {perf['error_rate']:.2%}",
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts
    
    def _get_chart_data(self) -> Dict[str, Any]:
        """차트 데이터"""
        if not self.monitor:
            return {}
        
        try:
            # 최근 1시간 데이터
            history = self.monitor.get_metrics_history(duration_minutes=60)
            
            return {
                'system_metrics': history.get('system', []),
                'performance_metrics': history.get('performance', []),
                'chart_config': {
                    'refresh_interval': self.config.refresh_interval,
                    'max_data_points': self.config.max_data_points
                }
            }
        except Exception as e:
            logger.error(f"차트 데이터 생성 실패: {str(e)}")
            return {}
    
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
            
            # 알림 개수
            alert_count = len(dashboard_data.get('alerts', []))
            critical_alerts = len([a for a in dashboard_data.get('alerts', []) 
                                 if a.get('severity') == 'critical'])
            
            # 시스템 상태 요약
            system_status = dashboard_data.get('system_status', {})
            overall_status = system_status.get('overall_status', 'unknown')
            
            # 성능 지표 요약
            performance = dashboard_data.get('performance_indicators', {})
            
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': overall_status,
                'alert_count': alert_count,
                'critical_alerts': critical_alerts,
                'cpu_percent': system_status.get('cpu', {}).get('percent', 0),
                'memory_percent': system_status.get('memory', {}).get('percent', 0),
                'response_time': performance.get('response_time', {}).get('value', 0),
                'error_rate': performance.get('error_rate', {}).get('value', 0),
                'throughput': performance.get('throughput', {}).get('value', 0)
            }
            
        except Exception as e:
            logger.error(f"대시보드 요약 생성 실패: {str(e)}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            } 