import requests
from bs4 import BeautifulSoup
import datetime
import os
import re
import sys
import time

def sanitize_filename(name):
    # 파일명에 사용할 수 없는 문자들을 밑줄로 대체
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# 오늘 날짜와 7일 전 날짜
today = datetime.date.today()
start_date = today - datetime.timedelta(days=7)

# 날짜 포맷 (두 자리 숫자 형식)
start_year = start_date.strftime("%Y")
start_month = start_date.strftime("%m")
start_day = start_date.strftime("%d")
end_year = today.strftime("%Y")
end_month = today.strftime("%m")
end_day = today.strftime("%d")


# 저장 폴더: project/consensus/miraeasset
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # crawling 폴더
PROJECT_DIR = os.path.dirname(CURRENT_DIR)  # project 폴더
download_dir = os.path.join(PROJECT_DIR, "consensus", "miraeasset")
os.makedirs(download_dir, exist_ok=True)

# 기본 설정
base_url = "https://securities.miraeasset.com"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
}

print("[미래에셋] 크롤링 시작")

# 종료 코드 판정용 집계
downloaded_count = 0
failed_count = 0

# 페이지 URL 템플릿
list_url_template = (
    f"{base_url}/bbs/board/message/list.do?"
    f"categoryId=1800&selectedId=1533&searchType=2"
    f"&searchStartYear={start_year}&searchStartMonth={start_month}&searchStartDay={start_day}"
    f"&searchEndYear={end_year}&searchEndMonth={end_month}&searchEndDay={end_day}"
    f"&listType=1&startId=zzzzz~&startPage=1&curPage={{page}}&direction=1"
)

# 첫 페이지에서 페이지 수 파악
first_page_url = list_url_template.format(page=1)
response = requests.get(first_page_url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")
paging = soup.select_one("p.bbs_paging")
if paging:
    total_pages = len(paging.find_all("span")) - 2
else:
    print("최근 7일간 미래에셋 리포트 없음.")
    total_pages = 0

# 각 페이지 순회
for page in range(1, total_pages + 1):
    print(f"[미래에셋] 페이지 {page} 처리중")
    page_url = list_url_template.format(page=page)
    response = requests.get(page_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    main_table = soup.find("table", class_="bbs_linetype2 mgt5")
    if not main_table:
        continue
    tbody = main_table.find("tbody")
    if not tbody:
        continue
    rows = tbody.find_all("tr")
    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 4:
            continue
        # 날짜
        date_text = tds[0].get_text(strip=True)
        # 제목
        subject_div = tds[1].find("div", class_="subject")
        if not subject_div:
            continue
        a_tag = subject_div.find("a")
        if not a_tag:
            continue
        title_text = a_tag.get_text(strip=True)
        # PDF 링크
        p_tag = tds[2].find("p", class_="bbsList_layer_icon")
        if not p_tag:
            continue
        a_pdf = p_tag.find("a")
        if not a_pdf or not a_pdf.has_attr("href"):
            continue
        href = a_pdf["href"]
        match = re.search(r"https://[^']+\.pdf", href)
        if not match:
            continue
        pdf_url = match.group()
        report_id_match = re.search(r"/(\d+)\.pdf", pdf_url)
        if not report_id_match:
            continue
        report_id = report_id_match.group(1)
        full_pdf_url = f"{pdf_url}?attachmentId={report_id}"
        # 작성자
        author_text = tds[3].get_text(strip=True)
        # 파일 이름 구성
        filename = f"{date_text}_{title_text}_{author_text}_미래에셋증권.pdf"
        filename = sanitize_filename(filename)
        file_path = os.path.join(download_dir, filename)
        # PDF 다운로드
        print(f"다운로드: {full_pdf_url} -> {file_path}")
        pdf_response = requests.get(full_pdf_url, headers=headers)
        if pdf_response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(pdf_response.content)
            downloaded_count += 1
        else:
            print(f"다운로드 실패: {full_pdf_url}, 상태코드: {pdf_response.status_code}")
            failed_count += 1
        time.sleep(1)

print("[미래에셋] 크롤링 종료")

# 조용히 성공하지 않는다. 최근 7일 조회라 한 건도 없으면 목록 구조 변경으로 본다.
if downloaded_count == 0:
    print("수집된 리포트가 없습니다. 목록 페이지 구조를 확인하세요.", file=sys.stderr)
    sys.exit(1)
if failed_count:
    print(f"{failed_count}건의 PDF 다운로드에 실패했습니다.", file=sys.stderr)
    sys.exit(1)
