
import requests
import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 상상인은 report_num만 조정해서 report 크롤링 가능

# Chrome 브라우저 설정
chrome_options = Options()
chrome_options.add_argument("--headless")  # 헤드리스 모드 (화면 표시 없음)
driver = webdriver.Chrome(options=chrome_options)

# 기본 다운로드 폴더 생성 (project/consensus/sangsangin)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # crawling 폴더
PROJECT_DIR = os.path.dirname(BASE_DIR)  # project 폴더
base_download_folder = os.path.join(PROJECT_DIR, "consensus", "sangsangin")
os.makedirs(base_download_folder, exist_ok=True)

# 기업리포트 페이지 접속
url = "https://www.sangsanginib.com/research/enterpriseReport/enterpriseReportView"
driver.get(url)

# 페이지 로딩 대기
WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
)

# 리포트 정보 수집 함수
def collect_report_info():
    soup = BeautifulSoup(driver.page_source, "html.parser")
    report_info_list = []
    
    # 테이블에서 리포트 정보 추출
    rows = soup.select("table tbody tr")
    print(f"총 테이블 행 수: {len(rows)}")
    
    for i, row in enumerate(rows):
        cells = row.select("td")
        print(f"\n--- 행 {i+1} (셀 개수: {len(cells)}) ---")
        
        # 모든 셀의 내용을 출력하여 구조 파악
        for j, cell in enumerate(cells):
            cell_text = cell.text.strip()
            print(f"셀 {j}: '{cell_text}'")
        
        if len(cells) >= 4:  # 최소 4개 셀이 있어야 처리
            # 첫 번째 셀은 번호
            report_num = cells[0].text.strip()
            
            # 실제 구조에 맞게 조정 필요
            # 임시로 다양한 패턴을 시도해보자
            if len(cells) >= 5:
                # 5개 셀: 번호, 종목명, 종목코드, 제목, 날짜
                stock_name = cells[1].text.strip()
                stock_code = cells[2].text.strip()
                title = cells[3].text.strip()
                reg_date = cells[4].text.strip()
            elif len(cells) == 4:
                # 4개 셀: 번호, 종목명, 제목, 날짜 또는 다른 구조
                stock_name = cells[1].text.strip()
                title = cells[2].text.strip()
                reg_date = cells[3].text.strip()
                stock_code = ""
            else:
                continue
            
            # 제목에서 불필요한 텍스트 제거
            title = title.replace("첨부파일 있음", "").strip()
            
            # 빈 값들 확인
            if not report_num or not stock_name or not title or not reg_date:
                print(f"빈 값 발견 - 번호: '{report_num}', 종목명: '{stock_name}', 제목: '{title}', 날짜: '{reg_date}'")
                continue
            
            print(f"✓ 추출완료 - 번호: {report_num}, 종목명: {stock_name}, 제목: {title}, 날짜: {reg_date}")
            
            report_info_list.append({
                "report_num": report_num,
                "stock_name": stock_name,
                "stock_code": stock_code, 
                "title": title,
                "reg_date": reg_date
            })
    
    return report_info_list

# 모든 페이지의 리포트 정보 수집
all_reports = []
current_page = 1
max_pages = 1  # 테스트를 위해 1페이지만 처리

while current_page <= max_pages:
    print(f"페이지 {current_page} 정보 수집 중...")
    
    # 현재 페이지의 리포트 정보 수집
    page_reports = collect_report_info()
    all_reports.extend(page_reports)
    
    # 다음 페이지 버튼 찾기
    try:
        next_button = driver.find_element(By.XPATH, "//a[contains(text(), '다음')]")
        next_button.click()
        
        # 페이지 로딩 대기
        time.sleep(2)
        current_page += 1
    except:
        print("마지막 페이지에 도달했거나 다음 페이지 버튼을 찾을 수 없습니다.")
        break

# 브라우저 종료
driver.quit()

# 기본 URL 패턴
base_url = "https://www.sangsanginib.com/_upload/attFile/CM0079/CM0079_{report_num}_1.pdf"

# PDF 다운로드 및 저장 함수
def download_pdf(report_info):
    report_num = str(int(report_info["report_num"]) + 108)
    stock_name = report_info["stock_name"]
    title = report_info["title"]
    reg_date = report_info["reg_date"]
    
    url = base_url.format(report_num=report_num)
    print(f"\n다운로드 시도: 번호={report_num}, 종목={stock_name}, 제목={title}, 날짜={reg_date}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            # URL에서 원본 파일명 추출
            filename = f"CM0079_{report_num}_1.pdf"
            file_path = os.path.join(base_download_folder, filename)
            
            with open(file_path, "wb") as f:
                f.write(response.content)
            
            print(f"✓ 성공: {filename} - 다운로드 완료 (종목: {stock_name}, 날짜: {reg_date})")
            return True
        else:
            print(f"✗ 실패: 리포트 번호 {report_num}에 해당하는 PDF 파일이 없습니다.")
            print(f"시도한 URL: {url}")
            return False
    
    except Exception as e:
        print(f"✗ 다운로드 중 오류 발생 ({report_num}): {e}")
        return False

# 수집한 모든 리포트 다운로드
for report_info in all_reports:
    download_result = download_pdf(report_info)
    
    # 서버에 과부하를 주지 않기 위해 성공적인 다운로드 후 잠시 대기
    if download_result:
        time.sleep(1)  # 1초 대기
