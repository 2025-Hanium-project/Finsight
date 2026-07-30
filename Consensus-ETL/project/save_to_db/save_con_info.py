import os
import sys
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
    # report 테이블 관련 코드는 삭제됨. report_metadata와 report_content만 사용
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
            UUID(), %s, %s, %s, NOW()
        )
        """
        cursor.execute(insert_content, (rationale, report_id, summary))

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
con_deleted_dir = os.path.join(pdf_root_path, '..', 'con_deleted')
con_error_dir = os.path.join(pdf_root_path, '..', 'con_error')
os.makedirs(con_deleted_dir, exist_ok=True)
os.makedirs(con_error_dir, exist_ok=True)

print(f"PDF 탐색 시작 경로: {pdf_root_path}")

except_list = ['fnguide','wisereport', 'miraeasset_consensus', 'miraeasset']

# 종료 코드 판정용 집계
success_count = 0
error_count = 0

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
                        success_count += 1
                        # 파일 이동 (처리 성공 시)
                        dest_path = os.path.join(con_deleted_dir, filename)
                        shutil.move(os.path.join(root, filename), dest_path)
                        print(f"  [파일 이동] {filename} → {dest_path}")
                    else:
                        print(f"  [경고] Stock_id를 찾을 수 없습니다: {parsed_data.get('stock_code')} / {parsed_data.get('stock_name')}")
                        # 파일 이동 (추출 실패 시)
                        dest_path = os.path.join(con_error_dir, filename)
                        shutil.move(os.path.join(root, filename), dest_path)
                        print(f"  [에러 파일 이동] {filename} → {dest_path}")
                        error_count += 1
                else:
                    print(f"  [오류] API 요청 실패 (상태 코드: {response.status_code}): {response.text}")
                    # 파일 이동 (API 요청 실패 시)
                    dest_path = os.path.join(con_error_dir, filename)
                    shutil.move(os.path.join(root, filename), dest_path)
                    print(f"  [에러 파일 이동] {filename} → {dest_path}")
                    error_count += 1

            except requests.exceptions.RequestException as e:
                # 연결 자체가 안 되는 것은 파일 문제가 아니라 API 장애다.
                # 여기서 con_error로 옮기면 API가 몇 분 죽은 사이 그날 수집분 전체가
                # 재처리 대상에서 사라진다. 파일은 그대로 두고 실패만 알린다.
                print(f"  [오류] API 연결 실패 (파일 유지): {e}")
                error_count += 1
                continue


print(f"모든 파일 처리 완료. 성공 {success_count}건, 실패 {error_count}건.")

# 조용히 성공하지 않는다. 처리 실패가 있으면 Airflow에 실패로 알린다.
# 성공 0건 자체는 실패로 보지 않는다. 처리된 파일은 con_deleted로 빠지므로
# 신규 리포트가 없는 날 0건은 정상이다 (크롤 단계와 판정 기준이 다르다).
if error_count:
    print(f"{error_count}건 처리에 실패했습니다.", file=sys.stderr)
    cursor.close()
    conn.close()
    sys.exit(1)
# ——————————————————————————
# 5) 종료
# ——————————————————————————
cursor.close()
conn.close()
