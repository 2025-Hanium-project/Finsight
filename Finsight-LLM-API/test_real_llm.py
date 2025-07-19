"""
실제 LLM API와 연동하여 새로운 Agent 구조 테스트
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Agent 모듈 import
from agents import (
    analyze_financial_statement,
    analyze_news,
    analyze_securities_report,
    analyze_market_data,
    assess_risk,
    analyze_growth,
    analyze_valuation,
    compare_peers,
    generate_dday_report,
    generate_dplus1_report,
    process_document,
    assess_data_quality,
    supervise_analysis
)

from utils.llm_client import get_llm_client
from utils.agent_base import get_collaboration_manager


async def test_financial_statement_agent():
    """재무제표 분석 에이전트 테스트"""
    print("\n=== 재무제표 분석 에이전트 테스트 ===")
    
    # 테스트용 재무 데이터
    financial_data = {
        "revenue": 1000000000,  # 10억원
        "operating_income": 150000000,  # 1.5억원
        "net_income": 120000000,  # 1.2억원
        "total_assets": 2000000000,  # 20억원
        "total_liabilities": 800000000,  # 8억원
        "current_assets": 800000000,  # 8억원
        "current_liabilities": 400000000,  # 4억원
        "cash": 200000000,  # 2억원
        "debt": 600000000,  # 6억원
        "equity": 1200000000,  # 12억원
        "year": 2024,
        "quarter": 4
    }
    
    try:
        result = await analyze_financial_statement(financial_data, "기업", "테스트기업")
        print("재무제표 분석 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return True
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        return False


async def test_news_analysis_agent():
    """뉴스 분석 에이전트 테스트"""
    print("\n=== 뉴스 분석 에이전트 테스트 ===")
    
    # 테스트용 뉴스 데이터
    news_data = {
        "headlines": [
            "테스트기업, 4분기 실적 예상치 상회",
            "테스트기업 신제품 출시로 시장 점유율 확대",
            "테스트기업, 해외 진출 계획 발표"
        ],
        "content": [
            "테스트기업이 4분기 실적에서 시장 예상치를 상회하는 호실적을 기록했다.",
            "신제품 출시로 인해 시장 점유율이 5%에서 8%로 확대되었다.",
            "해외 진출을 위한 전략적 파트너십을 체결했다."
        ],
        "sentiment": "positive",
        "source": "금융뉴스",
        "date": "2024-12-15"
    }
    
    try:
        result = await analyze_news(news_data, "기업", "테스트기업")
        print("뉴스 분석 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return True
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        return False


async def test_risk_assessment_agent():
    """리스크 평가 에이전트 테스트"""
    print("\n=== 리스크 평가 에이전트 테스트 ===")
    
    # 테스트용 리스크 데이터
    risk_data = {
        "market_volatility": "high",
        "industry_competition": "medium",
        "regulatory_environment": "stable",
        "financial_leverage": 0.6,
        "cash_flow_stability": "moderate",
        "geographic_concentration": "high",
        "customer_concentration": "medium",
        "supplier_dependency": "low"
    }
    
    try:
        result = await assess_risk(risk_data, "기업", "테스트기업")
        print("리스크 평가 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return True
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        return False


async def test_growth_analysis_agent():
    """성장성 분석 에이전트 테스트"""
    print("\n=== 성장성 분석 에이전트 테스트 ===")
    
    # 테스트용 성장 데이터
    growth_data = {
        "revenue_growth_rate": 0.15,  # 15%
        "profit_growth_rate": 0.20,  # 20%
        "market_growth_rate": 0.10,  # 10%
        "rd_investment": 50000000,  # 5천만원
        "new_markets": ["해외시장", "신규분야"],
        "product_development": "active",
        "competitive_advantage": "technology",
        "industry_trends": "positive"
    }
    
    try:
        result = await analyze_growth(growth_data, "기업", "테스트기업")
        print("성장성 분석 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return True
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        return False


async def test_valuation_agent():
    """밸류에이션 에이전트 테스트"""
    print("\n=== 밸류에이션 에이전트 테스트 ===")
    
    # 테스트용 밸류에이션 데이터
    valuation_data = {
        "current_price": 50000,  # 5만원
        "earnings_per_share": 2500,  # 2,500원
        "book_value_per_share": 15000,  # 1.5만원
        "free_cash_flow": 80000000,  # 8천만원
        "growth_rate": 0.12,  # 12%
        "discount_rate": 0.10,  # 10%
        "pe_ratio_industry": 20,
        "pb_ratio_industry": 1.5
    }
    
    try:
        result = await analyze_valuation(valuation_data, "기업", "테스트기업")
        print("밸류에이션 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return True
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        return False


async def test_dday_report_agent():
    """D-Day 보고서 에이전트 테스트"""
    print("\n=== D-Day 보고서 에이전트 테스트 ===")
    
    # 테스트용 종합 데이터
    report_data = {
        "financial_summary": {
            "revenue": 1000000000,
            "profit": 120000000,
            "growth_rate": 0.15
        },
        "market_analysis": {
            "market_size": "1000억원",
            "growth_potential": "높음",
            "competition_level": "중간"
        },
        "risk_factors": {
            "market_risk": "중간",
            "operational_risk": "낮음",
            "financial_risk": "낮음"
        }
    }
    
    try:
        result = await generate_dday_report(report_data, "기업", "테스트기업")
        print("D-Day 보고서 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return True
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        return False


async def test_agent_collaboration():
    """에이전트 간 협업 테스트"""
    print("\n=== 에이전트 간 협업 테스트 ===")
    
    # 협업 매니저 가져오기
    collaboration_manager = get_collaboration_manager()
    
    # 테스트용 데이터
    test_data = {
        "financial_data": {
            "revenue": 1000000000,
            "profit": 120000000
        },
        "news_data": {
            "headlines": ["테스트기업 실적 호조"],
            "sentiment": "positive"
        },
        "market_data": {
            "price": 50000,
            "volume": 1000000
        }
    }
    
    try:
        # 여러 에이전트 동시 실행
        tasks = [
            analyze_financial_statement(test_data.get("financial_data", {}), "기업", "테스트기업"),
            analyze_news(test_data.get("news_data", {}), "기업", "테스트기업"),
            analyze_market_data(test_data.get("market_data", {}), "기업", "테스트기업")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        print("협업 결과:")
        for i, result in enumerate(results, 1):
            if isinstance(result, Exception):
                print(f"에이전트 {i} 오류: {str(result)}")
            else:
                print(f"에이전트 {i}: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        return True
    except Exception as e:
        print(f"협업 테스트 중 오류 발생: {str(e)}")
        return False


async def test_llm_connection():
    """LLM 연결 테스트"""
    print("\n=== LLM 연결 테스트 ===")
    
    try:
        client = await get_llm_client()
        
        # 간단한 테스트 프롬프트
        test_prompt = """
다음 기업에 대한 간단한 분석을 JSON 형식으로 제공해주세요:

기업명: 테스트기업
매출: 10억원
영업이익: 1.2억원

분석 결과를 다음 형식으로 제공:
{
  "기업_건전성": "평가결과",
  "투자_권고": "권고사항",
  "신뢰도": 85
}
"""
        
        response = await client.generate_response(
            prompt=test_prompt,
            temperature=0.3,
            max_tokens=500
        )
        
        print("LLM 연결 테스트 성공!")
        print(f"응답: {response}")
        return True
        
    except Exception as e:
        print(f"LLM 연결 테스트 실패: {str(e)}")
        return False


async def main():
    """메인 테스트 함수"""
    print("FinsightAI 실제 LLM 연동 테스트 시작")
    print("=" * 60)
    
    # LLM 연결 테스트
    llm_ok = await test_llm_connection()
    if not llm_ok:
        print("❌ LLM 연결 실패. 테스트를 중단합니다.")
        return
    
    print("✅ LLM 연결 성공!")
    
    # 개별 에이전트 테스트
    test_results = []
    
    test_functions = [
        test_financial_statement_agent,
        test_news_analysis_agent,
        test_risk_assessment_agent,
        test_growth_analysis_agent,
        test_valuation_agent,
        test_dday_report_agent,
        test_agent_collaboration
    ]
    
    for test_func in test_functions:
        try:
            result = await test_func()
            test_results.append((test_func.__name__, result))
        except Exception as e:
            print(f"테스트 함수 실행 중 오류: {str(e)}")
            test_results.append((test_func.__name__, False))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약:")
    print("=" * 60)
    
    success_count = 0
    for test_name, success in test_results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{test_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n전체 테스트: {len(test_results)}개 중 {success_count}개 성공")
    
    if success_count == len(test_results):
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        print("⚠️ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")


if __name__ == "__main__":
    asyncio.run(main()) 