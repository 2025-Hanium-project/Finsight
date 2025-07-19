"""
성능 알림 시스템

성능 임계값을 모니터링하고 알림을 생성하는 기능을 제공합니다.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """알림 심각도"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """알림 타입"""
    CPU_HIGH = "cpu_high"
    MEMORY_HIGH = "memory_high"
    DISK_HIGH = "disk_high"
    RESPONSE_TIME_SLOW = "response_time_slow"
    ERROR_RATE_HIGH = "error_rate_high"
    THROUGHPUT_LOW = "throughput_low"
    COLLABORATION_ISSUE = "collaboration_issue"


@dataclass
class AlertRule:
    """알림 규칙"""
    name: str
    alert_type: AlertType
    metric: str
    threshold: float
    severity: AlertSeverity
    condition: str  # "above", "below", "equals"
    enabled: bool = True
    description: str = ""


@dataclass
class Alert:
    """알림"""
    id: str
    rule_name: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    timestamp: datetime
    metric_value: float
    threshold: float
    metadata: Dict[str, Any] = None


class PerformanceAlert:
    """성능 알림 클래스"""
    
    def __init__(self):
        """성능 알림 초기화"""
        self.alert_rules = {}
        self.active_alerts = []
        self.alert_history = []
        self.alert_callbacks = []
        
        # 기본 알림 규칙 설정
        self._setup_default_rules()
        
        logger.info("성능 알림 시스템 초기화 완료")
    
    def _setup_default_rules(self):
        """기본 알림 규칙 설정"""
        default_rules = [
            AlertRule(
                name="CPU 사용률 높음",
                alert_type=AlertType.CPU_HIGH,
                metric="cpu_percent",
                threshold=80.0,
                severity=AlertSeverity.WARNING,
                condition="above",
                description="CPU 사용률이 80%를 초과했습니다"
            ),
            AlertRule(
                name="CPU 사용률 매우 높음",
                alert_type=AlertType.CPU_HIGH,
                metric="cpu_percent",
                threshold=90.0,
                severity=AlertSeverity.CRITICAL,
                condition="above",
                description="CPU 사용률이 90%를 초과했습니다"
            ),
            AlertRule(
                name="메모리 사용률 높음",
                alert_type=AlertType.MEMORY_HIGH,
                metric="memory_percent",
                threshold=85.0,
                severity=AlertSeverity.WARNING,
                condition="above",
                description="메모리 사용률이 85%를 초과했습니다"
            ),
            AlertRule(
                name="메모리 사용률 매우 높음",
                alert_type=AlertType.MEMORY_HIGH,
                metric="memory_percent",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                condition="above",
                description="메모리 사용률이 95%를 초과했습니다"
            ),
            AlertRule(
                name="응답 시간 느림",
                alert_type=AlertType.RESPONSE_TIME_SLOW,
                metric="response_time",
                threshold=3.0,
                severity=AlertSeverity.WARNING,
                condition="above",
                description="응답 시간이 3초를 초과했습니다"
            ),
            AlertRule(
                name="응답 시간 매우 느림",
                alert_type=AlertType.RESPONSE_TIME_SLOW,
                metric="response_time",
                threshold=5.0,
                severity=AlertSeverity.CRITICAL,
                condition="above",
                description="응답 시간이 5초를 초과했습니다"
            ),
            AlertRule(
                name="에러율 높음",
                alert_type=AlertType.ERROR_RATE_HIGH,
                metric="error_rate",
                threshold=0.05,
                severity=AlertSeverity.WARNING,
                condition="above",
                description="에러율이 5%를 초과했습니다"
            ),
            AlertRule(
                name="에러율 매우 높음",
                alert_type=AlertType.ERROR_RATE_HIGH,
                metric="error_rate",
                threshold=0.1,
                severity=AlertSeverity.CRITICAL,
                condition="above",
                description="에러율이 10%를 초과했습니다"
            )
        ]
        
        for rule in default_rules:
            self.add_alert_rule(rule)
    
    def add_alert_rule(self, rule: AlertRule):
        """알림 규칙 추가"""
        self.alert_rules[rule.name] = rule
        logger.info(f"알림 규칙 추가: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """알림 규칙 제거"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"알림 규칙 제거: {rule_name}")
    
    def check_alerts(self, metrics: Dict[str, Any]) -> List[Alert]:
        """알림 체크"""
        new_alerts = []
        
        try:
            for rule_name, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                
                metric_value = metrics.get(rule.metric, 0)
                
                # 조건 체크
                should_alert = False
                if rule.condition == "above" and metric_value > rule.threshold:
                    should_alert = True
                elif rule.condition == "below" and metric_value < rule.threshold:
                    should_alert = True
                elif rule.condition == "equals" and metric_value == rule.threshold:
                    should_alert = True
                
                if should_alert:
                    # 이미 활성화된 알림인지 체크
                    existing_alert = self._find_active_alert(rule_name)
                    
                    if not existing_alert:
                        # 새 알림 생성
                        alert = Alert(
                            id=f"{rule_name}_{datetime.now().timestamp()}",
                            rule_name=rule_name,
                            alert_type=rule.alert_type,
                            severity=rule.severity,
                            message=rule.description,
                            timestamp=datetime.now(),
                            metric_value=metric_value,
                            threshold=rule.threshold,
                            metadata={
                                'metric': rule.metric,
                                'condition': rule.condition
                            }
                        )
                        
                        self.active_alerts.append(alert)
                        self.alert_history.append(alert)
                        new_alerts.append(alert)
                        
                        # 콜백 실행
                        self._execute_alert_callbacks(alert)
                        
                        logger.warning(f"알림 발생: {rule_name} - {rule.description}")
        
        except Exception as e:
            logger.error(f"알림 체크 실패: {str(e)}")
        
        return new_alerts
    
    def _find_active_alert(self, rule_name: str) -> Optional[Alert]:
        """활성 알림 찾기"""
        for alert in self.active_alerts:
            if alert.rule_name == rule_name:
                return alert
        return None
    
    def _execute_alert_callbacks(self, alert: Alert):
        """알림 콜백 실행"""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"알림 콜백 실행 실패: {str(e)}")
    
    def resolve_alert(self, alert_id: str):
        """알림 해결"""
        for i, alert in enumerate(self.active_alerts):
            if alert.id == alert_id:
                del self.active_alerts[i]
                logger.info(f"알림 해결: {alert.rule_name}")
                break
    
    def resolve_alerts_by_rule(self, rule_name: str):
        """규칙별 알림 해결"""
        self.active_alerts = [alert for alert in self.active_alerts if alert.rule_name != rule_name]
        logger.info(f"규칙별 알림 해결: {rule_name}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """알림 콜백 추가"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[Alert], None]):
        """알림 콜백 제거"""
        try:
            self.alert_callbacks.remove(callback)
        except ValueError:
            logger.warning("콜백을 찾을 수 없습니다")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """활성 알림 목록"""
        return [
            {
                'id': alert.id,
                'rule_name': alert.rule_name,
                'alert_type': alert.alert_type.value,
                'severity': alert.severity.value,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'metric_value': alert.metric_value,
                'threshold': alert.threshold,
                'metadata': alert.metadata
            }
            for alert in self.active_alerts
        ]
    
    def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """알림 히스토리"""
        return [
            {
                'id': alert.id,
                'rule_name': alert.rule_name,
                'alert_type': alert.alert_type.value,
                'severity': alert.severity.value,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'metric_value': alert.metric_value,
                'threshold': alert.threshold,
                'metadata': alert.metadata
            }
            for alert in self.alert_history[-limit:]
        ]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Dict[str, Any]]:
        """심각도별 알림"""
        return [
            {
                'id': alert.id,
                'rule_name': alert.rule_name,
                'alert_type': alert.alert_type.value,
                'severity': alert.severity.value,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'metric_value': alert.metric_value,
                'threshold': alert.threshold
            }
            for alert in self.active_alerts
            if alert.severity == severity
        ]
    
    def get_alert_rules(self) -> List[Dict[str, Any]]:
        """알림 규칙 목록"""
        return [
            {
                'name': rule.name,
                'alert_type': rule.alert_type.value,
                'metric': rule.metric,
                'threshold': rule.threshold,
                'severity': rule.severity.value,
                'condition': rule.condition,
                'enabled': rule.enabled,
                'description': rule.description
            }
            for rule in self.alert_rules.values()
        ]
    
    def update_alert_rule(self, rule_name: str, **kwargs):
        """알림 규칙 업데이트"""
        if rule_name in self.alert_rules:
            rule = self.alert_rules[rule_name]
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            logger.info(f"알림 규칙 업데이트: {rule_name}")
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """알림 요약"""
        severity_counts = {}
        for alert in self.active_alerts:
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_active_alerts': len(self.active_alerts),
            'severity_distribution': severity_counts,
            'total_rules': len(self.alert_rules),
            'enabled_rules': len([r for r in self.alert_rules.values() if r.enabled]),
            'timestamp': datetime.now().isoformat()
        }
    
    def clear_alert_history(self):
        """알림 히스토리 초기화"""
        self.alert_history.clear()
        logger.info("알림 히스토리 초기화 완료") 