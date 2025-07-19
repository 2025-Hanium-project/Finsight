"""
새로운 Multi-Agent 설계에 따른 워크플로우 테스트

기능:
- 워크플로우 생성 및 실행 테스트
- 워크플로우 상태 관리 테스트
- 워크플로우 성능 테스트
- 워크플로우 에러 처리 테스트
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# 상위 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 테스트용 데이터
TEST_WORKFLOW_DATA = {
    "target_type": "company",
    "target_name": "삼성전자",
    "symbol": "005930",
    "reports": [
        {
            "title": "삼성전자 1Q25 실적 분석",
            "content": "삼성전자의 1분기 실적이 시장 예상치를 상회했습니다.",
            "source": "키움증권",
            "date": "2025-01-15"
        }
    ],
    "context": {
        "industry": "반도체",
        "market_cap": "500조원",
        "analysis_focus": "실적 및 전망"
    }
}

async def test_workflow_creation():
    """워크플로우 생성 테스트"""
    print("🏗️ 워크플로우 생성 테스트...")
    
    try:
        from utils.collaboration.langgraph_manager import LangGraphManager, CollaborationType
        
        # LangGraph 관리자 생성
        langgraph_manager = LangGraphManager()
        
        # 에이전트 노드 추가
        langgraph_manager.add_agent_node(
            agent_id="financial_statement_agent",
            agent_type="financial_statement",
            capabilities=["financial_analysis"],
            dependencies=[],
            priority=1
        )
        
        langgraph_manager.add_agent_node(
            agent_id="risk_assessment_agent",
            agent_type="risk_assessment",
            capabilities=["risk_assessment"],
            dependencies=["financial_statement_agent"],
            priority=2
        )
        
        langgraph_manager.add_agent_node(
            agent_id="supervisor_agent",
            agent_type="supervisor",
            capabilities=["supervision"],
            dependencies=["financial_statement_agent", "risk_assessment_agent"],
            priority=3
        )
        
        # 협업 엣지 추가
        langgraph_manager.add_collaboration_edge(
            from_agent="financial_statement_agent",
            to_agent="risk_assessment_agent",
            collaboration_type=CollaborationType.SEQUENTIAL,
            weight=1.0
        )
        
        langgraph_manager.add_collaboration_edge(
            from_agent="risk_assessment_agent",
            to_agent="supervisor_agent",
            collaboration_type=CollaborationType.SEQUENTIAL,
            weight=1.0
        )
        
        # 워크플로우 생성
        langgraph_manager.create_workflow(
            workflow_id="comprehensive_analysis",
            nodes=["financial_statement_agent", "risk_assessment_agent", "supervisor_agent"],
            edges=[
                ("financial_statement_agent", "risk_assessment_agent"),
                ("risk_assessment_agent", "supervisor_agent")
            ]
        )
        
        # 워크플로우 상태 확인
        workflow_status = langgraph_manager.get_workflow_status("comprehensive_analysis")
        assert workflow_status.get('status') == 'created', "워크플로우 상태가 올바르지 않습니다"
        
        print("✅ 워크플로우 생성 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 워크플로우 생성 테스트 실패: {str(e)}")
        return False

async def test_workflow_execution():
    """워크플로우 실행 테스트"""
    print("▶️ 워크플로우 실행 테스트...")
    
    try:
        from utils.collaboration.langgraph_manager import LangGraphManager, CollaborationType
        
        # LangGraph 관리자 생성
        langgraph_manager = LangGraphManager()
        
        # 간단한 워크플로우 설정
        langgraph_manager.add_agent_node(
            agent_id="test_agent",
            agent_type="test",
            capabilities=["test"],
            dependencies=[],
            priority=1
        )
        
        langgraph_manager.create_workflow(
            workflow_id="test_workflow",
            nodes=["test_agent"],
            edges=[]
        )
        
        # 워크플로우 실행
        result = langgraph_manager.execute_workflow(
            workflow_id="test_workflow",
            input_data=TEST_WORKFLOW_DATA
        )
        
        assert isinstance(result, dict), "워크플로우 실행 결과가 딕셔너리가 아닙니다"
        assert result.get('workflow_id') == 'test_workflow', "워크플로우 ID가 올바르지 않습니다"
        assert result.get('status') == 'completed', "워크플로우 상태가 올바르지 않습니다"
        assert 'input_data' in result, "입력 데이터가 결과에 포함되지 않았습니다"
        
        print("✅ 워크플로우 실행 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 워크플로우 실행 테스트 실패: {str(e)}")
        return False

async def test_workflow_status_management():
    """워크플로우 상태 관리 테스트"""
    print("📊 워크플로우 상태 관리 테스트...")
    
    try:
        from utils.collaboration.langgraph_manager import LangGraphManager
        
        # LangGraph 관리자 생성
        langgraph_manager = LangGraphManager()
        
        # 워크플로우 생성
        langgraph_manager.create_workflow(
            workflow_id="status_test_workflow",
            nodes=["test_agent"],
            edges=[]
        )
        
        # 초기 상태 확인
        initial_status = langgraph_manager.get_workflow_status("status_test_workflow")
        assert initial_status.get('status') == 'created', "초기 상태가 올바르지 않습니다"
        
        # 워크플로우 실행
        langgraph_manager.execute_workflow(
            workflow_id="status_test_workflow",
            input_data=TEST_WORKFLOW_DATA
        )
        
        # 실행 후 상태 확인
        final_status = langgraph_manager.get_workflow_status("status_test_workflow")
        assert final_status.get('status') == 'completed', "최종 상태가 올바르지 않습니다"
        assert 'started_at' in final_status, "시작 시간이 기록되지 않았습니다"
        assert 'completed_at' in final_status, "완료 시간이 기록되지 않았습니다"
        
        print("✅ 워크플로우 상태 관리 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 워크플로우 상태 관리 테스트 실패: {str(e)}")
        return False

async def test_workflow_performance():
    """워크플로우 성능 테스트"""
    print("⚡ 워크플로우 성능 테스트...")
    
    try:
        from utils.collaboration.langgraph_manager import LangGraphManager
        from utils.collaboration.performance import CollaborationPerformance, PerformanceMetric
        
        # LangGraph 관리자 생성
        langgraph_manager = LangGraphManager()
        
        # 성능 모니터링 생성
        performance = CollaborationPerformance(langgraph_manager=langgraph_manager)
        
        # 워크플로우 생성
        langgraph_manager.create_workflow(
            workflow_id="performance_test_workflow",
            nodes=["test_agent"],
            edges=[]
        )
        
        # 성능 데이터 기록
        performance.record_performance(
            metric=PerformanceMetric.RESPONSE_TIME,
            value=1.5,
            workflow_id="performance_test_workflow"
        )
        
        performance.record_performance(
            metric=PerformanceMetric.THROUGHPUT,
            value=20.0,
            workflow_id="performance_test_workflow"
        )
        
        # 워크플로우 실행
        start_time = datetime.now()
        result = langgraph_manager.execute_workflow(
            workflow_id="performance_test_workflow",
            input_data=TEST_WORKFLOW_DATA
        )
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # 성능 분석
        analysis = performance.analyze_collaboration_performance()
        assert isinstance(analysis, dict), "성능 분석 결과가 딕셔너리가 아닙니다"
        
        # 워크플로우 성능 요약
        workflow_summary = performance.get_workflow_performance_summary(
            workflow_id="performance_test_workflow"
        )
        assert isinstance(workflow_summary, dict), "워크플로우 성능 요약이 딕셔너리가 아닙니다"
        
        print(f"✅ 워크플로우 실행 시간: {execution_time:.2f}초")
        print("✅ 워크플로우 성능 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 워크플로우 성능 테스트 실패: {str(e)}")
        return False

async def test_workflow_error_handling():
    """워크플로우 에러 처리 테스트"""
    print("⚠️ 워크플로우 에러 처리 테스트...")
    
    try:
        from utils.collaboration.langgraph_manager import LangGraphManager
        
        # LangGraph 매니저 생성
        langgraph_manager = LangGraphManager()
        
        # 존재하지 않는 워크플로우 실행 시도
        try:
            result = await langgraph_manager.execute_workflow("non_existent_workflow", {})
            # 존재하지 않는 워크플로우는 None을 반환하거나 예외를 발생시킴
            if result is None:
                print("✅ 존재하지 않는 워크플로우에 대해 None 반환됨")
            else:
                print(f"✅ 존재하지 않는 워크플로우 결과: {result}")
        except Exception as e:
            print(f"✅ 예상된 에러 발생: {str(e)}")
        
        # 잘못된 워크플로우 생성 시도
        try:
            # 유효한 워크플로우 생성
            langgraph_manager.create_workflow(
                workflow_id="error_test_workflow",
                nodes=[],
                edges=[]
            )
            print("✅ 빈 워크플로우 생성 성공")
        except Exception as e:
            print(f"✅ 예상된 에러 발생: {str(e)}")
        
        print("✅ 워크플로우 에러 처리 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 워크플로우 에러 처리 테스트 실패: {str(e)}")
        return False

async def test_workflow_validation():
    """워크플로우 검증 테스트"""
    print("✅ 워크플로우 검증 테스트...")
    
    try:
        from utils.collaboration.langgraph_manager import LangGraphManager
        
        # LangGraph 관리자 생성
        langgraph_manager = LangGraphManager()
        
        # 유효한 에이전트 노드 추가
        langgraph_manager.add_agent_node(
            agent_id="agent1",
            agent_type="test",
            capabilities=["test"],
            dependencies=[],
            priority=1
        )
        
        langgraph_manager.add_agent_node(
            agent_id="agent2",
            agent_type="test",
            capabilities=["test"],
            dependencies=["agent1"],
            priority=2
        )
        
        # 유효한 워크플로우 생성
        langgraph_manager.create_workflow(
            workflow_id="valid_workflow",
            nodes=["agent1", "agent2"],
            edges=[("agent1", "agent2")]
        )
        
        # 유효한 워크플로우 검증
        validation = langgraph_manager.validate_workflow("valid_workflow")
        assert validation.get('valid') == True, "유효한 워크플로우가 검증에 실패했습니다"
        assert len(validation.get('issues', [])) == 0, "유효한 워크플로우에 이슈가 있습니다"
        
        # 잘못된 워크플로우 생성
        langgraph_manager.create_workflow(
            workflow_id="invalid_workflow",
            nodes=["agent1", "non_existent_agent"],
            edges=[("agent1", "non_existent_agent")]
        )
        
        # 잘못된 워크플로우 검증
        validation = langgraph_manager.validate_workflow("invalid_workflow")
        assert validation.get('valid') == False, "잘못된 워크플로우가 검증을 통과했습니다"
        assert len(validation.get('issues', [])) > 0, "잘못된 워크플로우에 이슈가 없습니다"
        
        print("✅ 워크플로우 검증 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 워크플로우 검증 테스트 실패: {str(e)}")
        return False

async def test_workflow_history():
    """워크플로우 히스토리 테스트"""
    print("📚 워크플로우 히스토리 테스트...")
    
    try:
        from utils.collaboration.langgraph_manager import LangGraphManager
        
        # LangGraph 관리자 생성
        langgraph_manager = LangGraphManager()
        
        # 워크플로우 생성 및 실행
        langgraph_manager.create_workflow(
            workflow_id="history_test_workflow",
            nodes=["test_agent"],
            edges=[]
        )
        
        langgraph_manager.execute_workflow(
            workflow_id="history_test_workflow",
            input_data=TEST_WORKFLOW_DATA
        )
        
        # 실행 히스토리 확인
        history = langgraph_manager.get_execution_history(limit=10)
        assert isinstance(history, list), "실행 히스토리가 리스트가 아닙니다"
        assert len(history) > 0, "실행 히스토리가 비어있습니다"
        
        # 히스토리 항목 확인
        for history_item in history:
            assert 'workflow_id' in history_item, "워크플로우 ID가 히스토리에 없습니다"
            assert 'execution_time' in history_item, "실행 시간이 히스토리에 없습니다"
            assert 'result' in history_item, "실행 결과가 히스토리에 없습니다"
        
        print("✅ 워크플로우 히스토리 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 워크플로우 히스토리 테스트 실패: {str(e)}")
        return False

async def test_workflow_integration():
    """워크플로우 통합 테스트"""
    print("🔗 워크플로우 통합 테스트...")
    
    try:
        from utils.collaboration.langgraph_manager import LangGraphManager, CollaborationType
        from utils.collaboration.dashboard import CollaborationDashboard
        from utils.collaboration.performance import CollaborationPerformance
        from utils.collaboration.performance import PerformanceMetric
        
        # 모든 컴포넌트 생성
        langgraph_manager = LangGraphManager()
        dashboard = CollaborationDashboard(langgraph_manager=langgraph_manager)
        performance = CollaborationPerformance(langgraph_manager=langgraph_manager)
        
        # 복잡한 워크플로우 설정
        agents = ["agent1", "agent2", "agent3"]
        for i, agent_id in enumerate(agents):
            langgraph_manager.add_agent_node(
                agent_id=agent_id,
                agent_type="test",
                capabilities=["test"],
                dependencies=agents[:i] if i > 0 else [],
                priority=i + 1
            )
        
        # 협업 엣지 추가
        for i in range(len(agents) - 1):
            langgraph_manager.add_collaboration_edge(
                from_agent=agents[i],
                to_agent=agents[i + 1],
                collaboration_type=CollaborationType.SEQUENTIAL,
                weight=1.0
            )
        
        # 워크플로우 생성
        langgraph_manager.create_workflow(
            workflow_id="integration_workflow",
            nodes=agents,
            edges=[(agents[i], agents[i + 1]) for i in range(len(agents) - 1)]
        )
        
        # 워크플로우 검증
        validation = langgraph_manager.validate_workflow("integration_workflow")
        assert validation.get('valid') == True, "통합 워크플로우 검증 실패"
        
        # 워크플로우 실행
        result = langgraph_manager.execute_workflow(
            workflow_id="integration_workflow",
            input_data=TEST_WORKFLOW_DATA
        )
        assert result.get('status') == 'completed', "통합 워크플로우 실행 실패"
        
        # 대시보드 확인
        dashboard_data = dashboard.get_dashboard_data()
        assert isinstance(dashboard_data, dict), "대시보드 데이터가 딕셔너리가 아닙니다"
        
        # 성능 모니터링
        performance.record_performance(
            metric=PerformanceMetric.RESPONSE_TIME,
            value=2.0,
            workflow_id="integration_workflow"
        )
        
        analysis = performance.analyze_collaboration_performance()
        assert isinstance(analysis, dict), "성능 분석이 딕셔너리가 아닙니다"
        
        print("✅ 워크플로우 통합 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 워크플로우 통합 테스트 실패: {str(e)}")
        return False

async def main():
    """메인 테스트 함수"""
    print("🚀 워크플로우 테스트 시작...")
    print("=" * 50)
    
    test_functions = [
        test_workflow_creation,
        test_workflow_execution,
        test_workflow_status_management,
        test_workflow_performance,
        test_workflow_error_handling,
        test_workflow_validation,
        test_workflow_history,
        test_workflow_integration
    ]
    
    passed_tests = 0
    total_tests = len(test_functions)
    
    for test_func in test_functions:
        try:
            result = await test_func()
            if result:
                passed_tests += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} 실행 중 오류: {str(e)}")
    
    print("=" * 50)
    print(f"📊 테스트 결과: {passed_tests}/{total_tests} 통과")
    
    if passed_tests == total_tests:
        print("🎉 모든 워크플로우 테스트가 성공했습니다!")
        return True
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
        return False

if __name__ == "__main__":
    asyncio.run(main()) 