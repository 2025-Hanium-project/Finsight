import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.helpers import (
    logger, get_trading_date,
    log_data_collection, update_collection_time, save_to_csv,
    calculate_change_rate
)
from config.settings import settings

class SectorTrendCollector:
    """섹터별 동향 수집기 (KRX 업종 지수 기반)"""
    
    def __init__(self):
        # KRX 업종 지수 목록
        self.sector_indices = {
            '자동차': '5043',
            '반도체': '5044',
            '헬스케어': '5045',
            '은행': '5046',
            '에너지화학': '5048',
            '철강': '5049',
            '방송통신': '5051',
            '건설': '5052',
            '증권': '5054',
            '기계장비': '5055',
            '보험': '5056',
            '운송': '5057',
            '경기소비재': '5061',
            '필수소비재': '5062',
            '미디어&엔터테인먼트': '5063',
            '정보기술': '5064',
            '유틸리티': '5065'
        }

    def collect_sector_trends(self) -> List[Dict]:
        """KRX 업종 지수별 동향 수집"""
        try:
            trends_data = []
            trading_date = get_trading_date()
            
            # 더 넓은 기간으로 데이터 조회 (최근 7일)
            end_date = trading_date
            start_date = (datetime.strptime(trading_date, '%Y%m%d') - timedelta(days=7)).strftime('%Y%m%d')

            logger.info(f"수집 시작 - 기간: {start_date}~{end_date}")
            
            for sector_name, ticker_code in self.sector_indices.items():
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        df_ohlcv = stock.get_index_ohlcv_by_date(
                            fromdate=start_date,
                            todate=end_date,
                            ticker=ticker_code
                        )
                        
                        if not df_ohlcv.empty and len(df_ohlcv) >= 2:
                            df_ohlcv = df_ohlcv.sort_index()
                            latest = df_ohlcv.iloc[-1]
                            previous = df_ohlcv.iloc[-2]
                            
                            return_rate = calculate_change_rate(latest['종가'], previous['종가'])
                            volume_change = calculate_change_rate(latest['거래량'], previous['거래량'])
                            
                            sector_data = {
                                'sector_name': sector_name,
                                'date': datetime.strptime(trading_date, '%Y%m%d').strftime('%Y-%m-%d'),
                                'open': latest['시가'],
                                'high': latest['고가'],
                                'low': latest['저가'],
                                'close': latest['종가'],
                                'volume': latest['거래량'],
                                'return_rate': return_rate if return_rate is not None else 0.0,
                                'volume_change': volume_change if volume_change is not None else 0.0,
                                'collected_at': datetime.now()
                            }
                            trends_data.append(sector_data)
                            logger.info(f"'{sector_name}' 지수 수집 완료: 종가={sector_data['close']}, 수익률={sector_data['return_rate']:.2f}%")
                            break  # 성공하면 재시도 중단
                        else:
                            logger.warning(f"'{sector_name}' 지수({ticker_code})의 OHLCV 데이터를 가져올 수 없습니다. (기간: {start_date}~{end_date})")
                            break

                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"'{sector_name}' 지수({ticker_code}) 처리 중 오류 발생 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                            import time
                            time.sleep(1)  # 1초 대기 후 재시도
                        else:
                            logger.error(f"'{sector_name}' 지수({ticker_code}) 처리 중 최종 오류 발생: {str(e)}")
                            continue
            
            return trends_data
        except Exception as e:
            logger.error(f"collect_sector_trends 중 오류 발생: {str(e)}")
            return []
    
    def save_to_csv(self, data: List[Dict]):
        """CSV 파일로 저장"""
        try:
            if data:
                timestamp = datetime.now().strftime('%Y%m%d')
                save_to_csv(data, f'sector_trend_data_{timestamp}.csv')
                logger.info(f"Saved {len(data)} sector trend records to CSV")
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
    
    def collect_all(self):
        """섹터별 동향 수집 및 저장"""
        try:
            logger.info("Starting sector trend collection...")
            
            # 섹터별 동향 수집
            sector_data = self.collect_sector_trends()
            log_data_collection("sector_trends", len(sector_data))
            
            # CSV 파일로 저장
            if sector_data:
                self.save_to_csv(sector_data)
                update_collection_time("sector_trends")
            
            logger.info(f"Sector trend collection completed. Total: {len(sector_data)} records")
            
        except Exception as e:
            logger.error(f"Error in collect_all: {str(e)}")

def main():
    """메인 실행 함수"""
    collector = SectorTrendCollector()
    collector.collect_all()

if __name__ == "__main__":
    main() 