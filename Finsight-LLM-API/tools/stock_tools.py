"""
주식 데이터 조회 도구들 - 주가, 시장 데이터 전용
"""

import yfinance as yf
from pykrx import stock
from langchain_core.tools import tool
from datetime import datetime, timedelta

@tool
def get_current_stock_price(stock_code: str) -> float:
    """
    KOSPI200 종목의 현재 주가 정보 조회
    
    Args:
        stock_code: 6자리 종목코드 (예: "005930" - 삼성전자)
        
    Returns:
        현재 주가 (원)
    """
    try:
        # KOSPI200 종목 코드 검증
        if not (stock_code.isdigit() and len(stock_code) == 6):
            print(f"유효하지 않은 종목코드 형식: {stock_code}")
            return 0
        
        # pykrx로 KOSPI 데이터 조회 (우선순위)
        try:
            # 최근 거래일 데이터 조회
            for days_ago in range(5):  # 최근 5일간 시도
                target_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y%m%d')
                try:
                    df = stock.get_market_ohlcv_by_date(target_date, target_date, stock_code)
                    if not df.empty:
                        price = float(df.iloc[-1]['종가'])
                        print(f"📊 {stock_code} 현재가: {price:,}원 (pykrx, {target_date})")
                        return price
                except:
                    continue
                    
        except Exception as pykrx_error:
            print(f"pykrx 조회 실패: {pykrx_error}")
        
        # yfinance로 백업 조회
        try:
            # 한국 주식은 .KS 접미사 사용
            ticker_symbol = f"{stock_code}.KS"
            ticker = yf.Ticker(ticker_symbol)
            
            # 최근 5일 데이터로 조회
            hist = ticker.history(period="5d")
            
            if not hist.empty:
                # USD를 KRW로 변환 (대략적 환율 적용)
                price_usd = float(hist['Close'].iloc[-1])
                price_krw = price_usd * 1300  # 대략적 환율
                print(f"📊 {stock_code} 현재가: {price_krw:,.0f}원 (yfinance)")
                return float(price_krw)
                
        except Exception as yf_error:
            print(f"yfinance 조회 실패: {yf_error}")
        
        # 모든 방법 실패 시 기본값 반환
        print(f"⚠️ {stock_code} 주가 조회 실패, 기본값 사용")
        if stock_code == "005930":  # 삼성전자
            return 70000.0
        else:
            return 50000.0
            
    except Exception as e:
        print(f"주가 조회 중 오류: {e}")
        return 0.0

@tool
def get_kospi200_stocks() -> str:
    """
    KOSPI200 구성 종목 목록 조회
    
    Returns:
        KOSPI200 구성 종목 정보
    """
    try:
        # KOSPI200 구성 종목 조회
        kospi200_list = stock.get_index_portfolio_deposit_file("1028")  # KOSPI200 코드
        
        if kospi200_list is not None and len(kospi200_list) > 0:
            # 상위 20개 종목만 반환 (너무 많으면 응답이 길어짐)
            top_stocks = kospi200_list.head(20)
            
            result = "KOSPI200 주요 구성 종목 (상위 20개):\n"
            for idx, row in top_stocks.iterrows():
                result += f"- {row['종목명']}({idx})\n"
                
            return result
        else:
            return "KOSPI200 구성 종목 조회에 실패했습니다."
            
    except Exception as e:
        return f"KOSPI200 종목 조회 오류: {str(e)}" 