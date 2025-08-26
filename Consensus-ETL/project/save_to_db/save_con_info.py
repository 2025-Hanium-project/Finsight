import os
import pymysql
import requests
import shutil
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
    summary = row.get('summary')
    if rationale:
        insert_content = """
        INSERT INTO report_content (
            content_id,
            content_text,
            report_id,
            summary,
            created_at
        ) VALUES (
            UUID(), %s, %s, %s NOW()
        )
        """
        cursor.execute(insert_content, (rationale, report_id))

# # ——————————————————————————
# # 4) CSV 파일 읽어서 일괄 처리
# # ——————————————————————————
# base_dir = os.path.dirname(os.path.abspath(__file__))
# csv_folder = os.path.join(base_dir, '..', 'consensus_parsed')

# for fname in os.listdir(csv_folder):
#     if fname.endswith('bnk_consensus_reports.csv'):
#         df = pd.read_csv(os.path.join(csv_folder, fname))
#         for _, raw in df.iterrows():
#             # NaN → None
#             row = raw.where(pd.notnull(raw), None).to_dict()
#             stock_id = get_stock_id(str(row.get('stock_code')), str(row.get('stock_name')))
#             if stock_id:
#                 insert_report(row, stock_id)
#             else:
#                 print(f"[경고] Stock_id not found for {row.get('stock_code')} / {row.get('stock_name')}")


# llm api로 요청을 보내서 응답을 저장하는 것으로 대체
API_URL = "http://localhost:38000/workflow"
base_dir = os.path.dirname(os.path.abspath(__file__)) 
# 상위 폴더의 'Consensus-ETL/project/consensus' 경로
pdf_root_path = os.path.abspath(os.path.join(base_dir, '..', 'consensus'))
con_deleted_dir = os.path.join(pdf_root_path, '..','con_deleted')
os.makedirs(con_deleted_dir, exist_ok=True)

print(f"PDF 탐색 시작 경로: {pdf_root_path}")

except_list = ['fnguide','wisereport']

# pdf_root_path 하위의 모든 폴더와 파일을 순회
for root, dirs, files in os.walk(pdf_root_path):
    dirs[:] = [d for d in dirs if d not in except_list]
    for filename in files:
        if filename.lower().endswith('.pdf') or filename.lower().endswith('.png'):
            # API에 전달할 PDF 파일의 절대 경로
            pdf_abs_path = os.path.join(root, filename).replace('\\', '/')
            print(f"처리 중인 파일: {pdf_abs_path}")

            # API 요청 페이로드
            api_payload = {
                "request_type": "consensus",
                "file_path": pdf_abs_path
            }
            
            try:
                # LLM API에 POST 요청 보내기
                response = requests.post(API_URL, json=api_payload)

                # 요청 성공 시 (상태 코드 200)
                if response.status_code == 200:
                    # 응답 JSON을 바로 데이터로 사용
                    parsed_data = response.json()
                    print(parsed_data) # 파싱된 데이터 확인용 출력
                    
                    # Stock_id 조회
                    stock_id = get_stock_id(str(parsed_data.get('stock_code')), str(parsed_data.get('stock_name')))
                    
                    if stock_id:
                        # DB에 리포트 정보 삽입
                        insert_report(parsed_data, stock_id)
                        print(f"  [성공] DB 저장 완료: {parsed_data.get('report_title')}")
                        conn.commit()
                    else:
                        print(f"  [경고] Stock_id를 찾을 수 없습니다: {parsed_data.get('stock_code')} / {parsed_data.get('stock_name')}")
                     # 파일 이동 (처리 성공 시)
                    dest_path = os.path.join(con_deleted_dir, filename)
                    shutil.move(os.path.join(root, filename), dest_path)
                    print(f"  [파일 이동] {filename} → {dest_path}")
                else:
                    print(f"  [오류] API 요청 실패 (상태 코드: {response.status_code}): {response.text}")
            
            except requests.exceptions.RequestException as e:
                print(f"  [오류] API 연결 실패: {e}")


print("모든 파일 처리 완료. DB에 최종 커밋합니다.")
# ——————————————————————————
# 5) 종료
# ——————————————————————————
cursor.close()
conn.close()
