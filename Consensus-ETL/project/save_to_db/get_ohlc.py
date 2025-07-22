from pykrx import stock
import datetime
import pandas as pd

today = datetime.datetime.today().strftime("%Y%m%d")
# 코스피 티커 리스트
kospi_codes = stock.get_market_ticker_list(market="KOSPI")
# 코스닥 티커 리스트
kosdaq_codes = stock.get_market_ticker_list(market="KOSDAQ")

def get_ohlc_and_marketcap_df(codes, date, market):
    dfs = []
    cap_df = stock.get_market_cap_by_date(date, date, market=market)
    for code in codes:
        df = stock.get_market_ohlcv_by_date(date, date, code)
        if not df.empty:
            df['종목코드'] = code
            if code in cap_df.index:
                df['시가총액'] = cap_df.loc[code, '시가총액']
            else:
                df['시가총액'] = None
            dfs.append(df)
    if dfs:
        return pd.concat(dfs)
    else:
        return pd.DataFrame()

df_kospi = get_ohlc_and_marketcap_df(kospi_codes, today, market="KOSPI")
df_kosdaq = get_ohlc_and_marketcap_df(kosdaq_codes, today, market="KOSDAQ")
print(df_kospi)
print(df_kosdaq)