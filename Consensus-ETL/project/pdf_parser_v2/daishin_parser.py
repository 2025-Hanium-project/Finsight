import re
from pathlib import Path
import csv
import pymysql
from utils import read_files, extract_all_info


def get_code_by_name_from_db(stock_name):
    """DB에서 종목명으로 종목코드 조회"""
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


def clean_text(text: str) -> str:
    """빈 줄과 불필요한 공백 제거"""
    lines = text.splitlines()
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    return "\n".join(cleaned_lines)


def extract_content(info):
    """본문 내용만 추출 (자료: 이후는 제외)"""
    lines = info.splitlines()
    result_lines = []
    for line in lines:
        if line.strip().startswith('자료:'):
            break
        result_lines.append(line)
    return '\n'.join(result_lines).strip()


def extract_stock_name_and_code(info):
    """
    대신증권 보고서 전용 필드 추출 (6개월/목표주가 병합 대응)
    """
    pattern_code = r"^##\s*(.+?)\s*\((\d{6})\)"
    pattern_jaryo = r"자료:\s*([^,]+),"

    stock_name = stock_code = report_title = report_date = analyst = company_name = None
    opinion_change = rating = None
    target_price_change = target_price = None

    lines = info.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 종목명 + 코드
        match = re.match(pattern_code, line)
        if match and not stock_code:
            stock_name = match.group(1).strip()
            stock_code = match.group(2)
            # 종목명 줄 다음 1~3줄 안에서 애널리스트 이름 찾기
            for j in range(1, 4):
                if i + j < len(lines):
                    name_candidate = lines[i + j].strip()
                    if re.fullmatch(r"[가-힣]{2,4}", name_candidate):
                        analyst = name_candidate
                        break

        # 종목명만 있는 경우 (자료: ... 형태)
        match = re.match(pattern_jaryo, line)
        if match and not stock_code:
            stock_name = match.group(1).strip()
            stock_code = get_code_by_name_from_db(stock_name)

        # 날짜 (예: (25.06.16))
        if not report_date:
            date_match = re.search(r"\(\d{2}\.\d{2}\.\d{2}\)", line)
            if date_match:
                report_date = date_match.group(0).strip("()")

        # 이메일 기반 보조 추출 (아직 analyst 못 찾았을 때만)
        if '@' in line and not analyst:
            if i - 1 >= 0:
                prev_line = lines[i - 1].strip()
                if re.fullmatch(r"[가-힣]{2,4}", prev_line):
                    analyst = prev_line

        # 고정값
        report_type = "기업 분석"
        company_name = "대신증권"

        # 투자의견 추출 (NR 포함, 줄바꿈 대응)
        # 투자의견 추출 (NR 포함, 줄바꿈 대응)
        if '투자의견' in line and not rating:
            for k in range(0, 4):  # 현재 줄 + 다음 3줄까지 탐색
                if i + k < len(lines):
                    candidate = lines[i + k].strip()
                    rating_match = re.search(
                        r"(매수|매도|중립|BUY|SELL|N\.?R|Not\s*Rated)", 
                        candidate, 
                        re.IGNORECASE
                    )
                    if rating_match:
                        val = rating_match.group(1)
                        if re.match(r"^(N\.?R|Not\s*Rated)$", val, re.IGNORECASE):
                            rating = "NR"
                        else:
                            rating = val
                        break


        # 투자의견 변동 (유지, 상향, 하향)
        if '투자의견' in line and not opinion_change:
            change_match = re.search(r"(유지|상향|하향)", line)
            if change_match:
                opinion_change = change_match.group(1)

        # 목표주가 추출 (6개월과 분리된 경우 병합)
        combined_line = line
        if i + 1 < len(lines):
            combined_line += lines[i + 1].strip()

        if ('목표주가' in combined_line or '6개월' in combined_line) and not target_price:
            for k in range(0, 6):  # 현재 줄 + 다음 5줄까지 탐색
                if i + k < len(lines):
                    price_match = re.search(r"([\d,]+)", lines[i + k])
                    if price_match:
                        price_str = price_match.group(1).replace(",", "").strip()
                        if price_str.isdigit():
                            price_val = int(price_str)
                            if 1000 <= price_val <= 2000000:
                                target_price = price_val
                                break

        # 목표주가 변동 (유지, 상향, 하향)
        if ('목표주가' in combined_line or '6개월' in combined_line) and not target_price_change:
            change_match = re.search(r"(유지|상향|하향)", combined_line)
            if change_match:
                target_price_change = change_match.group(1)

        # 리포트 제목: 종목명 다음 첫 ## 제목
        if not report_title:
            title_match = re.match(r"^##\s*(.+)", line)
            if title_match and not re.search(r"\(\d{6}\)", line):
                report_title = title_match.group(1).strip()

        i += 1

    # NR이면 목표주가/변동값 없음 처리
    if rating == "NR":
        target_price = None
        target_price_change = None
        opinion_change = None

    # 필수값 없으면 None
    if not stock_code or not stock_name:
        return None

    return (
        stock_name, stock_code, report_title,
        report_date, report_type, analyst,
        company_name, rating, opinion_change,
        target_price, target_price_change
    )


if __name__ == "__main__":
    txt_list = read_files("daishin")
    info_list = extract_all_info(txt_list)
    results = []

    for info in info_list:
        file_info = clean_text(info['info'])
        main_content = extract_content(file_info)

        extracted = extract_stock_name_and_code(file_info)
        if not extracted:
            continue

        stock_name, stock_code, report_title, report_date, report_type, analyst, company_name, rating, opinion_change, target_price, target_price_change = extracted
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
    output_csv = output_dir / "daishin_consensus_reports.csv"

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
