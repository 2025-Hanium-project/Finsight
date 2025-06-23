import sys
import os
import time
from io import BytesIO
import zipfile
import xml.etree.ElementTree as ET
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pykrx import stock
from utils.helpers import logger, save_to_csv
from config.settings import settings

class FinancialCollector:
    """DART API를 사용하여 재무 정보 수집 (다중회사 조회)"""

    def __init__(self):
        self.api_key = settings.DART_API_KEY
        if not self.api_key:
            logger.error("DART API 키가 설정되지 않았습니다.")
            raise ValueError("DART API 키가 설정되지 않았습니다.")
        
        self.corp_code_map, self.stock_to_name_map = self._load_corp_codes()
        self.report_codes = {
            "1분기": "11013",
            "반기": "11012",
            "3분기": "11014",
            "사업보고서": "11011"
        }
        # 이미지 기준 실제 DART API에서 수집 가능한 항목만 수집 (연결재무제표 CFS)
        self.key_accounts = [
            '매출액', '영업이익', '법인세차감전순이익', '당기순이익',
            '자산총계', '부채총계', '자본총계', '자본금', '이익잉여금'
        ]
        # 계정과목 매칭을 위한 키워드 매핑 (실제 DART API 응답 기반)
        self.account_keywords = {
            '매출액': ['매출액', '매출'],
            '영업이익': ['영업이익'],
            '법인세차감전순이익': ['법인세차감전순이익', '법인세비용차감전순이익', '법인세차감전 순이익', '법인세비용차감전 순이익'],
            '당기순이익': ['당기순이익', '당기순이익(손실)', '당기순손익'],
            '자산총계': ['자산총계', '자산 총계'],
            '부채총계': ['부채총계', '부채 총계'],
            '자본총계': ['자본총계', '자본 총계'],
            '자본금': ['자본금'],
            '이익잉여금': ['이익잉여금']
        }

    def _load_corp_codes(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """DART에서 고유번호 파일을 다운로드하고 KOSPI 상장사 맵을 생성"""
        logger.info("DART 고유번호 목록 로드를 시작합니다...")
        corp_map = {}
        stock_map = {}
        
        try:
            # KOSPI 종목 코드 목록 가져오기
            kospi_tickers = set(stock.get_market_ticker_list(market="KOSPI"))
            logger.info(f"KOSPI 종목 {len(kospi_tickers)}개를 확인했습니다.")

            # DART 고유번호 파일 다운로드 및 파싱
            url = "https://opendart.fss.or.kr/api/corpCode.xml"
            params = {'crtfc_key': self.api_key}
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # 응답 내용 확인
            logger.debug(f"DART API 응답 상태: {response.status_code}")
            logger.debug(f"DART API 응답 헤더: {response.headers.get('content-type', 'unknown')}")
            logger.debug(f"응답 내용 처음 100바이트: {response.content[:100]}")
            
            # 응답이 ZIP 파일인지 확인 (DART는 ZIP 파일을 반환)
            content_type = response.headers.get('content-type', '').lower()
            if 'zip' in content_type or 'download' in content_type or response.content.startswith(b'PK'):
                logger.info("ZIP 파일 응답을 받았습니다. ZIP 파일로 처리합니다.")
                try:
                    with zipfile.ZipFile(BytesIO(response.content)) as z:
                        with z.open('CORPCODE.xml') as f:
                            tree = ET.parse(f)
                            root = tree.getroot()
                            for item in root.findall('.//list'):
                                stock_code = item.findtext('stock_code', '').strip()
                                if stock_code and stock_code in kospi_tickers:
                                    corp_code = item.findtext('corp_code', '').strip()
                                    corp_name = item.findtext('corp_name', '').strip()
                                    corp_map[stock_code] = corp_code
                                    stock_map[stock_code] = corp_name
                except Exception as zip_error:
                    logger.error(f"ZIP 파일 처리 중 오류: {zip_error}")
                    logger.debug(f"ZIP 파일 내용: {response.content[:200]}")
            else:
                # JSON 응답인 경우 (일반적으로 발생하지 않음)
                logger.info("JSON 응답을 받았습니다.")
                try:
                    data = response.json()
                    if data.get('status') == '000':
                        for item in data.get('list', []):
                            stock_code = item.get('stock_code', '').strip()
                            if stock_code and stock_code in kospi_tickers:
                                corp_code = item.get('corp_code', '').strip()
                                corp_name = item.get('corp_name', '').strip()
                                corp_map[stock_code] = corp_code
                                stock_map[stock_code] = corp_name
                    else:
                        logger.error(f"DART API 오류: {data.get('message')} (상태: {data.get('status')})")
                except ValueError as e:
                    logger.error(f"JSON 파싱 오류: {e}")
                    logger.debug(f"응답 내용: {response.text[:500]}...")
            
            logger.info(f"KOSPI 상장사 {len(corp_map)}개의 DART 고유번호를 로드했습니다.")
            return corp_map, stock_map
        except Exception as e:
            logger.error(f"DART 고유번호 로딩 중 오류 발생: {e}")
            logger.debug(f"전체 오류 정보: {str(e)}")
            return {}, {}

    def get_top_kospi_companies(self, top_n: int = 20) -> List[str]:
        """시가총액 기준 상위 KOSPI 기업 종목코드 반환"""
        try:
            # 시가총액 기준 상위 종목 조회
            df = stock.get_market_cap_by_ticker(date=datetime.now().strftime('%Y%m%d'), market="KOSPI")
            df = df.sort_values('시가총액', ascending=False).head(top_n)
            return df.index.tolist()
        except Exception as e:
            logger.error(f"상위 KOSPI 기업 조회 중 오류: {e}")
            # 기본값으로 대표 기업들 반환
            return ['005930', '000660', '035420', '051910', '006400', '035720', '207940', '068270', '323410', '105560']

    def collect_financial_statements(self, years: List[int] = None, all_kospi: bool = False, top_n: int = 20) -> pd.DataFrame:
        """지정된 연도에 대해 재무제표를 수집 (전체 KOSPI 또는 상위 기업만)"""
        if not self.corp_code_map:
            logger.error("기업 고유번호 맵이 비어있어 수집을 진행할 수 없습니다.")
            return pd.DataFrame()

        # 수집할 종목 코드 결정
        if all_kospi:
            stock_codes = list(self.corp_code_map.keys())
            logger.info(f"전체 KOSPI 상장사 {len(stock_codes)}개 대상으로 수집을 시작합니다.")
        else:
            stock_codes = [code for code in self.get_top_kospi_companies(top_n) if code in self.corp_code_map]
            logger.info(f"KOSPI 상위 {len(stock_codes)}개 기업 대상으로 수집을 시작합니다.")

        if not stock_codes:
            logger.error("수집할 종목이 없습니다.")
            return pd.DataFrame()

        # 연도가 지정되지 않은 경우 최근 3년 수집
        if years is None:
            current_year = datetime.now().year
            years = [current_year, current_year - 1, current_year - 2]

        all_data = []
        
        # DART API는 한번에 100개 기업까지 조회 가능
        chunk_size = 100
        code_chunks = [stock_codes[i:i + chunk_size] for i in range(0, len(stock_codes), chunk_size)]

        for year in years:
            for report_name, report_code in self.report_codes.items():
                logger.info(f"{year}년 {report_name} 재무 정보 수집을 시작합니다...")
                year_report_data = []
                
                for i, chunk in enumerate(code_chunks):
                    logger.info(f"  - {i+1}/{len(code_chunks)}번째 묶음 처리 중...")
                    
                    corp_codes_chunk = [self.corp_code_map[sc] for sc in chunk if sc in self.corp_code_map]
                    if not corp_codes_chunk:
                        continue

                    try:
                        data = self._fetch_multi_company_statements(corp_codes_chunk, str(year), report_code)
                        if data:
                            year_report_data.extend(data)
                            logger.info(f"    ✓ {len(data)}개 기업 데이터 수집 완료")
                        else:
                            logger.info(f"    - 데이터 없음")
                        time.sleep(1.0)  # API 요청 간 지연을 1초로 증가
                    except Exception as e:
                        logger.error(f"  - 묶음 처리 중 오류 발생: {e}")
                        time.sleep(2.0)  # 오류 발생 시 더 긴 지연
                
                if year_report_data:
                    all_data.extend(year_report_data)
                    logger.info(f"✓ {year}년 {report_name} 완료: {len(year_report_data)}개 레코드")
                else:
                    logger.warning(f"⚠ {year}년 {report_name} 데이터 없음")

        if not all_data:
            logger.warning("수집된 재무 데이터가 없습니다.")
            return pd.DataFrame()

        df = pd.DataFrame(all_data)
        return self._format_dataframe(df)

    def _fetch_multi_company_statements(self, corp_codes: List[str], year: str, report_code: str) -> List[Dict]:
        """다중회사 주요계정 API를 사용하여 재무제표를 가져옵니다."""
        url = "https://opendart.fss.or.kr/api/fnlttMultiAcnt.json"
        params = {
            'crtfc_key': self.api_key,
            'corp_code': ",".join(corp_codes),
            'bsns_year': year,
            'reprt_code': report_code,
            'fs_div': 'CFS'  # 연결재무제표 우선
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=120)  # 타임아웃을 120초로 증가
                response.raise_for_status()
                data = response.json()

                if data.get('status') != '000':
                    # status '013'은 데이터 없음을 의미하므로 오류로 처리하지 않음
                    if data.get('status') != '013':
                        logger.warning(f"DART API 오류: {data.get('message')} (상태: {data.get('status')})")
                    return []
                
                return self._parse_financial_data(data.get('list', []))
                
            except requests.exceptions.Timeout:
                logger.warning(f"API 요청 타임아웃 (시도 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 지수 백오프
                    continue
                else:
                    logger.error("최대 재시도 횟수 초과")
                    return []
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"API 요청 오류: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return []
                
            except ValueError:
                logger.error(f"JSON 파싱 오류. 응답: {response.text}")
                return []
                
        return []

    def _parse_financial_data(self, data_list: List[Dict]) -> List[Dict]:
        """API 응답 데이터를 파싱하여 재무 레코드 리스트로 변환 (연결재무제표 CFS만)"""
        records = {}
        for item in data_list:
            stock_code = item.get('stock_code')
            if not stock_code or item.get('fs_div') != 'CFS':  # 연결재무제표만 수집
                continue

            account_name = item.get('account_nm', '').strip()
            matched_account = self._match_account_name(account_name)
            if matched_account:
                key = (stock_code, item.get('bsns_year'), item.get('reprt_code'))
                if key not in records:
                    records[key] = {
                        'stock_code': stock_code,
                        'stock_name': self.stock_to_name_map.get(stock_code, ''),
                        'year': item.get('bsns_year'),
                        'quarter': self.report_code_to_quarter(item.get('reprt_code')),
                    }
                thstrm_amount = self._convert_to_numeric(item.get('thstrm_amount'))
                records[key][matched_account] = thstrm_amount
        return list(records.values())

    def _match_account_name(self, account_name: str) -> Optional[str]:
        """계정과목명을 키워드와 매칭하여 표준화된 계정과목명 반환"""
        if not account_name:
            return None
            
        account_name_lower = account_name.lower()
        
        for standard_name, keywords in self.account_keywords.items():
            for keyword in keywords:
                if keyword.lower() in account_name_lower:
                    return standard_name
        
        return None

    def _format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터프레임을 최종 형태로 피벗하고 정리합니다."""
        if df.empty:
            return df

        # 모든 key_accounts가 컬럼으로 존재하도록 보장
        for col in self.key_accounts:
            if col not in df.columns:
                df[col] = None
        # 컬럼 순서 정리
        base_cols = ['year', 'quarter', 'stock_code', 'stock_name']
        financial_cols = self.key_accounts
        cols = base_cols + financial_cols
        df = df[cols]
        df = df.sort_values(by=['year', 'quarter', 'stock_code']).reset_index(drop=True)
        return df
        
    def report_code_to_quarter(self, report_code: str) -> str:
        return {'11013': '1Q', '11012': '2Q', '11014': '3Q', '11011': '4Q'}.get(report_code, '')

    def _convert_to_numeric(self, value: str) -> Optional[float]:
        if not value or value == '-':
            return None
        try:
            # 쉼표 제거 후 숫자 변환
            cleaned_value = value.replace(',', '').strip()
            return float(cleaned_value)
        except (ValueError, TypeError):
            return None

    def get_fundamental_indicators(self, date: str = None, market: str = "KOSPI") -> pd.DataFrame:
        """
        pykrx를 이용해 PER, PBR, EPS, BPS, DIV 등 주요 밸류에이션 지표를 수집
        :param date: 조회 기준일 (YYYYMMDD), 기본값은 오늘
        :param market: 시장 구분 (KOSPI, KOSDAQ 등)
        :return: 종목코드별 밸류에이션 지표 DataFrame
        """
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        df = stock.get_market_fundamental_by_ticker(date, market=market)
        df = df.reset_index().rename(columns={'티커': 'stock_code'})
        # 컬럼명 한글 → 영문 변환 (선택)
        col_map = {
            'stock_code': 'stock_code',
            'PER': 'PER',
            'PBR': 'PBR',
            'EPS': 'EPS',
            'BPS': 'BPS',
            'DIV': 'DIV'
        }
        df = df.rename(columns=col_map)
        return df

    def merge_financial_and_fundamental(self, financial_df: pd.DataFrame, date: str = None, market: str = "KOSPI") -> pd.DataFrame:
        """
        재무제표 데이터와 pykrx 밸류에이션 지표를 종목코드 기준으로 병합
        :param financial_df: collect_financial_statements로 수집한 DataFrame
        :param date: pykrx 기준일 (YYYYMMDD), 기본값은 오늘
        :param market: 시장 구분 (KOSPI, KOSDAQ 등)
        :return: 병합된 DataFrame
        """
        if financial_df is None or financial_df.empty:
            return financial_df
        fundamental_df = self.get_fundamental_indicators(date=date, market=market)
        # 종목코드 기준 병합 (필요시 연도, 분기 등 추가 병합 가능)
        merged = pd.merge(financial_df, fundamental_df, how='left', left_on='stock_code', right_on='stock_code')
        return merged

    def collect_all(self, years: List[int] = None, all_kospi: bool = False, top_n: int = 20):
        """
        다른 수집기와 인터페이스 통일: 재무제표 수집 및 저장
        """
        try:
            logger.info("재무 정보 수집을 시작합니다...")
            
            # 기본값: 상위 20개 기업, 최근 3년 데이터
            if years is None:
                current_year = datetime.now().year
                years = [current_year, current_year - 1, current_year - 2]
            
            financial_df = self.collect_financial_statements(years=years, all_kospi=all_kospi, top_n=top_n)
            
            if not financial_df.empty:
                logger.info(f"총 {len(financial_df)}개의 재무제표 데이터를 수집했습니다.")
                
                # 데이터 품질 체크
                logger.info("재무제표 데이터 품질 체크 중...")
                for col in self.key_accounts:
                    non_null_count = financial_df[col].notna().sum()
                    logger.info(f"{col}: {non_null_count}/{len(financial_df)} ({(non_null_count/len(financial_df)*100):.1f}%)")
                
                # 재무제표 파일 저장
                today_str = datetime.now().strftime('%Y%m%d')
                financial_filename = (
                    f'financial_data_all_{today_str}.csv' if all_kospi
                    else f'financial_data_top{top_n}_{today_str}.csv'
                )
                save_to_csv(financial_df, financial_filename)
                logger.info(f"재무 데이터가 {financial_filename}에 저장되었습니다.")
            else:
                logger.warning("수집된 재무 데이터가 없습니다.")
                
            return financial_df
            
        except Exception as e:
            logger.error(f"재무 정보 수집 중 오류 발생: {str(e)}")
            raise

def main():
    """메인 실행 함수"""
    try:
        collector = FinancialCollector()
        
        # 기본값: 상위 20개 기업, 최근 3년 데이터
        all_kospi = False  # True로 변경하면 전체 KOSPI 수집
        top_n = 20
        
        logger.info("=== 재무 데이터 수집 시작 ===")
        
        # 통합 수집 (재무제표)
        financial_df = collector.collect_all(
            all_kospi=all_kospi, 
            top_n=top_n
        )
        
        # 결과 출력
        if financial_df is not None and not financial_df.empty:
            logger.info(f"✓ 재무제표 데이터: {len(financial_df)}개 레코드")
            print("--- 수집된 재무 데이터 (샘플) ---")
            print(financial_df.head())
            
            # 재무 데이터 품질 체크
            print("\n--- 재무 데이터 품질 체크 ---")
            for col in collector.key_accounts:
                non_null_count = financial_df[col].notna().sum()
                print(f"{col}: {non_null_count}/{len(financial_df)} ({(non_null_count/len(financial_df)*100):.1f}%)")
        
        logger.info("=== 데이터 수집 완료 ===")
            
    except ValueError as e:
        logger.error(f"초기화 오류: {e}")
    except Exception as e:
        logger.error(f"작업 중 예상치 못한 오류 발생: {e}")

if __name__ == "__main__":
    main() 