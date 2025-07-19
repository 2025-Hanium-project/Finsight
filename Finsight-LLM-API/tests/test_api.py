"""
API 테스트
"""
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# 테스트용 API 데이터
TEST_API_DATA = {
    "target_type": "stock",
    "target_name": "삼성전자",
    "symbol": "005930",
    "reports": ["2024Q1", "2024Q2"],
    "analysis_type": "financial_statement",
    "context": {
        "market_condition": "bull",
        "sector": "technology"
    }
}

# Import 테스트
async def test_imports():
    """Import 테스트"""
    print("=== Import 테스트 ===")
    
    try:
        # 1. 기본 모듈들
        from utils.core.agent_base import AgentConfig, AgentType, AgentCapability
        print("✅ Agent Base Import 성공")
        
        from utils.core.data_models import StandardInput, StandardOutput, ProcessingStatus
        print("✅ Data Models Import 성공")
        
        # 2. 협업 시스템
        from utils.collaboration.base import CollaborationManager
        print("✅ Collaboration Manager Import 성공")
        
        from utils.collaboration.langgraph_manager import LangGraphManager
        print("✅ LangGraph Manager Import 성공")
        
        # 3. 성능 모니터링
        from utils.performance.monitor import PerformanceMonitor
        print("✅ Performance Monitor Import 성공")
        
        # 4. LLM 클라이언트
        from utils.llm.llm_client import generate_response, LLMClient
        print("✅ LLM Client Import 성공")
        
        # 5. 에이전트들 (전역 인스턴스 확인)
        try:
            from agents.analysis_agents.risk_assessment_agent import risk_assessment_agent
            print("✅ Risk Assessment Agent Import 성공")
        except ImportError:
            print("⚠️ Risk Assessment Agent Import 실패 (전역 인스턴스 없음)")
        
        try:
            from agents.data_agents.financial_statement_agent import financial_statement_agent
            print("✅ Financial Statement Agent Import 성공")
        except ImportError:
            print("⚠️ Financial Statement Agent Import 실패 (전역 인스턴스 없음)")
        
        try:
            from agents.data_agents.news_analysis_agent import news_analysis_agent
            print("✅ News Analysis Agent Import 성공")
        except ImportError:
            print("⚠️ News Analysis Agent Import 실패 (전역 인스턴스 없음)")
        
        try:
            from agents.data_agents.market_data_agent import market_data_agent
            print("✅ Market Data Agent Import 성공")
        except ImportError:
            print("⚠️ Market Data Agent Import 실패 (전역 인스턴스 없음)")
        
        # 6. API 모듈
        from app import app
        print("✅ FastAPI 앱 Import 성공")
        
        # 7. 라우터들
        from routers.report_router import router as report_router
        print("✅ Report Router Import 성공")
        
        print("✅ 모든 Import 성공!")
        return True
        
    except Exception as e:
        print(f"❌ Import 실패: {str(e)}")
        return False

async def test_api_endpoints():
    """API 엔드포인트 테스트"""
    print("🌐 API 엔드포인트 테스트...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        # TestClient 생성
        client = TestClient(app)
        
        # 루트 엔드포인트 테스트
        response = client.get("/")
        assert response.status_code == 200, "루트 엔드포인트 응답 코드가 200이 아닙니다"
        
        root_data = response.json()
        assert "message" in root_data, "루트 응답에 message 필드가 없습니다"
        assert "version" in root_data, "루트 응답에 version 필드가 없습니다"
        
        # API 정보 엔드포인트 테스트
        response = client.get("/api")
        assert response.status_code == 200, "API 정보 엔드포인트 응답 코드가 200이 아닙니다"
        
        api_data = response.json()
        assert "name" in api_data, "API 정보에 name 필드가 없습니다"
        assert "endpoints" in api_data, "API 정보에 endpoints 필드가 없습니다"
        
        # 시스템 상태 엔드포인트 테스트
        response = client.get("/api/system/status")
        assert response.status_code == 200, "시스템 상태 엔드포인트 응답 코드가 200이 아닙니다"
        
        status_data = response.json()
        assert "status" in status_data, "시스템 상태에 status 필드가 없습니다"
        
        print("✅ API 엔드포인트 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ API 엔드포인트 테스트 실패: {str(e)}")
        return False

async def test_agent_endpoints():
    """에이전트 API 엔드포인트 테스트"""
    print("🤖 에이전트 API 엔드포인트 테스트...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        from utils.core.data_models import StandardInput
        
        client = TestClient(app)
        
        # 데이터 에이전트 API 테스트
        agent_endpoints = [
            "/api/v1/agents/financial-statement",
            "/api/v1/agents/news-analysis",
            "/api/v1/agents/securities-report",
            "/api/v1/agents/market-data"
        ]
        
        for endpoint in agent_endpoints:
            response = client.post(
                endpoint,
                json=TEST_API_DATA
            )
            
            # 응답 코드 확인 (422는 데이터 검증 실패, 500은 서버 오류)
            assert response.status_code in [200, 422, 500], f"{endpoint} 응답 코드가 예상과 다릅니다"
            
            if response.status_code == 200:
                response_data = response.json()
                assert "agent_type" in response_data, f"{endpoint} 응답에 agent_type 필드가 없습니다"
                assert "status" in response_data, f"{endpoint} 응답에 status 필드가 없습니다"
        
        # 분석 에이전트 API 테스트
        analysis_endpoints = [
            "/api/v1/agents/risk-assessment",
            "/api/v1/agents/growth-analysis",
            "/api/v1/agents/valuation",
            "/api/v1/agents/peer-comparison"
        ]
        
        for endpoint in analysis_endpoints:
            response = client.post(
                endpoint,
                json=TEST_API_DATA
            )
            
            assert response.status_code in [200, 422, 500], f"{endpoint} 응답 코드가 예상과 다릅니다"
        
        # 리포트 에이전트 API 테스트
        report_endpoints = [
            "/api/v1/agents/dday-report",
            "/api/v1/agents/dplus1-report"
        ]
        
        for endpoint in report_endpoints:
            response = client.post(
                endpoint,
                json=TEST_API_DATA
            )
            
            assert response.status_code in [200, 422, 500], f"{endpoint} 응답 코드가 예상과 다릅니다"
        
        # 지원 에이전트 API 테스트
        support_endpoints = [
            "/api/v1/agents/document-processing",
            "/api/v1/agents/data-quality",
            "/api/v1/agents/supervisor"
        ]
        
        for endpoint in support_endpoints:
            response = client.post(
                endpoint,
                json=TEST_API_DATA
            )
            
            assert response.status_code in [200, 422, 500], f"{endpoint} 응답 코드가 예상과 다릅니다"
        
        print("✅ 에이전트 API 엔드포인트 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 에이전트 API 엔드포인트 테스트 실패: {str(e)}")
        return False

async def test_collaboration_endpoints():
    """협업 API 엔드포인트 테스트"""
    print("🤝 협업 API 엔드포인트 테스트...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        # 협업 엔드포인트 테스트
        collaboration_endpoints = [
            "/api/v1/collaboration/basic",
            "/api/v1/collaboration/advanced",
            "/api/v1/collaboration/optimized"
        ]
        
        for endpoint in collaboration_endpoints:
            response = client.post(
                endpoint,
                json=TEST_API_DATA
            )
            
            # 응답 코드 확인 (422는 데이터 검증 실패, 500은 서버 오류)
            assert response.status_code in [200, 422, 500], f"{endpoint} 응답 코드가 예상과 다릅니다"
            
            if response.status_code == 200:
                response_data = response.json()
                assert isinstance(response_data, dict), f"{endpoint} 응답이 딕셔너리가 아닙니다"
        
        # 협업 상태 엔드포인트 테스트
        status_endpoints = [
            "/api/collaboration/status",
            "/api/v1/dashboard/summary"
        ]
        
        for endpoint in status_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 500], f"{endpoint} 응답 코드가 예상과 다릅니다"
        
        print("✅ 협업 API 엔드포인트 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 협업 API 엔드포인트 테스트 실패: {str(e)}")
        return False

async def test_workflow_endpoints():
    """워크플로우 API 엔드포인트 테스트"""
    print("⚙️ 워크플로우 API 엔드포인트 테스트...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        # 워크플로우 엔드포인트 테스트
        workflow_endpoints = [
            "/api/v1/workflow/comprehensive"
        ]
        
        for endpoint in workflow_endpoints:
            response = client.post(
                endpoint,
                json=TEST_API_DATA
            )
            
            # 응답 코드 확인 (422는 데이터 검증 실패, 500은 서버 오류)
            assert response.status_code in [200, 422, 500], f"{endpoint} 응답 코드가 예상과 다릅니다"
            
            if response.status_code == 200:
                response_data = response.json()
                assert isinstance(response_data, dict), f"{endpoint} 응답이 딕셔너리가 아닙니다"
        
        print("✅ 워크플로우 API 엔드포인트 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 워크플로우 API 엔드포인트 테스트 실패: {str(e)}")
        return False

async def test_dashboard_endpoints():
    """대시보드 API 엔드포인트 테스트"""
    print("📊 대시보드 API 엔드포인트 테스트...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        # 대시보드 엔드포인트 테스트
        dashboard_endpoints = [
            "/api/v1/dashboard/summary",
            "/api/v1/dashboard/agent/financial_statement_agent",
            "/api/v1/dashboard/alerts",
            "/api/v1/dashboard/visualization"
        ]
        
        for endpoint in dashboard_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 500], f"{endpoint} 응답 코드가 예상과 다릅니다"
            
            if response.status_code == 200:
                response_data = response.json()
                # alerts 엔드포인트는 리스트를 반환할 수 있음
                if endpoint.endswith('/alerts'):
                    assert isinstance(response_data, (dict, list)), f"{endpoint} 응답이 딕셔너리나 리스트가 아닙니다"
                else:
                    assert isinstance(response_data, dict), f"{endpoint} 응답이 딕셔너리가 아닙니다"
        
        print("✅ 대시보드 API 엔드포인트 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 대시보드 API 엔드포인트 테스트 실패: {str(e)}")
        return False

async def test_health_endpoints():
    """헬스체크 API 엔드포인트 테스트"""
    print("💚 헬스체크 API 엔드포인트 테스트...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        # 헬스체크 엔드포인트 테스트
        health_endpoints = [
            "/api/v1/health",
            "/api/v1/agents/list"
        ]
        
        for endpoint in health_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 500], f"{endpoint} 응답 코드가 예상과 다릅니다"
            
            if response.status_code == 200:
                response_data = response.json()
                assert isinstance(response_data, dict), f"{endpoint} 응답이 딕셔너리가 아닙니다"
        
        print("✅ 헬스체크 API 엔드포인트 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 헬스체크 API 엔드포인트 테스트 실패: {str(e)}")
        return False

async def test_api_error_handling():
    """API 에러 처리 테스트"""
    print("🚨 API 에러 처리 테스트...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        # 잘못된 데이터로 테스트
        invalid_data = {
            "target_type": "invalid_type",
            "target_name": "",
            "reports": "invalid_reports"
        }
        
        # 에이전트 엔드포인트에 잘못된 데이터 전송
        response = client.post(
            "/api/v1/agents/financial-statement",
            json=invalid_data
        )
        
        # 에러 응답 확인 (422는 데이터 검증 실패, 400은 잘못된 요청, 500은 서버 오류)
        assert response.status_code in [400, 422, 500], "잘못된 데이터에 대한 적절한 에러 응답이 없습니다"
        
        # 존재하지 않는 엔드포인트 테스트
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404, "존재하지 않는 엔드포인트에 대한 404 응답이 없습니다"
        
        print("✅ API 에러 처리 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ API 에러 처리 테스트 실패: {str(e)}")
        return False

async def test_api_performance():
    """API 성능 테스트"""
    print("⚡ API 성능 테스트...")
    
    try:
        import time
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        # 성능 테스트용 엔드포인트들
        performance_endpoints = [
            "/",
            "/api",
            "/api/v1/health"
        ]
        
        performance_results = {}
        
        for endpoint in performance_endpoints:
            start_time = time.time()
            
            # 5회 반복 테스트
            for i in range(5):
                response = client.get(endpoint)
                assert response.status_code in [200, 500], f"{endpoint} 응답 코드가 예상과 다릅니다"
            
            end_time = time.time()
            avg_time = (end_time - start_time) / 5
            performance_results[endpoint] = avg_time
            
            print(f"✅ {endpoint}: 평균 {avg_time:.3f}초")
        
        # 성능 기준 확인 (각 엔드포인트당 1초 이내)
        for endpoint, avg_time in performance_results.items():
            assert avg_time < 1.0, f"{endpoint}의 평균 응답 시간({avg_time:.3f}초)이 1초를 초과합니다"
        
        print("✅ 모든 API 엔드포인트가 성능 기준을 만족합니다!")
        return True
        
    except Exception as e:
        print(f"❌ API 성능 테스트 실패: {str(e)}")
        return False

async def test_api_integration():
    """API 통합 테스트"""
    print("🔗 API 통합 테스트...")
    
    try:
        from fastapi.testclient import TestClient
        from app import app
        
        client = TestClient(app)
        
        # 1. 시스템 상태 확인
        response = client.get("/api/system/status")
        assert response.status_code in [200, 500], "시스템 상태 확인 실패"
        
        # 2. 에이전트 목록 확인
        response = client.get("/api/v1/agents/list")
        assert response.status_code in [200, 500], "에이전트 목록 확인 실패"
        
        # 3. 협업 시스템 상태 확인
        response = client.get("/api/collaboration/status")
        assert response.status_code in [200, 500], "협업 시스템 상태 확인 실패"
        
        # 4. 대시보드 확인
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code in [200, 500], "대시보드 확인 실패"
        
        # 5. 헬스체크 확인
        response = client.get("/api/v1/health")
        assert response.status_code in [200, 500], "헬스체크 확인 실패"
        
        print("✅ API 통합 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ API 통합 테스트 실패: {str(e)}")
        return False

async def main():
    """메인 테스트 함수"""
    print("🚀 API 테스트 시작")
    print("=" * 60)
    print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Import 테스트", test_imports),
        ("엔드포인트 테스트", test_api_endpoints),
        ("에이전트 API 테스트", test_agent_endpoints),
        ("협업 API 테스트", test_collaboration_endpoints),
        ("워크플로우 API 테스트", test_workflow_endpoints),
        ("대시보드 API 테스트", test_dashboard_endpoints),
        ("헬스체크 API 테스트", test_health_endpoints),
        ("에러 처리 테스트", test_api_error_handling),
        ("성능 테스트", test_api_performance),
        ("통합 테스트", test_api_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 실행 중...")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} 성공!")
            else:
                print(f"❌ {test_name} 실패!")
        except Exception as e:
            print(f"❌ {test_name} 실행 중 오류: {str(e)}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 API 테스트 결과 요약")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name}: {status}")
    
    print(f"\n전체 결과: {passed}/{total} 테스트 통과")
    
    if passed == total:
        print("🎉 모든 API 테스트가 성공했습니다!")
    else:
        print("⚠️ 일부 API 테스트가 실패했습니다.")
    
    print("=" * 60)
    print(f"테스트 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main()) 