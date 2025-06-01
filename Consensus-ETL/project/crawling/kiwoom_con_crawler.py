import os
import re
import time
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 저장 경로 생성 (연도/월)
# 더보기 버튼 누르면 컨센서스 더 추가로 가져올 수 있음

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
download_path = os.path.join(PARENT_DIR, "consensus", "kiwoom")
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
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--disable-web-security')

driver = webdriver.Chrome(options=options)

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
        written_date = tds[6].text.strip().replace(".", "-")


        # Selenium WebElement에서 버튼을 찾음
        download_btn = tds[4].find_element(By.CLASS_NAME, "btn-filedown")
        download_btn.click()
        driver.execute_script("arguments[0].click();", download_btn)
        time.sleep(2)

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
        new_filename = f"{written_date}_{clean_title}_키움증권.pdf"
        new_path = os.path.join(download_path, new_filename)
        shutil.move(downloaded_file, new_path)
        print(f"[키움] 다운로드 완료: {new_filename}")
        downloaded_files.append(new_path)
        time.sleep(2)

    except Exception as e:
        print(f"[오류] {title} 처리 중 예외 발생: {e}")