import requests
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import logging
import time
import re

class FinancialStatementCollector:
    """
    DART 사업보고서 요약재무제표(단일회사 전체재무제표 API)에서
    이번기/저번기/저저번기(당기/전기/전전기) 데이터를 한 번에 수집하는 collector
    """
    DART_API_KEY = None

    # 주요 계정 리스트만 반환
    @staticmethod
    def get_major_accounts() -> dict:
        # account_id와 account_nm(한글명) 모두 반환
        # dart_api.json 분석 결과에 맞게 개선된 목록
        return {
            'ids': [
                # 자산 관련
                "ifrs-full_Assets", "ifrs-full_CurrentAssets", "ifrs-full_CashAndCashEquivalents", 
                "ifrs-full_CurrentTradeReceivables", "ifrs-full_Inventories", "ifrs-full_NoncurrentAssets", 
                "ifrs-full_PropertyPlantAndEquipment",
                # 부채 관련
                "ifrs-full_Liabilities", "ifrs-full_CurrentLiabilities", "ifrs-full_NoncurrentLiabilities",
                # 자본 관련
                "ifrs-full_Equity", "ifrs-full_IssuedCapital", "ifrs-full_RetainedEarnings",
                # 손익 관련
                "ifrs-full_Revenue", "dart_OperatingIncomeLoss", 
                "ifrs-full_ProfitLoss", "ifrs-full_ProfitLossAttributableToOwnersOfParent", 
                "ifrs-full_ProfitLossBeforeTax",
                "ifrs-full_BasicEarningsLossPerShare",
                # 이자비용 관련
                "ifrs-full_FinanceCosts", "ifrs-full_InterestPaidClassifiedAsOperatingActivities"
            ],
            'nms': [
                # 자산 관련
                "자산총계", "유동자산", "현금및현금성자산", "매출채권", "재고자산", "비유동자산", "유형자산",
                # 부채 관련
                "부채총계", "유동부채", "비유동부채",
                # 자본 관련
                "자본총계", "자본금", "이익잉여금",
                # 손익 관련
                "매출액", "영업이익", "당기순이익(손실)", "지배기업 소유주에게 귀속되는 당기순이익(손실)",
                "법인세비용차감전순손익", "기본주당이익",
                # 이자비용 관련
                "금융비용", "이자의 지급"
            ]
        }

    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            self.DART_API_KEY = api_key
        if not self.DART_API_KEY:
            raise ValueError("DART API 키가 설정되지 않았습니다. set_api_key 또는 생성자에서 전달 필요.")
        self.corp_code_map = self._load_corp_codes()

    @classmethod
    def set_api_key(cls, api_key: str):
        cls.DART_API_KEY = api_key

    def _load_corp_codes(self) -> Dict[str, str]:
        url = "https://opendart.fss.or.kr/api/corpCode.xml"
        params = {'crtfc_key': self.DART_API_KEY}
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        corp_map = {}
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            with z.open('CORPCODE.xml') as f:
                import xml.etree.ElementTree as ET
                tree = ET.parse(f)
                root = tree.getroot()
                for item in root.findall('.//list'):
                    stock_code = item.findtext('stock_code', '').strip()
                    corp_code = item.findtext('corp_code', '').strip()
                    if stock_code and corp_code:
                        corp_map[stock_code] = corp_code
        return corp_map

    def get_corp_code(self, stock_code: str) -> Optional[str]:
        return self.corp_code_map.get(stock_code)

    def _collect_raw_data(self, stock_code: str, year: int, report_code: str = "11011") -> dict:
        """
        DART API에서 원본 데이터 수집 (데이터 수집 전용)
        """
        corp_code = self.get_corp_code(stock_code)
        if not corp_code:
            raise ValueError(f"종목코드 {stock_code}에 대한 corp_code를 찾을 수 없습니다.")
        
        url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
        params = {
            'crtfc_key': self.DART_API_KEY,
            'corp_code': corp_code,
            'bsns_year': str(year),
            'reprt_code': report_code,
            'fs_div': 'CFS'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get('status') != '000':
                logging.warning(f"DART API 응답 오류: {data.get('message')}")
                return {"error": data.get('message')}
            return data
        except Exception as e:
            logging.error(f"재무제표 수집 중 오류 발생: {e}")
            return {"error": str(e)}

    def _preprocess_data(self, raw_data: dict, accounts: dict = None) -> dict:
        """
        원본 데이터에서 주요 계정만 추출하여 정리
        """
        if raw_data.get('status') != '000':
            return {'error': f"DART API 오류: {raw_data.get('message', '알 수 없는 오류')}"}
        
        data_list = raw_data.get('list', [])
        if not data_list:
            return {'error': '수집된 데이터가 없습니다.'}
        
        # 연도 추출 함수 개선
        def extract_year(thstrm_nm, bsns_year=None):
            """bsns_year가 있으면 우선 사용, 없으면 thstrm_nm에서 연도 추출 (예: '제 55 기' -> 2023)"""
            if bsns_year and str(bsns_year).isdigit():
                return int(bsns_year)
            try:
                # "제 55 기" 형태에서 숫자 추출
                match = re.search(r'제\s*(\d+)\s*기', thstrm_nm)
                if match:
                    period_num = int(match.group(1))
                    # 기준 연도와 기수는 현재 연도와 기수로 동적으로 계산
                    from datetime import datetime
                    now = datetime.now()
                    current_year = now.year
                    # DART는 12월 결산법인 기준, 2023년이면 55기, 2024년이면 56기
                    current_period = 56 + (now.year - 2024)
                    actual_year = current_year - (current_period - period_num)
                    return actual_year
                return None
            except:
                return None
        
        # 연도별로 데이터 정리
        by_year = {}
        years = set()
        
        # 연결재무제표 우선 추출 함수
        def get_consolidated_value(account_id, data_list, target_year):
            """연결재무제표 [member]가 포함된 account_detail을 우선 찾아서 반환"""
            for item in data_list:
                if (item.get('account_id') == account_id and 
                    '연결재무제표' in item.get('account_detail', '') and
                    extract_year(item.get('thstrm_nm', ''), item.get('bsns_year')) == target_year):
                    return item
            # 연결재무제표가 없으면 해당 연도의 첫 번째 값 반환
            for item in data_list:
                if (item.get('account_id') == account_id and 
                    extract_year(item.get('thstrm_nm', ''), item.get('bsns_year')) == target_year):
                    return item
            return None
        
        for item in data_list:
            account_id = item.get('account_id')
            if not account_id:
                continue
                
            # 연도 추출
            thstrm_nm = item.get('thstrm_nm', '')
            bsns_year = item.get('bsns_year', None)
            year = extract_year(thstrm_nm, bsns_year)
            if year is None:
                continue
                
            years.add(year)
            
            if year not in by_year:
                by_year[year] = {}
            
            # 자본총계와 부채총계는 연결재무제표 우선
            if account_id in ['ifrs-full_Equity', 'ifrs-full_Liabilities']:
                consolidated_item = get_consolidated_value(account_id, data_list, year)
                if consolidated_item:
                    item = consolidated_item
            
            # 이미 처리된 계정이면 건너뛰기 (연결재무제표 우선 처리로 인해)
            if account_id in by_year[year]:
                continue
            
            # 금액 추출 (빈 문자열 처리 개선)
            def safe_int(value):
                """안전한 정수 변환"""
                if not value or value.strip() == '':
                    return 0
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return 0
            
            amount = safe_int(item.get('thstrm_amount', '0'))
            frmtrm_amount = safe_int(item.get('frmtrm_amount', '0'))
            bfefrmtrm_amount = safe_int(item.get('bfefrmtrm_amount', '0'))
            
            by_year[year][account_id] = {
                'year': year,
                'account_id': account_id,
                'account_nm': item.get('account_nm', ''),
                'amount': amount,
                'frmtrm_amount': frmtrm_amount,
                'bfefrmtrm_amount': bfefrmtrm_amount,
                'account_detail': item.get('account_detail', '')
            }
        
        # 주요 계정만 필터링 (accounts가 제공된 경우)
        if accounts and 'ids' in accounts:
            filtered_by_year = {}
            for year in by_year:
                filtered_by_year[year] = {}
                for acc_id in accounts['ids']:
                    if acc_id in by_year[year]:
                        filtered_by_year[year][acc_id] = by_year[year][acc_id]
            by_year = filtered_by_year
        
        return {
            'by_year': by_year,
            'years': sorted(list(years)),
            'raw_count': len(data_list)
        }

    def _calculate_financial_ratios(self, preprocessed_data: dict) -> dict:
        """
        전처리된 데이터에서 주요 재무비율 계산 (비율 계산 전용)
        """
        by_year = preprocessed_data['by_year']
        years = preprocessed_data['years']
        ratios = {}
        
        for y in years:
            d = by_year.get(y, {})
            
            # 순이익: 여러 account_id 후보 중 존재하는 값 사용 (우선순위 적용)
            순이익_후보들 = [
                'ifrs-full_ProfitLoss',  # 기본 당기순이익
                'ifrs-full_ProfitLossAttributableToOwnersOfParent',  # 지배기업 소유주 귀속
                'ifrs-full_ProfitLoss',  # DART 특화 당기순이익
                'ifrs-full_ProfitLossBeforeTax'  # 법인세비용차감전순이익 (마지막 후보)
            ]
            순이익 = 0.0
            사용된_계정 = None
            for candidate in 순이익_후보들:
                if candidate in d and d[candidate]['amount'] != 0:
                    순이익 = float(d[candidate]['amount'])
                    사용된_계정 = candidate
                    print(f"✅ {y}년 당기순이익: {candidate} = {순이익:,.0f}")
                    break
            else:
                print(f"❌ {y}년 당기순이익: 데이터 없음")
                사용된_계정 = "없음"
            
            # 주요 계정값 추출
            자본 = float(d.get('ifrs-full_Equity', {}).get('amount', 0.0))
            자산 = float(d.get('ifrs-full_Assets', {}).get('amount', 0.0))
            매출 = float(d.get('ifrs-full_Revenue', {}).get('amount', 0.0))
            영업이익 = float(d.get('dart_OperatingIncomeLoss', {}).get('amount', 0.0))
            부채 = float(d.get('ifrs-full_Liabilities', {}).get('amount', 0.0))
            유동자산 = float(d.get('ifrs-full_CurrentAssets', {}).get('amount', 0.0))
            유동부채 = float(d.get('ifrs-full_CurrentLiabilities', {}).get('amount', 0.0))
            현금및현금성자산 = float(d.get('ifrs-full_CashAndCashEquivalents', {}).get('amount', 0.0))
            
            # 재무비율 계산 (0이 아닌 경우에만 계산)
            roe = (순이익 / 자본 * 100) if (자본 != 0 and 순이익 != 0) else None
            roa = (순이익 / 자산 * 100) if (자산 != 0 and 순이익 != 0) else None
            op_margin = (영업이익 / 매출 * 100) if (매출 != 0 and 영업이익 != 0) else None
            net_margin = (순이익 / 매출 * 100) if (매출 != 0 and 순이익 != 0) else None
            debt_ratio = (부채 / 자본 * 100) if (자본 != 0 and 부채 != 0) else None
            current_ratio = (유동자산 / 유동부채 * 100) if (유동부채 != 0 and 유동자산 != 0) else None
            cash_ratio = (현금및현금성자산 / 유동자산 * 100) if (유동자산 != 0 and 현금및현금성자산 != 0) else None
            
            # 이자보상배율 계산
            금융비용 = float(d.get('ifrs-full_FinanceCosts', {}).get('amount', 0.0))
            이자의지급 = float(d.get('ifrs-full_InterestPaidClassifiedAsOperatingActivities', {}).get('amount', 0.0))
            이자비용 = 금융비용 if 금융비용 != 0 else 이자의지급
            interest_coverage = (영업이익 / 이자비용) if (이자비용 != 0 and 영업이익 != 0) else None
            
            # 자산=자본+부채 검증
            자산_합계 = 자산
            자본부채_합계 = 자본 + 부채
            차이 = abs(자산_합계 - 자본부채_합계)
            차이율 = (차이 / 자산_합계 * 100) if 자산_합계 != 0 else None
            
            ratios[y] = {
                'ROE': roe,
                'ROA': roa,
                '영업이익률': op_margin,
                '순이익률': net_margin,
                '부채비율': debt_ratio,
                '유동비율': current_ratio,
                '현금비율': cash_ratio,
                '이자보상배율': interest_coverage,
                '자산_자본부채_차이율': 차이율
            }
        
        return ratios

    def collect_summary_financials(self, stock_code: str, year: int, report_code: str = "11011", accounts: dict = None) -> dict:
        """
        사업보고서 요약재무제표에서 주요 계정 데이터 수집 및 비율 계산까지 포함한 dict 반환
        반환: {by_year, ratios, years, raw_data} 형태
        """
        # 1단계: 원본 데이터 수집
        raw_data = self._collect_raw_data(stock_code, year, report_code)
        if "error" in raw_data:
            return raw_data
        
        # 2단계: 데이터 전처리
        preprocessed_data = self._preprocess_data(raw_data, accounts)
        
        # 3단계: 재무비율 계산
        ratios = self._calculate_financial_ratios(preprocessed_data)
        
        # 4단계: 최종 결과 반환
        return {
            **preprocessed_data,
            'ratios': ratios,
            'raw_data': raw_data,
            'stock_code': stock_code,
            'year': year
        }

    def collect_summary_financials_legacy(self, stock_code: str, year: int, report_code: str = "11011", accounts: dict = None) -> list:
        """
        기존 호환성을 위한 함수 (list 반환)
        """
        result = self.collect_summary_financials(stock_code, year, report_code, accounts)
        if "error" in result:
            return []
        
        # list 형태로 변환
        result_list = []
        for year_key, accounts_data in result['by_year'].items():
            for acc_id, data_item in accounts_data.items():
                result_list.append(data_item)
        
        return result_list 

    def collect_latest_summary_financials(self, stock_code: str, years: list = None, report_code: str = "11011", accounts: dict = None) -> dict:
        """
        가장 최근 연도부터 데이터가 있는 사업보고서 요약재무제표를 반환
        years: 시도할 연도 리스트 (기본값: 올해~3년 전)
        """
        from datetime import datetime
        if years is None:
            now = datetime.now()
            years = [now.year, now.year-1, now.year-2, now.year-3]
        for year in years:
            result = self.collect_summary_financials(stock_code, year, report_code, accounts)
            if 'by_year' in result and result['by_year'] and not result.get('error'):
                return result
        return {"error": f"{years} 중 데이터가 없습니다."} 