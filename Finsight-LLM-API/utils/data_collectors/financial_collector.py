import requests
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
import logging
import time

class FinancialStatementCollector:
    """
    DART 사업보고서 요약재무제표(단일회사 전체재무제표 API)에서
    이번기/저번기/저저번기(당기/전기/전전기) 데이터를 한 번에 수집하는 collector
    """
    DART_API_KEY = None
    # MAJOR_ACCOUNT_ALIASES 및 관련 함수/로직 전체 삭제

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
                "ifrs-full_ProfitLossBeforeTax", "dart_ProfitLoss",
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
                "법인세비용차감전순손익", "당기순이익", "기본주당이익",
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

    def collect_summary_financials(self, stock_code: str, year: int, report_code: str = "11011", accounts: dict = None) -> list:
        """
        사업보고서 요약재무제표(전체재무제표 API)에서 주요 계정(account_nm/account_id 기준)만 연도별로 합산해서 반환
        반환: [{year, account, amount, ...}] 형태로 연도별/계정별 합산값
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
                return []
            if accounts is None:
                accounts = self.get_major_accounts()
            ids = set(accounts['ids'])
            nms = set(accounts['nms'])
            result_map = {}
            account_nm_map = {}
            
            # 연결재무제표 우선 추출 함수
            def get_consolidated_value(account_id, data_list):
                """연결재무제표 [member]가 포함된 account_detail을 우선 찾아서 반환"""
                for item in data_list:
                    if (item.get('account_id') == account_id and 
                        '연결재무제표' in item.get('account_detail', '')):
                        return item
                # 연결재무제표가 없으면 첫 번째 값 반환
                for item in data_list:
                    if item.get('account_id') == account_id:
                        return item
                return None
            
            for item in data.get('list', []):
                acc_id = item.get('account_id', '')
                acc_nm = item.get('account_nm', '')
                matched = False
                if acc_id in ids:
                    matched = True
                elif acc_nm in nms:
                    matched = True
                
                if matched:
                    # 자본총계와 부채총계는 연결재무제표 우선
                    if acc_id in ['ifrs-full_Equity', 'ifrs-full_Liabilities']:
                        consolidated_item = get_consolidated_value(acc_id, data.get('list', []))
                        if consolidated_item:
                            item = consolidated_item
                    
                    year_key = item.get('thstrm_nm', '').replace('제 ', '').replace(' 기', '')
                    if year_key.isdigit():
                        year_key = int(year_key)
                    else:
                        year_key = year
                    
                    if year_key not in result_map:
                        result_map[year_key] = {}
                    
                    result_map[year_key][acc_id] = {
                        'year': year_key,
                        'account_id': acc_id,
                        'account_nm': acc_nm,
                        'amount': int(item.get('thstrm_amount', 0)),
                        'frmtrm_amount': int(item.get('frmtrm_amount', 0)),
                        'bfefrmtrm_amount': int(item.get('bfefrmtrm_amount', 0)),
                        'account_detail': item.get('account_detail', '')
                    }
                    account_nm_map[acc_id] = acc_nm
            
            # 결과 리스트로 변환
            result = []
            for year_key, accounts_data in result_map.items():
                for acc_id, data_item in accounts_data.items():
                    result.append(data_item)
            
            return result
            
        except Exception as e:
            logging.error(f"재무제표 수집 중 오류 발생: {e}")
            return [] 