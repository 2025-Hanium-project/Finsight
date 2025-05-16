import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime
import pandas as pd
import re
import PyPDF2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 설정
BASE_URL = "https://m.shinhansec.com/mweb/invt/shrh/ishrh1001?tabIdx=1"
DOWNLOAD_DIR = "reports"
LOG_FILE = "crawling_log.txt"

def log_message(message):
    """로그 메시지 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    print(log_entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def setup_driver():
    """웹 드라이버 설정"""
    log_message("웹 드라이버 설정 중...")
    
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # 디버깅 동안 헤드리스 비활성화
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # User-Agent 설정 (크롤링 차단 방지)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    # 다운로드 디렉토리 설정
    prefs = {
        "download.default_directory": os.path.abspath(DOWNLOAD_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True  # PDF를 브라우저에서 열지 않고 다운로드
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # 웹 드라이버 초기화
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_page_load_timeout(30)  # 페이지 로드 타임아웃 설정
    
    return driver

def navigate_to_reports(driver):
    """리포트 페이지로 이동"""
    log_message(f"리포트 페이지로 이동 중: {BASE_URL}")
    try:
        driver.get(BASE_URL)
        
        # 페이지 로드 대기 (페이지 전체가 로드될 때까지 기다림)
        time.sleep(5)  # 충분한 대기 시간 확보
        
        # 페이지 로드 확인 (리포트 항목이 로드될 때까지 대기)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".list__card-items"))
        )
        log_message("리포트 페이지 로딩 완료")
        
        # 페이지 소스 확인 (디버깅용)
        log_message("페이지 소스 확인 중...")
        page_source = driver.page_source
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        
        # 페이지 구조 파악을 위해 스크린샷 저장
        driver.save_screenshot("page_screenshot.png")
        log_message("페이지 소스와 스크린샷 저장 완료")
        
        return True
        
    except Exception as e:
        log_message(f"리포트 페이지 로딩 중 오류: {str(e)}")
        return False

def extract_reports_from_page(driver):
    """페이지에서 리포트 정보 추출"""
    log_message("페이지에서 리포트 정보 추출 중...")
    reports = []
    
    try:
        # 리포트 항목 찾기
        report_items = driver.find_elements(By.CSS_SELECTOR, ".list__card-items")
        log_message(f"{len(report_items)}개의 리포트 항목 발견")
        
        for item in report_items:
            try:
                # data 속성에서 정보 추출
                data_area = item.find_element(By.CSS_SELECTOR, ".list_data_area")
                
                # 데이터 속성 추출
                title = data_area.get_attribute("data-title")
                subtitle = data_area.get_attribute("data-subtitle")
                date = data_area.get_attribute("data-date")
                author = data_area.get_attribute("data-nickname")
                pdf_url = data_area.get_attribute("data-attachment_url")
                category = data_area.get_attribute("data-gubun")
                
                # 리포트 정보 저장
                reports.append({
                    "title": title,
                    "subtitle": subtitle,
                    "date": date,
                    "author": author,
                    "pdf_url": pdf_url,
                    "category": category,
                    "stock_name": title  # 종목명은 title과 동일함
                })
                
                log_message(f"리포트 추출: {title} - {subtitle}")
                
            except Exception as e:
                log_message(f"리포트 항목 처리 중 오류: {str(e)}")
                
        return reports
        
    except Exception as e:
        log_message(f"리포트 정보 추출 중 오류: {str(e)}")
        return []

def click_next_page(driver):
    """다음 페이지로 이동"""
    try:
        # 현재 활성화된 탭 찾기
        active_tab = driver.find_element(By.CSS_SELECTOR, ".tab-menu__list-item.active")
        tab_index = driver.find_elements(By.CSS_SELECTOR, ".tab-menu__list-item").index(active_tab) + 1
        
        # 현재 탭의 리포트 목록 컨테이너
        report_container = driver.find_element(By.CSS_SELECTOR, f"#tab{tab_index} .lazy__list")
        
        # 스크롤을 아래로 내려 더 많은 리포트 로드
        log_message("스크롤을 내려 더 많은 리포트 로드 중...")
        last_height = driver.execute_script("return arguments[0].scrollHeight", report_container)
        
        # 스크롤 다운 실행
        driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", report_container)
        time.sleep(2)
        
        # 새로운 높이 확인
        new_height = driver.execute_script("return arguments[0].scrollHeight", report_container)
        
        # 스크롤 후 높이가 같으면 더 이상 로드할 항목이 없음
        if new_height == last_height:
            log_message("더 이상 로드할 리포트가 없음")
            return False
        
        log_message("추가 리포트 로드 성공")
        return True
        
    except Exception as e:
        log_message(f"다음 페이지 로드 중 오류: {str(e)}")
        return False

def download_pdf(pdf_url, report):
    """PDF 다운로드"""
    if not pdf_url:
        log_message(f"PDF URL 없음: {report['title']}")
        return False
    
    log_message(f"PDF 다운로드 중: {pdf_url}")
    
    try:
        # 날짜 파싱
        date_str = report["date"]
        try:
            date_obj = datetime.strptime(date_str, "%Y.%m.%d")
        except ValueError:
            log_message(f"날짜 형식 파싱 실패: {date_str}, 현재 날짜 사용")
            date_obj = datetime.now()
        
        year = date_obj.year
        month = date_obj.month
        day = date_obj.day
        
        # 저장 경로 생성
        save_dir = os.path.join(DOWNLOAD_DIR, str(year), f"{month:02d}", f"{day:02d}")
        os.makedirs(save_dir, exist_ok=True)
        
        # 파일명 생성 (종목명_제목_날짜.pdf)
        sanitized_stock = re.sub(r'[\\/*?:"<>|]', "_", report['stock_name'])
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "_", report['subtitle'].strip())
        file_name = f"{sanitized_stock}_{sanitized_title}_{date_str.replace('.', '')}.pdf"
        save_path = os.path.join(save_dir, file_name)
        
        # 이미 파일이 존재하는 경우 스킵
        if os.path.exists(save_path):
            log_message(f"이미 존재하는 파일 건너뛰기: {save_path}")
            return True
        
        # PDF 다운로드
        response = requests.get(pdf_url, stream=True, timeout=30)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            log_message(f"PDF 다운로드 완료: {save_path}")
            return True
        else:
            log_message(f"PDF 다운로드 실패 (상태 코드: {response.status_code})")
            return False
            
    except Exception as e:
        log_message(f"PDF 다운로드 처리 중 오류: {str(e)}")
        return False

def extract_pdf_content(pdf_path):
    """PDF 내용 추출"""
    log_message(f"PDF 내용 추출 중: {pdf_path}")
    
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text()
            
            return text
    except Exception as e:
        log_message(f"PDF 내용 추출 중 오류: {str(e)}")
        return ""

def parse_pdf_content(text, report):
    """PDF 내용 파싱"""
    log_message(f"PDF 내용 파싱 중: {report['title']}")
    
    data = {
        "종목명": report["stock_name"],
        "제목": report["subtitle"],
        "작성일": report["date"],
        "애널리스트": report["author"],
        "카테고리": report["category"],
        "투자의견": None,
        "목표가": None,
        "요약": None
    }
    
    # 투자의견 추출 (다양한 패턴)
    opinion_patterns = [
        r'투자의견[:\s]*([\w\s가-힣]+)',
        r'투자의견/목표가[:\s]*([\w\s가-힣]+)',
        r'(매수|중립|매도)'
    ]
    
    for pattern in opinion_patterns:
        match = re.search(pattern, text)
        if match:
            data["투자의견"] = match.group(1).strip()
            break
    
    # 목표가 추출
    target_patterns = [
        r'목표가[:\s]*([0-9,]+원)',
        r'목표가[:\s]*([0-9,]+)',
        r'TP[:\s]*([0-9,]+)'
    ]
    
    for pattern in target_patterns:
        match = re.search(pattern, text)
        if match:
            data["목표가"] = match.group(1).strip()
            break
    
    # 요약 추출 (300자 이내)
    summary_patterns = [
        r'요약[:\s]*([\s\S]{10,1000}?)(?=\n\n|\r\n\r\n|$)',
        r'투자포인트[:\s]*([\s\S]{10,1000}?)(?=\n\n|\r\n\r\n|$)',
        r'코멘트[:\s]*([\s\S]{10,1000}?)(?=\n\n|\r\n\r\n|$)'
    ]
    
    for pattern in summary_patterns:
        match = re.search(pattern, text)
        if match:
            summary = match.group(1).strip()
            # 요약 길이 제한
            if len(summary) > 300:
                summary = summary[:297] + "..."
            data["요약"] = summary
            break
    
    return data

def save_metadata(reports):
    """메타데이터 저장"""
    if not reports:
        log_message("저장할 리포트 메타데이터가 없음")
        return None
        
    log_message(f"{len(reports)}개 리포트의 메타데이터 저장 중...")
    df = pd.DataFrame(reports)
    
    # CSV로 저장
    metadata_path = os.path.join(DOWNLOAD_DIR, "report_metadata.csv")
    df.to_csv(metadata_path, index=False, encoding="utf-8-sig")
    log_message(f"메타데이터 저장 완료: {metadata_path}")
    
    return df

def save_parsed_content(parsed_data):
    """파싱된 PDF 내용 저장"""
    if not parsed_data:
        log_message("저장할 파싱 데이터가 없음")
        return None
        
    log_message(f"{len(parsed_data)}개 파싱 결과 저장 중...")
    df = pd.DataFrame(parsed_data)
    
    # CSV로 저장
    parsed_path = os.path.join(DOWNLOAD_DIR, "parsed_reports.csv")
    df.to_csv(parsed_path, index=False, encoding="utf-8-sig")
    log_message(f"파싱 결과 저장 완료: {parsed_path}")
    
    return df

def main():
    """메인 실행 함수"""
    # 시작 시간 기록
    start_time = datetime.now()
    log_message(f"크롤링 시작: {start_time}")
    
    # 다운로드 디렉토리 생성
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    driver = None
    try:
        # 웹 드라이버 설정
        driver = setup_driver()
        
        # 리포트 페이지로 이동
        if not navigate_to_reports(driver):
            log_message("리포트 페이지 로딩 실패. 크롤링 종료.")
            return
        
        # 국내 탭이 이미 선택되어 있음 (tabIdx=1 파라미터로 인해)
        log_message("국내 리포트 탭이 선택됨")
        
        # 전체 리포트 목록
        all_reports = []
        
        # 첫 페이지 리포트 추출
        reports = extract_reports_from_page(driver)
        all_reports.extend(reports)
        
        # 스크롤을 통해 더 많은 리포트 로드 (최대 5페이지까지)
        for page in range(2, 6):
            log_message(f"추가 리포트 로드 시도 ({page}번째)...")
            
            # 다음 페이지 로드 시도
            if click_next_page(driver):
                # 새로 로드된 리포트 추출
                time.sleep(3)  # 로드 대기
                new_reports = extract_reports_from_page(driver)
                
                # 새 리포트가 없으면 종료
                if not new_reports:
                    log_message("더 이상 새 리포트가 없습니다.")
                    break
                    
                all_reports.extend(new_reports)
            else:
                log_message("더 이상 로드할 페이지가 없습니다.")
                break
        
        log_message(f"총 {len(all_reports)}개의 리포트를 찾았습니다.")
        
        # 메타데이터 저장
        save_metadata(all_reports)
        
        # PDF 다운로드 및 내용 파싱
        log_message("PDF 다운로드 및 내용 파싱 시작...")
        parsed_data = []
        
        for report in all_reports:
            pdf_url = report.get("pdf_url")
            if pdf_url:
                # PDF 다운로드
                download_success = download_pdf(pdf_url, report)
                
                if download_success:
                    # 다운로드된 PDF 경로 찾기
                    date_obj = datetime.strptime(report["date"], "%Y.%m.%d")
                    year = date_obj.year
                    month = date_obj.month
                    day = date_obj.day
                    
                    # 저장 디렉토리
                    save_dir = os.path.join(DOWNLOAD_DIR, str(year), f"{month:02d}", f"{day:02d}")
                    
                    # 파일명 패턴 생성
                    sanitized_stock = re.sub(r'[\\/*?:"<>|]', "_", report['stock_name'])
                    file_pattern = f"{sanitized_stock}_*_{date_obj.strftime('%Y%m%d')}.pdf"
                    
                    # 해당 패턴의 파일 찾기
                    pdf_files = [f for f in os.listdir(save_dir) if f.startswith(sanitized_stock) and f.endswith(f"_{date_obj.strftime('%Y%m%d')}.pdf")]
                    
                    if pdf_files:
                        pdf_path = os.path.join(save_dir, pdf_files[0])
                        
                        # PDF 내용 추출
                        pdf_text = extract_pdf_content(pdf_path)
                        
                        if pdf_text:
                            # PDF 내용 파싱
                            parsed_info = parse_pdf_content(pdf_text, report)
                            parsed_data.append(parsed_info)
                
            # 서버 부하 방지를 위한 대기
            time.sleep(1)
        
        # 파싱 결과 저장
        save_parsed_content(parsed_data)
        
        # 완료 시간 및 소요 시간 기록
        end_time = datetime.now()
        duration = end_time - start_time
        log_message(f"크롤링 완료: {end_time}")
        log_message(f"총 소요 시간: {duration}")
        log_message(f"총 {len(all_reports)}개 리포트 중 {len(parsed_data)}개 파싱 완료")
        
    except Exception as e:
        log_message(f"크롤링 중 오류 발생: {str(e)}")
        import traceback
        log_message(traceback.format_exc())
        
    finally:
        # 드라이버 종료
        if driver:
            driver.quit()
            log_message("웹 드라이버 종료")

if __name__ == "__main__":
    main()
