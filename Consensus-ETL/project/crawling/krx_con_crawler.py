import requests
import os
import time
from datetime import datetime
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, UnexpectedAlertPresentException
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import json

# 설정
BASE_URL = "http://data.krx.co.kr/contents/MDC/HARD/hardController/MDCHARD003.cmd"
KRX_MAIN = "http://data.krx.co.kr"
ALTERNATIVE_URLS = [
    "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201030300",
    "http://data.krx.co.kr/contents/MDC/HARD/hardController/MDCHARD003.cmd",
    "http://data.krx.co.kr/contents/MDC/99/MDC99bld.jsp?menuId=MDC0201030300"
]

# 저장 디렉토리 설정 (project/consensus/krx)
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
DOWNLOAD_DIR = os.path.join(project_root, "project", "consensus", "krx")

def log_message(message):
    """로그 메시지 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    print(log_entry)
    # 로그 파일에도 저장
    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"krx_download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def setup_driver():
    """웹 드라이버 설정"""
    log_message("웹 드라이버 설정 중...")
    
    chrome_options = Options()
    # 디버깅을 위해 헤드리스 모드 비활성화
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # User-Agent 설정
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 다운로드 디렉토리 설정
    prefs = {
        "download.default_directory": os.path.abspath(DOWNLOAD_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True,
        # 다중 다운로드 자동 허용
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.content_settings.exceptions.automatic_downloads.*,*.setting": 1,
        "profile.default_content_settings.multiple-automatic-downloads": 1
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # 추가 Chrome 옵션 - 다운로드 관련 보안 설정
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins-discovery")
    chrome_options.add_argument("--disable-default-apps")
    
    # 자동 다운로드 허용을 위한 추가 설정
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # 웹 드라이버 초기화
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_page_load_timeout(30)
    
    return driver

def check_service_availability(driver, url):
    """서비스 이용 가능성 확인"""
    log_message(f"서비스 이용 가능성 확인: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)
        
        # 페이지 소스 확인
        page_source = driver.page_source.lower()
        
        # 서비스 이용 불가 메시지 확인
        unavailable_keywords = [
            "service unavailable", 
            "서비스 이용 불가", 
            "일시적 접근 불안정",
            "점검중",
            "maintenance"
        ]
        
        for keyword in unavailable_keywords:
            if keyword in page_source:
                log_message(f"서비스 이용 불가 감지: {keyword}")
                return False
        
        return True
        
    except Exception as e:
        log_message(f"서비스 확인 중 오류: {str(e)}")
        return False

def try_alternative_access(driver):
    """대안 경로로 접근 시도"""
    log_message("대안 경로로 접근 시도 중...")
    
    # 1. KRX 메인 페이지부터 접근
    try:
        log_message(f"KRX 메인 페이지 접근: {KRX_MAIN}")
        driver.get(KRX_MAIN)
        time.sleep(5)
        
        # 메인 페이지에서 분석보고서 링크 찾기
        analysis_links = driver.find_elements(By.XPATH, "//a[contains(text(), '분석보고서') or contains(@href, 'MDCHARD')]")
        
        if analysis_links:
            log_message(f"{len(analysis_links)}개의 분석보고서 링크 발견")
            analysis_links[0].click()
            time.sleep(5)
            
            if check_service_availability(driver, driver.current_url):
                log_message("메인 페이지를 통한 접근 성공")
                return True
                
    except Exception as e:
        log_message(f"메인 페이지 접근 실패: {str(e)}")
    
    # 2. 대안 URL들 시도
    for alt_url in ALTERNATIVE_URLS:
        try:
            log_message(f"대안 URL 시도: {alt_url}")
            if check_service_availability(driver, alt_url):
                log_message("대안 URL 접근 성공")
                return True
                
        except Exception as e:
            log_message(f"대안 URL 접근 실패: {str(e)}")
            continue
    
    return False

def wait_for_dynamic_content(driver, max_wait=30):
    """동적 콘텐츠 로딩 대기 - KRX 특화"""
    log_message("동적 콘텐츠 로딩 대기 중...")
    
    # KRX 페이지에서 실제 데이터 로딩을 기다려야 함
    # 1. 기본 페이지 로딩 대기
    time.sleep(5)
    
    # 2. 데이터 테이블 또는 다운로드 버튼이 나타날 때까지 대기
    wait_conditions = [
        # 다운로드 버튼 (가장 중요)
        (By.CSS_SELECTOR, "button.btn_download"),
        (By.CSS_SELECTOR, ".btn_download"),
        
        # 데이터 테이블
        (By.CSS_SELECTOR, "table"),
        (By.CSS_SELECTOR, "tbody tr"),
        
        # 콘텐츠 영역
        (By.CSS_SELECTOR, ".CI-MDI-COMPONENT-WRAP"),
        (By.CSS_SELECTOR, ".content"),
    ]
    
    for by, selector in wait_conditions:
        try:
            WebDriverWait(driver, max_wait).until(
                EC.presence_of_element_located((by, selector))
            )
            log_message(f"콘텐츠 로딩 완료: {selector}")
            
            # 추가 대기 - JavaScript 데이터 로딩 완료
            time.sleep(3)
            return True
            
        except TimeoutException:
            continue
    
    log_message("동적 콘텐츠 로딩 시간 초과")
    return False

def debug_page_structure(driver):
    """페이지 구조 디버깅"""
    log_message("페이지 구조 분석 중...")
    
    try:
        # 페이지 제목 확인
        title = driver.title
        log_message(f"페이지 제목: {title}")
        
        # 현재 URL 확인
        current_url = driver.current_url
        log_message(f"현재 URL: {current_url}")
        
        # HTML 구조 분석
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # 주요 태그들 개수 확인
        tags_info = {
            'table': len(soup.find_all('table')),
            'div': len(soup.find_all('div')),
            'ul': len(soup.find_all('ul')),
            'li': len(soup.find_all('li')),
            'a': len(soup.find_all('a')),
            'button': len(soup.find_all('button'))
        }
        
        log_message(f"HTML 태그 개수: {tags_info}")
        
        # 클래스명이 포함된 주요 요소들 찾기
        elements_with_classes = soup.find_all(attrs={"class": True})
        unique_classes = set()
        for elem in elements_with_classes:
            classes = elem.get('class')
            if isinstance(classes, list):
                unique_classes.update(classes)
        
        log_message(f"발견된 CSS 클래스 (샘플): {list(unique_classes)[:20]}")
        
        # ID가 있는 요소들 찾기
        elements_with_ids = soup.find_all(attrs={"id": True})
        unique_ids = [elem.get('id') for elem in elements_with_ids]
        
        log_message(f"발견된 ID (샘플): {unique_ids[:10]}")
        
        # 페이지 소스 샘플 저장 (디버깅용)
        debug_file = os.path.join(DOWNLOAD_DIR, "page_source_debug.html")
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(page_source)
        log_message(f"페이지 소스 저장: {debug_file}")
        
        return soup
        
    except Exception as e:
        log_message(f"페이지 구조 분석 중 오류: {str(e)}")
        return None

def extract_reports_advanced(driver, soup=None):
    """향상된 리포트 추출 방법"""
    log_message("향상된 방법으로 리포트 정보 추출 시도...")
    
    if soup is None:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
    
    reports = []
    
    # 방법 1: 테이블 기반 추출 (기존 방법 개선)
    log_message("방법 1: 테이블 기반 추출 시도...")
    reports.extend(extract_from_tables(soup))
    
    # 방법 2: 리스트 기반 추출
    log_message("방법 2: 리스트 기반 추출 시도...")
    reports.extend(extract_from_lists(soup))
    
    # 방법 3: 링크 기반 추출
    log_message("방법 3: 링크 기반 추출 시도...")
    reports.extend(extract_from_links(soup))
    
    # 방법 4: JavaScript 데이터 추출
    log_message("방법 4: JavaScript 데이터 추출 시도...")
    reports.extend(extract_from_javascript(driver))
    
    # 중복 제거
    unique_reports = []
    seen_titles = set()
    
    for report in reports:
        title = report.get('title', '')
        if title and title not in seen_titles:
            unique_reports.append(report)
            seen_titles.add(title)
    
    log_message(f"추출된 고유 리포트: {len(unique_reports)}개")
    return unique_reports

def extract_from_tables(soup):
    """테이블에서 리포트 추출 - 실제 데이터 테이블 중심"""
    reports = []
    
    # 실제 데이터를 포함한 테이블만 찾기
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        
        if len(rows) < 2:  # 헤더 + 최소 1개 데이터 행
            continue
        
        # 테이블 내용이 실제 보고서 데이터인지 확인
        sample_text = table.get_text()
        if not any(keyword in sample_text for keyword in ['보고서', '분석', '리포트', 'PDF', '다운로드']):
            continue
            
        log_message(f"실제 데이터 테이블 발견: {len(rows)-1}개 행")
        
        for row in rows[1:]:  # 헤더 제외
            cells = row.find_all(['td', 'th'])
            if len(cells) < 3:  # 최소 3컬럼 필요
                continue
            
            # 셀 내용 확인
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            
            # 빈 행이나 의미없는 행 건너뛰기
            if not any(text for text in cell_texts):
                continue
            
            # 기본 정보 추출 (컬럼 순서 추정)
            report = {
                'title': '',
                'author': '',
                'date': '',
                'company': '',
                'pdf_url': '',
                'stock_name': ''
            }
            
            # 컬럼별 데이터 할당 (일반적인 순서: 제목, 회사명, 작성기관, 날짜)
            if len(cells) >= 4:
                report['title'] = cells[0].get_text(strip=True)
                report['company'] = cells[1].get_text(strip=True)
                report['author'] = cells[2].get_text(strip=True)
                report['date'] = cells[3].get_text(strip=True)
            elif len(cells) >= 3:
                report['title'] = cells[0].get_text(strip=True)
                report['author'] = cells[1].get_text(strip=True)
                report['date'] = cells[2].get_text(strip=True)
            
            # 다운로드 버튼 찾기 (btn_download 클래스)
            download_buttons = row.find_all('button', class_='btn_download')
            if download_buttons:
                data_index = download_buttons[0].get('data-index', '')
                if data_index:
                    report['pdf_url'] = f"btn_download_{data_index}"
                    log_message(f"다운로드 버튼 발견: {report['title'][:30]}... (data-index: {data_index})")
            
            # 링크 찾기
            if not report['pdf_url']:
                links = row.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    if href and ('.pdf' in href.lower() or 'download' in href.lower()):
                        report['pdf_url'] = urljoin(BASE_URL, href)
                        break
            
            # 유효한 리포트만 추가
            if report['title'] and len(report['title']) > 5:  # 제목이 의미있는 길이
                report['stock_name'] = report['company']  # 회사명을 종목명으로 사용
                reports.append(report)
                log_message(f"리포트 추출: {report['title'][:50]}... - {report['author']}")
    
    return reports

def extract_from_lists(soup):
    """리스트 구조에서 리포트 추출 - KRX 특화"""
    reports = []
    
    # KRX의 특정 리스트 구조 찾기 (btn_download가 있는 li들)
    download_items = soup.find_all('li')
    
    valid_items = []
    for item in download_items:
        # btn_download 버튼이 있는 항목만 선별
        download_btn = item.find('button', class_='btn_download')
        if download_btn:
            valid_items.append(item)
    
    if not valid_items:
        log_message("다운로드 버튼이 있는 리스트 항목을 찾을 수 없음")
        return reports
    
    log_message(f"유효한 리스트 항목 발견: {len(valid_items)}개")
    
    for item in valid_items:
        try:
            # 제목 추출 (dt 태그)
            dt_element = item.find('dt')
            title = dt_element.get_text(strip=True) if dt_element else ''
            
            # 종목명 추출
            stock_span = item.find('span', string=lambda text: text and '종목명' in text)
            stock_name = ''
            if stock_span and stock_span.next_sibling:
                stock_name = stock_span.next_sibling.strip()
            
            # 작성기관 추출
            author_span = item.find('span', string=lambda text: text and '작성기관' in text)
            author = ''
            if author_span and author_span.next_sibling:
                author = author_span.next_sibling.strip()
            
            # 등록일 추출
            date_span = item.find('span', string=lambda text: text and '등록일' in text)
            date = ''
            if date_span and date_span.next_sibling:
                date = date_span.next_sibling.strip()
            
            # 다운로드 버튼에서 data-index 추출
            download_btn = item.find('button', class_='btn_download')
            pdf_url = ''
            if download_btn:
                data_index = download_btn.get('data-index', '')
                if data_index:
                    pdf_url = f"btn_download_{data_index}"
            
            # 리포트 정보 구성
            if title and pdf_url:
                report = {
                    'title': title,
                    'author': author,
                    'date': date,
                    'stock_name': stock_name,
                    'pdf_url': pdf_url,
                    'company': stock_name  # 회사명과 종목명 동일하게 처리
                }
                
                reports.append(report)
                log_message(f"리포트 추출: {title[:50]}... - {stock_name} - data-index: {data_index}")
                
        except Exception as e:
            log_message(f"리스트 항목 처리 중 오류: {str(e)}")
            continue
    
    return reports

def extract_from_links(soup):
    """모든 링크에서 PDF 다운로드 링크 추출"""
    reports = []
    
    # PDF 또는 다운로드 관련 링크 찾기
    pdf_links = soup.find_all('a', href=lambda x: x and ('.pdf' in x.lower() or 'download' in x.lower()))
    
    log_message(f"PDF/다운로드 링크 발견: {len(pdf_links)}개")
    
    for link in pdf_links:
        href = link.get('href')
        text = link.get_text(strip=True)
        
        # 부모 요소에서 추가 정보 추출
        parent = link.find_parent(['tr', 'li', 'div'])
        parent_text = parent.get_text(strip=True) if parent else ''
        
        report = {
            'title': text or parent_text,
            'author': '',
            'date': '',
            'pdf_url': urljoin(BASE_URL, href),
            'stock_name': ''
        }
        
        if report['title']:
            reports.append(report)
    
    return reports

def extract_from_javascript(driver):
    """JavaScript에서 데이터 추출"""
    reports = []
    
    try:
        # JavaScript 변수에서 데이터 추출 시도
        js_data_scripts = [
            "return window.reportData || [];",
            "return window.dataList || [];", 
            "return window.reports || [];",
            "return typeof gridData !== 'undefined' ? gridData : [];",
            "return typeof tableData !== 'undefined' ? tableData : [];"
        ]
        
        for script in js_data_scripts:
            try:
                result = driver.execute_script(script)
                if result and isinstance(result, list):
                    log_message(f"JavaScript 데이터 발견: {len(result)}개 항목")
                    
                    for item in result:
                        if isinstance(item, dict):
                            report = {
                                'title': item.get('title', item.get('name', '')),
                                'author': item.get('author', item.get('institution', '')),
                                'date': item.get('date', item.get('publishDate', '')),
                                'pdf_url': item.get('downloadUrl', item.get('url', '')),
                                'stock_name': item.get('stockName', item.get('company', ''))
                            }
                            
                            if report['title']:
                                reports.append(report)
                    break
                    
            except Exception as e:
                continue
    
    except Exception as e:
        log_message(f"JavaScript 데이터 추출 중 오류: {str(e)}")
    
    return reports

def navigate_to_reports(driver):
    """리포트 페이지로 이동 (개선된 버전)"""
    log_message(f"리포트 페이지로 이동 시도: {BASE_URL}")
    
    # 1. 기본 URL 시도
    if check_service_availability(driver, BASE_URL):
        log_message("기본 URL 접근 성공")
        return True
    
    # 2. 대안 방법 시도
    if try_alternative_access(driver):
        log_message("대안 경로 접근 성공")
        return True
    
    log_message("모든 접근 방법 실패")
    return False

def handle_download_permission_dialog(driver):
    """다운로드 권한 요청 대화상자 자동 처리"""
    try:
        # JavaScript로 권한 요청 미리 승인
        driver.execute_script("""
            // 다중 다운로드 권한 자동 승인
            if (navigator.permissions && navigator.permissions.query) {
                navigator.permissions.query({name: 'downloads'}).then(function(result) {
                    if (result.state === 'prompt') {
                        console.log('다운로드 권한 요청됨');
                    }
                });
            }
            
            // 자동 다운로드 허용 설정
            window.addEventListener('beforeunload', function(e) {
                return undefined;
            });
        """)
        
        # 페이지 레벨에서 다운로드 권한 설정
        driver.execute_cdp_cmd('Page.setDownloadBehavior', {
            'behavior': 'allow',
            'downloadPath': os.path.abspath(DOWNLOAD_DIR)
        })
        
        log_message("다운로드 권한 자동 승인 설정 완료")
        
    except Exception as e:
        log_message(f"다운로드 권한 설정 중 오류: {str(e)}")

def main():
    """메인 실행 함수 (개선된 버전)"""
    start_time = datetime.now()
    log_message(f"KRX 크롤링 시작: {start_time}")
    
    # 다운로드 디렉토리 생성
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    driver = None
    try:
        # 웹 드라이버 설정
        driver = setup_driver()
        
        # 다운로드 권한 자동 승인 설정
        handle_download_permission_dialog(driver)
        
        # 리포트 페이지로 이동
        if not navigate_to_reports(driver):
            log_message("리포트 페이지 접근 실패. 크롤링 종료.")
            return
        
        # 동적 콘텐츠 로딩 대기
        wait_for_dynamic_content(driver)
        
        # 페이지 구조 디버깅
        soup = debug_page_structure(driver)
        
        # 향상된 방법으로 리포트 추출
        reports = extract_reports_advanced(driver, soup)
        
        if not reports:
            log_message("리포트를 찾을 수 없습니다. 수동 확인이 필요할 수 있습니다.")
            
            # 사용자에게 상황 안내
            log_message("다음을 확인해주세요:")
            log_message("1. KRX 웹사이트 접속 가능 여부")
            log_message("2. 웹사이트 구조 변경 여부") 
            log_message("3. 로그인 요구사항 변경 여부")
            return
        
        log_message(f"총 {len(reports)}개의 리포트를 찾았습니다.")
        
        # 리포트 정보 출력 (처음 3개)
        for i, report in enumerate(reports[:3]):
            log_message(f"리포트 {i+1}: {report['title'][:50]}...")
        
        # 메타데이터 저장
        save_metadata(reports)
        
        # PDF 다운로드
        log_message("PDF 다운로드 시작...")
        success_count = 0
        
        for i, report in enumerate(reports):
            log_message(f"다운로드 진행: {i+1}/{len(reports)}")
            
            pdf_url = report.get("pdf_url")
            if pdf_url:
                if download_pdf(pdf_url, report, driver):
                    success_count += 1
            
            # 서버 부하 방지를 위한 대기
            time.sleep(2)
        
        # 완료 시간 및 소요 시간 기록
        end_time = datetime.now()
        duration = end_time - start_time
        log_message(f"크롤링 완료: {end_time}")
        log_message(f"총 소요 시간: {duration}")
        log_message(f"총 {len(reports)}개 리포트 중 {success_count}개 다운로드 완료")
        
    except Exception as e:
        log_message(f"크롤링 중 오류 발생: {str(e)}")
        import traceback
        log_message(traceback.format_exc())
        
    finally:
        # 드라이버 종료
        if driver:
            driver.quit()
            log_message("웹 드라이버 종료")

def download_pdf(pdf_url, report, driver=None):
    """PDF 다운로드 (기존 함수 유지)"""
    if not pdf_url:
        log_message(f"PDF URL 없음: {report['title']}")
        return False
    
    # 버튼 클릭 방식 다운로드 시도
    if pdf_url.startswith('btn_download_') and driver:
        if download_pdf_by_button_click(driver, report):
            return True
    
    log_message(f"PDF 다운로드 중: {pdf_url}")
    
    try:
        # 날짜 파싱 및 정리
        date_str = report["date"]
        try:
            if '.' in date_str:
                date_obj = datetime.strptime(date_str, "%Y.%m.%d")
            elif '-' in date_str:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                date_obj = datetime.now()
            formatted_date = date_obj.strftime("%Y%m%d")
        except ValueError:
            log_message(f"날짜 형식 파싱 실패: {date_str}, 현재 날짜 사용")
            formatted_date = datetime.now().strftime("%Y%m%d")
        
        # 저장 디렉토리 생성
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        
        # 파일명 생성 (KRX_제목_날짜.pdf)
        def sanitize_filename(filename):
            return re.sub(r'[\\/*?:"<>|]', "_", filename)
        
        sanitized_title = sanitize_filename(report['title'])
        
        # 제목이 너무 긴 경우 줄이기
        if len(sanitized_title) > 100:
            sanitized_title = sanitized_title[:100]
        
        file_name = f"KRX_{sanitized_title}_{formatted_date}.pdf"
        save_path = os.path.join(DOWNLOAD_DIR, file_name)
        
        # 이미 파일이 존재하는 경우 스킵
        if os.path.exists(save_path):
            log_message(f"이미 존재하는 파일 건너뛰기: {save_path}")
            return True
        
        # PDF 다운로드
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": BASE_URL
        }
        
        # 세션 생성
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(pdf_url, stream=True, timeout=30)
        if response.status_code == 200:
            # Content-Type 확인
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' in content_type.lower() or 'application/octet-stream' in content_type:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # 파일 크기 확인
                file_size = os.path.getsize(save_path)
                if file_size > 1024:  # 1KB 이상인 경우만 성공으로 간주
                    log_message(f"PDF 다운로드 완료: {save_path} ({file_size} bytes)")
                    return True
                else:
                    log_message(f"PDF 파일이 너무 작음: {file_size} bytes, 삭제")
                    os.remove(save_path)
                    return False
            else:
                log_message(f"PDF가 아닌 콘텐츠 타입: {content_type}")
                return False
        else:
            log_message(f"PDF 다운로드 실패 (상태 코드: {response.status_code}): {pdf_url}")
            return False
            
    except Exception as e:
        log_message(f"PDF 다운로드 처리 중 오류: {str(e)}")
        return False

def download_pdf_by_button_click(driver, report):
    """다운로드 버튼 클릭을 통한 PDF 다운로드"""
    if not report.get('pdf_url') or not report['pdf_url'].startswith('btn_download_'):
        return False
    
    data_index = report['pdf_url'].split('_')[-1]
    log_message(f"다운로드 버튼 클릭 시도 (data-index: {data_index})")
    
    try:
        # 페이지가 로드된 상태에서 버튼 찾기
        download_button = None
        
        # 여러 방법으로 버튼 찾기 시도
        button_selectors = [
            f"button.btn_download[data-index='{data_index}']",
            f"button[data-index='{data_index}']",
            f".btn_download[data-index='{data_index}']",
            f"[data-index='{data_index}']"
        ]
        
        for selector in button_selectors:
            try:
                download_button = driver.find_element(By.CSS_SELECTOR, selector)
                log_message(f"다운로드 버튼 발견: {selector}")
                break
            except NoSuchElementException:
                continue
        
        if not download_button:
            log_message(f"다운로드 버튼을 찾을 수 없음 (data-index: {data_index})")
            return False
        
        # 버튼이 클릭 가능한지 확인
        if not download_button.is_enabled():
            log_message("다운로드 버튼이 비활성화됨")
            return False
        
        # 다운로드 전 파일 목록 확인
        download_dir_files_before = set(os.listdir(DOWNLOAD_DIR)) if os.path.exists(DOWNLOAD_DIR) else set()
        
        # 버튼 클릭 (JavaScript 실행)
        driver.execute_script("arguments[0].click();", download_button)
        log_message(f"다운로드 버튼 클릭됨 (data-index: {data_index})")
        
        # 잠시 대기하여 다운로드 시작 확인
        time.sleep(3)
        
        # 다운로드 완료 대기 (최대 60초)
        for wait_time in range(60):
            time.sleep(1)
            if os.path.exists(DOWNLOAD_DIR):
                download_dir_files_after = set(os.listdir(DOWNLOAD_DIR))
                new_files = download_dir_files_after - download_dir_files_before
                
                # 새로운 파일이 생성되었는지 확인
                for new_file in new_files:
                    file_path = os.path.join(DOWNLOAD_DIR, new_file)
                    
                    # .crdownload 파일은 다운로드 진행중
                    if new_file.endswith('.crdownload'):
                        log_message(f"다운로드 진행중: {new_file}")
                        continue
                    
                    # PDF 파일 확인
                    if new_file.endswith('.pdf') and os.path.getsize(file_path) > 1024:
                        # 파일명 정리 (KRX 형식으로)
                        sanitized_title = re.sub(r'[\\/*?:"<>|]', "_", report['title'][:100])
                        new_filename = f"KRX_{sanitized_title}_{datetime.now().strftime('%Y%m%d')}.pdf"
                        new_file_path = os.path.join(DOWNLOAD_DIR, new_filename)
                        
                        # 파일명 변경
                        try:
                            os.rename(file_path, new_file_path)
                            log_message(f"다운로드 완료: {new_filename}")
                            return True
                        except:
                            log_message(f"다운로드 완료: {new_file}")
                            return True
        
        log_message(f"다운로드 타임아웃 (60초) - data-index: {data_index}")
        return False
        
    except Exception as e:
        log_message(f"버튼 클릭 다운로드 실패: {str(e)}")
        return False

def save_metadata(reports):
    """메타데이터 저장 (기존 함수 유지)"""
    if not reports:
        log_message("저장할 리포트 메타데이터가 없음")
        return None
        
    log_message(f"{len(reports)}개 리포트의 메타데이터 저장 중...")
    df = pd.DataFrame(reports)
    
    # CSV로 저장
    metadata_path = os.path.join(DOWNLOAD_DIR, "krx_consensus_reports.csv")
    df.to_csv(metadata_path, index=False, encoding="utf-8-sig")
    log_message(f"메타데이터 저장 완료: {metadata_path}")
    
    return df

if __name__ == "__main__":
    main()
