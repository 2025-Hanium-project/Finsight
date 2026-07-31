import os
import sys
import time
import logging
import re
import requests
import ssl
import urllib3
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin, urlparse

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# 프로젝트 구조 기반 다운로드 경로 정의
BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # 현재 파이썬 파일 위치
PARENT_DIR = os.path.dirname(BASE_DIR)                         # 상위 (즉, project/)
DOWNLOAD_DIR = os.path.join(PARENT_DIR, "consensus", "ibks")   # 최종 저장 위치
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# 로깅 설정
def setup_logger():
    log_dir = os.path.join(DOWNLOAD_DIR, 'logs')  # 이전: os.getcwd()

    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'ibks_crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    logger = logging.getLogger('ibks_crawler')
    logger.setLevel(logging.INFO)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    console_handler = logging.StreamHandler()
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 기본 다운로드 폴더 생성
def create_download_directory():
    logger.info(f"다운로드 기본 디렉토리 생성: {DOWNLOAD_DIR}")
    return DOWNLOAD_DIR

# 날짜별 폴더 생성
def create_date_directory(base_dir, date_str):
    return base_dir

# Selenium 드라이버 설정
def setup_driver(download_dir):
    logger.info("Selenium 웹드라이버 설정")
    
    # 크롬 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # 최신 헤드리스 모드
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
    # SSL/네트워크 견고성 옵션 추가
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--ignore-certificate-errors-spki-list")
    chrome_options.add_argument("--ignore-ssl-errors-on-localhost")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    
    # PDF 다운로드 설정
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome 웹드라이버 초기화 성공")
        return driver
    except Exception as e:
        logger.error(f"웹드라이버 초기화 실패: {str(e)}")
        raise

# IBK투자증권 모바일 기업분석 페이지 크롤링
def crawl_ibks_company_analysis(start_date=None, days=7):
    """일주일치 기업분석 보고서 수집

    Returns:
        int: 종료 코드 (0=성공, 1=실패). Airflow가 재시도할 수 있게 전파한다.
    """
    base_url = "https://m.ibks.com/iko/IKO010201.do"
    base_dir = create_download_directory()
    # 시작일 설정 (기본값: 오늘)
    if start_date is None:
        start_date = datetime.now()
    # 일주일간의 날짜 생성
    date_range = [(start_date - timedelta(days=i)).strftime("%Y.%m.%d") for i in range(days)]
    date_range_short = [(start_date - timedelta(days=i)).strftime("%Y%m%d") for i in range(days)]
    logger.info(f"크롤링 기간: {date_range[-1]} ~ {date_range[0]}")
    
    # 웹드라이버 설정
    driver = setup_driver(base_dir)

    # 한 건이라도 받으면 0으로 바꾼다. 아무것도 못 받으면 실패로 끝낸다.
    exit_code = 1

    try:
        # 기업분석 페이지 접속
        logger.info(f"기업분석 페이지 접속: {base_url}")
        driver.get(base_url)
        
        # 페이지 로딩 대기 (최대 10초)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # 페이지 로딩 시간 부여 (더 길게 설정)
        time.sleep(5)
        # 1. 직접 API 호출 시도
        html_success = pattern_success = False
        api_success = try_api_approach(driver, date_range, base_dir)

        if not api_success:
            # 2. HTML 구조 분석 시도
            html_success = try_html_approach(driver, date_range, base_dir)
            
            if not html_success:
                # 3. 텍스트 패턴 기반 접근 시도
                pattern_success = try_pattern_approach(driver, date_range, base_dir)
                
                if not pattern_success:
                    logger.warning("모든 접근 방법 실패. 직접 코드 수정이 필요할 수 있습니다.")

        # 세 방법 중 하나라도 보고서를 받았으면 성공. 한 건도 없으면 사이트 구조 변경으로 본다.
        if api_success or html_success or pattern_success:
            exit_code = 0

    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}")
        exit_code = 1
    finally:
        # 드라이버 종료
        try:
            driver.quit()
            logger.info("웹드라이버 종료")
        except:
            pass

    logger.info("크롤링 완료")
    return exit_code

# API 기반 접근 방법
def try_api_approach(driver, date_range, base_dir):
    logger.info("API 기반 접근 방법 시도")
    success = False
    
    try:
        # 네트워크 요청 분석을 통해 발견한 API 엔드포인트
        # IBK 투자증권은 다음과 같은 API 형태를 사용할 가능성이 높음
        api_endpoints = [
            "https://m.ibks.com/iko/IKO010201.do?action=list",
            "https://m.ibks.com/iko/service/getReportList.do",
            "https://m.ibks.com/iko/api/getReportList.do"
        ]
        
        # 쿠키 및 세션 정보 수집
        cookies = driver.get_cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        
        # 헤더 설정
        headers = {
            'User-Agent': driver.execute_script("return navigator.userAgent"),
            'Referer': driver.current_url,
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        session = create_secure_session()
        for name, value in cookie_dict.items():
            session.cookies.set(name, value)
        
        for endpoint in api_endpoints:
            try:
                logger.info(f"API 엔드포인트 시도: {endpoint}")
                response = session.get(endpoint, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"API 응답 성공: {endpoint}")
                    
                    # JSON 응답인지 확인
                    try:
                        data = response.json()
                        logger.info("JSON 응답 데이터 발견")
                        
                        # 데이터 구조 분석 및 보고서 추출
                        reports = extract_reports_from_json(data)
                        
                        if reports:
                            logger.info(f"{len(reports)}개 보고서 발견")
                            success = process_api_reports(reports, date_range, base_dir, driver)
                            if success:
                                break
                    except ValueError:
                        # HTML 응답인 경우
                        logger.info("HTML 응답 데이터 발견")
            except Exception as e:
                logger.error(f"API 엔드포인트 {endpoint} 시도 중 오류: {str(e)}")
        
        # 성공 여부에 관계없이 디버그용 API 응답 저장
        # for i, endpoint in enumerate(api_endpoints):
        #     try:
        #         response = session.get(endpoint, headers=headers, timeout=10)
        #         debug_file = os.path.join(base_dir, f'api_response_{i+1}.txt')
        #         with open(debug_file, 'w', encoding='utf-8') as f:
        #             f.write(response.text)
        #         logger.info(f"API 응답 저장: {debug_file}")
        #     except:
        #         pass
        
        return success
    
    except Exception as e:
        logger.error(f"API 접근 방법 오류: {str(e)}")
        return False

# JSON 응답에서 보고서 추출
def extract_reports_from_json(data):
    reports = []
    
    # 일반적인 JSON 구조 탐색
    if isinstance(data, dict):
        # 가능한 키 이름들
        possible_keys = ['data', 'list', 'items', 'reports', 'result', 'reportList']
        
        for key in possible_keys:
            if key in data and isinstance(data[key], list):
                return data[key]
        
        # 깊이 1단계 탐색
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0:
                return value
            elif isinstance(value, dict):
                for inner_key, inner_value in value.items():
                    if isinstance(inner_value, list) and len(inner_value) > 0:
                        return inner_value
    
    return reports

# API로 가져온 보고서 처리
def process_api_reports(reports, date_range, base_dir, driver):
    success = False
    processed_count = 0
    
    for report in reports:
        try:
            # 날짜 필드 찾기
            date_str = None
            company_name = None
            download_url = None
            report_id = None
            
            # 일반적인 필드명 시도
            date_fields = ['date', 'regdate', 'reg_date', 'createdate', 'reportdate', 'rptDt']
            for field in date_fields:
                if field in report and report[field]:
                    date_value = report[field]
                    date_match = re.search(r'(\d{4}[-\.\/]\d{2}[-\.\/]\d{2}|\d{8})', str(date_value))
                    if date_match:
                        date_str = date_match.group(1).replace('-', '.').replace('/', '.')
                        if len(date_str) == 8:  # YYYYMMDD 형식
                            date_str = f"{date_str[:4]}.{date_str[4:6]}.{date_str[6:8]}"
                        break
            
            # 종목명 필드 찾기
            name_fields = ['title', 'name', 'companyName', 'rptTtl', 'subject']
            for field in name_fields:
                if field in report and report[field]:
                    title_text = report[field]
                    company_match = re.search(r'\[(.*?)\]', str(title_text))
                    if company_match:
                        company_name = company_match.group(1)
                        break
                    else:
                        company_name = title_text.split()[0] if title_text.split() else "Report"
                        break
            
            # 다운로드 URL 또는 ID 찾기
            url_fields = ['url', 'fileUrl', 'downloadUrl', 'fileDownloadUrl', 'attatchUrl']
            id_fields = ['id', 'reportId', 'seq', 'rptSeq', 'rptId']
            
            for field in url_fields:
                if field in report and report[field]:
                    download_url = report[field]
                    break
            
            for field in id_fields:
                if field in report and report[field]:
                    report_id = report[field]
                    break
            
            # 날짜 확인
            if date_str and date_str in date_range:
                logger.info(f"보고서 발견: {company_name}, {date_str}")
                processed = False
                
                # 다운로드 URL이 있는 경우
                if download_url:
                    try:
                        # URL이 상대 경로인 경우 절대 경로로 변환
                        if not download_url.startswith('http'):
                            download_url = urljoin(driver.current_url, download_url)
                        
                        # 다운로드 실행
                        processed = download_with_requests(driver, download_url, company_name, date_str.replace('.', ''), base_dir)
                        if processed:
                            processed_count += 1
                    except Exception as e:
                        logger.error(f"API 보고서 다운로드 중 오류: {str(e)}")
                
                # 보고서 ID만 있는 경우
                elif report_id:
                    try:
                        # 추정 다운로드 URL 생성
                        download_url = construct_download_url(driver.current_url, report_id)
                        
                        # 다운로드 실행
                        processed = download_with_requests(driver, download_url, company_name, date_str.replace('.', ''), base_dir)
                        if processed:
                            processed_count += 1
                    except Exception as e:
                        logger.error(f"API 보고서 ID 기반 다운로드 중 오류: {str(e)}")
        
        except Exception as e:
            logger.error(f"API 보고서 처리 중 오류: {str(e)}")
    
    logger.info(f"API 접근 방법으로 {processed_count}개 보고서 처리 완료")
    return processed_count > 0

# 보고서 ID 기반 다운로드 URL 구성
def construct_download_url(base_url, report_id):
    # URL 패턴 추정
    parsed_url = urlparse(base_url)
    base_path = os.path.dirname(parsed_url.path)
    
    # 가능한 다운로드 URL 패턴들
    possible_patterns = [
        f"{parsed_url.scheme}://{parsed_url.netloc}{base_path}/download.do?seq={report_id}",
        f"{parsed_url.scheme}://{parsed_url.netloc}{base_path}/fileDownload.do?reportId={report_id}",
        f"{parsed_url.scheme}://{parsed_url.netloc}/iko/IKO01/download.do?seq={report_id}&menuCode=IKO010201&attatchCd=ATTATCH1"
    ]
    
    logger.info(f"다운로드 URL 추정: {possible_patterns[0]}")
    return possible_patterns[0]  # 첫 번째 패턴 반환

# HTML 구조 분석 접근 방법
def try_html_approach(driver, date_range, base_dir):
    logger.info("HTML 구조 분석 접근 방법 시도")
    success = False
    processed_count = 0
    downloaded_files = set()  # 이미 다운로드한 파일 추적
    
    try:
        # 모든 텍스트 요소 추출 및 분석
        all_elements = driver.find_elements(By.XPATH, "//*[text()]")
        report_elements = []
        
        for element in all_elements:
            try:
                text = element.text.strip()
                if text and ('[' in text and ']' in text) and len(text) > 5:
                    # 보고서 제목 형태를 가진 요소 수집
                    report_elements.append(element)
                    logger.info(f"잠재적 보고서 제목 발견: {text}")
            except:
                continue
        
        logger.info(f"{len(report_elements)}개의 잠재적 보고서 요소 발견")
        
        # 중복 제거를 위한 처리된 보고서 추적
        processed_reports = set()
        
        for element in report_elements:
            try:
                # 요소 주변 텍스트 수집 (부모 요소) - 예외 처리 강화
                parent = None
                parent_text = ""
                
                try:
                    # 부모 요소 찾기 시도
                    parent = element.find_element(By.XPATH, "./..")
                    parent_text = parent.text
                except Exception as parent_error:
                    # 부모 요소 접근 실패 시 현재 요소 사용
                    logger.warning(f"부모 요소 접근 실패: {str(parent_error)}")
                    parent = element
                    parent_text = element.text
                
                # 날짜 추출
                date_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', parent_text)
                if date_match:
                    report_date = date_match.group(1)
                    logger.info(f"보고서 날짜: {report_date}")
                    
                    if report_date in date_range:
                        # 종목명 추출
                        title_text = element.text
                        company_match = re.search(r'\[(.*?)\]', title_text)
                        company_name = company_match.group(1) if company_match else title_text.split()[0]
                        
                        # 중복 방지: 같은 회사, 같은 날짜 조합 체크
                        report_key = f"{company_name}_{report_date}"
                        if report_key in processed_reports:
                            logger.info(f"이미 처리된 보고서 건너뜀: {report_key}")
                            continue
                        
                        processed_reports.add(report_key)
                        
                        # 다운로드 링크 찾기 (부모 요소 내) - 예외 처리 강화
                        download_links = []
                        try:
                            # 텍스트로 찾기
                            download_links = parent.find_elements(By.XPATH, ".//a[contains(text(), '파일') or contains(text(), '다운로드')]")
                        except Exception as link_error:
                            logger.warning(f"다운로드 링크 텍스트 검색 실패: {str(link_error)}")
                        
                        if not download_links:
                            try:
                                # href 속성으로 찾기
                                download_links = parent.find_elements(By.XPATH, ".//a[contains(@href, 'download')]")
                            except Exception as href_error:
                                logger.warning(f"다운로드 링크 href 검색 실패: {str(href_error)}")
                        
                        if download_links:
                            for link in download_links:
                                try:
                                    download_url = link.get_attribute('href')
                                    if download_url and download_url not in downloaded_files:
                                        logger.info(f"다운로드 URL: {download_url}")
                                        downloaded_files.add(download_url)
                                        
                                        # 다운로드 실행
                                        download_success = download_with_requests(driver, download_url, company_name, report_date.replace('.', ''), base_dir)
                                        if download_success:
                                            processed_count += 1
                                            success = True
                                            break
                                except Exception as e:
                                    logger.error(f"다운로드 링크 처리 중 오류: {str(e)}")
                        else:
                            logger.warning(f"다운로드 링크를 찾을 수 없음: {title_text}")
            except Exception as e:
                logger.error(f"보고서 요소 처리 중 오류: {str(e)}")
        
        logger.info(f"HTML 접근 방법으로 {processed_count}개 보고서 처리 완료")
        return processed_count > 0
    
    except Exception as e:
        logger.error(f"HTML 접근 방법 오류: {str(e)}")
        return False

# 텍스트 패턴 기반 접근 방법
def try_pattern_approach(driver, date_range, base_dir):
    logger.info("텍스트 패턴 기반 접근 방법 시도")
    success = False
    processed_count = 0
    
    try:
        # 전체 페이지 소스 분석
        page_source = driver.page_source
        
        # 샘플 디버그 페이지 분석
        # 각 보고서는 "##" 다음에 제목이 표시되는 패턴
        report_blocks = re.split(r'##\s+\[', page_source)
        
        if len(report_blocks) <= 1:
            logger.warning("## 패턴으로 보고서 블록을 찾을 수 없음. 대체 패턴 시도")
            # 대체 패턴: 종목명 정규표현식으로 분할
            report_blocks = re.split(r'<h[1-6][^>]*>\s*\[', page_source)
        
        logger.info(f"{len(report_blocks)}개의 잠재적 보고서 블록 발견")
        
        # 첫 번째 블록은 헤더 부분이므로 건너뜀
        for i, block in enumerate(report_blocks[1:], 1):
            try:
                # 블록을 복원 (분할 시 제거된 '[' 추가)
                block = '[' + block
                
                # 종목명 추출
                company_match = re.search(r'\[(.*?)\]', block)
                company_name = company_match.group(1) if company_match else f"Report{i}"
                
                # 날짜 추출
                date_match = re.search(r'(\d{4}\.\d{2}\.\d{2})', block)
                if date_match:
                    report_date = date_match.group(1)
                    logger.info(f"보고서 발견: [{company_name}] - {report_date}")
                    
                    if report_date in date_range:
                        # 다운로드 링크 찾기
                        download_match = re.search(r'href=[\'"]([^\'"]*download[^\'"]*)[\'"]', block)
                        if download_match:
                            download_url = download_match.group(1)
                            download_url = download_url.replace('&amp;', '&')  # HTML 엔티티 변환
                            
                            # URL이 상대 경로인 경우 절대 경로로 변환
                            if not download_url.startswith('http'):
                                download_url = urljoin(driver.current_url, download_url)
                            
                            logger.info(f"다운로드 URL: {download_url}")
                            
                            # 다운로드 실행
                            success = download_with_requests(driver, download_url, company_name, report_date.replace('.', ''), base_dir)
                            if success:
                                processed_count += 1
                        else:
                            # 파일 다운로드 텍스트 주변 탐색
                            download_text_match = re.search(r'파일\s*다운로드', block)
                            if download_text_match:
                                # 텍스트 주변 100자 이내의 href 추출
                                text_pos = block.find('파일 다운로드')
                                nearby_text = block[max(0, text_pos-100):min(len(block), text_pos+100)]
                                nearby_href = re.search(r'href=[\'"]([^\'"]*)[\'"]', nearby_text)
                                
                                if nearby_href:
                                    download_url = nearby_href.group(1)
                                    # 실제 다운로드 URL인지 확인
                                    if 'download' in download_url or '.pdf' in download_url:
                                        download_url = download_url.replace('&amp;', '&')
                                        
                                        # URL이 상대 경로인 경우 절대 경로로 변환
                                        if not download_url.startswith('http'):
                                            download_url = urljoin(driver.current_url, download_url)
                                        
                                        logger.info(f"텍스트 주변 다운로드 URL: {download_url}")
                                        
                                        # 다운로드 실행
                                        success = download_with_requests(driver, download_url, company_name, report_date.replace('.', ''), base_dir)
                                        if success:
                                            processed_count += 1
                                else:
                                    # 추정 다운로드 URL 생성 시도
                                    logger.info("다운로드 링크 추정 시도")
                                    
                                    # 디버그 페이지 샘플에서 추출한 URL 패턴 사용
                                    download_url = f"https://m.ibks.com/iko/IKO01/download.do?seq={i+1000}&menuCode=IKO010201&attatchCd=ATTATCH1"
                                    logger.info(f"추정 다운로드 URL: {download_url}")
                                    
                                    # 다운로드 실행
                                    success = download_with_requests(driver, download_url, company_name, report_date.replace('.', ''), base_dir)
                                    if success:
                                        processed_count += 1
                            else:
                                logger.warning(f"다운로드 링크를 찾을 수 없음: [{company_name}]")
                    else:
                        logger.info(f"크롤링 범위 외 날짜: {report_date}")
                else:
                    logger.warning(f"날짜를 찾을 수 없음: 블록 {i}")
            
            except Exception as e:
                logger.error(f"보고서 블록 {i} 처리 중 오류: {str(e)}")
        
        # 명시적 패턴 기반 처리
        explicit_success = process_explicit_patterns(page_source, date_range, base_dir, driver)

        logger.info(f"패턴 기반 접근 방법으로 {processed_count}개 보고서 처리 완료")
        # 명시적 패턴으로만 받은 경우도 성공으로 집계한다.
        return processed_count > 0 or explicit_success
    
    except Exception as e:
        logger.error(f"패턴 기반 접근 방법 오류: {str(e)}")
        return False


# 명시적 패턴 기반 처리 (디버그 페이지 구조 활용)
def process_explicit_patterns(page_source, date_range, base_dir, driver):
    logger.info("명시적 패턴 기반 처리 시도")
    processed_count = 0
    
    # 디버그 페이지 구조 기반 패턴
    pattern = r'## \[(.*?)\].*?(\d{4}\.\d{2}\.\d{2}).*?파일 다운로드'
    matches = re.finditer(pattern, page_source, re.DOTALL)
    
    for i, match in enumerate(matches):
        try:
            company_name = match.group(1)
            report_date = match.group(2)
            
            if report_date in date_range:
                logger.info(f"명시적 패턴으로 보고서 발견: [{company_name}] - {report_date}")
                
                # 추정 다운로드 URL 생성
                base_url = driver.current_url
                report_id = 4000 + i  # 임의의 ID (시스템에 따라 다를 수 있음)
                download_url = f"https://m.ibks.com/iko/IKO01/download.do?seq={report_id}&menuCode=IKO010201&attatchCd=ATTATCH1"
                
                logger.info(f"추정 다운로드 URL: {download_url}")
                
                # 다운로드 시도
                success = download_with_requests(driver, download_url, company_name, report_date.replace('.', ''), base_dir)
                if success:
                    processed_count += 1
                
                # 실패시 다른 패턴 시도
                if not success:
                    other_patterns = [
                        f"https://m.ibks.com/iko/download.do?fileName={company_name}_{report_date.replace('.', '')}.pdf",
                        f"https://m.ibks.com/iko/download.do?seq={report_id}",
                        f"https://m.ibks.com/iko/download.do?rptId={report_id}"
                    ]
                    
                    for alt_url in other_patterns:
                        logger.info(f"대체 다운로드 URL 시도: {alt_url}")
                        success = download_with_requests(driver, alt_url, company_name, report_date.replace('.', ''), base_dir)
                        if success:
                            processed_count += 1
                            break
        
        except Exception as e:
            logger.error(f"명시적 패턴 처리 중 오류: {str(e)}")
    
    logger.info(f"명시적 패턴으로 {processed_count}개 보고서 처리 완료")
    return processed_count > 0

# 다운로드 처리 (requests 사용)
def download_with_requests(driver, download_url, company_name, date_str, base_dir):
    """SSL 오류 해결을 위한 개선된 다운로드 함수"""
    try:
        # 날짜별 폴더 생성
        date_dir = create_date_directory(base_dir, date_str)
        
        # 안전한 세션 생성
        session = create_secure_session()
        
        # 쿠키 복사 (Selenium -> requests)
        selenium_cookies = driver.get_cookies()
        for cookie in selenium_cookies:
            session.cookies.set(cookie['name'], cookie['value'])
        
        # 헤더 업데이트
        session.headers.update({
            'Referer': driver.current_url,
            'User-Agent': driver.execute_script("return navigator.userAgent")
        })
        
        logger.info(f"SSL 호환 다운로드 시작: {download_url}")
        
        # 다중 시도 방식으로 다운로드
        for attempt in range(3):
            try:
                # 첫 번째 시도: 표준 방식
                if attempt == 0:
                    response = session.get(download_url, timeout=30, stream=True)
                
                # 두 번째 시도: SSL 컨텍스트 직접 설정
                elif attempt == 1:
                    logger.info("SSL 컨텍스트 직접 설정으로 재시도")
                    import ssl
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    
                    # SSL 컨텍스트를 사용한 어댑터 생성
                    from requests.adapters import HTTPAdapter
                    from urllib3.poolmanager import PoolManager
                    
                    class SSLAdapter(HTTPAdapter):
                        def init_poolmanager(self, *args, **kwargs):
                            kwargs['ssl_context'] = context
                            return super().init_poolmanager(*args, **kwargs)
                    
                    session.mount('https://', SSLAdapter())
                    response = session.get(download_url, timeout=30, stream=True)
                
                # 세 번째 시도: TLS 버전 명시
                else:
                    logger.info("TLS 버전 명시로 재시도")
                    import ssl
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    context.set_ciphers('DEFAULT@SECLEVEL=1')
                    
                    from requests.adapters import HTTPAdapter
                    from urllib3.poolmanager import PoolManager
                    
                    class TLSAdapter(HTTPAdapter):
                        def init_poolmanager(self, *args, **kwargs):
                            kwargs['ssl_context'] = context
                            return super().init_poolmanager(*args, **kwargs)
                    
                    session.mount('https://', TLSAdapter())
                    response = session.get(download_url, timeout=30, stream=True)
                
                logger.info(f"응답 상태 코드: {response.status_code}")
                
                # 성공적으로 응답 받음
                if response.status_code == 200:
                    break
                else:
                    logger.warning(f"시도 {attempt + 1} 실패 (상태 코드: {response.status_code})")
                    if attempt == 2:
                        logger.error(f"모든 시도 실패 (상태 코드: {response.status_code}): {download_url}")
                        return False
                    
            except requests.exceptions.SSLError as ssl_error:
                logger.error(f"SSL 오류 - 시도 {attempt + 1}: {str(ssl_error)}")
                if attempt == 2:
                    logger.error(f"모든 SSL 시도 실패: {download_url}")
                    return False
                continue
                
            except requests.exceptions.RequestException as req_error:
                logger.error(f"요청 오류 - 시도 {attempt + 1}: {str(req_error)}")
                if attempt == 2:
                    logger.error(f"모든 요청 시도 실패: {download_url}")
                    return False
                continue
        
        # 응답 내용 확인
        content_type = response.headers.get('Content-Type', '').lower()
        logger.info(f"Content-Type: {content_type}")
        
        if response.status_code == 200:
            # 응답 헤더에서 파일명 추출
            file_name = None
            content_disposition = response.headers.get('Content-Disposition', '')
            if content_disposition:
                # Content-Disposition 헤더에서 파일명 추출
                import re
                filename_match = re.search(r'filename[*]?=([^;]+)', content_disposition)
                if filename_match:
                    file_name = filename_match.group(1).strip('"\'')
                    # URL 디코딩
                    from urllib.parse import unquote
                    file_name = unquote(file_name)
                    logger.info(f"헤더에서 추출한 파일명: {file_name}")
            
            # 파일명이 없으면 URL에서 추출 시도
            if not file_name:
                from urllib.parse import urlparse
                parsed_url = urlparse(download_url)
                path_parts = parsed_url.path.split('/')
                for part in reversed(path_parts):
                    if part.endswith('.pdf'):
                        file_name = part
                        logger.info(f"URL에서 추출한 파일명: {file_name}")
                        break
            
            # 여전히 파일명이 없으면 기본 형식 사용
            if not file_name:
                file_name = f"{company_name}_{date_str}.pdf"
                logger.info(f"기본 파일명 사용: {file_name}")
            
            # 파일명에서 특수문자 제거 (Windows 파일시스템 호환성)
            import re
            file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
            
            file_path = os.path.join(date_dir, file_name)
            
            # 이미 존재하는 파일인지 확인
            if os.path.exists(file_path):
                logger.info(f"파일이 이미 존재합니다: {file_path}")
                return True
            
            # PDF 또는 일반 파일인 경우
            if 'application/pdf' in content_type or 'application/octet-stream' in content_type:
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                logger.info(f"SSL 호환 다운로드 완료: {file_path}")
                
                # PDF 유효성 확인
                if os.path.getsize(file_path) < 1000:  # 매우 작은 파일은 실패했을 가능성이 높음
                    with open(file_path, 'rb') as f:
                        content = f.read(4)
                        if content != b'%PDF':
                            logger.warning(f"다운로드된 파일이 유효한 PDF가 아닙니다: {file_path}")
                            os.remove(file_path)  # 유효하지 않은 파일 삭제
                            return False
                
                return True
            else:
                # HTML 응답인 경우 (로그인 페이지나 에러 페이지일 수 있음)
                logger.warning(f"PDF가 아닌 Content-Type 받음: {content_type}")
                
                # 응답 내용 확인
                error_file = os.path.join(base_dir, f'error_response_{int(time.time())}.html')
                with open(error_file, 'wb') as f:
                    f.write(response.content)
                logger.info(f"에러 응답 저장: {error_file}")
                
                return False
        else:
            logger.error(f"다운로드 실패 (상태 코드: {response.status_code}): {download_url}")
            return False
    
    except Exception as e:
        logger.error(f"SSL 호환 다운로드 처리 중 오류: {str(e)}")
        return False
    finally:
        # 세션 정리
        if 'session' in locals():
            session.close()

# SSL 오류 해결을 위한 requests 세션 설정
def create_secure_session():
    """SSL/TLS 호환성을 위한 requests 세션 생성"""
    session = requests.Session()
    
    # SSL 설정
    session.verify = False  # SSL 인증서 검증 비활성화
    
    # 타임아웃 설정
    session.timeout = 30
    
    # 헤더 설정
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    # SSL 어댑터 설정
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    logger.info("SSL 호환성 requests 세션 생성 완료")
    return session

# 메인 함수
if __name__ == "__main__":
    logger = setup_logger()
    logger.info("IBK투자증권 기업분석 보고서 크롤링 시작")
    
    exit_code = 1
    try:
        # 일주일치 보고서 크롤링 (오늘부터 7일간)
        exit_code = crawl_ibks_company_analysis()
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {str(e)}")
        exit_code = 1

    logger.info("프로그램 종료")
    sys.exit(exit_code)
