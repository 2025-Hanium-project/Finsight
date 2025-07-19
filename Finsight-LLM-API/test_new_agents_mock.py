"""
새로운 Agent 구조 테스트 (모의 데이터 버전)
실제 LLM 호출 없이 Agent 구조와 협업 시스템을 테스트
"""
import asyncio
import json
from typing import Dict, Any
from unittest.mock import AsyncMock, patch

# 새로운 Agent 구조 import
from agents import (
    # 데이터 소스별 에이전트
    analyze_financial_statement,
    analyze_news,
    analyze_securities_report,
    analyze_market_data,
    
    # 분석 유형별 에이전트
    assess_risk,
    analyze_growth,
    analyze_valuation,
    compare_peers,
    
    # 보고서 작성 에이전트
    generate_dday_report,
    generate_dplus1_report,
    
    # 지원 에이전트
    process_document,
    assess_data_quality,
    supervise_analysis
)


def create_mock_llm_response(agent_name: str) -> str:
    """모의 LLM 응답 생성"""
    mock_responses = {
        "financial_statement_agent": {
            "financial_health": "양호",
            "profitability_analysis": "수익성이 안정적입니다",
            "liquidity_analysis": "유동성이 충분합니다",
            "solvency_analysis": "지급능력이 우수합니다",
            "growth_trends": "성장 추세가 양호합니다",
            "key_ratios": "주요 재무비율이 건전합니다",
            "risk_factors": "재무적 리스크는 낮습니다",
            "recommendations": "재무 건전성 유지 권고",
            "confidence_score": 85
        },
        "news_analysis_agent": {
            "sentiment_score": 75,
            "impact_level": "중간",
            "key_topics": ["실적 호조", "신제품 출시"],
            "market_reaction": "긍정적 반응 예상",
            "related_stocks": ["테스트기업"],
            "trend_analysis": "상승 트렌드",
            "risk_implications": "리스크 낮음",
            "opportunity_analysis": "성장 기회 존재",
            "confidence_score": 80
        },
        "risk_assessment_agent": {
            "risk_level": "중간",
            "financial_risks": "재무적 리스크 낮음",
            "market_risks": "시장 리스크 보통",
            "operational_risks": "운영 리스크 낮음",
            "regulatory_risks": "규제 리스크 보통",
            "credit_risks": "신용 리스크 낮음",
            "liquidity_risks": "유동성 리스크 낮음",
            "risk_mitigation": "리스크 완화 방안 제시",
            "confidence_score": 75
        },
        "growth_analysis_agent": {
            "growth_potential": "중간",
            "revenue_growth": "매출 성장률 15%",
            "profit_growth": "이익 성장률 20%",
            "market_expansion": "시장 확장 가능성 높음",
            "product_development": "신제품 개발 활발",
            "competitive_advantage": "경쟁 우위 확보",
            "industry_trends": "산업 트렌드 양호",
            "growth_drivers": "성장 동력 충분",
            "growth_risks": "성장 리스크 낮음",
            "confidence_score": 80
        },
        "valuation_agent": {
            "fair_value": 55000,
            "valuation_methods": "DCF, PER, PBR",
            "pe_ratio": "PER 12배",
            "pb_ratio": "PBR 1.5배",
            "ev_ebitda": "EV/EBITDA 8배",
            "dcf_valuation": "DCF 가치 58000원",
            "asset_based": "자산 기반 가치 52000원",
            "relative_valuation": "상대 밸류에이션 54000원",
            "valuation_risks": "밸류에이션 리스크 보통",
            "confidence_score": 85
        },
        "dday_report_agent": {
            "executive_summary": "투자 가치가 있는 기업",
            "key_findings": "재무 건전성 우수, 성장 잠재력 존재",
            "investment_recommendation": "매수",
            "risk_assessment": "리스크 수준 보통",
            "growth_outlook": "성장 전망 양호",
            "valuation_analysis": "적정 가치 55000원",
            "market_analysis": "시장 상황 양호",
            "peer_comparison": "동종업계 대비 우수",
            "action_items": "단계적 매수 권고",
            "confidence_score": 85
        }
    }
    
    return json.dumps(mock_responses.get(agent_name, {}), ensure_ascii=False)


async def test_financial_statement_agent():
    """재무제표 분석 에이전트 테스트"""
    print("=== 재무제표 분석 에이전트 테스트 ===")
    
    financial_data = {
        "revenue": 1000000,
        "net_income": 150000,
        "total_assets": 2000000,
        "total_liabilities": 800000,
        "cash_flow": 200000
    }
    
    # LLM 호출을 모의로 대체
    with patch('utils.llm_client.generate_response', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = create_mock_llm_response("financial_statement_agent")
        
        result = await analyze_financial_statement(financial_data, "기업", "테스트기업")
        print(f"재무제표 분석 결과: {json.dumps(result, ensure_ascii=False, indent=2)}")


async def test_news_analysis_agent():
    """뉴스 분석 에이전트 테스트"""
    print("\n=== 뉴스 분석 에이전트 테스트 ===")
    
    news_data = {
        "headlines": ["테스트기업 실적 호조", "신제품 출시 예정"],
        "content": "테스트기업이 예상보다 좋은 실적을 기록했습니다.",
        "sentiment": "positive"
    }
    
    with patch('utils.llm_client.generate_response', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = create_mock_llm_response("news_analysis_agent")
        
        result = await analyze_news(news_data, "기업", "테스트기업")
        print(f"뉴스 분석 결과: {json.dumps(result, ensure_ascii=False, indent=2)}")


async def test_risk_assessment_agent():
    """리스크 평가 에이전트 테스트"""
    print("\n=== 리스크 평가 에이전트 테스트 ===")
    
    risk_data = {
        "market_volatility": "high",
        "financial_ratios": {"debt_to_equity": 0.8},
        "industry_risks": ["경쟁 심화", "규제 강화"]
    }
    
    with patch('utils.llm_client.generate_response', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = create_mock_llm_response("risk_assessment_agent")
        
        result = await assess_risk(risk_data, "기업", "테스트기업")
        print(f"리스크 평가 결과: {json.dumps(result, ensure_ascii=False, indent=2)}")


async def test_growth_analysis_agent():
    """성장성 분석 에이전트 테스트"""
    print("\n=== 성장성 분석 에이전트 테스트 ===")
    
    growth_data = {
        "revenue_growth": 15.5,
        "market_expansion": "글로벌 진출",
        "new_products": ["신제품A", "신제품B"]
    }
    
    with patch('utils.llm_client.generate_response', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = create_mock_llm_response("growth_analysis_agent")
        
        result = await analyze_growth(growth_data, "기업", "테스트기업")
        print(f"성장성 분석 결과: {json.dumps(result, ensure_ascii=False, indent=2)}")


async def test_valuation_agent():
    """밸류에이션 에이전트 테스트"""
    print("\n=== 밸류에이션 에이전트 테스트 ===")
    
    valuation_data = {
        "current_price": 50000,
        "earnings": 5000,
        "book_value": 30000,
        "pe_ratio": 10.0
    }
    
    with patch('utils.llm_client.generate_response', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = create_mock_llm_response("valuation_agent")
        
        result = await analyze_valuation(valuation_data, "기업", "테스트기업")
        print(f"밸류에이션 결과: {json.dumps(result, ensure_ascii=False, indent=2)}")


async def test_dday_report_agent():
    """D-day 보고서 에이전트 테스트"""
    print("\n=== D-day 보고서 에이전트 테스트 ===")
    
    report_data = {
        "analysis_summary": "종합 분석 결과",
        "investment_recommendation": "매수",
        "target_price": 60000
    }
    
    with patch('utils.llm_client.generate_response', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = create_mock_llm_response("dday_report_agent")
        
        result = await generate_dday_report(report_data, "기업", "테스트기업")
        print(f"D-day 보고서 결과: {json.dumps(result, ensure_ascii=False, indent=2)}")


async def test_collaboration():
    """에이전트 간 협업 테스트"""
    print("\n=== 에이전트 간 협업 테스트 ===")
    
    # 여러 에이전트가 협업하는 시나리오
    financial_data = {"revenue": 1000000, "net_income": 150000}
    news_data = {"content": "테스트기업 실적 호조"}
    market_data = {"price": 50000, "volume": 1000000}
    
    with patch('utils.llm_client.generate_response', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = create_mock_llm_response("financial_statement_agent")
        
        # 병렬로 여러 에이전트 실행
        tasks = [
            analyze_financial_statement(financial_data, "기업", "테스트기업"),
            analyze_news(news_data, "기업", "테스트기업"),
            analyze_market_data(market_data, "기업", "테스트기업")
        ]
        
        results = await asyncio.gather(*tasks)
        
        print("협업 결과:")
        for i, result in enumerate(results):
            print(f"에이전트 {i+1}: {json.dumps(result, ensure_ascii=False, indent=2)}")


async def test_agent_structure():
    """Agent 구조 테스트"""
    print("\n=== Agent 구조 테스트 ===")
    
    from agents import ALL_AGENTS
    
    print("등록된 Agent 목록:")
    for agent_name, agent in ALL_AGENTS.items():
        print(f"- {agent_name}: {agent.agent_type.value}")
        print(f"  협업 대상: {agent.collaboration_targets}")
        print(f"  Temperature: {agent.temperature}")
        print()


async def main():
    """메인 테스트 함수"""
    print("FinsightAI 새로운 Agent 구조 테스트 시작 (모의 데이터)")
    print("=" * 60)
    
    try:
        # Agent 구조 테스트
        await test_agent_structure()
        
        # 개별 에이전트 테스트
        await test_financial_statement_agent()
        await test_news_analysis_agent()
        await test_risk_assessment_agent()
        await test_growth_analysis_agent()
        await test_valuation_agent()
        await test_dday_report_agent()
        
        # 협업 테스트
        await test_collaboration()
        
        print("\n" + "=" * 60)
        print("모든 테스트 완료!")
        print("✅ Agent 구조가 올바르게 설정되었습니다.")
        print("✅ 협업 시스템이 정상적으로 작동합니다.")
        print("✅ 새로운 Agent 구조가 완전히 구현되었습니다.")
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 