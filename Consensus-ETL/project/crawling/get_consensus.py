# 컨센서스 크롤링 프로그램
import shutil
from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver
from datetime import datetime, timedelta
import time
import os
from bs4 import BeautifulSoup
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import undetected_chromedriver as uc
import requests
import urllib.parse
import pytesseract
from PIL import Image
import cv2
import numpy as np
from urllib.parse import urljoin
import json
import logging
from pathlib import Path
from utils import safe_filename, get_save_dir, download_file, date_str_now
from config import LOG_DIR, BASE_DOWNLOAD_PATH, USER_AGENT
from concurrent.futures import ThreadPoolExecutor, as_completed


# 로깅 설정 추가
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("consensus_pipeline.log", encoding="utf-8", mode="a"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("consensus_pipeline")

date = datetime.today() - timedelta(days=1)

# 증권사별 logger 생성 함수
def get_logger(company):
    logger = logging.getLogger(f"{company.upper()}_logger")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler(os.path.join(LOG_DIR, f"{company.upper()}.log"), encoding="utf-8", mode="a")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

# 날짜 정보 정리
year = date.strftime('%Y')
month = date.strftime('%m')
day = date.strftime('%d')
date_str_bar = date.strftime('%Y-%m-%d')
date_str_dot = date.strftime('%Y.%m.%d')
# 저장 경로 생성 (연도/월)
download_path = BASE_DOWNLOAD_PATH
os.makedirs(download_path, exist_ok=True)
prefs = {
    "plugins.plugins_disabled": ["Chrome PDF Viewer"],
    "plugins.always_open_pdf_externally": True,
    "download.default_directory": download_path,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True, 
    "safebrowsing.disable_download_protection": True
}

# options = uc.ChromeOptions()
options = webdriver.ChromeOptions()
options.add_experimental_option("prefs", prefs)
options.add_argument("--remote-allow-origins=*")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless=new")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument(f"user-agent={USER_AGENT}")
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--disable-web-security')

driver = webdriver.Chrome(options=options)

def wait_for_downloads(folder, timeout=100):
    start_time = time.time()
    while True:
        downloading = [f for f in os.listdir(folder) if f.endswith(".crdownload")]
        downloading2 = [f for f in os.listdir(folder) if f.endswith(".tmp")]
        if not downloading and not downloading2:
            break
        if time.time() - start_time > timeout:
            print("download timeout")
            break
        time.sleep(3)

# def get_hankyung(driver:WebDriver):

 
#     # 분석 리스트 페이지 열기
#     url = f"https://consensus.hankyung.com/analysis/list?skinType=business&sdate={date_str_bar}&edate={date_str_bar}&pagenum=50"
#     driver.get(url)
#     time.sleep(3)

#     # 렌더링된 HTML 파싱
#     soup = BeautifulSoup(driver.page_source, "html.parser")
#     results = []
#     rows = soup.select("table tbody tr")

#     # link, 제공 증권사, report id 리스트 생성성
#     for row in rows:
#         tds = row.find_all("td")
#         pdf_tag = row.select_one("div.dv_input a[href*='downpdf']")
#         if pdf_tag and len(tds) >= 6:
#             pdf_link = "https://consensus.hankyung.com" + pdf_tag["href"]
#             stock_name = tds[1].get_text(strip=True).split("(")[0]
#             provided_by = tds[5].get_text(strip=True)
#             report_idx = pdf_tag["href"].split("=")[-1]
#             results.append({
#                 "title" : stock_name,
#                 "link": pdf_link,
#                 "provided_by": provided_by,
#                 "report_idx": report_idx
#             })

#     # 1. PDF 전부 다운로드
#     for r in results:
#         filename = f"{r['report_idx']}.pdf"
#         full_path = os.path.join(download_path, filename)
#         if os.path.exists(full_path):
#             continue  # 이미 있으면 다운로드 생략

#         driver.get(r["link"])
#         wait_for_downloads(download_path)
#     time.sleep(2)

#     # 2. 다운로드된 PDF 이름 변경
#     for r in results:
#         report_idx = r["report_idx"]
#         provided_by = r["provided_by"].replace(" ", "_").replace("/", "_")
#         stock_name = r["title"]
#         old_path = os.path.join(download_path, f"{report_idx}.pdf")
        
#         if not os.path.exists(old_path):
#             print(f"No file: {stock_name}_{report_idx}.pdf")
#             continue

#         new_filename = f"{stock_name}_{provided_by}.pdf"
#         new_path = os.path.join(download_path, new_filename)

#         # 중복 방지
#         counter = 1
#         while os.path.exists(new_path):
#             new_filename = f"{stock_name}_{provided_by}_{counter}.pdf"
#             new_path = os.path.join(download_path, new_filename)
#             counter += 1

#         os.rename(old_path, new_path)
#         print(f"filename changed: {new_filename}")
#     if len(results) == 0:
#         print("There is no today's consensus in hankyung")
#     else:
#         print(f"총 {len(results)} # PDF saved (directory: {download_path})")

# def get_miraeasset(driver:WebDriver):
#     logger.info("[미래에셋] 크롤링 시작")
#     try:
#         # 해당 날짜의 컨센서스 paging 수 계산
#         url = f"https://securities.miraeasset.com/bbs/board/message/list.do?categoryId=1800&selectedId=1533&searchType=2&searchStartYear={year}&searchStartMonth={month}&searchStartDay={day}&searchEndYear={year}&searchEndMonth={month}&searchEndDay={day}&listType=1&startId=zzzzz~&startPage=1&curPage=1&direction=1"
#         driver.get(url)
#         soup = BeautifulSoup(driver.page_source, "html.parser")
#         paging = soup.select_one(" p.bbs_paging")
#         if paging:
#             page_num = len(paging.find_all("span"))-2
#         else:
#             print("There is no today's consensus in miraeasset")
#             return
#         # paging 수 만큼 순회하며 컨센서스 수집
#         for i in range(1,page_num+1):
#             url = f"https://securities.miraeasset.com/bbs/board/message/list.do?categoryId=1800&selectedId=1533&searchType=2&searchStartYear={year}&searchStartMonth={month}&searchStartDay={day}&searchEndYear={year}&searchEndMonth={month}&searchEndDay={day}&listType=1&startId=zzzzz~&startPage=1&curPage={i}&direction=1"
#             print(url)
#             driver.get(url)
#             soup = BeautifulSoup(driver.page_source, "html.parser")
#             rows = soup.select(" p.bbsList_layer_icon a")
#             for row in rows:
#                 href = row.get("href", "")
#                 match = re.search(r"https://[^']+\.pdf", href)
#                 if match:
#                     pre_pdf_url = match.group()
#                     report_id = re.search(r"/(\d+)\.pdf", pre_pdf_url).group(1)
#                     pdf_url = f"{pre_pdf_url}?attachmentId={report_id}"
#                     driver.get(pdf_url)
#                     wait_for_downloads(download_path)                
#                     downloaded_file = max(
#                         [os.path.join(download_path, f) for f in os.listdir(download_path) if f.endswith(".pdf")],
#                         key=os.path.getctime
#                     )

#                     # 파일명 정제 및 변경
#                     origin_name = row["title"]  # e.g., 20250430_더블유씨피 (393890_매수)
#                     name_part = re.sub(r"\s*\([^)]*\)", "", origin_name.split("_", 1)[-1])
#                     name_part = name_part.replace(".pdf", "")
#                     new_filename = f"{name_part}_미래에셋증권.pdf"
#                     new_path = os.path.join(download_path, new_filename)
#                     shutil.move(downloaded_file, new_path)
#                     time.sleep(1)
#     except Exception as e:
#         logger.error(f"[미래에셋] 오류: {e}")
#     logger.info("[미래에셋] 크롤링 종료")

def get_kiwoom(driver: WebDriver):
    url = "https://bbn.kiwoom.com/research/VAnalCRView"
    driver.get(url)

    downloaded_files = []
    # "더보기" 버튼 클릭
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "btn-list-more"))
    ).click()

    rows = driver.find_elements(By.CSS_SELECTOR, "#kwGridTable tbody tr")

    for row in rows:
        try:
            tds = row.find_elements(By.TAG_NAME, "td")
            if len(tds) < 7:
                continue

            title = tds[3].text.strip()
            date_str = tds[6].text.strip()

            if date_str != date_str_dot:
                continue

            # Selenium WebElement에서 버튼을 찾음
            download_btn = tds[4].find_element(By.CLASS_NAME, "btn-filedown")
            download_btn.click()
            driver.execute_script("arguments[0].click();", download_btn)
            time.sleep(2)
            wait_for_downloads(download_path)

            # 다운로드된 파일 이름 변경
            downloaded_file = max(
                [os.path.join(download_path, f) for f in os.listdir(download_path) if f.endswith(".pdf")],
                key=os.path.getctime
            )
            match = re.match(r'^[^(:\s]+', title)
            if match:
                clean_title = match.group()
            else:
                clean_title = title
            new_filename = f"{clean_title}_키움증권.pdf"
            new_path = os.path.join(download_path, new_filename)
            shutil.move(downloaded_file, new_path)
            print(f"[키움] 다운로드 완료: {new_filename}")
            downloaded_files.append(new_path)
            time.sleep(1)

        except Exception as e:
            logger = get_logger("KIWOOM")
            logger.error(f"[키움] 처리 중 오류 ({title}): {e}")
    # .pdf가 아닌 다운로드 파일은 삭제            
    for f in os.listdir(download_path):
        if not f.endswith(".pdf"):
            os.remove(os.path.join(download_path, f))
    return downloaded_files

def get_daishin(driver:WebDriver):
    url = "http://money2.daishin.co.kr/E5/ResearchCenter/Work/Research_BasicList.aspx?pr_code=4"
    driver.get(url)
    downloaded_files = []
    while True:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        table = driver.find_element(By.XPATH, "(//table)[1]")
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        row_ids = []
        is_next = True if rows[-1].find_elements(By.TAG_NAME, "td")[0].text.strip() == date_str_bar else False

        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")
            written_day = tds[0].text.strip()
            full_title = tds[1].text.strip()
            # 안전하게 split 처리
            try:
                split_bracket = full_title.split("]")
                if len(split_bracket) < 2:
                    print(f"[대신] 잘못된 포맷(대괄호): {full_title}")
                    continue
                split_space = split_bracket[-2].split(' ')
                if len(split_space) < 2:
                    print(f"[대신] 잘못된 포맷(공백): {full_title}")
                    continue
                target = split_space[1]
            except Exception as e:
                logger = get_logger("DAISHIN")
                logger.error(f"[대신] split 오류: {full_title}, {e}")
                continue
            is_target = target in ["Review", "Preview", "NDR"]
            after_bracket = full_title.split("]")[-1]  # 마지막 ] 뒤 문자열
            stock_name = after_bracket.split(":")[0].strip()

            if written_day == date_str_bar and is_target:
                if len(tds)<3:
                    continue
                try:
                    a_tag = tds[2].find_element(By.TAG_NAME, "a")  # 첨부파일 위치
                    href = a_tag.get_attribute("href")
                    match = re.search(r"rowid=(\d+)", href)
                    if match:
                        row_ids.append((match.group(1), stock_name))
                except Exception as e:
                    print(f"href 추출 실패: {e}")
        for id, stock_name in row_ids:
            pdf_url = f"http://money2.daishin.co.kr/E5/ResearchCenter/Work/Research_BasicRead.aspx?rowid={id}&pr_code=4&page=1"
            driver.get(pdf_url)
            img_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "imgAttach")))

            # 클릭 실행
            img_button.click()
            # 다운이 안되서 여기서 멈춤 그냥
            time.sleep(2)
            try:
                downloaded_file = max(
                    [os.path.join(download_path, f) for f in os.listdir(download_path) if f.endswith(".pdf")],
                    key=os.path.getctime
                )
                new_filename = f"{stock_name}_대신증권.pdf"
                new_path = os.path.join(download_path, new_filename)
                shutil.move(downloaded_file, new_path)
                time.sleep(2)
                print(f"[대신] 다운로드 완료: {new_filename}")
            except Exception as e:
                print(f"파일 이동 실패: {e}")
        
        if is_next:
            url = "http://money2.daishin.co.kr/E5/ResearchCenter/Work/Research_BasicList.aspx?pr_code=4"
            driver.get(url)
            # click the next page button
            next_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "id_ucPageSelect_id_btnRightPage")))
            next_btn.click()
            time.sleep(2)
        else:
            break

def get_bnk(driver: WebDriver, max_pages=3, max_reports=10, logger=None, company=None):
    import re
    import shutil
    if logger is None:
        logger = get_logger(company or "BNK")
    if company is None:
        company = "BNK"
    base_url = 'https://www.bnkfn.co.kr'
    list_url = 'https://www.bnkfn.co.kr/research/analysingCompany.jspx'
    download_dir = os.path.join(download_path, company)
    by_date_dir = os.path.join(download_dir, 'by_date')
    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(by_date_dir, exist_ok=True)
    downloaded_set = set(os.listdir(download_dir))
    all_reports = []
    # 1. 전체 페이지에서 리포트 정보 수집
    for page in range(1, max_pages + 1):
        page_url = f"{list_url}?page={page}" if page > 1 else list_url
        try:
            driver.get(page_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table')
            if not table:
                logger.warning(f"[BNK] {page}페이지에서 테이블 없음")
                continue
            rows = table.find_all('tr')[1:]
            for row in rows:
                columns = row.find_all('td')
                if len(columns) < 6:
                    continue
                report_no = columns[0].text.strip()
                title_element = columns[1]
                title = title_element.text.strip()
                title_link = title_element.find('a')
                has_link = bool(title_link)
                has_attachment = bool(columns[3].find('img'))
                date_val = columns[4].text.strip()
                author = columns[2].text.strip() if len(columns) > 2 else ""
                if has_link or has_attachment:
                    all_reports.append({
                        'no': report_no,
                        'title': title,
                        'date': date_val,
                        'author': author
                    })
                if len(all_reports) >= max_reports:
                    break
            if len(all_reports) >= max_reports:
                break
            time.sleep(1)
        except Exception as e:
            logger.error(f"[BNK] {page}페이지 크롤링 오류: {e}")
            continue
    # 2. 각 리포트별 다운로드
    for idx, report in enumerate(all_reports, 1):
        try:
            report_no = report['no']
            title = report['title']
            date_val = report['date']
            author = report['author']
            safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)
            file_name = f"{date_val.replace('.', '')}_{report_no}_{safe_title}.pdf"
            file_path = os.path.join(download_dir, file_name)
            date_dir = os.path.join(by_date_dir, date_val.replace('.', '-'))
            os.makedirs(date_dir, exist_ok=True)
            date_file_path = os.path.join(date_dir, file_name)
            if os.path.exists(file_path):
                logger.info(f"[BNK] 이미 다운로드됨: {file_name}")
                continue
            # 리스트 페이지 새로고침
            driver.get(list_url)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            report_rows = driver.find_elements(By.TAG_NAME, "tr")
            target_row = None
            for row in report_rows:
                try:
                    if report_no in row.text and title in row.text:
                        target_row = row
                        break
                except:
                    continue
            if not target_row:
                logger.warning(f"[BNK] 행 탐색 실패: {report_no} {title}")
                continue
            # 제목 링크 클릭
            try:
                title_link = target_row.find_element(By.CSS_SELECTOR, "td:nth-child(2) a")
                driver.execute_script("arguments[0].click();", title_link)
                time.sleep(5)
                current_url = driver.current_url
                pdf_url = None
                if '.pdf' in current_url:
                    pdf_url = current_url
                else:
                    pdf_elements = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='.pdf'], object[data*='.pdf'], embed[src*='.pdf'], a[href*='.pdf']")
                    for elem in pdf_elements:
                        if elem.tag_name == 'iframe':
                            pdf_url = elem.get_attribute('src')
                        elif elem.tag_name == 'object':
                            pdf_url = elem.get_attribute('data')
                        elif elem.tag_name == 'embed':
                            pdf_url = elem.get_attribute('src')
                        elif elem.tag_name == 'a':
                            pdf_url = elem.get_attribute('href')
                        if pdf_url and '.pdf' in pdf_url:
                            break
                if pdf_url and pdf_url.startswith('/'):
                    pdf_url = base_url + pdf_url
                if pdf_url and pdf_url.startswith('http'):
                    try:
                        resp = requests.get(pdf_url, stream=True, timeout=15)
                        if resp.status_code == 200 and 'pdf' in resp.headers.get('Content-Type', '').lower():
                            with open(file_path, 'wb') as f:
                                for chunk in resp.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            shutil.copy(file_path, date_file_path)
                            logger.info(f"[BNK] 다운로드 완료: {file_name}")
                        else:
                            logger.warning(f"[BNK] PDF 응답 오류: {pdf_url}")
                    except Exception as e:
                        logger.error(f"[BNK] PDF 다운로드 오류: {e}")
                else:
                    logger.warning(f"[BNK] PDF URL 추출 실패: {report_no} {title}")
            except Exception as e:
                logger.error(f"[BNK] 제목 링크 클릭 오류: {e}")
                continue
            time.sleep(2)
        except Exception as e:
            logger.error(f"[BNK] 다운로드 오류: {e}")
            continue

def get_ds(driver=None, max_pages=3, logger=None, company=None):
    if logger is None:
        logger = get_logger(company or "DS")
    if company is None:
        company = "DS"
    session = requests.Session()
    all_reports = []
    for page in range(1, max_pages + 1):
        url = f"https://www.ds-sec.co.kr/bbs/board.php?bo_table=sub03_02&page={page}"
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.ds-sec.co.kr/'
            }
            response = session.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            report_items = soup.select('table.board_list tr:not(:first-child)')
            if not report_items:
                report_items = soup.select('tr')
            for item in report_items:
                try:
                    cols = item.select('td')
                    if len(cols) < 3:
                        continue
                    num_col = cols[0].text.strip()
                    if not num_col.isdigit():
                        continue
                    title_link = cols[1].select_one('a')
                    if not title_link:
                        continue
                    title = title_link.text.strip()
                    href = title_link.get('href', '')
                    wr_id_match = re.search(r'wr_id=(\d+)', href)
                    if not wr_id_match:
                        continue
                    wr_id = wr_id_match.group(1)
                    date_str = cols[3].text.strip() if len(cols) > 3 else ""
                    views = cols[4].text.strip() if len(cols) > 4 else "0"
                    all_reports.append({
                        'id': num_col,
                        'title': title,
                        'date': date_str,
                        'views': views,
                        'wr_id': wr_id
                    })
                except Exception as e:
                    logger = get_logger("DS")
                    logger.error(f"[DS] 항목 처리 오류: {e}")
                    continue
            time.sleep(1)
        except Exception as e:
            logger = get_logger("DS")
            logger.error(f"[DS] {page}페이지 처리 오류: {e}")
            break
    print(f"[DS] {len(all_reports)}개 리포트 정보 수집 완료")
    if not all_reports:
        print("[DS] 수집된 리포트가 없습니다.")
        return
    for idx, report in enumerate(all_reports):
        print(f"[DS] 리포트 처리 중 ({idx+1}/{len(all_reports)}): {report['title']}")
        # 날짜 폴더 경로를 기존과 동일하게 사용
        save_folder = download_path
        os.makedirs(save_folder, exist_ok=True)
        # 첨부파일 정보 가져오기
        wr_id = report['wr_id']
        att_url = f"https://www.ds-sec.co.kr/bbs/board.php?bo_table=sub03_02&wr_id={wr_id}"
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.ds-sec.co.kr/bbs/board.php?bo_table=sub03_02'
            }
            resp = session.get(att_url, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            file_links = soup.select('section#bo_v_file a')
            if not file_links:
                file_links = soup.select('a[href*="download.php"]')
            for link in file_links:
                file_name = link.text.strip()
                if not file_name:
                    spans = link.select('span')
                    file_name = ' '.join([span.text.strip() for span in spans if span.text.strip()])
                file_name = re.sub(r'\([^)]*\)', '', file_name).strip()
                file_url = link.get('href')
                if not file_url:
                    continue
                if not file_url.startswith('http'):
                    file_url = urllib.parse.urljoin('https://www.ds-sec.co.kr/', file_url)
                if not file_name:
                    file_name_match = re.search(r'no=(\d+)', file_url)
                    if file_name_match:
                        file_name = f"report_{wr_id}_{file_name_match.group(1)}.pdf"
                    else:
                        file_name = f"report_{wr_id}.pdf"
                if not file_name.lower().endswith('.pdf'):
                    file_name += '.pdf'
                new_filename = safe_filename(file_name, company) + '.pdf'
                new_path = os.path.join(save_folder, new_filename)
                counter = 1
                while os.path.exists(new_path):
                    new_filename = safe_filename(file_name, company) + f'_{counter}.pdf'
                    new_path = os.path.join(save_folder, new_filename)
                    counter += 1
                # 파일 다운로드
                try:
                    file_resp = session.get(file_url, headers=headers, stream=True)
                    file_resp.raise_for_status()
                    with open(new_path, 'wb') as f:
                        for chunk in file_resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    logger.info(f"[DS] 다운로드 완료: {new_filename}")
                except Exception as e:
                    logger.error(f"[DS] 파일 다운로드 오류: {file_url}, {e}")
            time.sleep(2)
        except Exception as e:
            logger = get_logger("DS")
            logger.error(f"[DS] 첨부파일 처리 오류: {att_url}, {e}")
            continue

def get_hana(driver, max_pages=3, logger=None, company=None):
    if logger is None:
        logger = get_logger(company or "HANA")
    if company is None:
        company = "HANA"
    """
    하나증권 리포트 PDF를 다운로드하는 함수입니다.
    driver: selenium WebDriver
    max_pages: 최대 크롤링 페이지 수
    """
    base_url = "https://www.hanaw.com/main/research/research/list.cmd?pid=3&cid=2"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    session = requests.Session()
    for page in range(1, max_pages + 1):
        page_url = f"{base_url}&page={page}"
        print(f"[하나] 페이지 URL: {page_url}")
        try:
            driver.get(page_url)
            time.sleep(5)
            report_elements = driver.find_elements(By.CSS_SELECTOR, "div.daily_bbs > ul > li")
            print(f"[하나] 발견된 항목 수: {len(report_elements)}")
            for element in report_elements:
                try:
                    title_elem = element.find_element(By.CSS_SELECTOR, "h3 > a.more_btn")
                    title = title_elem.text.strip()
                    if not title:
                        continue
                    # 날짜
                    try:
                        date_elem = element.find_element(By.CSS_SELECTOR, "li.mb7.m-info.info > span.txtbasic")
                        date_text = date_elem.text.strip()
                        date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', date_text)
                        if date_match:
                            year, month, day = date_match.group(1), date_match.group(2), date_match.group(3)
                        else:
                            year, month, day = year, month, day  # 전역변수 fallback
                    except Exception:
                        year, month, day = year, month, day
                    # PDF 파일명 및 링크
                    try:
                        pdf_elem = element.find_element(By.CSS_SELECTOR, "div.pdf > a")
                        pdf_filename = pdf_elem.text.strip()
                        pdf_link = pdf_elem.get_attribute('href')
                    except Exception:
                        pdf_filename = ""
                        pdf_link = ""
                    if not pdf_filename or not pdf_link:
                        print(f"[하나] PDF 정보 없음: {title}")
                        continue
                    # 저장 경로
                    save_dir = get_save_dir(f"{year}/{month}/{day}", company)
                    os.makedirs(save_dir, exist_ok=True)
                    new_filename = safe_filename(title, company) + '.pdf'
                    save_path = os.path.join(save_dir, new_filename)
                    counter = 1
                    while os.path.exists(save_path):
                        new_filename = safe_filename(title, company) + f'_{counter}.pdf'
                        save_path = os.path.join(save_dir, new_filename)
                        counter += 1
                    if os.path.exists(save_path):
                        logger.info(f"[하나] 이미 존재: {save_path}")
                        continue
                    print(f"[하나] PDF 다운로드 시도: {pdf_link}")
                    # PDF 다운로드
                    try:
                        resp = session.get(pdf_link, headers=headers, timeout=30)
                        if resp.status_code == 200 and 'application/pdf' in resp.headers.get('Content-Type', ''):
                            with open(save_path, 'wb') as f:
                                f.write(resp.content)
                            logger.info(f"[하나] PDF 다운로드 성공: {new_filename}")
                        else:
                            logger.warning(f"[하나] PDF 다운로드 실패 (상태 코드: {resp.status_code}): {pdf_link}")
                    except Exception as e:
                        logger.error(f"[하나] PDF 다운로드 오류: {e}")
                    time.sleep(2)
                except Exception as e:
                    logger = get_logger("HANA")
                    logger.error(f"[하나] 항목 처리 오류: {e}")
            time.sleep(3)
        except Exception as e:
            logger = get_logger("HANA")
            logger.error(f"[하나] 페이지 크롤링 오류: {e}")
            continue

def get_heungkuk(max_pages=5, logger=None, company=None):
    if logger is None:
        logger = get_logger(company or "HEUNGKUK")
    if company is None:
        company = "HEUNGKUK"
    """
    흥국증권 리포트 이미지 및 OCR 텍스트를 다운로드하는 함수입니다.
    max_pages: 최대 크롤링 페이지 수
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.heungkuksec.co.kr/'
    }
    processed_reports = set()
    for page in range(1, max_pages + 1):
        list_url = f'https://www.heungkuksec.co.kr/research/company/list.do?currentPage={page}'
        print(f"[흥국] 리스트 페이지: {list_url}")
        try:
            response = requests.get(list_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            report_rows = soup.select('table tr')
            print(f"[흥국] {page}페이지에서 {len(report_rows)}개 행 발견")
            for row in report_rows:
                try:
                    title_cell = row.select_one('td:nth-child(2)')
                    if not title_cell:
                        continue
                    title_text = title_cell.text.strip()
                    if not title_text:
                        continue
                    analyst_cell = row.select_one('td:nth-child(3)')
                    analyst = analyst_cell.text.strip() if analyst_cell else "Unknown"
                    date_cell = row.select_one('td:nth-child(4)')
                    date_str = date_cell.text.strip() if date_cell else "Unknown"
                    link_elem = row.select_one('a')
                    if not link_elem:
                        continue
                    href = link_elem.get('href', '')
                    report_id = None
                    if href and 'key=' in href:
                        match = re.search(r'key=(\d+)', href)
                        if match:
                            report_id = match.group(1)
                    if not report_id:
                        onclick = link_elem.get('onclick', '')
                        if onclick and 'key=' in onclick:
                            match = re.search(r'key=(\d+)', onclick)
                            if match:
                                report_id = match.group(1)
                    if not report_id:
                        print(f"[흥국] report_id 추출 실패: {href}")
                        continue
                    if report_id in processed_reports:
                        continue
                    processed_reports.add(report_id)
                    detail_url = f'https://www.heungkuksec.co.kr/research/company/view.do?key={report_id}'
                    try:
                        detail_response = requests.get(detail_url, headers=headers)
                        detail_response.raise_for_status()
                        detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                        # 날짜 파싱 및 폴더 이름 생성
                        try:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                            save_folder = download_path
                        except ValueError:
                            print(f"[흥국] 날짜 파싱 실패: {date_str}")
                            save_folder = download_path
                        os.makedirs(save_folder, exist_ok=True)
                        # 유효한 파일명으로 변환
                        valid_title = ''.join(c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in title_text)
                        valid_title = valid_title[:100]
                        # 보고서 이미지 URL 추출
                        img_elements = detail_soup.select('table tr td img[src^="http://www.heungkuksec.co.kr/upload/"]')
                        print(f"[흥국] {report_id}번 리포트 이미지 {len(img_elements)}개 발견")
                        all_extracted_text = ""
                        for i, img in enumerate(img_elements):
                            img_url = img['src']
                            try:
                                img_response = requests.get(img_url, headers=headers)
                                img_response.raise_for_status()
                                img_filename = os.path.join(save_folder, f'{valid_title}_report_{report_id}_{i+1}.jpg')
                                with open(img_filename, 'wb') as f:
                                    f.write(img_response.content)
                                print(f"[흥국] 이미지 저장: {img_filename}")
                                # OCR 처리
                                try:
                                    img_cv = cv2.imread(img_filename)
                                    img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                                    img_cv = cv2.threshold(img_cv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                                    custom_config = r'--oem 3 --psm 6 -l kor+eng'
                                    text = pytesseract.image_to_string(img_cv, config=custom_config)
                                except Exception as e:
                                    logger = get_logger("HEUNGKUK")
                                    logger.error(f"[흥국] OCR 오류: {e}")
                                    text = ""
                                text_filename = os.path.join(save_folder, f'{valid_title}_report_{report_id}_{i+1}_text.txt')
                                with open(text_filename, 'w', encoding='utf-8') as f:
                                    f.write(text)
                                all_extracted_text += f"\n\n--- Image {i+1} ---\n\n"
                                all_extracted_text += text
                                print(f"[흥국] OCR 텍스트 저장: {text_filename}")
                            except Exception as e:
                                logger = get_logger("HEUNGKUK")
                                logger.error(f"[흥국] 이미지 다운로드 오류: {img_url}, {e}")
                        # 전체 추출 텍스트 저장
                        if all_extracted_text:
                            full_text_filename = os.path.join(save_folder, f'{valid_title}_report_{report_id}_full_text.txt')
                            with open(full_text_filename, 'w', encoding='utf-8') as f:
                                f.write(all_extracted_text)
                            print(f"[흥국] 전체 OCR 텍스트 저장: {full_text_filename}")
                        # 메타데이터 저장
                        meta_filename = os.path.join(save_folder, f'{valid_title}_report_{report_id}_meta.txt')
                        with open(meta_filename, 'w', encoding='utf-8') as f:
                            f.write(f'Title: {title_text}\n')
                            f.write(f'Report ID: {report_id}\n')
                            f.write(f'Author: {analyst}\n')
                            f.write(f'Date: {date_str}\n')
                            f.write(f'URL: {detail_url}\n')
                        print(f"[흥국] 메타데이터 저장: {meta_filename}")
                        time.sleep(1)
                    except Exception as e:
                        logger = get_logger("HEUNGKUK")
                        logger.error(f"[흥국] 상세페이지 처리 오류: {e}")
                except Exception as e:
                    logger = get_logger("HEUNGKUK")
                    logger.error(f"[흥국] 행 파싱 오류: {e}")
                    continue
            print(f"[흥국] {page}페이지 완료")
            time.sleep(2)
        except Exception as e:
            logger = get_logger("HEUNGKUK")
            logger.error(f"[흥국] 페이지 처리 오류: {e}")
            continue
    print(f"[흥국] 총 {len(processed_reports)}개 리포트 완료")

def get_ibk(driver, days=3, logger=None, company=None):
    if logger is None:
        logger = get_logger(company or "IBK")
    if company is None:
        company = "IBK"
    """
    IBK투자증권 리포트 PDF를 robust하게 다운로드 (API 실패 시 HTML/패턴 fallback)
    driver: selenium WebDriver
    days: 최근 N일간 크롤링
    """
    import re
    import requests
    from datetime import datetime, timedelta
    from urllib.parse import urljoin
    logger.info("[IBK] 크롤링 시작")
    base_url = "https://m.ibks.com/iko/IKO010201.do"
    start_date = datetime.now()
    date_range = [(start_date - timedelta(days=i)).strftime("%Y.%m.%d") for i in range(days)]
    date_range_short = [(start_date - timedelta(days=i)).strftime("%Y%m%d") for i in range(days)]
    try:
        driver.get(base_url)
        time.sleep(5)
        # 쿠키 복사
        cookies = driver.get_cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        headers = {
            'User-Agent': driver.execute_script("return navigator.userAgent"),
            'Referer': driver.current_url,
            'X-Requested-With': 'XMLHttpRequest'
        }
        session = requests.Session()
        for name, value in cookie_dict.items():
            session.cookies.set(name, value)
        # 1. API 접근
        api_endpoints = [
            "https://m.ibks.com/iko/IKO010201.do?action=list",
            "https://m.ibks.com/iko/service/getReportList.do",
            "https://m.ibks.com/iko/api/getReportList.do"
        ]
        api_success = False
        for endpoint in api_endpoints:
            try:
                resp = session.get(endpoint, headers=headers, timeout=10)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        reports = []
                        if isinstance(data, dict):
                            for key in ['data','list','items','reports','result','reportList']:
                                if key in data and isinstance(data[key], list):
                                    reports = data[key]
                                    break
                        if reports:
                            for report in reports:
                                # 날짜/종목/다운로드 URL 추출
                                date_str, company_name, download_url = None, None, None
                                for field in ['date','regdate','reg_date','createdate','reportdate','rptDt']:
                                    if field in report and report[field]:
                                        m = re.search(r'(\d{4}[-\./]\d{2}[-\./]\d{2}|\d{8})', str(report[field]))
                                        if m:
                                            date_str = m.group(1).replace('-', '.').replace('/', '.')
                                            if len(date_str)==8:
                                                date_str = f"{date_str[:4]}.{date_str[4:6]}.{date_str[6:8]}"
                                            break
                                for field in ['title','name','companyName','rptTtl','subject']:
                                    if field in report and report[field]:
                                        t = str(report[field])
                                        m = re.search(r'\[(.*?)\]', t)
                                        company_name = m.group(1) if m else t.split()[0] if t.split() else "Report"
                                        break
                                for field in ['url','fileUrl','downloadUrl','fileDownloadUrl','attatchUrl']:
                                    if field in report and report[field]:
                                        download_url = report[field]
                                        break
                                if date_str and date_str in date_range and company_name and download_url:
                                    # 파일명/폴더
                                    date_folder = get_save_dir(date_str, company)
                                    os.makedirs(date_folder, exist_ok=True)
                                    file_name = safe_filename(company_name, company) + '.pdf'
                                    file_path = os.path.join(date_folder, file_name)
                                    if os.path.exists(file_path):
                                        logger.info(f"[IBK] 이미 존재: {file_path}")
                                        continue
                                    # 상대경로 보정
                                    if not download_url.startswith('http'):
                                        download_url = urljoin(driver.current_url, download_url)
                                    # 다운로드
                                    try:
                                        s = requests.Session()
                                        for c in cookies:
                                            s.cookies.set(c['name'], c['value'])
                                        r = s.get(download_url, headers=headers, stream=True, timeout=30)
                                        if r.status_code==200 and ('application/pdf' in r.headers.get('Content-Type','') or 'octet-stream' in r.headers.get('Content-Type','')):
                                            with open(file_path, 'wb') as f:
                                                for chunk in r.iter_content(8192):
                                                    if chunk: f.write(chunk)
                                            if os.path.getsize(file_path)<1000:
                                                with open(file_path,'rb') as f:
                                                    if f.read(4)!=b'%PDF':
                                                        logger.warning(f"[IBK] 유효하지 않은 PDF: {file_path}"); os.remove(file_path); continue
                                            logger.info(f"[IBK] 다운로드 완료: {file_path}")
                                            api_success = True
                                        else:
                                            logger.warning(f"[IBK] PDF가 아닌 응답: {download_url}")
                                    except Exception as e:
                                        logger.error(f"[IBK] 다운로드 오류: {e}")
                    except Exception as e:
                        logger.error(f"[IBK] API JSON 파싱 오류: {e}")
            except Exception as e:
                logger.error(f"[IBK] API 접근 오류: {e}")
        if api_success:
            logger.info("[IBK] API 기반 다운로드 성공")
            return
        # 2. HTML 구조 fallback
        try:
            all_elements = driver.find_elements(By.XPATH, "//*[text()]")
            for element in all_elements:
                try:
                    text = element.text.strip()
                    if text and ('[' in text and ']' in text) and len(text)>5:
                        parent = element.find_element(By.XPATH, "./..")
                        parent_text = parent.text
                        m = re.search(r'(\d{4}\.\d{2}\.\d{2})', parent_text)
                        if m:
                            report_date = m.group(1)
                            if report_date in date_range:
                                t = element.text
                                m2 = re.search(r'\[(.*?)\]', t)
                                company_name = m2.group(1) if m2 else t.split()[0]
                                # 다운로드 링크
                                links = parent.find_elements(By.XPATH, ".//a[contains(text(), '파일') or contains(text(), '다운로드')]")
                                if not links:
                                    links = parent.find_elements(By.XPATH, ".//a[contains(@href, 'download')]")
                                for link in links:
                                    try:
                                        download_url = link.get_attribute('href')
                                        if download_url:
                                            date_folder = get_save_dir(report_date, company)
                                            os.makedirs(date_folder, exist_ok=True)
                                            file_name = safe_filename(company_name, company) + '.pdf'
                                            file_path = os.path.join(date_folder, file_name)
                                            if os.path.exists(file_path):
                                                logger.info(f"[IBK] 이미 존재: {file_path}")
                                                continue
                                            if not download_url.startswith('http'):
                                                download_url = urljoin(driver.current_url, download_url)
                                            s = requests.Session()
                                            for c in cookies:
                                                s.cookies.set(c['name'], c['value'])
                                            r = s.get(download_url, headers=headers, stream=True, timeout=30)
                                            if r.status_code==200 and ('application/pdf' in r.headers.get('Content-Type','') or 'octet-stream' in r.headers.get('Content-Type','')):
                                                with open(file_path, 'wb') as f:
                                                    for chunk in r.iter_content(8192):
                                                        if chunk: f.write(chunk)
                                                if os.path.getsize(file_path)<1000:
                                                    with open(file_path,'rb') as f:
                                                        if f.read(4)!=b'%PDF':
                                                            logger.warning(f"[IBK] 유효하지 않은 PDF: {file_path}"); os.remove(file_path); continue
                                                logger.info(f"[IBK] 다운로드 완료: {file_path}")
                                            else:
                                                logger.warning(f"[IBK] PDF가 아닌 응답: {download_url}")
                                    except Exception as e:
                                        logger.error(f"[IBK] HTML 다운로드 오류: {e}")
                except Exception: pass
        except Exception as e:
            logger.error(f"[IBK] HTML fallback 오류: {e}")
        # 3. 패턴 기반 fallback
        try:
            page_source = driver.page_source
            report_blocks = re.split(r'##\s+\[', page_source)
            if len(report_blocks)<=1:
                report_blocks = re.split(r'<h[1-6][^>]*>\s*\[', page_source)
            for i, block in enumerate(report_blocks[1:], 1):
                try:
                    block = '['+block
                    m = re.search(r'\[(.*?)\]', block)
                    company_name = m.group(1) if m else f"Report{i}"
                    m2 = re.search(r'(\d{4}\.\d{2}\.\d{2})', block)
                    if m2:
                        report_date = m2.group(1)
                        if report_date in date_range:
                            m3 = re.search(r'href=[\'\"]([^\'\"]*download[^\'\"]*)[\'\"]', block)
                            if m3:
                                download_url = m3.group(1).replace('&amp;', '&')
                                if not download_url.startswith('http'):
                                    download_url = urljoin(driver.current_url, download_url)
                                date_folder = get_save_dir(report_date, company)
                                os.makedirs(date_folder, exist_ok=True)
                                file_name = safe_filename(company_name, company) + '.pdf'
                                file_path = os.path.join(date_folder, file_name)
                                if os.path.exists(file_path):
                                    logger.info(f"[IBK] 이미 존재: {file_path}")
                                    continue
                                s = requests.Session()
                                for c in cookies:
                                    s.cookies.set(c['name'], c['value'])
                                r = s.get(download_url, headers=headers, stream=True, timeout=30)
                                if r.status_code==200 and ('application/pdf' in r.headers.get('Content-Type','') or 'octet-stream' in r.headers.get('Content-Type','')):
                                    with open(file_path, 'wb') as f:
                                        for chunk in r.iter_content(8192):
                                            if chunk: f.write(chunk)
                                    if os.path.getsize(file_path)<1000:
                                        with open(file_path,'rb') as f:
                                            if f.read(4)!=b'%PDF':
                                                logger.warning(f"[IBK] 유효하지 않은 PDF: {file_path}"); os.remove(file_path); continue
                                    logger.info(f"[IBK] 다운로드 완료: {file_path}")
                                else:
                                    logger.warning(f"[IBK] PDF가 아닌 응답: {download_url}")
                except Exception: pass
        except Exception as e:
            logger.error(f"[IBK] 패턴 fallback 오류: {e}")
    except Exception as e:
        logger.error(f"[IBK] 크롤링 오류: {e}")
    logger.info("[IBK] 크롤링 완료")

def get_im(max_pages=5):
    """
    IM증권 리포트 PDF를 다운로드하는 함수입니다.
    max_pages: 최대 크롤링 페이지 수
    """
    import random
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://m.imfnsec.com:442/mobile/research/rs01.jsp'
    })
    base_url = "https://m.imfnsec.com:442"
    report_list_url = f"{base_url}/mobile/research/rs01.jsp"
    def extract_pdf_path(onclick_attr):
        if not onclick_attr:
            return None
        pdf_match = re.search(r"view_pdf\('([^']+)'\)", onclick_attr)
        if pdf_match:
            return pdf_match.group(1)
        return None
    all_reports = []
    for page in range(1, max_pages + 1):
        params = {"page": page} if page > 1 else {}
        try:
            response = session.get(report_list_url, params=params)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            report_items = soup.select('tr')
            for item in report_items:
                try:
                    link_elem = item.select_one('td.tal a')
                    if not link_elem:
                        continue
                    onclick = link_elem.get('href', '')
                    pdf_path = extract_pdf_path(onclick)
                    if not pdf_path:
                        continue
                    title_elem = link_elem.select_one('p:not(.d)')
                    date_elem = link_elem.select_one('p.d')
                    if not title_elem or not date_elem:
                        continue
                    title_text = title_elem.get_text().strip()
                    date_text = date_elem.get_text().strip()
                    pdf_url = urljoin(base_url, pdf_path)
                    all_reports.append({
                        'title': title_text,
                        'date': date_text,
                        'pdf_url': pdf_url,
                        'pdf_path': pdf_path
                    })
                except Exception as e:
                    logger = get_logger("IM")
                    logger.error(f"[IM] 리포트 항목 처리 오류: {e}")
                    continue
            time.sleep(random.uniform(1.5, 3.0))
        except Exception as e:
            logger = get_logger("IM")
            logger.error(f"[IM] {page}페이지 처리 오류: {e}")
            continue
    print(f"[IM] 총 {len(all_reports)}개 리포트 수집 완료")
    # PDF 다운로드
    for report in all_reports:
        try:
            date_str = report['date'].replace('/', '')
            safe_title = ''.join(c for c in report['title'] if c.isalnum() or c in ' _-')[:50]
            original_filename = os.path.basename(report['pdf_path'])
            filename = f"{date_str}_{safe_title}_{original_filename}"
            save_path = os.path.join(download_path, filename)
            if os.path.exists(save_path):
                print(f"[IM] 이미 존재: {save_path}")
                continue
            pdf_response = session.get(report['pdf_url'], stream=True)
            pdf_response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in pdf_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[IM] 다운로드 완료: {save_path}")
            time.sleep(random.uniform(1.0, 2.0))
        except Exception as e:
            logger = get_logger("IM")
            logger.error(f"[IM] PDF 다운로드 오류: {e}")
            continue

def get_kyobo(driver, max_pages=3, logger=None):
    if logger is None:
        logger = logging.getLogger("consensus_pipeline")
    logger.info("[교보] 크롤링 시작")
    base_url = "https://m.iprovest.com/weblogic/ResearchServlet/newReports"
    try:
        driver.get(base_url)
        time.sleep(3)
        for page in range(1, max_pages + 1):
            logger.info(f"[교보] {page}페이지 처리 중...")
            if page > 1:
                try:
                    page_elements = driver.find_elements(By.XPATH, f"//a[text()='{page}']")
                    if not page_elements:
                        logger.warning(f"[교보] {page}페이지 링크를 찾을 수 없습니다.")
                        break
                    page_elements[0].click()
                    time.sleep(3)
                except Exception as e:
                    logger.error(f"[교보] 페이지 이동 오류: {e}")
                    break
            try:
                items = driver.find_elements(By.CSS_SELECTOR, "ul > li")
                logger.info(f"[교보] {len(items)}개 리포트 항목 발견")
                for idx, item in enumerate(items):
                    try:
                        item_text = item.text
                        if not item_text or len(item_text) < 5:
                            continue
                        # 제목 추출
                        try:
                            title_elem = item.find_element(By.CSS_SELECTOR, "h4, h3, strong")
                            title = title_elem.text.strip()
                        except Exception:
                            lines = item_text.split('\n')
                            title = lines[0] if lines else f"리포트_{idx+1}"
                        # 다운로드 버튼 탐색
                        download_button = None
                        buttons = item.find_elements(By.TAG_NAME, "button")
                        for btn in buttons:
                            if '다운로드' in btn.text:
                                download_button = btn
                                break
                        if not download_button:
                            links = item.find_elements(By.TAG_NAME, "a")
                            for link in links:
                                if '다운로드' in link.text or 'download' in (link.get_attribute("class") or "").lower():
                                    download_button = link
                                    break
                        if not download_button:
                            try:
                                download_images = item.find_elements(By.XPATH, ".//img[contains(@src, 'download') or contains(@alt, '다운로드')]")
                                if download_images:
                                    parent = driver.execute_script("return arguments[0].parentNode;", download_images[0])
                                    if hasattr(parent, 'tag_name') and parent.tag_name.lower() == 'a':
                                        download_button = parent
                            except:
                                pass
                        if not download_button:
                            logger.warning(f"[교보] 다운로드 버튼을 찾을 수 없음: {title}")
                            continue
                        # 날짜 추출
                        date = None
                        date_match = re.search(r'(\d{4}/\d{2}/\d{2})', item_text)
                        if date_match:
                            date = date_match.group(1)
                        # 종목명, 분석가, 카테고리 추출
                        stock_name = None
                        analyst = None
                        category = None
                        lines = item_text.split('\n')
                        for line in lines:
                            if '기업분석' in line or '산업분석' in line or '채권전략' in line:
                                parts = line.split()
                                if len(parts) >= 1:
                                    category = parts[0]
                                if len(parts) >= 3:
                                    stock_name = parts[-2]
                                    analyst = parts[-1]
                        # 버튼 클릭
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_button)
                            time.sleep(1)
                            download_button.click()
                        except Exception as e:
                            try:
                                driver.execute_script("arguments[0].click();", download_button)
                            except Exception as js_e:
                                logger.error(f"[교보] 다운로드 버튼 클릭 실패: {e}, JS 오류: {js_e}")
                                continue
                        time.sleep(3)
                        # 다운로드된 파일 찾기
                        try:
                            files = os.listdir(download_path)
                            pdf_files = [f for f in files if f.endswith('.pdf') and not f.startswith('._')]
                            if not pdf_files:
                                logger.warning(f"[교보] PDF 파일을 찾을 수 없음: {title}")
                                continue
                            latest_file = max(pdf_files, key=lambda f: os.path.getmtime(os.path.join(download_path, f)))
                            downloaded_file = os.path.join(download_path, latest_file)
                            # 날짜별 폴더
                            if not date:
                                date_obj = datetime.now()
                            else:
                                try:
                                    if '/' in date:
                                        date_obj = datetime.strptime(date, '%Y/%m/%d')
                                    elif '-' in date:
                                        date_obj = datetime.strptime(date, '%Y-%m-%d')
                                    else:
                                        date_obj = datetime.now()
                                except:
                                    date_obj = datetime.now()
                            save_dir = get_save_dir(date_obj.strftime('%Y%m%d'), category)
                            os.makedirs(save_dir, exist_ok=True)
                            stock_name_clean = (stock_name or "").replace('/', '_').strip()
                            title_clean = title.replace('/', '_').strip()
                            date_for_filename = date_obj.strftime('%Y%m%d')
                            if stock_name_clean:
                                filename = f"{stock_name_clean}_{title_clean}_{date_for_filename}.pdf"
                            else:
                                filename = f"{title_clean}_{date_for_filename}.pdf"
                            filename = re.sub(r'[\\/:*?"<>|]', '', filename)
                            filename = filename[:150] + '.pdf' if len(filename) > 150 else filename
                            target_path = os.path.join(save_dir, filename)
                            if os.path.exists(target_path):
                                logger.info(f"[교보] 이미 존재: {target_path}")
                                continue
                            shutil.move(downloaded_file, target_path)
                            logger.info(f"[교보] 파일 저장 완료: {target_path}")
                        except Exception as e:
                            logger.error(f"[교보] 파일 이동 실패: {e}")
                    except Exception as e:
                        logger.error(f"[교보] 리포트 항목 처리 오류: {e}")
                        continue
            except Exception as e:
                logger = get_logger("DS")
                logger.error(f"[DS] {page}페이지 처리 오류: {e}")
                continue
        logger.info("[교보] 크롤링 완료")
    except Exception as e:
        logger.error(f"[교보] 전체 처리 오류: {e}")
    logger.info("[교보] 크롤링 종료")

def get_naver(driver: WebDriver, max_pages=5):
    logger = logging.getLogger("consensus_pipeline")
    import random
    base_url = "https://finance.naver.com"
    all_reports = []
    for page_num in range(1, max_pages + 1):
        url = f"https://finance.naver.com/research/company_list.naver?page={page_num}"
        print(f"[네이버] 리포트 목록 페이지 크롤링: {url}")
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'table.type_1'))
            )
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            trs = soup.select('table.type_1 > tbody > tr')
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) < 5:
                    continue
                stock_name = tds[0].get_text(strip=True)
                stock_code = ""
                stock_a = tds[0].find('a')
                if stock_a and 'code=' in stock_a['href']:
                    stock_code = stock_a['href'].split('code=')[-1]
                title = tds[1].get_text(strip=True)
                report_url = base_url + tds[1].find('a')['href'] if tds[1].find('a') else ""
                company = tds[2].get_text(strip=True)
                date = tds[4].get_text(strip=True)
                pdf_link = ""
                pdf_tag = tds[3].find('a', href=True)
                if pdf_tag and '.pdf' in pdf_tag['href']:
                    pdf_link = pdf_tag['href']
                    if not pdf_link.startswith('http'):
                        pdf_link = base_url + pdf_link
                all_reports.append({
                    'title': title,
                    'url': report_url,
                    'date': date,
                    'company': company,
                    'stock_name': stock_name,
                    'stock_code': stock_code,
                    'pdf_link': pdf_link
                })
            time.sleep(random.uniform(1.0, 2.0))
        except Exception as e:
            logger = get_logger("NAVER")
            logger.error(f"[네이버] {page_num}페이지 처리 오류: {e}")
            continue
    print(f"[네이버] 총 {len(all_reports)}개 리포트 수집 완료")
    # PDF 다운로드
    for report_info in all_reports:
        try:
            pdf_url = report_info.get('pdf_link', '')
            if not pdf_url or not pdf_url.endswith('.pdf'):
                continue
            date_str = report_info['date'].replace('.', '')
            safe_title = ''.join(c for c in report_info['title'] if c.isalnum() or c in ' _-')[:50]
            file_name = safe_filename(report_info['company'], report_info['stock_name']) + f"_{date_str}_{safe_title}.pdf"
            file_path = os.path.join(download_path, file_name)
            if os.path.exists(file_path):
                print(f"[네이버] 이미 다운로드된 파일: {file_name}")
                continue
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
                'Referer': 'https://finance.naver.com/research/company_list.naver'
            }
            response = requests.get(pdf_url, headers=headers)
            if response.status_code == 200 and response.content[:4] == b'%PDF':
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                print(f"[네이버] PDF 다운로드 완료: {file_name}")
            else:
                logger.error(f"[네이버] PDF 다운로드 실패: {pdf_url}")
            time.sleep(random.uniform(1.5, 4.0))
        except Exception as e:
            logger.error(f"[네이버] PDF 다운로드 오류: {e}")
            continue

def get_sangsangin(driver: WebDriver, max_pages=10):
    """
    상상인증권 리포트 PDF를 다운로드하는 함수입니다.
    driver: selenium WebDriver
    max_pages: 최대 크롤링 페이지 수
    """
    base_url = "https://www.sangsanginib.com/_upload/attFile/CM0079/CM0079_{report_num}_1.pdf"
    all_reports = []
    current_page = 1
    def collect_report_info():
        soup = BeautifulSoup(driver.page_source, "html.parser")
        report_info_list = []
        rows = soup.select("table tbody tr")
        for row in rows:
            cells = row.select("td")
            if len(cells) >= 5:
                report_num = cells[0].text.strip()
                stock_name = cells[1].text.strip()
                stock_code = cells[2].text.strip()
                title = cells[3].text.strip()
                reg_date = cells[4].text.strip()
                report_info_list.append({
                    "report_num": report_num,
                    "stock_name": stock_name,
                    "stock_code": stock_code,
                    "title": title,
                    "reg_date": reg_date
                })
        return report_info_list
    url = "https://www.sangsanginib.com/research/enterpriseReport/enterpriseReportView"
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
    )
    while current_page <= max_pages:
        print(f"[상상인] {current_page}페이지 정보 수집 중...")
        page_reports = collect_report_info()
        all_reports.extend(page_reports)
        try:
            next_button = driver.find_element(By.XPATH, "//a[contains(text(), '다음')]")
            next_button.click()
            time.sleep(2)
            current_page += 1
        except:
            print("[상상인] 마지막 페이지에 도달했거나 다음 페이지 버튼을 찾을 수 없습니다.")
            break
    print(f"[상상인] 총 {len(all_reports)}개 리포트 수집 완료")
    for report_info in all_reports:
        report_num = report_info["report_num"]
        stock_name = report_info["stock_name"]
        title = report_info["title"]
        reg_date = report_info["reg_date"].replace(".", "-")
        url = base_url.format(report_num=report_num)
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                save_folder = download_path
                os.makedirs(save_folder, exist_ok=True)
                filename = safe_filename(stock_name, "상상인") + f"_{report_num}.pdf"
                filename = "".join([c for c in filename if c.isalnum() or c in [' ', '.', '_', '-']]).strip()
                file_path = os.path.join(save_folder, filename)
                if os.path.exists(file_path):
                    print(f"[상상인] 이미 존재: {file_path}")
                    continue
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"[상상인] 다운로드 완료: {file_path}")
                time.sleep(1)
            else:
                print(f"[상상인] PDF 없음: {url}")
        except Exception as e:
            logger = get_logger("SANGSANGIN")
            logger.error(f"[상상인] 다운로드 오류 ({report_num}): {e}")
            continue

def get_shinhan(driver, max_pages=3, company="신한"):
    import re
    import requests
    from datetime import datetime
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    logger.info("[신한] 크롤링 시작")
    base_url = "https://m.shinhansec.com/mweb/invt/shrh/ishrh1001?tabIdx=1"
    try:
        driver.get(base_url)
        time.sleep(5)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".list__card-items"))
        )
        all_reports = []
        for page in range(1, max_pages+1):
            logger.info(f"[신한] {page}페이지 리포트 추출 중...")
            try:
                report_items = driver.find_elements(By.CSS_SELECTOR, ".list__card-items")
                for item in report_items:
                    try:
                        data_area = item.find_element(By.CSS_SELECTOR, ".list_data_area")
                        title = data_area.get_attribute("data-title")
                        subtitle = data_area.get_attribute("data-subtitle")
                        date = data_area.get_attribute("data-date")
                        author = data_area.get_attribute("data-nickname")
                        pdf_url = data_area.get_attribute("data-attachment_url")
                        category = data_area.get_attribute("data-gubun")
                        all_reports.append({
                            "title": title,
                            "subtitle": subtitle,
                            "date": date,
                            "author": author,
                            "pdf_url": pdf_url,
                            "category": category,
                            "stock_name": title
                        })
                    except Exception as e:
                        logger.error(f"[신한] 리포트 항목 처리 오류: {e}")
                # 다음 페이지/스크롤 (스크롤 다운)
                try:
                    report_container = driver.find_element(By.CSS_SELECTOR, ".lazy__list")
                    last_height = driver.execute_script("return arguments[0].scrollHeight", report_container)
                    driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", report_container)
                    time.sleep(2)
                    new_height = driver.execute_script("return arguments[0].scrollHeight", report_container)
                    if new_height == last_height:
                        logger.info("[신한] 더 이상 로드할 리포트 없음")
                        break
                except Exception as e:
                    logger.info(f"[신한] 스크롤/페이지 이동 종료: {e}")
                    break
            except Exception as e:
                logger.error(f"[신한] {page}페이지 리포트 추출 오류: {e}")
                break
        logger.info(f"[신한] 총 {len(all_reports)}개 리포트 추출 완료")
        # PDF 다운로드
        for report in all_reports:
            pdf_url = report.get("pdf_url")
            if not pdf_url:
                logger.warning(f"[신한] PDF URL 없음: {report.get('title')}")
                continue
            date_str = report.get("date")
            try:
                date_obj = datetime.strptime(date_str, "%Y.%m.%d")
            except Exception:
                date_obj = datetime.now()
            year = str(date_obj.year)
            month = f"{date_obj.month:02d}"
            day = f"{date_obj.day:02d}"
            save_dir = get_save_dir(date_obj.strftime('%Y%m%d'), company)
            os.makedirs(save_dir, exist_ok=True)
            sanitized_stock = re.sub(r'[\\/*?:"<>|]', "_", str(report['stock_name']))
            sanitized_title = re.sub(r'[\\/*?:"<>|]', "_", str(report['subtitle']).strip())
            file_name = safe_filename(sanitized_stock, sanitized_title) + f"_{date_obj.strftime('%Y%m%d')}.pdf"
            save_path = os.path.join(save_dir, file_name)
            if os.path.exists(save_path):
                logger.info(f"[신한] 이미 존재: {save_path}")
                continue
            try:
                resp = requests.get(pdf_url, stream=True, timeout=30)
                if resp.status_code == 200 and resp.content[:4] == b'%PDF':
                    with open(save_path, 'wb') as f:
                        f.write(resp.content)
                    logger.info(f"[신한] PDF 다운로드 완료: {save_path}")
                else:
                    logger.error(f"[신한] PDF 다운로드 실패 (상태 코드: {resp.status_code}): {pdf_url}")
            except Exception as e:
                logger.error(f"[신한] PDF 다운로드 오류: {e}")
            time.sleep(1)
    except Exception as e:
        logger.error(f"[신한] 전체 처리 오류: {e}")
    logger.info("[신한] 크롤링 종료")

def get_yj(driver=None):
    """
    유진투자증권 리포트 PDF를 다운로드하는 함수입니다.
    driver: 미사용 (호환성 위해 파라미터만 둠)
    """
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    import time
    url = "https://m.eugenefn.com/ii30r.do"
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    try:
        response = session.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        pdf_links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.endswith(".pdf") and "amail" in href:
                full_url = urljoin("https://www.eugenefn.com/", href)
                title = link.text.strip()
                pdf_links.append((title, full_url))
        print(f"[유진] 총 {len(pdf_links)}개 PDF 발견")
        for idx, (title, pdf_url) in enumerate(pdf_links, 1):
            try:
                filename = pdf_url.split("/")[-1]
                # 파일명에 제목 일부 추가 (중복 방지)
                safe_title = ''.join(c for c in title if c.isalnum() or c in ' _-')[:30]
                if safe_title:
                    filename = f"{safe_title}_{filename}"
                save_path = os.path.join(download_path, filename)
                if os.path.exists(save_path):
                    print(f"[유진] 이미 존재: {save_path}")
                    continue
                pdf_response = session.get(pdf_url, headers=headers)
                pdf_response.raise_for_status()
                with open(save_path, "wb") as f:
                    f.write(pdf_response.content)
                print(f"[유진] 다운로드 완료: {save_path}")
                time.sleep(1)
            except Exception as e:
                logger = get_logger("YUJIN")
                logger.error(f"[유진] 다운로드 오류: {e}")
        if not pdf_links:
            print("[유진] 오늘 리포트 없음")
    except Exception as e:
        logger = get_logger("YUJIN")
        logger.error(f"[유진] 페이지 접근 오류: {e}")

def get_yuanta(driver, max_pages=5, company="유안타"):
    import re
    import requests
    from datetime import datetime
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    logger.info("[유안타] 크롤링 시작")
    base_url = "https://www.myasset.com/myasset/research/rs_list/rs_list.cmd?cd006=&cd007=RE01&cd008="
    try:
        driver.get(base_url)
        time.sleep(5)
        # robust 페이지 수 확인
        try:
            soup = BeautifulSoup(driver.page_source, "html.parser")
            page_links = soup.select(".pagination a, .paging a, ul.pagination li a")
            page_numbers = [int(a.text) for a in page_links if a.text.isdigit()]
            total_pages = max(page_numbers) if page_numbers else 1
            pages_to_crawl = min(total_pages, max_pages)
        except Exception:
            pages_to_crawl = 1
        logger.info(f"[유안타] {pages_to_crawl}페이지 크롤링 예정")
        for page in range(1, pages_to_crawl + 1):
            if page > 1:
                moved = False
                selectors = [
                    f"//a[text()='{page}']",
                    f"//a[contains(@href, 'javascript:goPage({page})')]",
                    f"//a[@data-page='{page}']",
                    f"//li[@class='page-item']/a[text()='{page}']"
                ]
                for selector in selectors:
                    try:
                        page_link = driver.find_element(By.XPATH, selector)
                        page_link.click()
                        time.sleep(5)
                        moved = True
                        logger.info(f"[유안타] {page}페이지 이동 성공")
                        break
                    except:
                        continue
                if not moved:
                    logger.warning(f"[유안타] {page}페이지 이동 실패")
                    continue
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
                )
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            except Exception as e:
                logger.error(f"[유안타] 페이지 {page}에서 리포트 목록을 찾을 수 없음: {e}")
                continue
            logger.info(f"[유안타] 페이지 {page}에서 {len(rows)}개 리포트 발견")
            for idx, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 5:
                        continue
                    date = cells[0].text.strip()
                    stock = cells[1].text.strip() if len(cells) > 1 else "Unknown"
                    title = cells[3].text.strip() if len(cells) > 3 else "No Title"
                    attachment_cell = cells[4] if len(cells) > 4 else None
                    pdf_filename = None
                    pdf_link = None
                    if attachment_cell:
                        try:
                            pdf_filename_element = attachment_cell.find_element(By.TAG_NAME, "a")
                            pdf_filename = pdf_filename_element.text.strip()
                            pdf_link = pdf_filename_element.get_attribute("href")
                        except:
                            pdf_filename = None
                            pdf_link = None
                        # HTML에서 직접 추출
                        if not pdf_filename or not pdf_filename.endswith('.pdf'):
                            try:
                                html_source = attachment_cell.get_attribute("innerHTML")
                                if '_0_ko.pdf' in html_source:
                                    filename_match = re.search(r'(\d+_\d+_ko\.pdf)', html_source)
                                    if filename_match:
                                        pdf_filename = filename_match.group(1)
                            except:
                                pass
                    # robust 파일명 생성
                    date_str = date.replace('/', '')
                    safe_stock = re.sub(r'[\\/*?:"<>|]', '_', stock)
                    safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)[:50]
                    filename = safe_filename(safe_stock, safe_title) + f"_{date_str}.pdf"
                    # 날짜별 폴더
                    save_dir = get_save_dir(date_str, company)
                    os.makedirs(save_dir, exist_ok=True)
                    save_path = os.path.join(save_dir, filename)
                    if os.path.exists(save_path):
                        logger.info(f"[유안타] 이미 존재: {save_path}")
                        continue
                    # 1. 파일명 패턴으로 직접 URL 구성하여 다운로드 시도
                    if pdf_filename and ('_0_ko.pdf' in pdf_filename or '_ko.pdf' in pdf_filename):
                        date_match = re.match(r'(\d{4})(\d{2})(\d{2})(\d+)', pdf_filename)
                        if date_match:
                            year, month, day, time_part = date_match.groups()
                            pdf_url = f"https://file.myasset.com/sitemanager/upload/{year}/{month}{day}/{time_part[:6]}/{pdf_filename}"
                            try:
                                resp = requests.get(pdf_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=30)
                                if resp.status_code == 200:
                                    with open(save_path, 'wb') as f:
                                        for chunk in resp.iter_content(chunk_size=8192):
                                            if chunk:
                                                f.write(chunk)
                                    logger.info(f"[유안타] 파일명 패턴 다운로드 완료: {save_path}")
                                    continue
                                else:
                                    logger.error(f"[유안타] 파일명 패턴 PDF 다운로드 실패 (상태 코드: {resp.status_code}): {pdf_url}")
                            except Exception as e:
                                logger.error(f"[유안타] 파일명 패턴 PDF 다운로드 오류: {e}")
                    # 2. 직접 다운로드 시도 (pdf_link)
                    if pdf_link and pdf_link.endswith('.pdf'):
                        try:
                            resp = requests.get(pdf_link, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=30)
                            if resp.status_code == 200:
                                with open(save_path, 'wb') as f:
                                    for chunk in resp.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                                logger.info(f"[유안타] 직접 다운로드 완료: {save_path}")
                                continue
                            else:
                                logger.error(f"[유안타] 직접 PDF 다운로드 실패 (상태 코드: {resp.status_code}): {pdf_link}")
                        except Exception as e:
                            logger.error(f"[유안타] 직접 PDF 다운로드 오류: {e}")
                    # 3. 첨부파일 직접 클릭 (Selenium)
                    try:
                        if attachment_cell:
                            pdf_filename_element = attachment_cell.find_element(By.TAG_NAME, "a")
                            driver.execute_script("window.open(arguments[0].href, '_blank');", pdf_filename_element)
                            time.sleep(3)
                            if len(driver.window_handles) > 1:
                                driver.switch_to.window(driver.window_handles[-1])
                                pdf_url = driver.current_url
                                if pdf_url.endswith('.pdf'):
                                    try:
                                        resp = requests.get(pdf_url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True, timeout=30)
                                        if resp.status_code == 200:
                                            with open(save_path, 'wb') as f:
                                                for chunk in resp.iter_content(chunk_size=8192):
                                                    if chunk:
                                                        f.write(chunk)
                                            logger.info(f"[유안타] Selenium으로 다운로드 완료: {save_path}")
                                        else:
                                            logger.error(f"[유안타] Selenium PDF 다운로드 실패 (상태 코드: {resp.status_code}): {pdf_url}")
                                    except Exception as e:
                                        logger.error(f"[유안타] Selenium PDF 다운로드 오류: {e}")
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                    except Exception as e:
                        logger.error(f"[유안타] 첨부파일 클릭 오류: {e}")
                except Exception as e:
                    logger.error(f"[유안타] 행 처리 오류: {e}")
                    continue
        logger.info("[유안타] 크롤링 완료")
    except Exception as e:
        logger.error(f"[유안타] 전체 처리 오류: {e}")
    logger.info("[유안타] 크롤링 종료")

def get_save_dir(date_str, company):
    from datetime import datetime
    date_str = date_str.replace('.', '/').replace('-', '/').replace(' ', '')
    parts = date_str.split('/')
    if len(parts) == 3:
        year, month, day = parts
    else:
        now = datetime.now()
        year, month, day = now.strftime('%Y'), now.strftime('%m'), now.strftime('%d')
    save_dir = os.path.join(download_path, year, month, day, company.upper())
    os.makedirs(save_dir, exist_ok=True)
    return save_dir

def run_requests_crawlers():
    """
    requests 기반 크롤러를 병렬로 실행한다.
    """
    results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(get_ds): 'get_ds',
            executor.submit(get_hana, driver): 'get_hana',
            executor.submit(get_heungkuk): 'get_heungkuk',
            executor.submit(get_yj): 'get_yj',
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                results[name] = result
            except Exception as e:
                logger.error(f"{name} 실행 중 에러: {e}")
                results[name] = None
    return results

# Selenium 기반 크롤러(순차 실행)
if __name__ == "__main__":
    logger.info("크롤링 파이프라인 시작")
    # wait_for_downloads(download_path, timeout=100)
    # get_daishin(driver=driver)
    # get_kiwoom(driver=driver)
    # get_miraeasset(driver)
    # get_hankyung(driver)
    # get_bnk(driver=driver, max_pages=3, max_reports=10, logger=logger, company=None)
    # get_ds()
    # get_hana(driver)
    # get_heungkuk()
    # get_ibk(driver)
    # get_im()
    # get_kyobo(driver)
    # get_naver(driver)
    # get_sangsangin(driver)
    # get_shinhan(driver)
    # get_yj()
    # get_yuanta(driver)
    # get_kyobo(driver, max_pages=3, logger=None)
    logger.info("크롤링 파이프라인 종료")
