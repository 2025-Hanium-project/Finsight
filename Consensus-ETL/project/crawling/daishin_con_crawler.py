import shutil
from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver
from datetime import datetime, timedelta
import time
import os
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import logging
from config import LOG_DIR
import requests
from bs4 import BeautifulSoup

download_path = "daishin_consensus"
if not os.path.exists(download_path):
    os.makedirs(download_path)
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


options = webdriver.ChromeOptions()
options.add_experimental_option("prefs", prefs)
options.add_argument("--remote-allow-origins=*")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--headless=new")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--disable-web-security')

driver = webdriver.Chrome(options=options)

def get_logger(company):
    logger = logging.getLogger(f"{company.upper()}_logger")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler(os.path.join(LOG_DIR, f"{company.upper()}.log"), encoding="utf-8", mode="a")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

url = "http://money2.daishin.co.kr/E5/ResearchCenter/Work/Research_BasicList.aspx?pr_code=4"
driver.get(url)
downloaded_files = []
for i in range(5):
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
    table = driver.find_element(By.XPATH, "(//table)[1]")
    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
    row_ids = []

    for row in rows:
        tds = row.find_elements(By.TAG_NAME, "td")
        written_day = tds[0].text.strip()
        full_title = tds[1].text.strip()
        after_bracket = full_title.split("]")[-1]  # 마지막 ] 뒤 문자열
        stock_name = after_bracket.split(":")[0].strip()

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
    for row_id, stock_name in row_ids:
        try:
            print(row_id)
            # 상세 페이지 접속
            detail_url = f"http://money2.daishin.co.kr/E5/ResearchCenter/Work/Research_BasicRead.aspx?rowid={row_id}&pr_code=4&page=1"
            driver.get(detail_url)
            time.sleep(1)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            title_tag = soup.select_one("div.tbl_type09 th.subject")
            title = title_tag.text.strip() if title_tag else "제목 없음"
            post_date = None
            th_tags = soup.select("div.tbl_type09 th")
            for th in th_tags:
                if th.find("img", alt="게시일"):
                    td = th.find_next_sibling("td")
                    if td:
                        post_date = td.text.strip().split(" ")[0]
                    break
            print("제목:", title)
            print("게시일:", post_date)
            # a 태그 중 다운로드 링크 추출
            pdf_a_tag = soup.find("a", href=re.compile(r"filedownload\.aspx"))
            if not pdf_a_tag:
                print(f"[대신] PDF 링크 없음: {stock_name}")
                continue

            pdf_href = pdf_a_tag["href"]
            full_pdf_url = f"http://money2.daishin.co.kr{pdf_href}"

            # PDF 다운로드
            response = requests.get(full_pdf_url)
            if response.status_code == 200:
                filename = f"{post_date}_{stock_name}.pdf"
                # if not filename.endswith(".pdf"):
                #     filename = f"{stock_name}_대신증권.pdf"
                save_path = os.path.join(download_path, filename)
                with open(save_path, "wb") as f:
                    f.write(response.content)
                print(f"[대신] 다운로드 완료: {filename}")
            else:
                print(f"[대신] 다운로드 실패: {response.status_code} | {full_pdf_url}")
            time.sleep(1)

        except Exception as e:
            print(f"[대신] 예외 발생: {e}")
    
    url = "http://money2.daishin.co.kr/E5/ResearchCenter/Work/Research_BasicList.aspx?pr_code=4"
    driver.get(url)
    # click the next page button
    for k in range(1,i+1):
        next_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "id_ucPageSelect_id_btnRightPage")))
        next_btn.click()
        time.sleep(2)
