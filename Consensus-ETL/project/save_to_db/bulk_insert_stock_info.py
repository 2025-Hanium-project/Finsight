from pykrx import stock
import pymysql
import pandas as pd

# 1. 종목 코드와 이름 수집
kospi_codes = stock.get_market_ticker_list(market="KOSPI")
kosdaq_codes = stock.get_market_ticker_list(market="KOSDAQ")
all_codes = kospi_codes + kosdaq_codes

stock_list = []
for code in all_codes:
    name = stock.get_market_ticker_name(code)
    stock_list.append((code, name))

# 2. DB 연결 설정
conn = pymysql.connect(
    host='finsight.kro.kr',
    port=32503,
    user='etluser',
    password='data123!',
    db='finsight_database',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)
cursor = conn.cursor()

# 3. Bulk Insert
insert_sql = """
    INSERT INTO Stock (stock_code, stock_name)
    VALUES (%s, %s)
    ON DUPLICATE KEY UPDATE stock_name = VALUES(stock_name)
"""

try:
    cursor.executemany(insert_sql, stock_list)
    conn.commit()
    print(f"{cursor.rowcount} rows inserted/updated.")
except Exception as e:
    print("Error:", e)
    conn.rollback()
finally:
    cursor.close()
    conn.close()
