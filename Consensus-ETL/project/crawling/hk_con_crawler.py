import requests
from bs4 import BeautifulSoup
import datetime
import os
import re

def sanitize_filename(name):
    # 파일명에 사용할 수 없는 문자들을 밑줄로 대체
    return re.sub(r'[\\/*?:"<>|]', "_", name)

# 오늘 날짜와 7일 전 날짜(YYYY-MM-DD)
today = datetime.date.today()
end_date = today.strftime("%Y-%m-%d")
start_date = (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")

base_url = "https://consensus.hankyung.com"
# 페이지 URL 템플릿 (페이지 번호에 따라 now_page 값 변경)
list_url_template = f"{base_url}/analysis/list?&sdate={start_date}&edate={end_date}&order_type=&now_page={{page}}"

# PDF 파일 저장 폴더 생성
download_dir = "hk_consensus"
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# 브라우저처럼 보이도록 headers 추가
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                  " Chrome/90.0.4430.93 Safari/537.36"
}
# 1페이지부터 20페이지까지 순회
for page in range(1, 21):
    list_url = list_url_template.format(page=page)
    print(f"페이지 {page} 처리중: {list_url}")
    response = requests.get(list_url, headers=headers)
    if response.status_code != 200:
        print(f"페이지 {page} 불러오기 실패, 상태코드: {response.status_code}")
        continue

    # BeautifulSoup으로 파싱
    soup = BeautifulSoup(response.text, "html.parser")
    # 테이블이 포함된 div부터 찾기 (outerHTML가 이 부분에 있음)
    table_div = soup.find("div", class_="table_style01")
    if not table_div:
        print(f"페이지 {page}에서 div.table_style01를 찾지 못했습니다.")
        continue

    table = table_div.find("table")
    if not table:
        print(f"페이지 {page}에서 table을 찾지 못했습니다.")
        continue

    tbody = table.find("tbody")
    if not tbody:
        print(f"페이지 {page}에 tbody를 찾지 못했습니다.")
        continue
    rows = tbody.find_all("tr")
    if not rows:
        print(f"페이지 {page}에 데이터 행이 없습니다.")
        continue

    for row in rows:
        tds = row.find_all("td")
        if len(tds) < 6:
            continue

        date_text = tds[0].get_text(strip=True)
        category = tds[1].get_text(strip=True)
        a_title = tds[2].find("a")
        title = a_title.get_text(strip=True) if a_title else "NoTitle"
        author = tds[3].get_text(strip=True)
        brokerage = tds[4].get_text(strip=True)
        a_pdf = tds[5].find("a")
        if a_pdf and a_pdf.has_attr("href"):
            href = a_pdf["href"]
            pdf_url = base_url + href
        else:
            continue

        filename = f"{date_text}|{category}|{title}|{author}|{brokerage}.pdf"
        filename = sanitize_filename(filename)
        file_path = os.path.join(download_dir, filename)

        print(f"다운로드: {pdf_url} -> {file_path}")
        pdf_response = requests.get(pdf_url, headers=headers)
        if pdf_response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(pdf_response.content)
        else:
            print(f"PDF 다운로드 실패: {pdf_url}, 상태코드 {pdf_response.status_code}")