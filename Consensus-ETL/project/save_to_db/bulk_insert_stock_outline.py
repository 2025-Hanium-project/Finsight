import pymysql
import requests
from bs4 import BeautifulSoup

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

def get_company_summary(stock_code: str):
    url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    summary_div = soup.find("div", id="summary_info")
    if not summary_div:
        return None

    paragraphs = [p.get_text(strip=True) for p in summary_div.find_all("p")]

    
    return paragraphs

def upsert_stock_profile(stock_id: str, overview: str):
    sql = ''''
        INSERT INTO stock_profile (Stock_id, overview)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            overview = VALUES(overview),
            updated_at = CURRENT_TIMESTAMP
    '''
    cursor.execute(sql, (stock_id, overview))