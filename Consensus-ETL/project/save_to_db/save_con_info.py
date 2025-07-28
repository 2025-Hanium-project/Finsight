import os
import pandas as pd
import pymysql

# ——————————————————————————
# 1) DB 연결 설정
# ——————————————————————————
conn = pymysql.connect(
    host='finsight.kro.kr',
    port=32503,
    user='etluser',
    password='data123!',
    db='finsight_database',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor  # dict 형태로 fetch
)
cursor = conn.cursor()

# ——————————————————————————
# 2) 종목 ID 조회 함수
# ——————————————————————————
def get_stock_id(stock_code, stock_name):
    # ① stock_code 우선
    sql = "SELECT Stock_id FROM Stock WHERE stock_code = %s"
    cursor.execute(sql, (stock_code,))
    row = cursor.fetchone()
    if row:
        return row['Stock_id']
    # ② 없으면 stock_name
    sql = "SELECT Stock_id FROM Stock WHERE stock_name = %s"
    cursor.execute(sql, (stock_name,))
    row = cursor.fetchone()
    return row['Stock_id'] if row else None

# ——————————————————————————
# 3) 리포트 삽입 함수 (RETURNING 사용)
# ——————————————————————————
def insert_report(row, stock_id):
    # 1) report_metadata INSERT & report_id RETURNING
    insert_sql = """
    INSERT INTO report_metadata (
        report_title,
        report_date,
        report_type,
        analyst_name,
        company_name,
        rating,
        opinion_change,
        target_price,
        target_price_change,
        Stock_id,
        created_at
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
    )
    RETURNING report_id
    """
    cursor.execute(insert_sql, (
        row['report_title'],
        row['report_date'],
        row.get('report_type', '일반'),
        row.get('analyst_name'),
        row.get('company_name'),
        row.get('rating'),
        row.get('opinion_change'),
        row.get('target_price'),
        row.get('target_price_change'),
        stock_id
    ))
    # 생성된 report_id 받아오기
    report_id = cursor.fetchone()['report_id']

    # 2) report_content INSERT
    rationale = row.get('investment_rationale')
    if rationale:
        insert_content = """
        INSERT INTO report_content (
            content_id,
            content_text,
            report_id,
            created_at
        ) VALUES (
            UUID(), %s, %s, NOW()
        )
        """
        cursor.execute(insert_content, (rationale, report_id))

# ——————————————————————————
# 4) CSV 파일 읽어서 일괄 처리
# ——————————————————————————
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_folder = os.path.join(base_dir, '..', 'consensus_parsed')

for fname in os.listdir(csv_folder):
    if fname.endswith('bnk_consensus_reports.csv'):
        df = pd.read_csv(os.path.join(csv_folder, fname))
        for _, raw in df.iterrows():
            # NaN → None
            row = raw.where(pd.notnull(raw), None).to_dict()
            stock_id = get_stock_id(str(row.get('stock_code')), str(row.get('stock_name')))
            if stock_id:
                insert_report(row, stock_id)
            else:
                print(f"[경고] Stock_id not found for {row.get('stock_code')} / {row.get('stock_name')}")

# ——————————————————————————
# 5) 커밋 & 종료
# ——————————————————————————
conn.commit()
cursor.close()
conn.close()
print("DB 저장 완료")
