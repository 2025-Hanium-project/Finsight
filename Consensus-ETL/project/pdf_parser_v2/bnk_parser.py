from utils import read_files, extract_all_info


import re
import pymysql
import csv
from pathlib import Path


# 생각해보니 종목코드나 종목명 하나만 추출하면 된다. 어차피 stock table에 있는 두 정보로 stock_id를 알아내서 FK로
# report_metadata table에 저장하기 때문에.
def get_code_by_name_from_db(stock_name):
    """
    DB에서 종목명으로 종목코드 조회
    """
    conn = pymysql.connect(
        host='finsight.kro.kr',
        port=32503,
        user='etluser',
        password='data123!',
        db='finsight_database',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            sql = "SELECT stock_code FROM Stock WHERE REPLACE(stock_name, ' ', '') = %s"
            cursor.execute(sql, (stock_name.replace(" ", ""),))
            result = cursor.fetchone()
            if result:
                return result['stock_code']
    finally:
        conn.close()
    return None


def extract_content(info):
    """
    '자료:'로 시작하는 줄이 나오기 전까지의 텍스트만 반환
    """
    lines = info.splitlines()
    result_lines = []
    for line in lines:
        if line.strip().startswith('자료:'):
            break
        result_lines.append(line)
    return '\n'.join(result_lines)



def extract_stock_name_and_code(info):
    pattern_code = r"^##\s*(.+?)\s*\((\d{6})\)"
    pattern_jaryo = r"자료:\s*([^,]+),"
    pattern_title = r"^##\s*(.+)"
    pattern_date = r"\d{4}/\d{1,2}/\d{1,2}"
    pattern_analyst = r"^##\s*([가-힣]{2,3})$"
    pattern_rating = r"\|\s*투자의견\s*\[([^\]]+)\]\s*\|\s*([가-힣]+)"
    pattern_target = r"목표주가.*\[\s*([가-힣]+)\s*\].*\|\s*([\d,]+)원\s+([\d\.]+)%"


    stock_name = stock_code = report_title = report_date = analyst = company_name = None
    opinion_change = rating = None
    target_price_change = target_price = None

    lines = info.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 종목명, 코드
        match = re.match(pattern_code, line)
        if match and not stock_code:
            stock_name = match.group(1).strip()
            stock_code = match.group(2)
        # 종목명만 있는 경우 (자료:)
        match = re.match(pattern_jaryo, line)
        if match and not stock_code:
            stock_name = match.group(1).strip()
            stock_code = get_code_by_name_from_db(stock_name)
        # 제목
        match = re.match(pattern_title, line)
        if match and not report_title:
            if not re.match(pattern_code, line):
                report_title = match.group(1).strip()
        # 날짜
        match = re.search(pattern_date, line)
        if match and not report_date:
            report_date = match.group().strip()

        # 애널리스트
        if '@' in line and not analyst:
            match = re.match(r"([가-힣]{2,3})", line)
            if match:
                analyst = match.group(1).strip()
        elif not analyst:
            match = re.match(pattern_analyst, line)
            if match:
                analyst = match.group(1).strip()

        # 리포트 고정 정보
        report_type = "기업 분석"
        company_name = "bnk투자증권"

        # 투자 의견 - 1) 한 줄 버전
        match = re.search(pattern_rating, line)
        if match and not rating and not opinion_change:
            opinion_change = match.group(1).strip()
            rating = match.group(2).strip()
        # 투자 의견 - 2) 세 줄 나눠진 버전
        if '투자의견' in line and not rating and not opinion_change:
            if i + 2 < len(lines):
                next_line = lines[i + 2].strip()
                next_next_line = lines[i + 4].strip()
                bracket_match = re.match(r"\[([^\]]+)\]", next_line)
                rating_match = re.match(r"[가-힣]{2,}", next_next_line)
                if bracket_match and rating_match:
                    opinion_change = bracket_match.group(1).strip()
                    rating = rating_match.group(0).strip()
                    i += 2  # 건너뛴 만큼 증가
        # 목표기, 상승/하락 여력 추출
        match = re.search(pattern_target, line)
        if match:
            target_price_change = match.group(1).strip()  # 상향 or 하향
            target_price = int(match.group(2).replace(",", ""))  # 숫자형 변환

        if '목표주가' in line and not target_price_change and not target_price:
            if i + 2 < len(lines):
                next_line = lines[i + 2].strip()
                next_next_line = lines[i + 4].strip()
                bracket_match = re.match(r"\[([^\]]+)\]", next_line)
                price_match = re.search(r"([\d,]+)원", next_next_line)

                if bracket_match and price_match:
                    target_price_change = bracket_match.group(1).strip()
                    target_price = int(price_match.group(0).strip().replace("원", "").replace(",",""))
                    i += 2  # 건너뛴 만큼 증가
                
        i += 1


    return (
        stock_name, stock_code, report_title,
        report_date, report_type, analyst,
        company_name, rating, opinion_change,
        target_price_change, target_price, 
    )


if __name__ == "__main__":
    txt_list = read_files("bnk")
    info_list = extract_all_info(txt_list)
    results = []
    for info in info_list:
        file_info = info['info']
        main_content = extract_content(file_info)
        stock_name, stock_code, report_title, report_date, report_type, analyst, company_name, rating, opinion_change, target_price_change, target_price = extract_stock_name_and_code(file_info)
        # current_price, investment_rationale는 예시로 None 처리 (추출 함수 필요시 추가)

        print(report_title)
        investment_rationale = main_content
        results.append([
            stock_code,
            stock_name,
            report_title,
            report_date,
            report_type,
            analyst,
            company_name,
            rating,
            opinion_change,
            target_price,
            target_price_change,
            investment_rationale
        ])
    # CSV 저장
    output_dir = Path(__file__).parent.parent / "consensus_parsed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / "bnk_consensus_reports.csv"
    columns = [
        "stock_code",
        "stock_name",
        "report_title",
        "report_date",
        "report_type",
        "analyst_name",
        "company_name",
        "rating",
        "opinion_change",
        "target_price",
        "target_price_change",
        "investment_rationale"
    ]
    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(results)
    print(f"CSV 저장 완료: {output_csv}")