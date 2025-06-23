import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, List
from utils.helpers import (
    logger, calculate_change_rate, save_to_csv
)

class ExchangeRateCollector:
    """환율 정보 수집기 (Yahoo Finance 전용)"""
    
    def __init__(self):
        # 주요 통화 페어 설정
        self.currencies = {
            'USD/KRW': 'KRW=X',      # 달러/원
            'EUR/KRW': 'EURKRW=X',   # 유로/원
            'JPY/KRW': 'JPYKRW=X',   # 엔/원
            'EUR/USD': 'EURUSD=X',   # 유로/달러
            'USD/JPY': 'USDJPY=X',   # 달러/엔
            'GBP/USD': 'GBPUSD=X',   # 파운드/달러
            'USD/CNY': 'USDCNY=X'    # 달러/위안
        }
    
    def collect_exchange_rates(self) -> List[Dict]:
        """Yahoo Finance를 통한 환율 수집"""
        try:
            rates_data = []
            
            for currency_name, ticker in self.currencies.items():
                try:
                    # yfinance를 사용하여 환율 정보 수집
                    ticker_obj = yf.Ticker(ticker)
                    hist = ticker_obj.history(period="5d", timeout=30)
                    
                    if len(hist) >= 1:
                        latest = hist.iloc[-1]
                        
                        # 안전한 float 변환
                        try:
                            current_rate = float(latest['Close'])
                        except (ValueError, TypeError):
                            logger.warning(f"Invalid rate data for {currency_name}")
                            continue
                        
                        # 변화량 계산 (데이터가 2개 이상인 경우)
                        if len(hist) >= 2:
                            previous = hist.iloc[-2]
                            try:
                                previous_rate = float(previous['Close'])
                                change_amount = current_rate - previous_rate
                                change_rate = calculate_change_rate(current_rate, previous_rate)
                            except (ValueError, TypeError):
                                change_amount = 0.0
                                change_rate = 0.0
                        else:
                            change_amount = 0.0
                            change_rate = 0.0
                        
                        data = {
                            'currency_pair': currency_name,
                            'rate': current_rate,
                            'change_amount': change_amount,
                            'change_rate': change_rate if change_rate is not None else 0.0,
                            'base_date': latest.name.strftime('%Y-%m-%d'),
                            'collected_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        rates_data.append(data)
                        logger.info(f"Collected {currency_name}: {current_rate:.4f}")
                    else:
                        logger.warning(f"No data available for {currency_name}")
                        
                except Exception as e:
                    logger.error(f"Error collecting {currency_name}: {str(e)}")
                    continue
            
            return rates_data
            
        except Exception as e:
            logger.error(f"Error in collect_exchange_rates: {str(e)}")
            return []
    
    def save_to_csv(self, data: List[Dict]) -> str:
        """CSV 파일에 저장"""
        try:
            if data:
                timestamp = datetime.now().strftime('%Y%m%d')
                filename = f'exchange_rate_data_{timestamp}.csv'
                save_to_csv(data, filename)
                logger.info(f"Saved {len(data)} exchange rate records to {filename}")
                return filename
            else:
                logger.warning("No exchange rate data to save")
                return None
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
            return None
    
    def collect_all(self) -> str:
        """환율 정보 수집 및 저장"""
        try:
            logger.info("Starting exchange rate collection...")
            
            # Yahoo Finance에서 환율 수집
            rates_data = self.collect_exchange_rates()
            
            if rates_data:
                # CSV 파일로 저장
                filename = self.save_to_csv(rates_data)
                logger.info(f"Exchange rate collection completed. Total records: {len(rates_data)}")
                return filename
            else:
                logger.warning("No exchange rate data collected")
                return None
                
        except Exception as e:
            logger.error(f"Error in collect_all: {str(e)}")
            return None

def main():
    """메인 실행 함수"""
    try:
        collector = ExchangeRateCollector()
        filename = collector.collect_all()
        
        if filename:
            print(f"환율 데이터 수집 완료: {filename}")
        else:
            print("환율 데이터 수집 실패")
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    main() 