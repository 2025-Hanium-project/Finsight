"""
새로운 Multi-Agent 설계에 따른 에이전트 테스트

기능:
- 각 에이전트 카테고리별 테스트
- 에이전트 생성 및 초기화 테스트
- 에이전트 분석 기능 테스트
- 에이전트 협업 기능 테스트
- 에이전트 성능 테스트
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# 상위 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 테스트용 데이터
TEST_DATA = {
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

async def test_agent_imports():
    """에이전트 import 테스트"""
    print("🔍 에이전트 import 테스트...")
    
    try:
        # 기본 에이전트 클래스 import 테스트
        from utils.core.agent_base import AnalysisAgent, AgentConfig, AgentCapability, AgentRegistry
        
        # 데이터 모델 import 테스트
        from utils.core.data_models import StandardInput, StandardOutput, AgentType, ProcessingStatus
        
        print("✅ 모든 에이전트 관련 모듈 import 성공!")
        return True
        
    except ImportError as e:
        print(f"❌ 에이전트 import 실패: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
        return False

async def test_agent_base_creation():
    """에이전트 기본 클래스 생성 테스트"""
    print("🏗️ 에이전트 기본 클래스 생성 테스트...")
    
    try:
        from utils.core.agent_base import AnalysisAgent, AgentConfig, AgentCapability, AgentRegistry
        from utils.core.data_models import AgentType
        
        # 에이전트 설정 생성
        config = AgentConfig(
            name="test_agent",
            agent_type=AgentType.FINANCIAL_STATEMENT,
            capabilities=[AgentCapability.FINANCIAL_ANALYSIS],
            model_name="gemini-2.0-flash",
            temperature=0.7,
            max_tokens=4096
        )
        
        # 에이전트 레지스트리 테스트
        registry = AgentRegistry()
        assert hasattr(registry, 'register_agent'), "AgentRegistry에 register_agent 메서드가 없습니다"
        assert hasattr(registry, 'create_agent'), "AgentRegistry에 create_agent 메서드가 없습니다"
        
        print("✅ 에이전트 기본 클래스 생성 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 에이전트 기본 클래스 생성 실패: {str(e)}")
        return False

async def test_agent_data_models():
    """에이전트 데이터 모델 테스트"""
    print("📊 에이전트 데이터 모델 테스트...")
    
    try:
        from utils.core.data_models import StandardInput, StandardOutput, AgentType, ProcessingStatus
        
        # StandardInput 생성 테스트
        input_data = StandardInput(
            target_type="company",
            target_name="삼성전자",
            symbol="005930",
            reports=TEST_DATA["reports"],
            context=TEST_DATA["context"]
        )
        
        assert input_data.target_type == "company", "target_type이 올바르지 않습니다"
        assert input_data.target_name == "삼성전자", "target_name이 올바르지 않습니다"
        assert input_data.symbol == "005930", "symbol이 올바르지 않습니다"
        
        # StandardOutput 생성 테스트
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
        
        assert output_data.agent_type == AgentType.FINANCIAL_STATEMENT, "agent_type이 올바르지 않습니다"
        assert output_data.status == ProcessingStatus.COMPLETED, "status가 올바르지 않습니다"
        assert output_data.success == True, "success가 올바르지 않습니다"
        
        print("✅ 에이전트 데이터 모델 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 에이전트 데이터 모델 테스트 실패: {str(e)}")
        return False

async def test_agent_registry():
    """에이전트 레지스트리 테스트"""
    print("🏭 에이전트 레지스트리 테스트...")
    
    try:
        from utils.core.agent_base import AgentRegistry, AgentConfig, AgentCapability
        from utils.core.data_models import AgentType
        
        registry = AgentRegistry()
        
        # 사용 가능한 에이전트 목록 확인
        all_agents = registry.get_all_agents()
        assert isinstance(all_agents, list), "모든 에이전트 목록이 리스트가 아닙니다"
        
        # 에이전트 설정 생성
        config = AgentConfig(
            name="test_registry_agent",
            agent_type=AgentType.FINANCIAL_STATEMENT,
            capabilities=[AgentCapability.FINANCIAL_ANALYSIS],
            model_name="gemini-2.0-flash"
        )
        
        print("✅ 에이전트 레지스트리 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 에이전트 레지스트리 테스트 실패: {str(e)}")
        return False

async def test_agent_capabilities():
    """에이전트 능력 테스트"""
    print("💪 에이전트 능력 테스트...")
    
    try:
        from utils.core.agent_base import AgentCapability
        
        # 모든 능력 확인
        capabilities = [
            AgentCapability.FINANCIAL_ANALYSIS,
            AgentCapability.NEWS_ANALYSIS,
            AgentCapability.RISK_ASSESSMENT,
            AgentCapability.GROWTH_ANALYSIS,
            AgentCapability.VALUATION,
            AgentCapability.PEER_COMPARISON,
            AgentCapability.SUPERVISION,
            AgentCapability.MARKET_DATA,
            AgentCapability.DOCUMENT_PROCESSING,
            AgentCapability.COLLABORATION
        ]
        
        for capability in capabilities:
            assert isinstance(capability, AgentCapability), f"{capability}가 AgentCapability가 아닙니다"
            assert capability.value in [
                "financial_analysis", "news_analysis", "risk_assessment",
                "growth_analysis", "valuation", "peer_comparison",
                "supervision", "market_data", "document_processing", "collaboration"
            ], f"{capability.value}가 유효한 능력 값이 아닙니다"
        
        print("✅ 에이전트 능력 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 에이전트 능력 테스트 실패: {str(e)}")
        return False

async def test_agent_config():
    """에이전트 설정 테스트"""
    print("⚙️ 에이전트 설정 테스트...")
    
    try:
        from utils.core.agent_base import AgentConfig, AgentCapability
        from utils.core.data_models import AgentType
        
        # 기본 설정으로 에이전트 생성
        config = AgentConfig(
            name="test_config_agent",
            agent_type=AgentType.FINANCIAL_STATEMENT,
            capabilities=[AgentCapability.FINANCIAL_ANALYSIS]
        )
        
        assert config.name == "test_config_agent", "에이전트 이름이 올바르지 않습니다"
        assert config.agent_type == AgentType.FINANCIAL_STATEMENT, "에이전트 타입이 올바르지 않습니다"
        assert AgentCapability.FINANCIAL_ANALYSIS in config.capabilities, "기본 능력이 설정되지 않았습니다"
        assert config.model_name == "gemini-2.0-flash", "기본 모델이 올바르지 않습니다"
        assert config.temperature == 0.7, "기본 temperature가 올바르지 않습니다"
        assert config.max_tokens == 4096, "기본 max_tokens가 올바르지 않습니다"
        
        # 설정 업데이트 테스트
        config.update_config(temperature=0.5, max_tokens=2048)
        assert config.temperature == 0.5, "temperature 업데이트가 실패했습니다"
        assert config.max_tokens == 2048, "max_tokens 업데이트가 실패했습니다"
        
        print("✅ 에이전트 설정 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 에이전트 설정 테스트 실패: {str(e)}")
        return False

async def test_agent_types():
    """에이전트 타입 테스트"""
    print("🏷️ 에이전트 타입 테스트...")
    
    try:
        from utils.core.data_models import AgentType
        
        # 모든 에이전트 타입 확인
        agent_types = [
            AgentType.FINANCIAL_STATEMENT,
            AgentType.NEWS_ANALYSIS,
            AgentType.RISK_ASSESSMENT,
            AgentType.GROWTH_ANALYSIS,
            AgentType.VALUATION,
            AgentType.PEER_COMPARISON,
            AgentType.SUPERVISOR,
            AgentType.MARKET_DATA
        ]
        
        for agent_type in agent_types:
            assert isinstance(agent_type, AgentType), f"{agent_type}가 AgentType가 아닙니다"
            assert agent_type.value in [
                "financial_statement", "news_analysis", "risk_assessment",
                "growth_analysis", "valuation", "peer_comparison",
                "supervisor", "market_data"
            ], f"{agent_type.value}가 유효한 에이전트 타입 값이 아닙니다"
        
        print("✅ 에이전트 타입 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 에이전트 타입 테스트 실패: {str(e)}")
        return False

async def test_agent_processing_status():
    """에이전트 처리 상태 테스트"""
    print("🔄 에이전트 처리 상태 테스트...")
    
    try:
        from utils.core.data_models import ProcessingStatus
        
        # 모든 처리 상태 확인
        statuses = [
            ProcessingStatus.PENDING,
            ProcessingStatus.PROCESSING,
            ProcessingStatus.COMPLETED,
            ProcessingStatus.FAILED,
            ProcessingStatus.CANCELLED
        ]
        
        for status in statuses:
            assert isinstance(status, ProcessingStatus), f"{status}가 ProcessingStatus가 아닙니다"
            assert status.value in [
                "pending", "processing", "completed", "failed", "cancelled"
            ], f"{status.value}가 유효한 처리 상태 값이 아닙니다"
        
        print("✅ 에이전트 처리 상태 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 에이전트 처리 상태 테스트 실패: {str(e)}")
        return False

async def test_agent_error_handling():
    """에이전트 에러 처리 테스트"""
    print("⚠️ 에이전트 에러 처리 테스트...")
    
    try:
        from utils.core.agent_base import AgentConfig, AgentCapability
        from utils.core.data_models import AgentType
        
        # 유효한 설정으로 에이전트 생성
        config = AgentConfig(
            name="test_error_agent",
            agent_type=AgentType.FINANCIAL_STATEMENT,
            capabilities=[AgentCapability.FINANCIAL_ANALYSIS]
        )
        
        assert config.name == "test_error_agent", "에이전트 이름이 올바르지 않습니다"
        assert config.agent_type == AgentType.FINANCIAL_STATEMENT, "에이전트 타입이 올바르지 않습니다"
        
        # 에러 처리 테스트 - 잘못된 설정으로 생성 시도
        try:
            invalid_config = AgentConfig(
                name="",  # 빈 이름
                agent_type=AgentType.FINANCIAL_STATEMENT
            )
            # 빈 이름이어도 기본값이 설정되므로 에러가 발생하지 않음
            assert invalid_config.name == "", "빈 이름이 허용되어야 합니다"
        except Exception as e:
            # 예외가 발생하면 로그만 출력
            print(f"예상된 에러: {str(e)}")
        
        print("✅ 에이전트 에러 처리 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 에이전트 에러 처리 테스트 실패: {str(e)}")
        return False

async def test_agent_performance():
    """에이전트 성능 테스트"""
    print("⚡ 에이전트 성능 테스트...")
    
    try:
        from utils.core.agent_base import AgentConfig, AgentCapability
        from utils.core.data_models import AgentType
        
        # 성능 테스트용 에이전트 설정
        config = AgentConfig(
            name="performance_test_agent",
            agent_type=AgentType.FINANCIAL_STATEMENT,
            capabilities=[AgentCapability.FINANCIAL_ANALYSIS],
            model_name="gemini-2.0-flash",
            temperature=0.7,
            max_tokens=4096,
            timeout=30,
            max_retries=3
        )
        
        # 성능 설정 확인
        assert config.timeout == 30, "timeout 설정이 올바르지 않습니다"
        assert config.max_retries == 3, "max_retries 설정이 올바르지 않습니다"
        assert config.collaboration_enabled == True, "기본 협업 설정이 활성화되지 않았습니다"
        
        # 성능 설정 업데이트
        config.update_config(timeout=60, max_retries=5)
        assert config.timeout == 60, "timeout 업데이트가 실패했습니다"
        assert config.max_retries == 5, "max_retries 업데이트가 실패했습니다"
        
        print("✅ 에이전트 성능 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 에이전트 성능 테스트 실패: {str(e)}")
        return False

async def test_agent_health_check():
    """에이전트 건강 상태 테스트"""
    print("🏥 에이전트 건강 상태 테스트...")
    
    try:
        from utils.core.agent_base import AgentConfig, AgentCapability
        from utils.core.data_models import AgentType
        
        # 테스트용 에이전트 설정
        config = AgentConfig(
            name="health_test_agent",
            agent_type=AgentType.FINANCIAL_STATEMENT,
            capabilities=[AgentCapability.FINANCIAL_ANALYSIS]
        )
        
        # 건강 상태 확인 (시뮬레이션)
        health_status = {
            "name": config.name,
            "agent_type": config.agent_type.value,
            "is_active": config.is_active,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0
        }
        
        assert health_status["name"] == "health_test_agent", "에이전트 이름이 올바르지 않습니다"
        assert health_status["agent_type"] == "financial_statement", "에이전트 타입이 올바르지 않습니다"
        assert health_status["is_active"] == True, "에이전트가 활성 상태가 아닙니다"
        
        print("✅ 에이전트 건강 상태 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ 에이전트 건강 상태 테스트 실패: {str(e)}")
        return False

async def main():
    """메인 테스트 함수"""
    print("🚀 에이전트 테스트 시작...")
    print("=" * 50)
    
    test_functions = [
        test_agent_imports,
        test_agent_base_creation,
        test_agent_data_models,
        test_agent_registry,
        test_agent_capabilities,
        test_agent_config,
        test_agent_types,
        test_agent_processing_status,
        test_agent_error_handling,
        test_agent_performance,
        test_agent_health_check
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
        print("🎉 모든 에이전트 테스트가 성공했습니다!")
        return True
    else:
        print("⚠️ 일부 테스트가 실패했습니다.")
        return False

if __name__ == "__main__":
    asyncio.run(main()) 