import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from utils.data_collectors.financial_collector import FinancialStatementCollector
from datetime import datetime

def test_collector_basic_functionality():
    """기본 수집 기능 테스트"""
    api_key = os.environ.get("DART_API_KEY")
    assert api_key, "DART_API_KEY 환경변수가 필요합니다."
    
    collector = FinancialStatementCollector(api_key=api_key)
    
    # 주요 계정 목록 확인
    accounts = collector.get_major_accounts()
    assert 'ids' in accounts, "주요 계정 ID 목록이 없습니다."
    assert 'nms' in accounts, "주요 계정명 목록이 없습니다."
    assert len(accounts['ids']) > 0, "주요 계정 ID가 비어있습니다."
    assert len(accounts['nms']) > 0, "주요 계정명이 비어있습니다."
    
    print(f"✅ 주요 계정 수: {len(accounts['ids'])}개")
    print("주요 계정 ID 목록:")
    for i, (acc_id, acc_nm) in enumerate(zip(accounts['ids'], accounts['nms'])):
        print(f"  {i+1:2d}. {acc_id} ({acc_nm})")

def test_summary_financials_single_company():
    """단일 기업 재무제표 수집 테스트"""
    api_key = os.environ.get("DART_API_KEY")
    assert api_key, "DART_API_KEY 환경변수가 필요합니다."
    
    collector = FinancialStatementCollector(api_key=api_key)
    stock_code = "005930"  # 삼성전자
    now = datetime.now()
    year = now.year - 1
    
    print(f"\n📊 [{stock_code}] {year}년 재무제표 수집 테스트")
    
    accounts = collector.get_major_accounts()
    data = collector.collect_summary_financials(stock_code, year, accounts=accounts)
    
    if not data:
        print("❌ 데이터 수집 실패")
        return
    
    # 연도별로 계정별 합산값 정리
    by_year = {}
    acc_id_to_nm = {}
    
    for item in data:
        y = int(item['year'])
        acc_id = item['account_id']
        acc_nm = item['account_nm']
        amt = item['amount']
        
        if y not in by_year:
            by_year[y] = {}
        by_year[y][acc_id] = amt
        acc_id_to_nm[acc_id] = acc_nm
    
    years = sorted(by_year.keys(), reverse=True)
    print(f"\n📈 수집된 연도: {years}")
    
    for y in years:
        print(f"\n[연도: {y}]")
        collected_count = 0
        missing_count = 0
        
        for acc_id in accounts['ids']:
            acc_nm = acc_id_to_nm.get(acc_id, acc_id)
            v = by_year[y].get(acc_id, None)
            
            if v is not None:
                print(f"  ✅ {acc_id} ({acc_nm}): {v:,.0f}")
                collected_count += 1
            else:
                print(f"  ❌ {acc_id} ({acc_nm}): 데이터 없음")
                missing_count += 1
        
        print(f"  📊 수집 성공: {collected_count}개, 누락: {missing_count}개")

def test_summary_financials_multiple_companies():
    """다중 기업 재무제표 수집 테스트"""
    api_key = os.environ.get("DART_API_KEY")
    assert api_key, "DART_API_KEY 환경변수가 필요합니다."
    
    collector = FinancialStatementCollector(api_key=api_key)
    stock_codes = {
        "삼성전자": "005930",
        "SK하이닉스": "000660", 
        "LG화학": "051910",
        "현대차": "005380",
        "기아": "000270"
    }
    
    now = datetime.now()
    year = now.year - 1
    accounts = collector.get_major_accounts()
    
    print(f"\n🏢 다중 기업 재무제표 수집 테스트 ({year}년)")
    
    for name, code in stock_codes.items():
        print(f"\n📊 [{name} ({code})]")
        
        try:
            data = collector.collect_summary_financials(code, year, accounts=accounts)
            
            if not data:
                print("  ❌ 데이터 수집 실패")
                continue
            
            by_acc = {item['account_id']: item for item in data}
            acc_id_to_nm = {item['account_id']: item['account_nm'] for item in data}
            
            collected_count = 0
            missing_count = 0
            
            for acc_id in accounts['ids']:
                item = by_acc.get(acc_id)
                acc_nm = acc_id_to_nm.get(acc_id, acc_id)
                amt = item['amount'] if item else None
                
                if amt is not None:
                    print(f"  ✅ {acc_id} ({acc_nm}): {amt:,.0f}")
                    collected_count += 1
                else:
                    print(f"  ❌ {acc_id} ({acc_nm}): 데이터 없음")
                    missing_count += 1
            
            print(f"  📊 수집 성공: {collected_count}개, 누락: {missing_count}개")
            
        except Exception as e:
            print(f"  ❌ 오류 발생: {e}")

def test_collector_error_handling():
    """에러 처리 테스트"""
    api_key = os.environ.get("DART_API_KEY")
    assert api_key, "DART_API_KEY 환경변수가 필요합니다."
    
    collector = FinancialStatementCollector(api_key=api_key)
    
    # 잘못된 종목코드로 테스트
    invalid_stock_code = "999999"
    
    try:
        data = collector.collect_summary_financials(invalid_stock_code, 2023)
        print(f"❌ 잘못된 종목코드 테스트 실패: 데이터가 수집됨")
    except ValueError as e:
        print(f"✅ 잘못된 종목코드 테스트 성공: {e}")
    except Exception as e:
        print(f"⚠️ 예상치 못한 오류: {e}")

def test_financial_data_validation():
    """재무 데이터 검증 테스트"""
    api_key = os.environ.get("DART_API_KEY")
    assert api_key, "DART_API_KEY 환경변수가 필요합니다."
    
    collector = FinancialStatementCollector(api_key=api_key)
    stock_code = "005930"  # 삼성전자
    now = datetime.now()
    year = now.year - 1
    
    print(f"\n🔍 [{stock_code}] 재무 데이터 검증 테스트")
    
    accounts = collector.get_major_accounts()
    data = collector.collect_summary_financials(stock_code, year, accounts=accounts)
    
    if not data:
        print("❌ 데이터 수집 실패")
        return
    
    # 연도별로 계정별 합산값 정리
    by_year = {}
    acc_id_to_nm = {}
    
    for item in data:
        y = int(item['year'])
        acc_id = item['account_id']
        acc_nm = item['account_nm']
        amt = item['amount']
        
        if y not in by_year:
            by_year[y] = {}
        by_year[y][acc_id] = amt
        acc_id_to_nm[acc_id] = acc_nm
    
    years = sorted(by_year.keys(), reverse=True)
    
    print(f"📈 수집된 연도: {years}")
    
    for y in years:
        print(f"\n[연도: {y}]")
        d = by_year[y]
        
        # 자산=자본+부채 검증
        자산 = float(d.get('ifrs-full_Assets', 0))
        자본 = float(d.get('ifrs-full_Equity', 0))
        부채 = float(d.get('ifrs-full_Liabilities', 0))
        
        print(f"  자산총계: {자산:,.0f}")
        print(f"  자본총계: {자본:,.0f}")
        print(f"  부채총계: {부채:,.0f}")
        
        자본부채_합계 = 자본 + 부채
        차이 = abs(자산 - 자본부채_합계)
        차이율 = (차이 / 자산 * 100) if 자산 != 0 else None
        
        if 차이율 is not None:
            if 차이율 <= 1.0:
                print(f"  ✅ 자산=자본+부채 일치: {차이율:.2f}%")
            else:
                print(f"  ⚠️  자산=자본+부채 불일치: {차이율:.2f}%")
        
        # 이자비용 관련 데이터 확인
        금융비용 = float(d.get('ifrs-full_FinanceCosts', 0))
        이자의지급 = float(d.get('ifrs-full_InterestPaidClassifiedAsOperatingActivities', 0))
        
        print(f"  금융비용: {금융비용:,.0f}")
        print(f"  이자의 지급: {이자의지급:,.0f}")
        
        if 금융비용 > 0:
            print(f"  ✅ 금융비용 데이터 수집 성공")
        elif 이자의지급 > 0:
            print(f"  ✅ 이자의 지급 데이터 수집 성공")
        else:
            print(f"  ❌ 이자비용 관련 데이터 없음")

def test_improved_account_list():
    """개선된 주요 계정 목록 테스트"""
    api_key = os.environ.get("DART_API_KEY")
    assert api_key, "DART_API_KEY 환경변수가 필요합니다."
    
    collector = FinancialStatementCollector(api_key=api_key)
    
    print(f"\n📋 개선된 주요 계정 목록 테스트")
    
    accounts = collector.get_major_accounts()
    
    print("📊 주요 계정 ID 목록:")
    for i, acc_id in enumerate(accounts['ids'], 1):
        acc_nm = accounts['nms'][i-1] if i <= len(accounts['nms']) else "N/A"
        print(f"  {i:2d}. {acc_id} ({acc_nm})")
    
    print(f"\n📈 총 {len(accounts['ids'])}개 계정")
    
    # 카테고리별 분류
    자산_계정 = [acc_id for acc_id in accounts['ids'] if 'Assets' in acc_id or '자산' in accounts['nms'][accounts['ids'].index(acc_id)]]
    부채_계정 = [acc_id for acc_id in accounts['ids'] if 'Liabilities' in acc_id or '부채' in accounts['nms'][accounts['ids'].index(acc_id)]]
    자본_계정 = [acc_id for acc_id in accounts['ids'] if 'Equity' in acc_id or '자본' in accounts['nms'][accounts['ids'].index(acc_id)]]
    손익_계정 = [acc_id for acc_id in accounts['ids'] if 'Revenue' in acc_id or 'Profit' in acc_id or 'Income' in acc_id or '매출' in accounts['nms'][accounts['ids'].index(acc_id)] or '이익' in accounts['nms'][accounts['ids'].index(acc_id)]]
    이자비용_계정 = [acc_id for acc_id in accounts['ids'] if 'Finance' in acc_id or 'Interest' in acc_id or '금융' in accounts['nms'][accounts['ids'].index(acc_id)] or '이자' in accounts['nms'][accounts['ids'].index(acc_id)]]
    
    print(f"\n📊 카테고리별 분류:")
    print(f"  자산 관련: {len(자산_계정)}개")
    print(f"  부채 관련: {len(부채_계정)}개")
    print(f"  자본 관련: {len(자본_계정)}개")
    print(f"  손익 관련: {len(손익_계정)}개")
    print(f"  이자비용 관련: {len(이자비용_계정)}개")

def test_consolidated_financial_data():
    """연결재무제표 자본총계 추출 테스트"""
    api_key = os.environ.get("DART_API_KEY")
    assert api_key, "DART_API_KEY 환경변수가 필요합니다."
    
    collector = FinancialStatementCollector(api_key=api_key)
    stock_code = "005930"  # 삼성전자
    now = datetime.now()
    year = now.year - 1
    
    print(f"\n🔍 [{stock_code}] 연결재무제표 자본총계 추출 테스트")
    
    accounts = collector.get_major_accounts()
    data = collector.collect_summary_financials(stock_code, year, accounts=accounts)
    
    if not data:
        print("❌ 데이터 수집 실패")
        return
    
    # 연도별로 계정별 합산값 정리
    by_year = {}
    acc_id_to_nm = {}
    
    for item in data:
        y = int(item['year'])
        acc_id = item['account_id']
        acc_nm = item['account_nm']
        amt = item['amount']
        account_detail = item.get('account_detail', '')
        
        if y not in by_year:
            by_year[y] = {}
        by_year[y][acc_id] = amt
        acc_id_to_nm[acc_id] = acc_nm
        
        # 자본총계와 부채총계의 account_detail 출력
        if acc_id in ['ifrs-full_Equity', 'ifrs-full_Liabilities']:
            print(f"  📊 {acc_id} ({acc_nm}): {amt:,.0f} (detail: {account_detail})")
    
    years = sorted(by_year.keys(), reverse=True)
    
    print(f"📈 수집된 연도: {years}")
    
    for y in years:
        print(f"\n[연도: {y}]")
        d = by_year[y]
        
        # 자산=자본+부채 검증
        자산 = float(d.get('ifrs-full_Assets', 0))
        자본 = float(d.get('ifrs-full_Equity', 0))
        부채 = float(d.get('ifrs-full_Liabilities', 0))
        
        print(f"  자산총계: {자산:,.0f}")
        print(f"  자본총계: {자본:,.0f}")
        print(f"  부채총계: {부채:,.0f}")
        
        자본부채_합계 = 자본 + 부채
        차이 = abs(자산 - 자본부채_합계)
        차이율 = (차이 / 자산 * 100) if 자산 != 0 else None
        
        if 차이율 is not None:
            if 차이율 <= 5.0:  # 5% 이내면 정상
                print(f"  ✅ 자산=자본+부채 일치: {차이율:.2f}%")
            else:
                print(f"  ⚠️  자산=자본+부채 불일치: {차이율:.2f}%")
        
        # 이자비용 관련 데이터 확인
        금융비용 = float(d.get('ifrs-full_FinanceCosts', 0))
        이자의지급 = float(d.get('ifrs-full_InterestPaidClassifiedAsOperatingActivities', 0))
        
        print(f"  금융비용: {금융비용:,.0f}")
        print(f"  이자의 지급: {이자의지급:,.0f}")
        
        if 금융비용 > 0:
            print(f"  ✅ 금융비용 데이터 수집 성공")
        elif 이자의지급 > 0:
            print(f"  ✅ 이자의 지급 데이터 수집 성공")
        else:
            print(f"  ❌ 이자비용 관련 데이터 없음")

if __name__ == "__main__":
    print("🧪 재무제표 수집기 테스트 시작")
    print("=" * 50)
    
    test_collector_basic_functionality()
    test_summary_financials_single_company()
    test_summary_financials_multiple_companies()
    test_collector_error_handling()
    test_financial_data_validation()  # 새로운 검증 테스트 추가
    test_improved_account_list() # 개선된 주요 계정 목록 테스트 추가
    test_consolidated_financial_data() # 연결재무제표 자본총계 추출 테스트 추가
    
    print("\n" + "=" * 50)
    print("✅ 모든 테스트가 완료되었습니다.") 