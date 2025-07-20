from pykrx import stock
import pandas as pd
import pymysql
import uuid

# DB 연결 정보
conn = pymysql.connect(
    host='30.0.0.33',
    user='etluser',
    password='data123!',
    db='finsight_database',
    charset='utf8'
)
cursor = conn.cursor()

def insert_stock(stock_code, stock_name):
    sql = """
    INSERT INTO Stock (stock_code, stock_name)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE stock_name=VALUES(stock_name)
    """
    cursor.execute(sql, (stock_code, stock_name))

# 코스피/코스닥 종목 코드와 이름 insert
for market, market_name in [("KOSPI", "코스피"), ("KOSDAQ", "코스닥")]:
    codes = stock.get_market_ticker_list(market=market)
    for code in codes:
        name = stock.get_market_ticker_name(code)
        insert_stock(code, name)

conn.commit()
cursor.close()
conn.close()
print("Insert 완료")