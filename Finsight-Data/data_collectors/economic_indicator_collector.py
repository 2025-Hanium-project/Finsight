import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yfinance as yf
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.helpers import (
    logger, calculate_change_rate, make_api_request,
    log_data_collection, update_collection_time, save_to_csv
)
from config.settings import settings

class EconomicIndicatorCollector:
    """경제 지표 수집기"""
    
    def __init__(self):
        pass
    
    def collect_ecos_indicators(self) -> List[Dict]:
        """한국은행 ECOS API를 통한 경제 지표 수집"""
        try:
            indicators_data = []
            
            if not settings.ECOS_API_KEY:
                logger.info("ECOS API key not configured, skipping ECOS indicators collection")
                return indicators_data
            
            # 주요 경제 지표 코드 (사용자 제공 스크린샷 기반)
            ecos_indicators = {
                '소비자물가지수': {'code': '901Y009', 'item_code': '0', 'period': 'M'},
                '생산자물가지수': {'code': '404Y014', 'item_code': '*AA', 'period': 'M'},
                '실업률': {'code': '901Y027', 'item_code': 'I61BC', 'period': 'M'},
                '경제성장률': {'code': '902Y015', 'item_code': 'KOR', 'period': 'Q'},
            }
            
            base_url = f"http://ecos.bok.or.kr/api/StatisticSearch/{settings.ECOS_API_KEY}/json/kr/1/20/" # 데이터 수 20개로 증가
            
            for indicator_name, config in ecos_indicators.items():
                try:
                    period = config['period']
                    now = datetime.now()
                    
                    if period == 'M':
                        end_date = now.strftime('%Y%m')
                        start_date = (now - timedelta(days=365*2)).strftime('%Y%m') # 2년치 데이터 요청
                    elif period == 'Q':
                        end_q = (now.month - 1) // 3 + 1
                        end_year = now.year
                        end_date = f"{end_year}Q{end_q}"
                        start_date = f"{end_year - 2}Q{end_q}" # 2년전 같은 분기
                    else: # 연간
                        end_date = str(now.year)
                        start_date = str(now.year - 2)

                    request_url = f"{base_url}{config['code']}/{period}/{start_date}/{end_date}/{config['item_code']}"
                    
                    response = make_api_request(request_url)
                    response_json = response.json()

                    if 'StatisticSearch' in response_json:
                        data = response_json['StatisticSearch']['row']
                        if data and len(data) >= 2:
                            data = sorted(data, key=lambda x: x['TIME']) # 시간순으로 정렬
                            latest_item = data[-1]
                            previous_item = data[-2]
                            
                            latest = float(latest_item['DATA_VALUE'])
                            previous = float(previous_item['DATA_VALUE'])

                            date_str = latest_item['TIME']
                            if period == 'Q':
                                date_obj = datetime.strptime(f"{date_str[:4]}-{(int(date_str[5])-1)*3+1:02d}-01", '%Y-%m-%d')
                            else: # M or A
                                date_obj = datetime.strptime(date_str, '%Y%m' if period == 'M' else '%Y')
                            
                            indicator_data = {
                                'indicator_name': indicator_name,
                                'indicator_value': latest,
                                'change_rate': calculate_change_rate(latest, previous),
                                'period': config['period'],
                                'date': date_obj,
                                'collected_at': datetime.now()
                            }
                            
                            indicators_data.append(indicator_data)
                            logger.info(f"Collected ECOS {indicator_name}: {latest:.2f}")
                        else:
                            logger.warning(f"ECOS {indicator_name} collected less than 2 data points. Skipping.")
                    elif 'RESULT' in response_json:
                         logger.error(f"ECOS API Error for {indicator_name}: {response_json['RESULT']['MESSAGE']} ({response_json['RESULT']['CODE']})")
                    else:
                        logger.warning(f"Unexpected ECOS response for {indicator_name}: {response_json}")
                            
                except Exception as e:
                    logger.error(f"Error collecting ECOS {indicator_name}: {str(e)}")
                    continue
            
            return indicators_data
            
        except Exception as e:
            logger.error(f"Error in collect_ecos_indicators: {str(e)}")
            return []
    
    def collect_fred_indicators(self) -> List[Dict]:
        """FRED API를 통한 미국 경제 지표 수집"""
        try:
            indicators_data = []
            
            # FRED API 키가 있는 경우에만 실행
            if not settings.FRED_API_KEY:
                logger.info("FRED API key not configured, skipping FRED indicators collection")
                return indicators_data
            
            # FRED 시리즈 ID
            fred_indicators = {
                '미국_CPI': 'CPIAUCSL',      # 소비자물가지수
                '미국_PPI': 'PPIACO',        # 생산자물가지수
                '미국_실업률': 'UNRATE',     # 실업률
                # '미국_ISM_PMI': 'MANPMI',      # ISM 제조업 PMI (오류로 임시 비활성화)
                '미국_소비자신뢰지수': 'UMCSENT'  # 소비자신뢰지수
            }
            
            base_url = "https://api.stlouisfed.org/fred/series/observations"
            
            for indicator_name, series_id in fred_indicators.items():
                try:
                    params = {
                        'api_key': settings.FRED_API_KEY,
                        'series_id': series_id,
                        'file_type': 'json',
                        'limit': 2,
                        'sort_order': 'desc'
                    }
                    
                    response = make_api_request(base_url, params=params)
                    response_json = response.json()

                    if 'observations' in response_json:
                        observations = response_json['observations']
                        if len(observations) >= 2:
                            latest_str = observations[0]['value']
                            previous_str = observations[1]['value']

                            # FRED 값에 '.'이 포함될 수 있으므로 유효성 검사 추가
                            if latest_str != '.' and previous_str != '.':
                                latest = float(latest_str)
                                previous = float(previous_str)
                                
                                indicator_data = {
                                    'indicator_name': indicator_name,
                                    'indicator_value': latest,
                                    'change_rate': calculate_change_rate(latest, previous),
                                    'period': 'M',
                                    'date': datetime.strptime(observations[0]['date'], '%Y-%m-%d'),
                                    'collected_at': datetime.now()
                                }
                                
                                indicators_data.append(indicator_data)
                                logger.info(f"Collected FRED {indicator_name}: {latest:.2f}")
                            else:
                                logger.warning(f"FRED {indicator_name} contains non-numeric data. Skipping.")
                        else:
                            logger.warning(f"FRED {indicator_name} collected less than 2 data points. Skipping.")
                    elif 'error_message' in response_json:
                        logger.error(f"FRED API Error for {indicator_name}: {response_json['error_message']} ({response_json.get('error_code')})")
                    else:
                        logger.warning(f"Unexpected FRED response for {indicator_name}: {response_json}")
                            
                except Exception as e:
                    logger.error(f"Error collecting FRED {indicator_name}: {str(e)}")
                    continue
            
            return indicators_data
            
        except Exception as e:
            logger.error(f"Error in collect_fred_indicators: {str(e)}")
            return []
    
    def collect_kosis_indicators(self) -> List[Dict]:
        """통계청 KOSIS API를 통한 경제 지표 수집"""
        try:
            indicators_data = []
            
            # KOSIS API 키가 없는 경우 건너뛰기
            if not settings.KOSIS_API_KEY:
                logger.info("KOSIS API key not configured, skipping KOSIS indicators collection")
                return indicators_data

            base_url = "https://kosis.kr/openapi/Param/statisticsParameterData.do"
            
            # KOSIS 통계표 정보
            kosis_indicators = {
                '소비자물가지수': {
                    'tblId': 'DT_1J1A002', 'itmId': 'T10', 'objL1': '0', 'prdSe': 'M'
                },
                '실업률': {
                    'tblId': 'DT_1DA7002S', 'itmId': 'T1', 'objL1': '1', 'objL2': '1', 'prdSe': 'M'
                },
                '경제활동인구': { # GDP 대용
                    'tblId': 'DT_1DA7001S', 'itmId': 'T1', 'objL1': '1', 'objL2': '1', 'prdSe': 'M'
                },
                '제조업생산능력지수': { # PMI 대용
                    'tblId': 'DT_1IX1001', 'itmId': 'I00', 'objL1': '01', 'prdSe': 'M'
                }
            }
            
            end_date = datetime.now().strftime('%Y%m')
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m')

            for indicator_name, config in kosis_indicators.items():
                try:
                    params = {
                        'method': 'getList',
                        'apiKey': settings.KOSIS_API_KEY,
                        'format': 'json',
                        'jsonVD': 'Y',
                        'tblId': config['tblId'],
                        'itmId': config.get('itmId'),
                        'objL1': config.get('objL1'),
                        'objL2': config.get('objL2'),
                        'prdSe': config['prdSe'],
                        'startPrdDe': start_date,
                        'endPrdDe': end_date
                    }
                    # None 값인 파라미터 제거
                    params = {k: v for k, v in params.items() if v is not None}
                    
                    response = make_api_request(base_url, params=params)
                    response_json = response.json()
                    
                    if response_json and isinstance(response_json, list):
                        if len(response_json) >= 2:
                            data = sorted(response_json, key=lambda x: x['PRD_DE'])
                            latest_item = data[-1]
                            previous_item = data[-2]
                            
                            latest_value = float(latest_item['DT'])
                            previous_value = float(previous_item['DT'])
                            
                            indicator_data = {
                                'indicator_name': indicator_name,
                                'indicator_value': latest_value,
                                'change_rate': calculate_change_rate(latest_value, previous_value),
                                'period': config['prdSe'],
                                'date': datetime.strptime(latest_item['PRD_DE'], '%Y%m'),
                                'collected_at': datetime.now()
                            }
                            indicators_data.append(indicator_data)
                            logger.info(f"Collected KOSIS {indicator_name}: {latest_value:.2f}")
                        else:
                            logger.warning(f"KOSIS {indicator_name} collected less than 2 data points. Skipping.")
                    elif response_json and 'errMsg' in response_json:
                        logger.error(f"KOSIS API Error for {indicator_name}: {response_json['errMsg']}")
                    else:
                        logger.warning(f"Unexpected KOSIS response for {indicator_name}: {response_json}")

                except Exception as e:
                    logger.error(f"Error collecting KOSIS {indicator_name}: {str(e)}")
                    continue
            
            return indicators_data

        except Exception as e:
            logger.error(f"Error in collect_kosis_indicators: {str(e)}")
            return []
    
    def collect_pmi_data(self) -> List[Dict]:
        """PMI 데이터 수집 (Yahoo Finance 기반)"""
        try:
            indicators_data = []
            
            # PMI 관련 ETF/지수 (실제 PMI 데이터는 유료 API 필요)
            pmi_tickers = {
                '글로벌_PMI': '^VIX',  # 변동성 지수 (PMI 대용)
                '미국_경제활성지수': '^DJI',  # 다우존스 (경제 활성도 대용)
            }
            
            for indicator_name, ticker in pmi_tickers.items():
                try:
                    # yfinance를 사용하여 데이터 수집
                    ticker_obj = yf.Ticker(ticker)
                    hist = ticker_obj.history(period="2d")
                    
                    if len(hist) >= 2:
                        latest = hist.iloc[-1]
                        previous = hist.iloc[-2]
                        
                        data = {
                            'indicator_name': indicator_name,
                            'indicator_value': float(latest['Close']),
                            'change_rate': calculate_change_rate(latest['Close'], previous['Close']),
                            'period': 'D',
                            'date': latest.name,
                            'collected_at': datetime.now()
                        }
                        
                        indicators_data.append(data)
                        logger.info(f"Collected {indicator_name}: {data['indicator_value']:.2f}")
                        
                except Exception as e:
                    logger.error(f"Error collecting PMI {indicator_name}: {str(e)}")
                    continue
            
            return indicators_data
            
        except Exception as e:
            logger.error(f"Error in collect_pmi_data: {str(e)}")
            return []
    
    def save_to_csv(self, data: List[Dict]):
        """CSV 파일로 저장"""
        try:
            # CSV 파일로 저장
            if data:
                timestamp = datetime.now().strftime('%Y%m%d')
                save_to_csv(data, f'economic_indicator_data_{timestamp}.csv')
                logger.info(f"Saved {len(data)} economic indicator records to CSV")
            
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
    
    def collect_all(self):
        """모든 경제 지표 수집"""
        try:
            logger.info("Starting economic indicator collection...")
            
            # ECOS 경제 지표 수집
            ecos_data = self.collect_ecos_indicators()
            log_data_collection("ecos_indicators", len(ecos_data))

            # KOSIS 경제 지표 수집 (임시 비활성화)
            # kosis_data = self.collect_kosis_indicators()
            # log_data_collection("kosis_indicators", len(kosis_data))
            
            # FRED 경제 지표 수집
            fred_data = self.collect_fred_indicators()
            log_data_collection("fred_indicators", len(fred_data))
            
            # PMI 데이터 수집
            pmi_data = self.collect_pmi_data()
            log_data_collection("pmi_data", len(pmi_data))
            
            # CSV에 저장
            all_data = ecos_data + fred_data + pmi_data
            if all_data:
                self.save_to_csv(all_data)
                update_collection_time("economic_indicators")
            
            logger.info(f"Economic indicator collection completed. Total: {len(all_data)} records")
            
        except Exception as e:
            logger.error(f"Error in collect_all: {str(e)}")

def main():
    """메인 실행 함수"""
    collector = EconomicIndicatorCollector()
    collector.collect_all()

if __name__ == "__main__":
    main() 