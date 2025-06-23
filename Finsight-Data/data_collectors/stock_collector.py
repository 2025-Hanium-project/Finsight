import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pykrx import stock
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from utils.helpers import (
    logger, get_trading_date, validate_stock_code
)
from config.settings import settings

class StockCollector:
    """개별 종목 정보 수집기"""
    def __init__(self):
        pass

    def collect_stock_basic_data(self, stock_codes: List[str] = None, all_kospi: bool = False) -> List[Dict]:
        """종목 기본 데이터 수집"""
        try:
            if stock_codes is None:
                stock_codes = self._get_all_kospi_stocks() if all_kospi else self._get_top_stocks()
            stock_data = []
            trading_date = get_trading_date()
            prev_date = (datetime.strptime(trading_date, '%Y%m%d') - timedelta(days=5)).strftime('%Y%m%d')
            for stock_code in stock_codes:
                try:
                    df = stock.get_market_ohlcv(fromdate=prev_date, todate=trading_date, ticker=stock_code)
                    if not df.empty and len(df) >= 2:
                        df = df.sort_index()
                        latest = df.iloc[-1]
                        previous = df.iloc[-2]
                        close_col = '종가' if '종가' in latest else 'CLSPRC'
                        change_rate_col = '등락률' if '등락률' in latest else 'CHG_RATE'
                        volume_col = '거래량' if '거래량' in latest else 'ACC_TRDVOL'
                        stock_name = self._get_stock_name(stock_code)
                        market_cap = self._get_market_cap(stock_code, trading_date)
                        current_price = float(latest[close_col])
                        prev_price = float(previous[close_col])
                        change_amount = current_price - prev_price
                        data = {
                            'stock_code': stock_code.zfill(6),
                            'stock_name': stock_name,
                            'open_price': float(latest['시가']) if '시가' in latest else None,
                            'high_price': float(latest['고가']) if '고가' in latest else None,
                            'low_price': float(latest['저가']) if '저가' in latest else None,
                            'close_price': current_price,
                            'volume': int(latest[volume_col]) if volume_col in latest else 0,
                            'change_amount': change_amount,
                            'change_rate': float(latest[change_rate_col]) if change_rate_col in latest else 0.0,
                            'market_cap': market_cap,
                            'base_date': datetime.strptime(trading_date, '%Y%m%d').strftime('%Y-%m-%d'),
                            'collected_at': datetime.now()
                        }
                        stock_data.append(data)
                        logger.info(f"Collected {stock_name}({stock_code}): {data['close_price']:,.0f} ({change_amount:+,.0f})")
                    else:
                        logger.warning(f"No data available for stock {stock_code}")
                except Exception as e:
                    logger.error(f"Error collecting stock {stock_code}: {e}", exc_info=False)
                    continue
            return stock_data
        except Exception as e:
            logger.error(f"Error in collect_stock_basic_data: {e}", exc_info=True)
            return []

    def _get_top_stocks(self, top_n: int = 20) -> List[str]:
        try:
            trading_date = get_trading_date()
            try:
                df_kospi = stock.get_market_cap_by_ticker(trading_date, market='KOSPI')
                df_kospi_sorted = df_kospi.sort_values(by="시가총액", ascending=False)
                return df_kospi_sorted.head(top_n).index.tolist()
            except Exception as e:
                logger.warning(f"Error getting KOSPI market cap data, using fallback: {e}")
                return [
                    '005930', '000660', '207940', '373220', '012450',
                    '005380', '035420', '105560', '005935', '329180',
                    '000270', '034020', '068270', '035720', '055550',
                    '028260', '042660', '012330', '009540', '032830'
                ]
        except Exception as e:
            logger.error(f"Error getting top KOSPI stocks: {e}")
            return [
                '005930', '000660', '207940', '373220', '012450',
                '005380', '035420', '105560', '005935', '329180',
                '000270', '034020', '068270', '035720', '055550',
                '028260', '042660', '012330', '009540', '032830'
            ]

    def _get_stock_name(self, stock_code: str) -> str:
        try:
            return stock.get_market_ticker_name(stock_code)
        except Exception as e:
            logger.error(f"Error getting stock name for {stock_code}: {str(e)}")
            return stock_code

    def _get_market_cap(self, stock_code: str, trading_date: str) -> Optional[float]:
        try:
            market_cap_data = stock.get_market_cap(trading_date)
            if stock_code in market_cap_data.index:
                return float(market_cap_data.loc[stock_code, '시가총액'])
            return None
        except Exception as e:
            logger.error(f"Error getting market cap for {stock_code}: {str(e)}")
            return None

    def save_to_csv(self, stock_data: List[Dict]):
        try:
            if stock_data:
                timestamp = datetime.now().strftime('%Y%m%d')
                filename = f'stock_data_{timestamp}.csv'
                df = pd.DataFrame(stock_data)
                df['stock_code'] = df['stock_code'].astype(str)
                filepath = os.path.join(settings.DATA_DIR, filename)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                logger.info(f"종목 데이터 저장 완료: {len(stock_data)}개 레코드 → {filename}")
        except Exception as e:
            logger.error(f"CSV 저장 중 오류 발생: {str(e)}")

    def collect_all(self, all_kospi: bool = False):
        try:
            logger.info("Starting stock data collection...")
            stock_data = self.collect_stock_basic_data(all_kospi=all_kospi)
            if stock_data:
                self.save_to_csv(stock_data)
            logger.info(f"Stock data collection completed. Stocks: {len(stock_data)}")
        except Exception as e:
            logger.error(f"Error in collect_all: {str(e)}")

    def _get_all_kospi_stocks(self) -> List[str]:
        try:
            trading_date = get_trading_date()
            df_kospi = stock.get_market_cap_by_ticker(trading_date, market='KOSPI')
            df_kospi_sorted = df_kospi.sort_values(by="시가총액", ascending=False)
            return df_kospi_sorted.index.tolist()
        except Exception as e:
            logger.error(f"Error getting all KOSPI stocks: {e}")
            return self._get_top_stocks()

def main():
    try:
        collector = StockCollector()
        all_kospi = False
        collector.collect_all(all_kospi=all_kospi)
        print(f"종목 데이터 수집 완료 (KOSPI {'전체' if all_kospi else '상위 20개'})")
    except Exception as e:
        print(f"오류 발생: {str(e)}")

if __name__ == "__main__":
    main() 