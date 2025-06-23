import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, List
from utils.helpers import (
    logger, calculate_change_rate, save_to_csv, make_api_request,
    log_data_collection, update_collection_time
)
from config.settings import settings

class InterestRateCollector:
    """금리 정보 수집기 (Yahoo Finance + ECOS API)"""
    
    def __init__(self):
        # 미국 국채 금리 티커 (5년, 10년, 30년물)
        self.interest_rates = {
            'US_5Y_Treasury': '^FVX',       # 미국 5년물 국채수익률
            'US_10Y_Treasury': '^TNX',      # 미국 10년물 국채수익률
            'US_30Y_Treasury': '^TYX',      # 미국 30년물 국채수익률
        }
        self.ecos_api_key = settings.ECOS_API_KEY
    
    @staticmethod
    def _format_ecos_date(date_str: str) -> str:
        """ECOS 날짜 문자열(YYYYMMDD 또는 YYYYMM)을 'YYYY-MM-DD' 형식으로 변환"""
        if not date_str or not isinstance(date_str, str):
            return datetime.now().strftime('%Y-%m-%d')
        try:
            if len(date_str) == 8:  # YYYYMMDD
                return datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
            elif len(date_str) == 6:  # YYYYMM
                # 월의 마지막 날짜로 변환
                dt = datetime.strptime(date_str, '%Y%m')
                last_day = dt.replace(day=1) + pd.DateOffset(months=1) - pd.DateOffset(days=1)
                return last_day.strftime('%Y-%m-%d')
            return date_str
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            return date_str

    def collect_interest_rates(self) -> List[Dict]:
        """Yahoo Finance를 통한 금리 수집"""
        try:
            rates_data = []
            
            for rate_name, ticker in self.interest_rates.items():
                try:
                    ticker_obj = yf.Ticker(ticker)
                    hist = ticker_obj.history(period="5d", timeout=30)
                    if len(hist) >= 1:
                        latest = hist.iloc[-1]
                        current_rate = float(latest['Close'])
                        change_amount = 0.0
                        change_rate = 0.0

                        if len(hist) >= 2:
                            previous = hist.iloc[-2]
                            previous_rate = float(previous['Close'])
                            change_amount = current_rate - previous_rate
                            change_rate = calculate_change_rate(current_rate, previous_rate) or 0.0
                        
                        data = {
                            'rate_type': rate_name,
                            'rate_value': current_rate,
                            'maturity': self._get_maturity(rate_name),
                            'change_amount': change_amount,
                            'change_rate': change_rate,
                            'base_date': latest.name.strftime('%Y-%m-%d'),
                            'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'source': 'Yahoo Finance'
                        }
                        rates_data.append(data)
                        logger.info(f"Collected {rate_name}: {current_rate:.2f}%")
                    else:
                        logger.warning(f"No data available for {rate_name}")
                except Exception as e:
                    logger.error(f"Error collecting {rate_name}: {str(e)}")
                    continue
            return rates_data
        except Exception as e:
            logger.error(f"Error in collect_interest_rates: {str(e)}")
            return []

    def _process_ecos_response(self, response_data: Dict, codes_map: Dict, date_key: str, item_key: str = 'ITEM_CODE1') -> List[Dict]:
        """ECOS API 응답을 공통으로 처리하는 함수"""
        processed_data = []
        if 'StatisticSearch' in response_data and response_data['StatisticSearch'].get('row'):
            all_rows = response_data['StatisticSearch']['row']
            
            # 각 항목별로 모든 데이터를 그룹화
            grouped_rows = {}
            for row in all_rows:
                item_code = row.get(item_key)
                if item_code in codes_map:
                    grouped_rows.setdefault(item_code, []).append(row)
            
            # 그룹화된 데이터를 기반으로 최신값 및 변화율 계산
            for item_code, rows in grouped_rows.items():
                if len(rows) >= 1:
                    latest = rows[-1]
                    current_rate = float(latest['DATA_VALUE'])
                    change_amount = 0.0
                    change_rate = 0.0

                    if len(rows) >= 2:
                        previous = rows[-2]
                        previous_rate = float(previous['DATA_VALUE'])
                        change_amount = current_rate - previous_rate
                        change_rate = calculate_change_rate(current_rate, previous_rate) or 0.0
                        
                    rate_name, maturity = codes_map[item_code]
                    processed_data.append({
                        'rate_type': rate_name, 'rate_value': current_rate, 'maturity': maturity,
                        'change_amount': change_amount, 'change_rate': change_rate,
                        'base_date': self._format_ecos_date(latest.get('TIME')),
                        'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'source': 'ECOS'
                    })
                    logger.info(f"Collected {maturity}: {current_rate:.2f}%")
        return processed_data

    def collect_ecos_rates(self) -> List[Dict]:
        """ECOS API를 통한 한국 기준금리 및 시장금리 수집"""
        try:
            rates_data = []
            if not self.ecos_api_key:
                logger.info("ECOS API key not configured, skipping ECOS rates")
                return rates_data

            logger.info("Starting ECOS API collection...")

            # --- 1. 일별 금리 (기준금리, 시장금리) ---
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - pd.DateOffset(days=365)).strftime('%Y%m%d')

            # 1-1. 기준금리 (통계코드: 722Y001, 항목코드: 0101000)
            try:
                url = f"https://ecos.bok.or.kr/api/StatisticSearch/{self.ecos_api_key}/json/kr/1/1000/722Y001/D/{start_date}/{end_date}/0101000"
                response = make_api_request(url)
                data = response.json()
                rates_data.extend(self._process_ecos_response(data, {'0101000': ('KR_Base_Rate', '한국 기준금리')}, 'D'))
            except Exception as e:
                logger.error(f"Error collecting ECOS Base Rate (722Y001): {str(e)}")

            # 1-2. 시장금리 (통계코드: 817Y002) - 각 항목별로 개별 호출
            daily_items = {
                '010502000': ('KR_CD_91D', '한국 CD(91일)'),
                '010101000': ('KR_Call_Rate', '한국 콜금리(익일물)'),
                '010200000': ('KR_3Y_Treasury', '한국 국고채(3년)'),
                '010300000': ('KR_3Y_Corp_Bond', '한국 회사채(3년,AA-)')
            }
            
            for item_code, (rate_name, display_name) in daily_items.items():
                try:
                    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{self.ecos_api_key}/json/kr/1/1000/817Y002/D/{start_date}/{end_date}/{item_code}"
                    response = make_api_request(url)
                    data = response.json()
                    rates_data.extend(self._process_ecos_response(data, {item_code: (rate_name, display_name)}, 'D'))
                except Exception as e:
                    logger.error(f"Error collecting ECOS Daily Market Rate {display_name} ({item_code}): {str(e)}")

            # --- 2. 월별 금리 (COFIX) ---
            end_month = datetime.now().strftime('%Y%m')
            start_month = (datetime.now() - pd.DateOffset(months=24)).strftime('%Y%m')
            
            # COFIX 잔액 (통계코드: 121Y013, 항목코드: D000900)
            try:
                url = f"https://ecos.bok.or.kr/api/StatisticSearch/{self.ecos_api_key}/json/kr/1/1000/121Y013/M/{start_month}/{end_month}/D000900"
                response = make_api_request(url)
                data = response.json()
                rates_data.extend(self._process_ecos_response(data, {'D000900': ('KR_COFIX_Balance', '한국 COFIX(잔액)')}, 'M', item_key='ITEM_CODE2'))
            except Exception as e:
                logger.error(f"Error collecting COFIX Balance (121Y013): {str(e)}")
                
            # COFIX 신규 (통계코드: 121Y002, 항목코드: C000900)
            try:
                url = f"https://ecos.bok.or.kr/api/StatisticSearch/{self.ecos_api_key}/json/kr/1/1000/121Y002/M/{start_month}/{end_month}/C000900"
                response = make_api_request(url)
                data = response.json()
                rates_data.extend(self._process_ecos_response(data, {'C000900': ('KR_COFIX_New', '한국 COFIX(신규취급액)')}, 'M', item_key='ITEM_CODE2'))
            except Exception as e:
                logger.error(f"Error collecting COFIX New (121Y002): {str(e)}")

            logger.info(f"ECOS collection completed. Total ECOS records: {len(rates_data)}")
            return rates_data
            
        except Exception as e:
            logger.error(f"Error in collect_ecos_rates: {str(e)}")
            return []

    def _get_maturity(self, rate_name: str) -> str:
        maturity_map = {
            'US_5Y_Treasury': '미국 5년물 국채',
            'US_10Y_Treasury': '미국 10년물 국채',
            'US_30Y_Treasury': '미국 30년물 국채',
        }
        return maturity_map.get(rate_name, 'N/A')
    
    def save_to_csv(self, data: List[Dict]):
        try:
            if data:
                timestamp = datetime.now().strftime('%Y%m%d')
                save_to_csv(data, f'interest_rate_data_{timestamp}.csv')
                logger.info(f"Saved {len(data)} interest rate records to CSV")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
    
    def collect_all(self):
        try:
            logger.info("Starting interest rate collection...")
            
            # Yahoo Finance 금리
            rates_data = self.collect_interest_rates()
            log_data_collection("yahoo_interest_rates", len(rates_data))
            
            # ECOS API 금리
            ecos_data = self.collect_ecos_rates()
            log_data_collection("ecos_interest_rates", len(ecos_data))
            
            # CSV에 저장
            all_data = rates_data + ecos_data
            if all_data:
                self.save_to_csv(all_data)
                update_collection_time("interest_rates")
            
            logger.info(f"Interest rate collection completed. Total: {len(all_data)} records")
            
        except Exception as e:
            logger.error(f"Error in collect_all: {str(e)}")

def main():
    collector = InterestRateCollector()
    collector.collect_all()

if __name__ == "__main__":
    main() 