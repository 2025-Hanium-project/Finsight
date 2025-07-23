import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from agents.data_agents.financial_statement_agent import FinancialStatementAgent

def test_financial_statement_agent_basic():
    """기본 에이전트 기능 테스트"""
    api_key = os.environ.get("DART_API_KEY")
    assert api_key, "DART_API_KEY 환경변수가 필요합니다."
    
    agent = FinancialStatementAgent()
    
    # 에이전트 설정 확인
    assert agent.config.name == "financial_statement_agent", "에이전트 이름이 올바르지 않습니다."
    assert agent.temperature == 0.2, "에이전트 temperature가 올바르지 않습니다."
    
    print("✅ 에이전트 기본 설정 확인 완료")
    print(f"  - 에이전트 이름: {agent.config.name}")
    print(f"  - Temperature: {agent.temperature}")

async def test_financial_statement_agent_analysis():
    """에이전트 재무제표 분석 테스트"""
    api_key = os.environ.get("DART_API_KEY")
    assert api_key, "DART_API_KEY 환경변수가 필요합니다."
    
    stock_code = "005930"  # 삼성전자
    agent = FinancialStatementAgent()
    context = {"stock_code": stock_code, "dart_api_key": api_key}
    
    print(f"\n📊 [{stock_code}] 에이전트 재무제표 분석 테스트")
    
    try:
        result = await agent._provide_financial_metrics(context)
        
        if "error" in result:
            print(f"❌ 분석 오류: {result['error']}")
            return
        
        print("✅ 데이터 수집 및 분석 완료")
        print(f"📈 수집 연도: {result['years']}")
        
        # 주요 계정 데이터 출력
        by_year = result["by_year"]
        acc_id_to_nm = {}
        
        # account_id → account_nm 매핑 생성
        for y in by_year:
            for acc_id, amt in by_year[y].items():
                if isinstance(amt, dict) and "account_nm" in amt:
                    acc_id_to_nm[acc_id] = amt["account_nm"]
                elif "raw_data" in result:
                    for item in result["raw_data"]:
                        if item["account_id"] == acc_id:
                            acc_id_to_nm[acc_id] = item["account_nm"]
        
        # 연도별 데이터 출력
        for y in result["years"]:
            print(f"\n[연도: {y}]")
            collected_count = 0
            missing_count = 0
            
            for acc_id, amt in by_year[y].items():
                acc_nm = acc_id_to_nm.get(acc_id, acc_id)
                if isinstance(amt, dict):
                    amount = amt.get("amount", 0)
                else:
                    amount = amt
                
                if amount is not None and amount != 0:
                    print(f"  ✅ {acc_id} ({acc_nm}): {amount:,.0f}")
                    collected_count += 1
                else:
                    print(f"  ❌ {acc_id} ({acc_nm}): 데이터 없음")
                    missing_count += 1
            
            print(f"  📊 수집 성공: {collected_count}개, 누락: {missing_count}개")
            
            # 재무비율 출력
            if y in result.get("ratios", {}):
                print("  📊 주요 재무비율:")
                ratios = result["ratios"][y]
                for ratio_name, ratio_value in ratios.items():
                    if ratio_value is not None:
                        print(f"    ✅ {ratio_name}: {ratio_value:.2f}%")
                    else:
                        print(f"    ❌ {ratio_name}: 계산 불가")
        
        # 분석 결과 텍스트 출력
        if "analysis_result" in result:
            print(f"\n🤖 LLM 분석 결과:")
            print("-" * 50)
            print(result["analysis_result"])
            print("-" * 50)
        elif "analysis" in result:
            print(f"\n🤖 LLM 분석 결과:")
            print("-" * 50)
            print(result["analysis"])
            print("-" * 50)
        else:
            print("\n⚠️ LLM 분석 결과가 없습니다.")
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")

async def test_financial_statement_agent_full_analysis():
    """전체 분석 프로세스 테스트"""
    api_key = os.environ.get("DART_API_KEY")
    assert api_key, "DART_API_KEY 환경변수가 필요합니다."
    
    stock_code = "005930"  # 삼성전자
    agent = FinancialStatementAgent()
    
    print(f"\n🔍 [{stock_code}] 전체 분석 프로세스 테스트")
    
    try:
        # 전체 분석 실행
        input_data = {
            "stock_code": stock_code,
            "dart_api_key": api_key,
            "analysis_type": "comprehensive"
        }
        
        result = await agent.analyze(input_data)
        
        if "error" in result:
            print(f"❌ 전체 분석 오류: {result['error']}")
            return
        
        print("✅ 전체 분석 완료")
        
        # 분석 결과 구조 확인
        expected_keys = ["analysis", "analysis_result", "financial_data", "ratios", "years", "by_year"]
        print(f"\n📋 결과 구조 분석:")
        for key in expected_keys:
            if key in result:
                print(f"  ✅ {key}: 포함됨")
                if key == "years" and result[key]:
                    print(f"    📈 수집 연도: {result[key]}")
                elif key == "ratios" and result[key]:
                    latest_year = max(result.get("years", [])) if result.get("years") else None
                    if latest_year and latest_year in result[key]:
                        print(f"    📊 {latest_year}년 주요 비율:")
                        for ratio_name, ratio_value in result[key][latest_year].items():
                            if ratio_value is not None:
                                print(f"      ✅ {ratio_name}: {ratio_value:.2f}%")
                elif key in ["analysis", "analysis_result"] and result[key]:
                    print(f"    🤖 LLM 응답 길이: {len(result[key])}자")
            else:
                print(f"  ❌ {key}: 누락됨")
        
        # LLM 분석 결과 출력
        if "analysis" in result:
            print(f"\n🤖 LLM 분석 결과 (analysis):")
            print("=" * 60)
            print(result["analysis"])
            print("=" * 60)
        elif "analysis_result" in result:
            print(f"\n🤖 LLM 분석 결과 (analysis_result):")
            print("=" * 60)
            print(result["analysis_result"])
            print("=" * 60)
        else:
            print("\n⚠️ LLM 분석 결과가 없습니다.")
            print("🔍 전체 결과 키:", list(result.keys()))
            
        # 실행 시간 출력
        if "execution_time" in result:
            print(f"\n⏱️ 실행 시간: {result['execution_time']:.2f}초")
        
        # 전체 결과 요약
        print(f"\n📊 전체 결과 요약:")
        print(f"  - 총 키 개수: {len(result.keys())}")
        print(f"  - 재무 데이터: {'포함' if 'financial_data' in result else '누락'}")
        print(f"  - LLM 분석: {'포함' if any(k in result for k in ['analysis', 'analysis_result']) else '누락'}")
        print(f"  - 재무비율: {'포함' if 'ratios' in result else '누락'}")
        
    except Exception as e:
        print(f"❌ 전체 분석 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

async def test_financial_statement_agent_multiple_companies():
    """다중 기업 분석 테스트"""
    api_key = os.environ.get("DART_API_KEY")
    assert api_key, "DART_API_KEY 환경변수가 필요합니다."
    
    agent = FinancialStatementAgent()
    stock_codes = {
        "삼성전자": "005930",
        "SK하이닉스": "000660",
        "LG화학": "051910"
    }
    
    print(f"\n🏢 다중 기업 에이전트 분석 테스트")
    
    for name, code in stock_codes.items():
        print(f"\n📊 [{name} ({code})]")
        
        try:
            context = {"stock_code": code, "dart_api_key": api_key}
            result = await agent._provide_financial_metrics(context)
            
            if "error" in result:
                print(f"  ❌ 분석 오류: {result['error']}")
                continue
            
            # 간단한 요약 출력
            years = result.get("years", [])
            ratios = result.get("ratios", {})
            
            print(f"  📈 수집 연도: {years}")
            
            # 최신 연도의 주요 비율만 출력
            if years and years[0] in ratios:
                latest_ratios = ratios[years[0]]
                print("  📊 주요 재무비율:")
                for ratio_name, ratio_value in latest_ratios.items():
                    if ratio_value is not None:
                        print(f"    ✅ {ratio_name}: {ratio_value:.2f}%")
                    else:
                        print(f"    ❌ {ratio_name}: 계산 불가")
            
            print("  ✅ 분석 완료")
            
        except Exception as e:
            print(f"  ❌ 오류 발생: {e}")

async def main():
    """메인 테스트 실행"""
    print("🧪 재무제표 에이전트 테스트 시작")
    print("=" * 60)
    
    # 기본 기능 테스트
    test_financial_statement_agent_basic()
    
    # 개별 분석 테스트
    await test_financial_statement_agent_analysis()
    
    # 전체 분석 테스트
    await test_financial_statement_agent_full_analysis()
    
    # 다중 기업 테스트
    await test_financial_statement_agent_multiple_companies()
    
    print("\n" + "=" * 60)
    print("✅ 모든 에이전트 테스트가 완료되었습니다.")

if __name__ == "__main__":
    asyncio.run(main()) 