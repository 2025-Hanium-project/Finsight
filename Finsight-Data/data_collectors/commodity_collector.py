import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
from utils.helpers import (
    logger, calculate_change_rate, make_api_request,
    log_data_collection, update_collection_time, save_to_csv
)
from config.settings import settings

class CommodityCollector:
    """원자재 가격 수집기 (Yahoo Finance 기반)"""
    
    def __init__(self):
        pass
    
    def collect_yahoo_commodities(self) -> List[Dict]:
        """Yahoo Finance를 통한 원자재 가격 수집"""
        try:
            commodities_data = []
            
            # 주요 원자재 티커
            commodity_tickers = {
                'WTI_원유': 'CL=F',
                '브렌트_원유': 'BZ=F',
                '금': 'GC=F',
                '은': 'SI=F',
                '구리': 'HG=F',
                '천연가스': 'NG=F',
                '옥수수': 'ZC=F',
                '대두': 'ZS=F',
                '밀': 'ZW=F',
            }
            
            for commodity_name, ticker in commodity_tickers.items():
                try:
                    commodity = yf.Ticker(ticker)
                    hist = commodity.history(period="5d")
                    
                    if not hist.empty and len(hist) >= 2:
                        hist = hist.dropna()
                        if not hist.empty and len(hist) >= 2:
                            latest = hist.iloc[-1]
                            previous = hist.iloc[-2]
                            
                            data = {
                                'commodity_name': commodity_name,
                                'price': float(latest['Close']),
                                'change_rate': calculate_change_rate(latest['Close'], previous['Close']),
                                'date': latest.name,
                                'collected_at': datetime.now()
                            }
                            
                            commodities_data.append(data)
                            logger.info(f"Collected {commodity_name}: ${data['price']:.2f}")
                    else:
                        logger.warning(f"No data for {commodity_name} ({ticker})")

                    time.sleep(0.5)
                        
                except Exception as e:
                    logger.error(f"Error collecting {commodity_name}: {str(e)}")
                    continue
            
            return commodities_data
            
        except Exception as e:
            logger.error(f"Error in collect_yahoo_commodities: {str(e)}")
            return []
    
    def save_to_csv(self, data: List[Dict]):
        """CSV 파일로 저장"""
        try:
            if data:
                timestamp = datetime.now().strftime('%Y%m%d')
                save_to_csv(data, f'commodity_price_data_{timestamp}.csv')
                logger.info(f"Saved {len(data)} commodity price records to CSV")
        except Exception as e:
            logger.error(f"Error saving data to CSV: {str(e)}")

    def collect_all(self):
        """모든 원자재 가격 수집"""
        try:
            logger.info("Starting commodity price collection...")
            
            # Yahoo Finance 원자재 수집
            yahoo_data = self.collect_yahoo_commodities()
            log_data_collection("yahoo_commodities", len(yahoo_data))
            
            # CSV에 저장
            if yahoo_data:
                self.save_to_csv(yahoo_data)
                update_collection_time("commodity_prices")
            
            logger.info(f"Commodity price collection completed. Total: {len(yahoo_data)} records")
        except Exception as e:
            logger.error(f"Error in collect_all: {str(e)}")

def main():
    """메인 실행 함수"""
    collector = CommodityCollector()
    collector.collect_all()

if __name__ == "__main__":
    main() 