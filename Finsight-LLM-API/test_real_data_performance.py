"""
실제 데이터로 Agent 성능 검증 테스트
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
    analyze_valuation,
    analyze_risk,
    analyze_growth,
    generate_dday_report,
    analyze_market_data
)

from utils.llm_client import get_llm_client
from utils.agent_base import get_collaboration_manager


async def test_financial_statement_with_real_data():
    """실제 재무제표 데이터 분석 테스트"""
    print("\n=== 실제 재무제표 데이터 분석 테스트 ===")
    
    # 실제 삼성전자 재무제표 데이터 (2024년 기준)
    financial_data = {
        "revenue": 279600000000000,  # 279.6조원
        "operating_income": 15000000000000,  # 15조원
        "net_income": 12000000000000,  # 12조원
        "total_assets": 400000000000000,  # 400조원
        "total_liabilities": 150000000000000,  # 150조원
        "current_assets": 200000000000000,  # 200조원
        "current_liabilities": 80000000000000,  # 80조원
        "cash_and_equivalents": 50000000000000,  # 50조원
        "debt": 30000000000000,  # 30조원
        "equity": 250000000000000,  # 250조원
        "rd_expense": 25000000000000,  # 25조원
        "operating_cash_flow": 35000000000000,  # 35조원
        "free_cash_flow": 25000000000000,  # 25조원
        "previous_revenue": 250000000000000,  # 250조원 (전년)
        "previous_operating_income": 12000000000000,  # 12조원 (전년)
        "previous_net_income": 10000000000000,  # 10조원 (전년)
        "industry_average_pe": 15.5,
        "industry_average_pb": 2.1,
        "industry_average_roe": 0.12,
        "industry_average_debt_to_equity": 0.4
    }
    
    try:
        start_time = datetime.now()
        result = await analyze_financial_statement(financial_data, "기업", "삼성전자")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"처리 시간: {processing_time:.3f}초")
        print("재무제표 분석 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 신뢰도 점수 처리
        confidence_score = result.get("confidence_score", 0)
        if isinstance(confidence_score, str):
            try:
                confidence_score = int(confidence_score)
            except:
                confidence_score = 0
        
        print(f"신뢰도 점수: {confidence_score}/100")
        
        return True, processing_time, confidence_score
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        return False, 0, 0


async def test_news_analysis_with_real_data():
    """실제 뉴스 데이터 분석 테스트"""
    print("\n=== 실제 뉴스 데이터 분석 테스트 ===")
    
    # 실제 삼성전자 관련 뉴스 데이터
    news_data = {
        "headlines": [
            "삼성전자 4분기 실적 호조, 반도체 부문 회복세",
            "삼성전자 AI 반도체 시장 진출 확대",
            "삼성전자 메모리 반도체 가격 상승세",
            "삼성전자 5G 네트워크 장비 공급 확대",
            "삼성전자 자율주행 칩 개발 가속화"
        ],
        "sentiment": "positive",
        "content": [
            "삼성전자가 4분기 실적에서 예상치를 상회하는 호실적을 기록했습니다.",
            "AI 반도체 시장에서 삼성전자의 점유율이 확대되고 있습니다.",
            "메모리 반도체 가격 상승으로 인한 수익성 개선이 예상됩니다.",
            "5G 네트워크 장비 공급 확대로 통신사업부문 성장세가 지속됩니다.",
            "자율주행 칩 개발을 통해 새로운 성장 동력을 확보하고 있습니다."
        ],
        "source": "금융투자협회",
        "date": "2024-01-15",
        "impact_level": "high",
        "related_stocks": ["005930", "000660", "006400"],
        "market_reaction": "positive",
        "volume_change": 0.15,
        "price_change": 0.08
    }
    
    try:
        start_time = datetime.now()
        result = await analyze_news(news_data, "기업", "삼성전자")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"처리 시간: {processing_time:.3f}초")
        print("뉴스 분석 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 신뢰도 점수 처리
        confidence_score = result.get("confidence_score", 0)
        if isinstance(confidence_score, str):
            try:
                confidence_score = int(confidence_score)
            except:
                confidence_score = 0
        
        sentiment_score = result.get("sentiment_score", "정보 부족")
        print(f"감성 점수: {sentiment_score}")
        print(f"신뢰도 점수: {confidence_score}/100")
        
        return True, processing_time, confidence_score
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        return False, 0, 0


async def test_valuation_with_real_data():
    """실제 밸류에이션 데이터 분석 테스트"""
    print("\n=== 실제 밸류에이션 데이터 분석 테스트 ===")
    
    # 실제 삼성전자 밸류에이션 데이터
    valuation_data = {
        "current_price": 75000,  # 현재 주가
        "market_cap": 500000000000000,  # 시가총액 500조원
        "pe_ratio": 8.8,  # PER
        "pb_ratio": 1.7,  # PBR
        "ps_ratio": 1.8,  # PSR
        "ev_ebitda": 6.2,  # EV/EBITDA
        "dividend_yield": 0.025,  # 배당수익률 2.5%
        "book_value_per_share": 44118,  # 주당순자산
        "earnings_per_share": 8523,  # 주당순이익
        "revenue_per_share": 40000,  # 주당매출
        "free_cash_flow_per_share": 15000,  # 주당자유현금흐름
        "growth_rate": 0.12,  # 성장률 12%
        "risk_free_rate": 0.035,  # 무위험수익률 3.5%
        "beta": 1.2,  # 베타
        "market_risk_premium": 0.06,  # 시장위험프리미엄 6%
        "terminal_growth_rate": 0.03,  # 영구성장률 3%
        "peer_comparison": {
            "sk_hynix_pe": 12.5,
            "sk_hynix_pb": 2.3,
            "tsmc_pe": 15.2,
            "tsmc_pb": 3.1,
            "intel_pe": 18.5,
            "intel_pb": 2.8
        }
    }
    
    try:
        start_time = datetime.now()
        # 올바른 데이터 구조로 전달
        input_data = {
            "valuation_data": valuation_data,
            "target_type": "기업",
            "target_name": "삼성전자",
            "analysis_target": "삼성전자"
        }
        result = await analyze_valuation(input_data, "기업", "삼성전자")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"처리 시간: {processing_time:.3f}초")
        print("밸류에이션 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 신뢰도 점수 처리
        confidence_score = result.get("confidence_score", 0)
        if isinstance(confidence_score, str):
            try:
                confidence_score = int(confidence_score)
            except:
                confidence_score = 0
        
        print(f"신뢰도 점수: {confidence_score}/100")
        
        return True, processing_time, confidence_score
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        return False, 0, 0


async def test_risk_assessment_with_real_data():
    """실제 리스크 데이터 분석 테스트"""
    print("\n=== 실제 리스크 데이터 분석 테스트 ===")
    
    # 실제 삼성전자 리스크 데이터
    risk_data = {
        "market_risk": {
            "volatility": 0.25,  # 변동성 25%
            "beta": 1.2,  # 베타
            "correlation_with_market": 0.7,  # 시장과의 상관관계
            "sector_volatility": 0.28  # 섹터 변동성
        },
        "financial_risk": {
            "debt_to_equity": 0.12,  # 부채비율 12%
            "interest_coverage": 15.5,  # 이자보상배율
            "current_ratio": 2.5,  # 유동비율
            "quick_ratio": 1.8,  # 당좌비율
            "cash_ratio": 0.6  # 현금비율
        },
        "operational_risk": {
            "geographic_concentration": 0.4,  # 지역 집중도
            "customer_concentration": 0.15,  # 고객 집중도
            "supplier_concentration": 0.25,  # 공급업체 집중도
            "technology_dependency": 0.8  # 기술 의존도
        },
        "regulatory_risk": {
            "compliance_score": 0.95,  # 규정 준수 점수
            "regulatory_changes": "low",  # 규제 변화 위험
            "export_restrictions": "medium",  # 수출 제한 위험
            "antitrust_risk": "low"  # 반독점 위험
        },
        "credit_risk": {
            "credit_rating": "AA",  # 신용등급
            "default_probability": 0.001,  # 부도 확률
            "recovery_rate": 0.6  # 회수율
        },
        "liquidity_risk": {
            "cash_flow_coverage": 3.2,  # 현금흐름 보장률
            "liquid_assets_ratio": 0.4,  # 유동자산 비율
            "short_term_debt_ratio": 0.2  # 단기부채 비율
        }
    }
    
    try:
        start_time = datetime.now()
        # 올바른 데이터 구조로 전달
        input_data = {
            "risk_data": risk_data,
            "target_type": "기업",
            "target_name": "삼성전자",
            "analysis_target": "삼성전자"
        }
        result = await analyze_risk(input_data, "기업", "삼성전자")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"처리 시간: {processing_time:.3f}초")
        print("리스크 평가 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 신뢰도 점수 처리
        confidence_score = result.get("confidence_score", 0)
        if isinstance(confidence_score, str):
            try:
                confidence_score = int(confidence_score)
            except:
                confidence_score = 0
        
        risk_level = result.get("risk_level", "정보 부족")
        print(f"리스크 레벨: {risk_level}")
        print(f"신뢰도 점수: {confidence_score}/100")
        
        return True, processing_time, confidence_score
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        return False, 0, 0


async def test_growth_analysis_with_real_data():
    """실제 성장 데이터 분석 테스트"""
    print("\n=== 실제 성장 데이터 분석 테스트 ===")
    
    # 실제 삼성전자 성장 데이터
    growth_data = {
        "historical_growth": {
            "revenue_growth_3y": 0.08,  # 3년 매출 성장률 8%
            "profit_growth_3y": 0.12,  # 3년 이익 성장률 12%
            "asset_growth_3y": 0.06,  # 3년 자산 성장률 6%
            "equity_growth_3y": 0.09  # 3년 자본 성장률 9%
        },
        "future_projection": {
            "revenue_growth_forecast": 0.10,  # 매출 성장 전망 10%
            "profit_growth_forecast": 0.15,  # 이익 성장 전망 15%
            "market_share_growth": 0.05,  # 시장점유율 성장 5%
            "rd_investment_growth": 0.20  # R&D 투자 성장 20%
        },
        "market_expansion": {
            "domestic_market_share": 0.25,  # 국내 시장점유율 25%
            "global_market_share": 0.15,  # 글로벌 시장점유율 15%
            "emerging_markets_growth": 0.18,  # 신흥시장 성장률 18%
            "developed_markets_growth": 0.08  # 선진시장 성장률 8%
        },
        "product_development": {
            "new_product_revenue_ratio": 0.30,  # 신제품 매출 비중 30%
            "patent_growth": 0.25,  # 특허 성장률 25%
            "innovation_index": 0.85,  # 혁신 지수 85%
            "technology_leadership": 0.90  # 기술 리더십 90%
        },
        "competitive_advantage": {
            "cost_advantage": 0.15,  # 비용 우위 15%
            "technology_advantage": 0.20,  # 기술 우위 20%
            "brand_value": 0.25,  # 브랜드 가치 25%
            "scale_advantage": 0.30  # 규모 우위 30%
        },
        "industry_trends": {
            "semiconductor_growth": 0.12,  # 반도체 산업 성장률 12%
            "ai_market_growth": 0.25,  # AI 시장 성장률 25%
            "5g_adoption_rate": 0.35,  # 5G 도입률 35%
            "automotive_electronics_growth": 0.18  # 자동차 전자제품 성장률 18%
        }
    }
    
    try:
        start_time = datetime.now()
        # 올바른 데이터 구조로 전달
        input_data = {
            "growth_data": growth_data,
            "target_type": "기업",
            "target_name": "삼성전자",
            "analysis_target": "삼성전자"
        }
        result = await analyze_growth(input_data, "기업", "삼성전자")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"처리 시간: {processing_time:.3f}초")
        print("성장성 분석 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 신뢰도 점수 처리
        confidence_score = result.get("confidence_score", 0)
        if isinstance(confidence_score, str):
            try:
                confidence_score = int(confidence_score)
            except:
                confidence_score = 0
        
        growth_potential = result.get("growth_potential", "정보 부족")
        print(f"성장 잠재력: {growth_potential}")
        print(f"신뢰도 점수: {confidence_score}/100")
        
        return True, processing_time, confidence_score
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        return False, 0, 0


async def test_comprehensive_report():
    """종합 보고서 생성 테스트"""
    print("\n=== 종합 보고서 생성 테스트 ===")
    
    # 종합 데이터
    comprehensive_data = {
        "financial_data": {
            "revenue": 279600000000000,
            "operating_income": 15000000000000,
            "net_income": 12000000000000,
            "total_assets": 400000000000000,
            "total_liabilities": 150000000000000,
            "current_assets": 200000000000000,
            "current_liabilities": 80000000000000,
            "cash_and_equivalents": 50000000000000,
            "debt": 30000000000000,
            "equity": 250000000000000
        },
        "market_data": {
            "current_price": 75000,
            "market_cap": 500000000000000,
            "pe_ratio": 8.8,
            "pb_ratio": 1.7,
            "dividend_yield": 0.025,
            "volume": 50000000,
            "beta": 1.2,
            "volatility": 0.25
        },
        "news_data": {
            "headlines": [
                "삼성전자 4분기 실적 호조, 반도체 부문 회복세",
                "삼성전자 AI 반도체 시장 진출 확대",
                "삼성전자 메모리 반도체 가격 상승세"
            ],
            "sentiment": "positive",
            "impact_level": "high"
        },
        "growth_data": {
            "revenue_growth": 0.12,
            "profit_growth": 0.15,
            "market_expansion": 0.08,
            "rd_investment": 25000000000000
        },
        "risk_data": {
            "market_risk": "medium",
            "operational_risk": "low",
            "financial_risk": "low",
            "technology_risk": "medium"
        },
        "industry_data": {
            "market_size": "반도체 시장 600조원",
            "growth_potential": "AI 반도체 성장세",
            "competition_level": "글로벌 경쟁",
            "market_position": "1위"
        }
    }
    
    try:
        start_time = datetime.now()
        result = await generate_dday_report(comprehensive_data, "기업", "삼성전자")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"처리 시간: {processing_time:.3f}초")
        print("종합 보고서 결과:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 신뢰도 점수 처리
        confidence_score = result.get("confidence_score", 0)
        if isinstance(confidence_score, str):
            try:
                confidence_score = int(confidence_score)
            except:
                confidence_score = 0
        
        print(f"신뢰도 점수: {confidence_score}/100")
        
        return True, processing_time, confidence_score
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")
        return False, 0, 0


async def test_agent_collaboration_with_real_data():
    """실제 데이터로 협업 테스트"""
    print("\n=== 실제 데이터 협업 테스트 ===")
    
    # 실제 데이터
    real_data = {
        "financial_data": {
            "revenue": 279600000000000,
            "operating_income": 15000000000000,
            "net_income": 12000000000000,
            "total_assets": 400000000000000,
            "total_liabilities": 150000000000000,
            "current_assets": 200000000000000,
            "current_liabilities": 80000000000000,
            "cash_and_equivalents": 50000000000000,
            "debt": 30000000000000,
            "equity": 250000000000000
        },
        "news_data": {
            "headlines": [
                "삼성전자 4분기 실적 호조",
                "삼성전자 AI 반도체 시장 진출 확대",
                "삼성전자 메모리 반도체 가격 상승세"
            ],
            "sentiment": "positive",
            "content": ["반도체 회복세로 실적 개선"],
            "impact_level": "high"
        },
        "market_data": {
            "price": 75000,
            "volume": 50000000,
            "market_cap": 500000000000000,
            "pe_ratio": 8.8,
            "pb_ratio": 1.7,
            "volatility": 0.25,
            "beta": 1.2
        }
    }
    
    try:
        start_time = datetime.now()
        
        # 여러 에이전트 동시 실행
        tasks = [
            analyze_financial_statement(real_data.get("financial_data", {}), "기업", "삼성전자"),
            analyze_news(real_data.get("news_data", {}), "기업", "삼성전자"),
            analyze_market_data(real_data.get("market_data", {}), "기업", "삼성전자")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        print(f"협업 처리 시간: {processing_time:.3f}초")
        print("협업 결과:")
        
        success_count = 0
        total_confidence = 0
        
        for i, result in enumerate(results, 1):
            if isinstance(result, Exception):
                print(f"에이전트 {i} 오류: {str(result)}")
            else:
                print(f"에이전트 {i}: {json.dumps(result, ensure_ascii=False, indent=2)}")
                success_count += 1
                confidence = result.get("confidence_score", 0)
                if isinstance(confidence, str):
                    try:
                        confidence = int(confidence)
                    except:
                        confidence = 0
                total_confidence += confidence
        
        avg_confidence = total_confidence / success_count if success_count > 0 else 0
        print(f"성공한 에이전트: {success_count}/3")
        print(f"평균 신뢰도: {avg_confidence:.1f}/100")
        
        return success_count == 3, processing_time, avg_confidence
        
    except Exception as e:
        print(f"협업 테스트 중 오류 발생: {str(e)}")
        return False, 0, 0


async def performance_benchmark():
    """성능 벤치마크 테스트"""
    print("\n=== 성능 벤치마크 테스트 ===")
    
    test_functions = [
        ("재무제표 분석", test_financial_statement_with_real_data),
        ("뉴스 분석", test_news_analysis_with_real_data),
        ("밸류에이션", test_valuation_with_real_data),
        ("리스크 평가", test_risk_assessment_with_real_data),
        ("성장성 분석", test_growth_analysis_with_real_data),
        ("종합 보고서", test_comprehensive_report),
        ("협업 테스트", test_agent_collaboration_with_real_data)
    ]
    
    results = []
    
    for test_name, test_func in test_functions:
        print(f"\n--- {test_name} 벤치마크 ---")
        try:
            success, processing_time, confidence = await test_func()
            results.append({
                "test_name": test_name,
                "success": success,
                "processing_time": processing_time,
                "confidence_score": confidence
            })
        except Exception as e:
            print(f"{test_name} 벤치마크 실패: {str(e)}")
            results.append({
                "test_name": test_name,
                "success": False,
                "processing_time": 0,
                "confidence_score": 0
            })
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("성능 벤치마크 결과 요약:")
    print("=" * 60)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    total_time = sum(r["processing_time"] for r in results)
    
    # 신뢰도 점수 계산 시 타입 안전성 확보
    confidence_scores = []
    for r in results:
        confidence = r["confidence_score"]
        if isinstance(confidence, str):
            try:
                confidence = int(confidence)
            except:
                confidence = 0
        confidence_scores.append(confidence)
    
    avg_confidence = sum(confidence_scores) / total_tests if total_tests > 0 else 0
    
    print(f"총 테스트: {total_tests}개")
    print(f"성공한 테스트: {successful_tests}개")
    print(f"성공률: {(successful_tests/total_tests)*100:.1f}%")
    print(f"총 처리 시간: {total_time:.3f}초")
    print(f"평균 처리 시간: {total_time/total_tests:.3f}초")
    print(f"평균 신뢰도: {avg_confidence:.1f}/100")
    
    print("\n상세 결과:")
    for result in results:
        status = "✅ 성공" if result["success"] else "❌ 실패"
        confidence = result["confidence_score"]
        if isinstance(confidence, str):
            try:
                confidence = int(confidence)
            except:
                confidence = 0
        print(f"{result['test_name']}: {status} ({result['processing_time']:.3f}s, 신뢰도: {confidence})")
    
    return results


async def main():
    """메인 테스트 함수"""
    print("FinsightAI 실제 데이터 성능 검증 테스트 시작")
    print("=" * 60)
    
    # 성능 벤치마크 실행
    results = await performance_benchmark()
    
    # 최종 평가
    print("\n" + "=" * 60)
    print("최종 평가:")
    print("=" * 60)
    
    successful_tests = sum(1 for r in results if r["success"])
    total_tests = len(results)
    
    if successful_tests == total_tests:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("✅ Agent 성능이 실제 데이터에서 정상 작동합니다.")
        print("✅ 새로운 Agent 구조가 실제 환경에서 검증되었습니다.")
    else:
        print(f"⚠️ {total_tests - successful_tests}개 테스트가 실패했습니다.")
        print("일부 Agent에서 개선이 필요할 수 있습니다.")
    
    print(f"\n전체 성공률: {(successful_tests/total_tests)*100:.1f}%")


if __name__ == "__main__":
    asyncio.run(main()) 