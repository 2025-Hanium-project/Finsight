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
import json

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
        time.sleep(10)  # 충분한 대기 시간 확보
        
        # 페이지 소스 확인 (디버깅용)
        log_message("페이지 소스 확인 중...")
        page_source = driver.page_source
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        
        # 페이지 구조 파악을 위해 스크린샷 저장
        driver.save_screenshot("page_screenshot.png")
        log_message("페이지 소스와 스크린샷 저장 완료")
        
        # 네트워크 요청 분석을 위한 JavaScript 실행
        try:
            # 페이지의 모든 network 요청 확인
            log_message("네트워크 요청 분석 중...")
            driver.execute_script("""
            var performanceEntries = window.performance.getEntries();
            return JSON.stringify(performanceEntries);
            """)
            
            # 모든 XHR 요청 분석
            xhr_requests = driver.execute_script("""
            var xhrRequests = [];
            var entries = window.performance.getEntries();
            for (var i = 0; i < entries.length; i++) {
                if (entries[i].initiatorType === 'xmlhttprequest') {
                    xhrRequests.push({
                        url: entries[i].name,
                        duration: entries[i].duration,
                        startTime: entries[i].startTime
                    });
                }
            }
            return JSON.stringify(xhrRequests);
            """)
            
            # XHR 요청 분석 결과 저장
            if xhr_requests:
                with open("xhr_requests.json", "w", encoding="utf-8") as f:
                    f.write(xhr_requests)
                log_message("XHR 요청 정보 저장 완료")
        except Exception as e:
            log_message(f"네트워크 요청 분석 중 오류: {str(e)}")
        
        # 페이지 로드 확인
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        log_message("리포트 페이지 로딩 완료")
        
        # 국내 종목 탭 클릭 (필요한 경우)
        try:
            # 탭 메뉴 존재 여부 확인
            tabs = driver.find_elements(By.CSS_SELECTOR, ".tab_list li, .tabs li, ul.tab li")
            if tabs:
                log_message(f"{len(tabs)}개의 탭 메뉴 발견")
                for i, tab in enumerate(tabs):
                    log_message(f"탭 {i+1}: {tab.text}")
                    
                # 국내 종목 탭 클릭 (첫 번째 또는 "국내" 텍스트 포함된 탭)
                for tab in tabs:
                    if "국내" in tab.text or tab.get_attribute("data-tab-idx") == "1":
                        log_message(f"'{tab.text}' 탭 클릭 중...")
                        tab.click()
                        time.sleep(3)  # 탭 전환 대기
                        break
        except Exception as e:
            log_message(f"탭 전환 중 오류: {str(e)}")
        
        # API 요청 직접 시도
        try:
            log_message("API 요청 직접 시도 중...")
            # 페이지에서 API 호출 시도
            api_response = driver.execute_script("""
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/mweb/invt/shrh/ishrh1001_list?tabIdx=1&pageIndex=1', false);
            xhr.send(null);
            return xhr.responseText;
            """)
            
            if api_response:
                log_message("API 응답 수신 성공")
                with open("api_response.json", "w", encoding="utf-8") as f:
                    f.write(api_response)
            else:
                log_message("API 응답 수신 실패")
        except Exception as e:
            log_message(f"API 요청 시도 중 오류: {str(e)}")
            
        return True
        
    except Exception as e:
        log_message(f"리포트 페이지 로딩 중 오류: {str(e)}")
        return False

def fetch_reports_via_api(driver, page_number=1):
    """API를 통해 리포트 데이터 직접 가져오기"""
    log_message(f"API를 통해 리포트 데이터 가져오기 (페이지 {page_number})...")
    reports = []
    
    try:
        # 직접 API URL로 요청
        api_url = f"https://m.shinhansec.com/mweb/invt/shrh/ishrh1001_list?tabIdx=1&pageIndex={page_number}"
        
        # requests 모듈로 직접 요청
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Referer": "https://m.shinhansec.com/mweb/invt/shrh/ishrh1001?tabIdx=1",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest"
        }
        
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            log_message("API 응답 성공")
            
            try:
                json_data = response.json()
                with open(f"api_response_page{page_number}.json", "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
                
                # JSON 구조 분석
                log_message("JSON 구조 분석 중...")
                
                # JSON 데이터에서 리포트 목록 찾기
                # 일반적인 구조는 data.list 또는 items 등의 형태
                report_items = None
                
                if 'data' in json_data and isinstance(json_data['data'], dict):
                    # data 필드가 있고 그것이 딕셔너리인 경우
                    data = json_data['data']
                    
                    # list, items, results 등의 일반적인 필드명 확인
                    for field in ['list', 'items', 'results', 'reports', 'content']:
                        if field in data and isinstance(data[field], list):
                            report_items = data[field]
                            log_message(f"리포트 목록 발견: data.{field}")
                            break
                    
                    # 특정 필드를 찾지 못한 경우 모든 리스트 타입 필드 찾기
                    if report_items is None:
                        for key, value in data.items():
                            if isinstance(value, list) and len(value) > 0:
                                report_items = value
                                log_message(f"리포트 목록 발견: data.{key}")
                                break
                elif 'items' in json_data and isinstance(json_data['items'], list):
                    # 루트 레벨에 items 필드가 있는 경우
                    report_items = json_data['items']
                    log_message("리포트 목록 발견: items")
                elif 'list' in json_data and isinstance(json_data['list'], list):
                    # 루트 레벨에 list 필드가 있는 경우
                    report_items = json_data['list']
                    log_message("리포트 목록 발견: list")
                
                # 리포트 아이템이 없으면 모든 리스트 타입 탐색
                if report_items is None:
                    for key, value in json_data.items():
                        if isinstance(value, list) and len(value) > 0:
                            report_items = value
                            log_message(f"리포트 목록 발견: {key}")
                            break
                
                if report_items and len(report_items) > 0:
                    log_message(f"{len(report_items)}개의 리포트 항목 발견")
                    
                    # 첫 번째 항목 구조 분석
                    first_item = report_items[0]
                    log_message(f"첫 번째 항목 구조: {first_item.keys() if isinstance(first_item, dict) else '딕셔너리 아님'}")
                    
                    # 리포트 정보 추출
                    for item in report_items:
                        if isinstance(item, dict):
                            # 필드명 매핑 (실제 JSON 구조에 맞게 수정 필요)
                            # 예시 필드명들로 시도
                            date_fields = ['date', 'reportDate', 'createdAt', 'pubDate', 'rptDt']
                            title_fields = ['title', 'reportTitle', 'rptTtl']
                            stock_fields = ['stockName', 'companyName', 'company', 'secNm']
                            pdf_fields = ['pdfUrl', 'fileUrl', 'attachmentUrl', 'fileDownUrl']
                            analyst_fields = ['analystName', 'author', 'writerNm']
                            
                            # 실제 필드명 찾기
                            date = None
                            for field in date_fields:
                                if field in item:
                                    date = item[field]
                                    break
                                    
                            title = None
                            for field in title_fields:
                                if field in item:
                                    title = item[field]
                                    break
                                    
                            stock_name = None
                            for field in stock_fields:
                                if field in item:
                                    stock_name = item[field]
                                    break
                                    
                            pdf_url = None
                            for field in pdf_fields:
                                if field in item and item[field]:
                                    pdf_url = item[field]
                                    # 상대 URL인 경우 기본 URL 추가
                                    if pdf_url.startswith('/'):
                                        pdf_url = f"https://m.shinhansec.com{pdf_url}"
                                    break
                                    
                            analyst = None
                            for field in analyst_fields:
                                if field in item:
                                    analyst = item[field]
                                    break
                            
                            # 필드를 찾지 못한 경우 모든 필드 탐색
                            if date is None or title is None or stock_name is None:
                                for key, value in item.items():
                                    log_message(f"필드: {key} = {value}")
                            
                            # 리포트 정보 저장
                            reports.append({
                                "date": date or "날짜 없음",
                                "stock_name": stock_name or "종목명 없음",
                                "title": title or "제목 없음",
                                "pdf_url": pdf_url,
                                "analyst": analyst or "정보 없음"
                            })
                            
                            log_message(f"리포트 추출: {stock_name} - {title}")
                else:
                    log_message("리포트 목록을 찾을 수 없음")
                    # 전체 JSON 구조 출력
                    log_message(f"JSON 구조: {json.dumps(json_data, ensure_ascii=False)[:500]}")
                    
            except json.JSONDecodeError:
                log_message("JSON 파싱 실패")
                with open(f"api_response_raw_page{page_number}.txt", "w", encoding="utf-8") as f:
                    f.write(response.text)
        else:
            log_message(f"API 요청 실패 (상태 코드: {response.status_code})")
    
    except Exception as e:
        log_message(f"API를 통한 리포트 가져오기 오류: {str(e)}")
    
    return reports

def extract_reports_from_html(driver):
    """HTML에서 리포트 정보 추출"""
    log_message("HTML에서 리포트 정보 추출 중...")
    reports = []
    
    # 페이지 소스 가져오기
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # 리포트 컨테이너 탐색 (다양한 선택자 시도)
    containers = [
        soup.select("ul.lst > li"),  # 일반적인 리스트 형태
        soup.select("table.board_list tbody tr"),  # 테이블 형태
        soup.select(".rpt-lst li"),  # 특정 클래스의 리스트
        soup.select(".report_list > li, .report_list > div"),  # 다른 형태
        soup.select(".report-container .item"),  # 또 다른 형태
    ]
    
    report_items = []
    for container in containers:
        if container:
            report_items = container
            log_message(f"{len(container)}개의 리포트 항목 발견")
            break
    
    if not report_items:
        log_message("HTML에서 리포트 항목을 찾을 수 없음")
        return []
    
    # 각 리포트 항목 처리
    for item in report_items:
        try:
            # 항목의 모든 텍스트와 링크 분석
            texts = [text.strip() for text in item.stripped_strings]
            links = item.select("a")
            
            if len(texts) < 3:  # 최소한의 정보가 없으면 스킵
                continue
                
            # 텍스트 배열에서 정보 추출 (위치 기반)
            date = texts[0] if len(texts) > 0 else "날짜 없음"
            stock_name = texts[1] if len(texts) > 1 else "종목명 없음"
            title = texts[2] if len(texts) > 2 else "제목 없음"
            analyst = texts[3] if len(texts) > 3 else "정보 없음"
            
            # PDF 링크 찾기
            pdf_url = None
            for link in links:
                href = link.get("href", "")
                if "pdf" in href.lower() or "download" in href.lower() or "file" in href.lower():
                    pdf_url = href
                    # 상대 URL인 경우 기본 URL 추가
                    if pdf_url.startswith('/'):
                        pdf_url = f"https://m.shinhansec.com{pdf_url}"
                    break
            
            reports.append({
                "date": date,
                "stock_name": stock_name,
                "title": title,
                "pdf_url": pdf_url,
                "analyst": analyst
            })
            
            log_message(f"리포트 추출: {stock_name} - {title}")
            
        except Exception as e:
            log_message(f"리포트 항목 처리 중 오류: {str(e)}")
    
    return reports

def download_pdf(driver, report):
    """PDF 다운로드"""
    # PDF URL이 없으면 건너뛰기
    if not report.get("pdf_url"):
        log_message(f"PDF URL 없음: {report['title']}")
        return False
    
    pdf_url = report["pdf_url"]
    log_message(f"PDF 다운로드 중: {pdf_url}")
    
    try:
        # 날짜 파싱 (형식: 2025.05.09 or 25.05.09)
        date_str = report["date"]
        
        # 날짜가 문자열이 아니면 현재 날짜 사용
        if not isinstance(date_str, str):
            date_obj = datetime.now()
            log_message(f"날짜가 문자열이 아님: {date_str}, 현재 날짜 사용")
        else:
            # 날짜 형식 정규화
            try:
                if len(date_str) == 8:  # YY.MM.DD 형식
                    date_obj = datetime.strptime(date_str, "%y.%m.%d")
                elif len(date_str) == 10:  # YYYY.MM.DD 형식
                    date_obj = datetime.strptime(date_str, "%Y.%m.%d")
                else:
                    # 날짜 형식이 다르면 현재 날짜 사용
                    date_obj = datetime.now()
                    log_message(f"날짜 형식 인식 불가: {date_str}, 현재 날짜 사용")
            except ValueError:
                date_obj = datetime.now()
                log_message(f"날짜 형식 파싱 실패: {date_str}, 현재 날짜 사용")
        
        year = date_obj.year
        month = date_obj.month
        day = date_obj.day
        
        # 저장 경로 생성
        save_dir = os.path.join(DOWNLOAD_DIR, str(year), f"{month:02d}", f"{day:02d}")
        os.makedirs(save_dir, exist_ok=True)
        
        # 파일명 생성 (종목명_제목_날짜.pdf)
        sanitized_stock = re.sub(r'[\\/*?:"<>|]', "_", str(report['stock_name']))
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "_", str(report['title']))
        file_name = f"{sanitized_stock}_{sanitized_title}_{date_obj.strftime('%Y%m%d')}.pdf"
        save_path = os.path.join(save_dir, file_name)
        
        # 이미 파일이 존재하는 경우 스킵
        if os.path.exists(save_path):
            log_message(f"이미 존재하는 파일 건너뛰기: {save_path}")
            return True
        
        # PDF 다운로드 방식 1: requests 사용
        try:
            response = requests.get(pdf_url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                log_message(f"PDF 다운로드 완료: {save_path}")
                return True
            else:
                log_message(f"PDF 다운로드 실패 (상태 코드: {response.status_code})")
        except Exception as e:
            log_message(f"requests로 PDF 다운로드 중 오류: {str(e)}")
            
            # 방식 1 실패 시 방식 2: Selenium 사용
            try:
                # 새 탭에서 PDF 열기
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[1])
                driver.get(pdf_url)
                
                # PDF가 다운로드될 때까지 대기
                time.sleep(5)
                
                # 다운로드된 파일이 있는지 확인
                downloaded_files = os.listdir(DOWNLOAD_DIR)
                if downloaded_files:
                    # 가장 최근에 다운로드된 파일
                    latest_file = max([os.path.join(DOWNLOAD_DIR, f) for f in downloaded_files if os.path.isfile(os.path.join(DOWNLOAD_DIR, f))], 
                                    key=os.path.getctime)
                    
                    # 파일 이동
                    os.rename(latest_file, save_path)
                    log_message(f"Selenium으로 PDF 다운로드 완료: {save_path}")
                    
                    # 탭 닫기
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    return True
                
                # 탭 닫기
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                log_message("Selenium으로 PDF 다운로드 실패")
                return False
                
            except Exception as e:
                log_message(f"Selenium으로 PDF 다운로드 중 오류: {str(e)}")
                
                # 열린 탭 정리
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    
                return False
    
    except Exception as e:
        log_message(f"PDF 다운로드 처리 중 오류: {str(e)}")
        return False

def save_metadata(reports):
    """메타데이터 저장"""
    if not reports:
        log_message("저장할 리포트 메타데이터가 없음")
        return None
        
    log_message(f"{len(reports)}개 리포트의 메타데이터 저장 중...")
    df = pd.DataFrame(reports)
    
    # 날짜 열 변환 시도
    try:
        # 날짜 열을 문자열로 변환
        df['date'] = df['date'].astype(str)
        
        # YY.MM.DD 또는 YYYY.MM.DD 형식 처리
        date_converted = []
        for date_str in df['date']:
            try:
                if len(date_str) == 8:  # YY.MM.DD 형식
                    date_obj = datetime.strptime(date_str, "%y.%m.%d")
                elif len(date_str) == 10:  # YYYY.MM.DD 형식
                    date_obj = datetime.strptime(date_str, "%Y.%m.%d")
                else:
                    # 날짜 형식이 다르면 원래 값 유지
                    date_obj = date_str
                
                # datetime 객체면 일관된 형식으로 변환
                if isinstance(date_obj, datetime):
                    date_converted.append(date_obj.strftime("%Y-%m-%d"))
                else:
                    date_converted.append(date_str)
            except:
                date_converted.append(date_str)
                
        df['date_normalized'] = date_converted
    except Exception as e:
        log_message(f"날짜 형식 변환 실패: {str(e)}. 원래 형식 유지.")
    
    # CSV로 저장
    metadata_path = os.path.join(DOWNLOAD_DIR, "report_metadata.csv")
    df.to_csv(metadata_path, index=False, encoding="utf-8-sig")
    log_message(f"메타데이터 저장 완료: {metadata_path}")
    
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
        
        # 방법 1: API를 통해 리포트 가져오기
        reports = fetch_reports_via_api(driver)
        
        # 방법 1이 실패하면 방법 2: HTML에서 리포트 추출
        if not reports:
            log_message("API를 통한 방법 실패, HTML에서 직접 추출 시도...")
            reports = extract_reports_from_html(driver)
        
        if not reports:
            log_message("리포트 추출 실패. 크롤링 종료.")
            return
        
        log_message(f"총 {len(reports)}개의 리포트 추출 완료")
        
        # 각 리포트에 대해 PDF 다운로드
        for report in reports:
            download_pdf(driver, report)
            # 서버 부하 방지를 위한 대기
            time.sleep(1)
        
        # 메타데이터 저장
        save_metadata(reports)
        
        # 완료 시간 및 소요 시간 기록
        end_time = datetime.now()
        duration = end_time - start_time
        log_message(f"크롤링 완료: {end_time}")
        log_message(f"총 소요 시간: {duration}")
        
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
