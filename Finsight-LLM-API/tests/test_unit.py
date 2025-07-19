"""
단위 테스트
"""
import asyncio
import json
from datetime import datetime

async def test_agent_creation():
    """에이전트 생성 테스트"""
    print("=== 에이전트 생성 테스트 ===")
    
    try:
        from utils.core.agent_base import AgentConfig, AgentCapability
        from utils.core.data_models import AgentType
        
        # 에이전트 설정 생성
        config = AgentConfig(
            name="test_agent",
            agent_type=AgentType.RISK_ASSESSMENT,
            capabilities=[AgentCapability.RISK_ASSESSMENT],
            model_name="gemini-2.0-flash"
        )
        
        print(f"에이전트 이름: {config.name}")
        print(f"에이전트 타입: {config.agent_type}")
        print(f"모델 이름: {config.model_name}")
        print(f"능력: {config.capabilities}")
        
        print("✅ 에이전트 생성 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 에이전트 생성 테스트 실패: {str(e)}")
        return False


async def test_collaboration_manager():
    """협업 매니저 테스트"""
    print("\n=== 협업 매니저 테스트 ===")
    
    try:
        from utils.collaboration.base import CollaborationManager
        
        # 매니저 생성
        manager = CollaborationManager()
        
        # 상태 확인
        status = manager.get_collaboration_status()
        print(f"초기 상태: {json.dumps(status, ensure_ascii=False, indent=2)}")
        
        print("✅ 협업 매니저 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 협업 매니저 테스트 실패: {str(e)}")
        return False


async def test_message_creation():
    """메시지 생성 테스트"""
    print("\n=== 메시지 생성 테스트 ===")
    
    try:
        from utils.core.data_models import CollaborationMessage, MessagePriority
        import uuid
        
        # 메시지 생성
        message = CollaborationMessage(
            id=str(uuid.uuid4()),
            source_agent="test_agent",
            target_agent="target_agent",
            message_type="test_request",
            content={"test": "data"},
            priority=MessagePriority.HIGH
        )
        
        print(f"소스 에이전트: {message.source_agent}")
        print(f"타겟 에이전트: {message.target_agent}")
        print(f"메시지 타입: {message.message_type}")
        print(f"우선순위: {message.priority}")
        
        print("✅ 메시지 생성 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 메시지 생성 테스트 실패: {str(e)}")
        return False


async def test_langgraph_manager():
    """LangGraph 매니저 테스트"""
    print("\n=== LangGraph 매니저 테스트 ===")
    
    try:
        from utils.collaboration.langgraph_manager import LangGraphManager, CollaborationType
        
        # LangGraph 매니저 생성
        manager = LangGraphManager()
        
        # 에이전트 노드 추가
        manager.add_agent_node(
            agent_id="test_agent",
            agent_type="test",
            capabilities=["test"],
            dependencies=[],
            priority=1
        )
        
        # 협업 엣지 추가
        manager.add_collaboration_edge(
            from_agent="test_agent",
            to_agent="test_agent",
            collaboration_type=CollaborationType.SEQUENTIAL,
            weight=1.0
        )
        
        # 워크플로우 생성
        manager.create_workflow(
            workflow_id="test_workflow",
            nodes=["test_agent"],
            edges=[]
        )
        
        # 워크플로우 상태 확인
        status = manager.get_workflow_status("test_workflow")
        print(f"워크플로우 상태: {json.dumps(status, ensure_ascii=False, indent=2)}")
        
        print("✅ LangGraph 매니저 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ LangGraph 매니저 테스트 실패: {str(e)}")
        return False


async def test_dashboard():
    """대시보드 테스트"""
    print("\n=== 대시보드 테스트 ===")
    
    try:
        from utils.collaboration.dashboard import CollaborationDashboard
        from utils.collaboration.langgraph_manager import LangGraphManager
        
        # LangGraph 매니저 생성
        langgraph_manager = LangGraphManager()
        
        # 대시보드 생성
        dashboard = CollaborationDashboard(langgraph_manager=langgraph_manager)
        
        # 대시보드 시작
        dashboard.start_dashboard()
        
        # 대시보드 데이터 확인
        dashboard_data = dashboard.get_dashboard_data()
        print(f"대시보드 데이터: {json.dumps(dashboard_data, ensure_ascii=False, indent=2)}")
        
        # 대시보드 중지
        dashboard.stop_dashboard()
        
        print("✅ 대시보드 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 대시보드 테스트 실패: {str(e)}")
        return False


async def test_performance_monitoring():
    """성능 모니터링 테스트"""
    print("\n=== 성능 모니터링 테스트 ===")
    
    try:
        from utils.performance.monitor import PerformanceMonitor
        from utils.performance.metrics import PerformanceMetrics
        from utils.performance.alerts import PerformanceAlert
        
        # 성능 모니터링 생성
        monitor = PerformanceMonitor()
        metrics = PerformanceMetrics()
        alerts = PerformanceAlert()
        
        # 시스템 메트릭 수집
        system_metrics = monitor.collect_system_metrics()
        print(f"시스템 메트릭: {json.dumps(system_metrics, ensure_ascii=False, indent=2)}")
        
        # 성능 메트릭 기록
        metrics.record_metric("cpu_usage", 45.2)
        metrics.record_metric("memory_usage", 67.8)
        metrics.record_metric("response_time", 1.2)
        
        # 메트릭 요약
        summary = metrics.get_metrics_summary()
        print(f"메트릭 요약: {json.dumps(summary, ensure_ascii=False, indent=2)}")
        
        # 알림 체크
        alert_results = alerts.check_alerts(system_metrics)
        print(f"알림 결과: {len(alert_results)}개 알림")
        
        print("✅ 성능 모니터링 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 성능 모니터링 테스트 실패: {str(e)}")
        return False


async def test_data_models():
    """데이터 모델 테스트"""
    print("\n=== 데이터 모델 테스트 ===")
    
    try:
        from utils.core.data_models import StandardInput, StandardOutput, AgentType, ProcessingStatus
        
        # StandardInput 생성
        input_data = StandardInput(
            target_type="company",
            target_name="삼성전자",
            symbol="005930",
            reports=[],
            context={"industry": "반도체"}
        )
        
        print(f"입력 타겟: {input_data.target_name}")
        print(f"입력 심볼: {input_data.symbol}")
        
        # StandardOutput 생성
        output_data = StandardOutput(
            agent_type=AgentType.FINANCIAL_STATEMENT,
            target_type="company",
            target_name="삼성전자",
            symbol="005930",
            status=ProcessingStatus.COMPLETED,
            success=True,
            result={"analysis": "테스트 결과"},
            execution_time=1.5
        )
        
        print(f"출력 에이전트: {output_data.agent_type}")
        print(f"출력 상태: {output_data.status}")
        print(f"출력 성공: {output_data.success}")
        
        print("✅ 데이터 모델 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 데이터 모델 테스트 실패: {str(e)}")
        return False


async def main():
    """메인 테스트 함수"""
    print("단위 테스트 시작")
    print("=" * 50)
    
    tests = [
        test_agent_creation,
        test_collaboration_manager,
        test_message_creation,
        test_langgraph_manager,
        test_dashboard,
        test_performance_monitoring,
        test_data_models
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("단위 테스트 결과 요약")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"통과: {passed}/{total}")
    print(f"성공률: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("✅ 모든 단위 테스트 통과!")
        return True
    else:
        print("❌ 일부 단위 테스트 실패")
        return False


if __name__ == "__main__":
    asyncio.run(main()) 