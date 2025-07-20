import pandas as pd
import pymysql
import os
import numpy as np

# DB 연결 정보
conn = pymysql.connect(
    host='30.0.0.33',
    user='etluser',
    password='data123!',
    db='finsight_database',
    charset='utf8'
)
cursor = conn.cursor()

def get_stock_id(stock_code, stock_name):
    # stock_code 우선, 없으면 stock_name으로 조회
    sql = "SELECT Stock_id FROM Stock WHERE stock_code = %s"
    cursor.execute(sql, (stock_code,))
    result = cursor.fetchone()
    if result:
        return result[0]
    sql = "SELECT Stock_id FROM Stock WHERE stock_name = %s"
    cursor.execute(sql, (stock_name,))
    result = cursor.fetchone()
    return result[0] if result else None

def insert_report(row, stock_id):
    sql = """
    INSERT INTO report_metadata (
        report_title, report_date, report_type, analyst_name, company_name,
        rating, opinion_change, target_price, current_price, created_at, Stock_id
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s
    )
    """
    cursor.execute(sql, (
        row['report_title'],
        row['report_date'],
        row.get('report_type', '일반'),  # 기본값 예시
        row.get('analyst_name', None),
        row.get('company_name', None),
        row.get('rating', None)[:10] if row.get('rating', None) else None,
        row.get('opinion_change', None),
        row.get('target_price', None),
        row.get('current_price', None),
        stock_id
    ))

    # report_id(PK) 가져오기 (방금 insert한 row)
    cursor.execute("SELECT LAST_INSERT_ID()")
    report_id_row = cursor.fetchone()
    if report_id_row:
        report_id = report_id_row[0]
        # report_content에 investment_rationale 저장
        if 'investment_rationale' in row and row['investment_rationale']:
            sql2 = """
            INSERT INTO report_content (content_id, content_text, report_id, created_at)
            VALUES (UUID(), %s, %s, NOW())
            """
            cursor.execute(sql2, (row['investment_rationale'], report_id))

# consensus_parsed 폴더 내 모든 csv 파일 처리
csv_folder = '/home/etluser/Finsight-service/Consensus-ETL/project/consensus_parsed'
for fname in os.listdir(csv_folder):
    if fname.endswith('bnk_consensus_reports.csv'):
        df = pd.read_csv(os.path.join(csv_folder, fname))
        for _, row in df.iterrows():
            # NaN을 None으로 변환
            row = row.where(pd.notnull(row), None)
            stock_id = get_stock_id(str(row['stock_code']), str(row['stock_name']))
            if stock_id:
                insert_report(row, stock_id)
            else:
                print(f"Stock_id not found for {row['stock_code']} / {row['stock_name']}")

conn.commit()
cursor.close()
conn.close()
print("DB 저장 완료")