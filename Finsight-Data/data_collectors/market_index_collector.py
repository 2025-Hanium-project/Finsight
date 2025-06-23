import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yfinance as yf
from pykrx import stock
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.helpers import (
    logger, calculate_change_rate, get_trading_date, 
    log_data_collection, update_collection_time, save_to_csv
)
from config.settings import settings

def get_latest_trading_date():
    """오늘이 평일(월~금)이고 장 마감 후면 오늘, 아니면 가장 최근 평일 반환"""
    now = datetime.now()
    # 일요일(6), 토요일(5) 체크 및 장 마감(16시 이후) 체크
    if now.weekday() < 5 and now.hour >= 16:
        return now.strftime('%Y%m%d')
    # 아니면 가장 최근 평일
    days_back = 1
    while True:
        check = now - timedelta(days=days_back)
        if check.weekday() < 5:
            return check.strftime('%Y%m%d')
        days_back += 1

class MarketIndexCollector:
    """시장 지수 데이터 수집기"""
    
    def __init__(self):
        pass
    
    def collect_korea_indices(self) -> List[Dict]:
        """국내 주식 지수 수집"""
        try:
            indices_data = []
            trading_date = get_latest_trading_date()
            prev_date = (datetime.strptime(trading_date, "%Y%m%d") - timedelta(days=5)).strftime("%Y%m%d")
            logger.info(f"Using trading date: {trading_date}, prev date: {prev_date}")
            for index_name, index_code in settings.KOREA_INDICES.items():
                try:
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            logger.info(f"Collecting {index_name} (attempt {attempt + 1})")
                            try:
                                df = stock.get_index_ohlcv_by_date(fromdate=prev_date, todate=trading_date, ticker=index_code)
                            except Exception as krx_error:
                                logger.warning(f"KRX API error for {index_name}: {krx_error}")
                                df = self._get_index_from_components(index_name, index_code, prev_date, trading_date)
                            if not df.empty and len(df) >= 2:
                                df = df.sort_index()
                                latest = df.iloc[-1]
                                previous = df.iloc[-2]
                                base_date = df.index[-1]  # 종가 기준 날짜
                                close_col = '종가' if '종가' in df.columns else 'CLSPRC_IDX'
                                close_value = latest[close_col] if close_col in latest else 0
                                prev_close_value = previous[close_col] if close_col in previous else close_value
                                if pd.isna(close_value):
                                    close_value = 0
                                if pd.isna(prev_close_value):
                                    prev_close_value = close_value
                                # 등락, 등락률 직접 계산
                                change_value = close_value - prev_close_value
                                change_rate_value = ((close_value - prev_close_value) / prev_close_value * 100) if prev_close_value else 0
                                volume_col = '거래량' if '거래량' in df.columns else 'ACC_TRDVOL'
                                data = {
                                    'index_name': index_name,
                                    'index_code': index_code,
                                    'index_value': float(close_value),
                                    'change_amount': float(change_value),
                                    'change_rate': float(change_rate_value),
                                    'volume': int(latest[volume_col]) if volume_col in latest and not pd.isna(latest[volume_col]) else 0,
                                    'base_date': str(base_date)[:10],
                                    'collected_at': datetime.now()
                                }
                                indices_data.append(data)
                                logger.info(f"Collected {index_name}: {data['index_value']:.2f}")
                                break
                            else:
                                logger.warning(f"Insufficient data for {index_name}: {len(df) if not df.empty else 0} records")
                                break
                        except Exception as e:
                            if attempt < max_retries - 1:
                                logger.warning(f"Attempt {attempt + 1} failed for {index_name}: {e}. Retrying...")
                                time.sleep(2)
                            else:
                                logger.error(f"Error collecting {index_name} after {max_retries} attempts: {e}")
                except Exception as e:
                    logger.error(f"Error collecting {index_name}: {e}")
            return indices_data
        except Exception as e:
            logger.error(f"Error in collect_korea_indices: {e}", exc_info=True)
            return []
    
    def collect_global_indices(self) -> List[Dict]:
        """해외 주식 지수 수집"""
        try:
            indices_data = []
            trading_date = get_latest_trading_date()
            end_date = datetime.strptime(trading_date, "%Y%m%d").strftime("%Y-%m-%d")
            start_date = (datetime.strptime(trading_date, "%Y%m%d") - timedelta(days=10)).strftime("%Y-%m-%d")
            logger.info(f"Using global indices date range: {start_date} ~ {end_date}")
            
            for index_name, ticker in settings.GLOBAL_INDICES.items():
                try:
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            logger.info(f"Collecting {index_name} (attempt {attempt + 1})")
                            import warnings
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore")
                                hist = yf.download(ticker, start=start_date, end=end_date, progress=False, threads=False, auto_adjust=True)
                            
                            if len(hist) >= 2:
                                latest = hist.iloc[-1]
                                previous = hist.iloc[-2]
                                base_date = hist.index[-1]
                                # 데이터 형식 안전하게 처리
                                try:
                                    close_value = latest['Close']
                                    if isinstance(close_value, pd.Series):
                                        close_value = close_value.values[0]
                                    close_value = float(close_value) if not pd.isna(close_value) else 0
                                except Exception as e:
                                    logger.warning(f"{index_name} close_value 변환 실패: {e}")
                                    close_value = 0
                                try:
                                    prev_close = previous['Close']
                                    if isinstance(prev_close, pd.Series):
                                        prev_close = prev_close.values[0]
                                    prev_close = float(prev_close) if not pd.isna(prev_close) else close_value
                                except Exception as e:
                                    logger.warning(f"{index_name} prev_close 변환 실패: {e}")
                                    prev_close = close_value
                                try:
                                    volume = latest['Volume']
                                    if isinstance(volume, pd.Series):
                                        volume = volume.values[0]
                                    volume = float(volume) if not pd.isna(volume) else None
                                except Exception:
                                    volume = None
                                data = {
                                    'index_name': index_name,
                                    'index_code': ticker,
                                    'index_value': close_value,
                                    'change_amount': close_value - prev_close,
                                    'change_rate': calculate_change_rate(close_value, prev_close),
                                    'volume': volume,
                                    'base_date': str(base_date)[:10],
                                    'collected_at': datetime.now()
                                }
                                indices_data.append(data)
                                logger.info(f"Collected {index_name}: {data['index_value']:.2f}")
                                break
                            else:
                                logger.warning(f"Insufficient data for {index_name}: {len(hist)} records")
                                break
                        except Exception as e:
                            logger.warning(f"{index_name} 수집 중 예외 발생: {e}")
                            if attempt < max_retries - 1:
                                logger.warning(f"Attempt {attempt + 1} failed for {index_name}: {e}. Retrying...")
                                time.sleep(5)
                            else:
                                logger.error(f"Error collecting {index_name} after {max_retries} attempts: {e}")
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Error collecting {index_name}: {str(e)}")
            return indices_data
        except Exception as e:
            logger.error(f"Error in collect_global_indices: {str(e)}")
            return []
    
    def save_to_csv(self, data: List[Dict]):
        """CSV 파일로 저장"""
        try:
            if data:
                timestamp = datetime.now().strftime('%Y%m%d')
                save_to_csv(data, f'market_index_data_{timestamp}.csv')
                logger.info(f"Saved {len(data)} market index records to CSV")
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
    
    def collect_all(self):
        """모든 시장 지수 수집"""
        try:
            logger.info("Starting market index collection...")
            
            # 국내 지수 수집
            korea_data = self.collect_korea_indices()
            log_data_collection("korea_indices", len(korea_data))
            
            # 해외 지수 수집
            global_data = self.collect_global_indices()
            log_data_collection("global_indices", len(global_data))
            
            # CSV 파일로 저장
            all_data = korea_data + global_data
            if all_data:
                self.save_to_csv(all_data)
                update_collection_time("market_indices")
            
            logger.info(f"Market index collection completed. Total: {len(all_data)} records")
            
        except Exception as e:
            logger.error(f"Error in collect_all: {str(e)}")

def main():
    """메인 실행 함수"""
    collector = MarketIndexCollector()
    collector.collect_all()

if __name__ == "__main__":
    main() 