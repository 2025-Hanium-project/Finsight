"""
새로운 Multi-Agent 설계에 따른 테스트 실행 스크립트

기능:
- 모든 테스트 실행
- 카테고리별 테스트 실행
- 개별 테스트 실행
- 테스트 결과 요약
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Tuple, Dict, Any

# 상위 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def run_agent_tests():
    """에이전트 테스트 실행"""
    print("🤖 에이전트 테스트 실행 중...")
    try:
        from test_agents import main as agent_main
        return await agent_main()
    except Exception as e:
        print(f"❌ 에이전트 테스트 실행 실패: {str(e)}")
        return False

async def run_collaboration_tests():
    """협업 시스템 테스트 실행"""
    print("🤝 협업 시스템 테스트 실행 중...")
    try:
        from test_collaboration import main as collaboration_main
        return await collaboration_main()
    except Exception as e:
        print(f"❌ 협업 시스템 테스트 실행 실패: {str(e)}")
        return False

async def run_api_tests():
    """API 테스트 실행"""
    print("🌐 API 테스트 실행 중...")
    try:
        from test_api import main as api_main
        return await api_main()
    except Exception as e:
        print(f"❌ API 테스트 실행 실패: {str(e)}")
        return False

async def run_llm_tests():
    """LLM 테스트 실행"""
    print("🧠 LLM 테스트 실행 중...")
    try:
        from test_llm import main as llm_main
        return await llm_main()
    except Exception as e:
        print(f"❌ LLM 테스트 실행 실패: {str(e)}")
        return False

async def run_workflow_tests():
    """워크플로우 테스트 실행"""
    print("⚙️ 워크플로우 테스트 실행 중...")
    try:
        from test_workflow import main as workflow_main
        return await workflow_main()
    except Exception as e:
        print(f"❌ 워크플로우 테스트 실행 실패: {str(e)}")
        return False

async def run_unit_tests():
    """단위 테스트 실행"""
    print("🔧 단위 테스트 실행 중...")
    try:
        from test_unit import main as unit_main
        return await unit_main()
    except Exception as e:
        print(f"❌ 단위 테스트 실행 실패: {str(e)}")
        return False

async def run_performance_tests():
    """성능 테스트 실행"""
    print("⚡ 성능 테스트 실행 중...")
    try:
        # 성능 관련 테스트들을 직접 실행
        from utils.performance.monitor import PerformanceMonitor
        from utils.performance.optimizer import PerformanceOptimizer
        from utils.performance.dashboard import PerformanceDashboard
        from utils.performance.metrics import PerformanceMetrics
        from utils.performance.alerts import PerformanceAlert
        
        # 성능 모니터링 테스트
        monitor = PerformanceMonitor()
        assert monitor is not None, "성능 모니터링 초기화 실패"
        
        # 성능 최적화 테스트
        optimizer = PerformanceOptimizer()
        assert optimizer is not None, "성능 최적화 초기화 실패"
        
        # 성능 대시보드 테스트
        dashboard = PerformanceDashboard()
        assert dashboard is not None, "성능 대시보드 초기화 실패"
        
        # 성능 메트릭 테스트
        metrics = PerformanceMetrics()
        assert metrics is not None, "성능 메트릭 초기화 실패"
        
        # 성능 알림 테스트
        alerts = PerformanceAlert()
        assert alerts is not None, "성능 알림 초기화 실패"
        
        print("✅ 성능 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 성능 테스트 실행 실패: {str(e)}")
        return False

async def run_utils_tests():
    """Utils 테스트 실행"""
    print("🛠️ Utils 테스트 실행 중...")
    try:
        # Utils 모듈 import 테스트
        from utils.core.agent_base import AnalysisAgent, AgentConfig, AgentCapability, AgentRegistry
        from utils.core.data_models import StandardInput, StandardOutput, AgentType, ProcessingStatus
        from utils.llm.llm_client import generate_response, LLMClient
        from utils.collaboration.base import CollaborationBase, CollaborationManager
        from utils.collaboration.langgraph_manager import LangGraphManager
        from utils.collaboration.dashboard import CollaborationDashboard
        from utils.collaboration.performance import CollaborationPerformance
        from utils.performance.monitor import PerformanceMonitor
        from utils.performance.optimizer import PerformanceOptimizer
        from utils.performance.dashboard import PerformanceDashboard
        from utils.performance.metrics import PerformanceMetrics
        from utils.performance.alerts import PerformanceAlert
        
        print("✅ Utils 모듈 import 성공!")
        
        # 기본 클래스 생성 테스트
        config = AgentConfig(
            name="test_agent",
            agent_type=AgentType.FINANCIAL_STATEMENT,
            capabilities=[AgentCapability.FINANCIAL_ANALYSIS]
        )
        assert config.name == "test_agent", "AgentConfig 생성 실패"
        
        registry = AgentRegistry()
        assert registry is not None, "AgentRegistry 생성 실패"
        
        langgraph_manager = LangGraphManager()
        assert langgraph_manager is not None, "LangGraphManager 생성 실패"
        
        dashboard = CollaborationDashboard()
        assert dashboard is not None, "CollaborationDashboard 생성 실패"
        
        performance = CollaborationPerformance()
        assert performance is not None, "CollaborationPerformance 생성 실패"
        
        print("✅ Utils 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ Utils 테스트 실행 실패: {str(e)}")
        return False

async def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 전체 테스트 시작")
    print("=" * 80)
    print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    test_categories = [
        ("Utils 테스트", run_utils_tests),
        ("에이전트 테스트", run_agent_tests),
        ("협업 시스템 테스트", run_collaboration_tests),
        ("워크플로우 테스트", run_workflow_tests),
        ("성능 테스트", run_performance_tests),
        ("API 테스트", run_api_tests),
        ("LLM 테스트", run_llm_tests),
        ("단위 테스트", run_unit_tests)
    ]
    
    results = []
    
    for category_name, test_func in test_categories:
        print(f"\n📋 {category_name} 실행 중...")
        try:
            result = await test_func()
            results.append((category_name, result))
            if result:
                print(f"✅ {category_name} 성공!")
            else:
                print(f"❌ {category_name} 실패!")
        except Exception as e:
            print(f"❌ {category_name} 실행 중 오류: {str(e)}")
            results.append((category_name, False))
    
    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 전체 테스트 결과 요약")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for category_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{category_name}: {status}")
    
    print(f"\n전체 결과: {passed}/{total} 카테고리 통과")
    
    if passed == total:
        print("🎉 모든 테스트가 성공했습니다!")
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
    
    print("=" * 80)
    print(f"테스트 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return passed == total

async def run_category_tests(category: str):
    """카테고리별 테스트 실행"""
    category_map = {
        "utils": run_utils_tests,
        "agents": run_agent_tests,
        "collaboration": run_collaboration_tests,
        "workflow": run_workflow_tests,
        "performance": run_performance_tests,
        "api": run_api_tests,
        "llm": run_llm_tests,
        "unit": run_unit_tests
    }
    
    if category not in category_map:
        print(f"❌ 알 수 없는 테스트 카테고리: {category}")
        print("사용 가능한 카테고리:")
        for cat in category_map.keys():
            print(f"  - {cat}")
        return False
    
    print(f"🚀 {category} 테스트 시작")
    print("=" * 60)
    print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        result = await category_map[category]()
        
        print("=" * 60)
        if result:
            print(f"✅ {category} 테스트 성공!")
        else:
            print(f"❌ {category} 테스트 실패!")
        print("=" * 60)
        print(f"테스트 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        return result
        
    except Exception as e:
        print(f"❌ {category} 테스트 실행 중 오류: {str(e)}")
        return False

def print_usage():
    """사용법 출력"""
    print("사용법:")
    print("  python run_tests.py [category|all]")
    print("")
    print("카테고리:")
    print("  utils         - Utils 모듈 테스트")
    print("  agents        - 에이전트 테스트")
    print("  collaboration - 협업 시스템 테스트")
    print("  workflow     - 워크플로우 테스트")
    print("  performance  - 성능 테스트")
    print("  api          - API 테스트")
    print("  llm          - LLM 테스트")
    print("  unit         - 단위 테스트")
    print("  all          - 모든 테스트 (기본값)")
    print("")
    print("예시:")
    print("  python run_tests.py all")
    print("  python run_tests.py agents")
    print("  python run_tests.py collaboration")

def main():
    """메인 함수"""
    import sys
    
    if len(sys.argv) > 1:
        category = sys.argv[1].lower()
        if category == "all":
            asyncio.run(run_all_tests())
        else:
            asyncio.run(run_category_tests(category))
    else:
        # 기본값으로 모든 테스트 실행
        asyncio.run(run_all_tests())

if __name__ == "__main__":
    main() 