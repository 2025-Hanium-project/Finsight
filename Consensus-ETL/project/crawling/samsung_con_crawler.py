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
import logging

# 설정
BASE_URL = "https://www.samsungpop.com/sscommon/jsp/search/research/research_pop.jsp"
# 저장 디렉토리 설정 (project/consensus/samsung)
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
DOWNLOAD_DIR = os.path.join(project_root, "project", "consensus", "samsung")

def log_message(message):
    """로그 메시지 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    print(log_entry)
    # 로그 파일에도 저장
    log_dir = os.path.join(os.path.dirname(__file__), "..", "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"samsung_download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def setup_driver():
    """웹 드라이버 설정"""
    log_message("웹 드라이버 설정 중...")
    
    chrome_options = Options()
    # 헤드리스 모드를 비활성화하여 디버깅 용이하게 함
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # User-Agent 설정
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    # 다운로드 디렉토리 설정
    prefs = {
        "download.default_directory": os.path.abspath(DOWNLOAD_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # 웹 드라이버 초기화
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.set_page_load_timeout(30)
    
    return driver

def check_and_handle_login_alert(driver):
    """로그인 알림창 확인 및 처리"""
    log_message("로그인 알림창 확인 중...")
    
    try:
        # alert 창이 있는지 확인 (최대 5초 대기)
        alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
        alert_text = alert.text
        log_message(f"알림창 감지: {alert_text}")
        
        # "로그인을 한 후 이용할 수 있습니다" 메시지인지 확인
        if "로그인" in alert_text:
            log_message("로그인 알림창 확인됨. 확인 버튼 클릭 후 크롤링 진행...")
            alert.accept()  # 확인 버튼 클릭
            time.sleep(2)
            return True
        else:
            log_message(f"예상하지 못한 알림창: {alert_text}")
            alert.accept()
            return True
            
    except TimeoutException:
        # 알림창이 없는 경우
        log_message("알림창 없음. 정상 진행...")
        return True
    except Exception as e:
        log_message(f"알림창 처리 중 오류: {str(e)}")
        try:
            # 혹시 남은 alert가 있다면 처리
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass
        return True

def navigate_to_reports(driver, start_count=0):
    """리포트 페이지로 이동"""
    url = f"{BASE_URL}?startCount={start_count}"
    log_message(f"리포트 페이지로 이동 중: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)
        
        # 로그인 알림창 확인 및 처리
        check_and_handle_login_alert(driver)
        
        # 테이블이 로드될 때까지 대기
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.tbl-type.board"))
        )
        log_message("리포트 페이지 로딩 완료")
        return True
        
    except TimeoutException:
        log_message("페이지 로딩 타임아웃")
        return False
    except Exception as e:
        log_message(f"페이지 로딩 중 오류: {str(e)}")
        return False

def extract_reports_from_page(driver):
    """페이지에서 리포트 정보 추출"""
    log_message("페이지에서 리포트 정보 추출 중...")
    reports = []
    
    try:
        # 테이블 찾기 - 정확한 클래스명 사용
        table = driver.find_element(By.CSS_SELECTOR, "table.tbl-type.board")
        
        # tbody가 없으므로 직접 tr 요소들 찾기
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        log_message(f"{len(rows)}개의 리포트 행 발견")
        
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 3:
                    continue
                
                # 첫 번째 셀: 제목과 링크
                title_cell = cells[0]
                title_link = title_cell.find_element(By.TAG_NAME, "a")
                
                title = title_link.text.strip()
                # title 속성에서 전체 제목 가져오기
                full_title = title_link.get_attribute("title")
                if full_title:
                    title = full_title.replace("PDF 원문보기(새창열림)", "").strip()
                
                pdf_url = title_link.get_attribute("href")
                
                # 두 번째 셀: 작성자
                author = cells[1].text.strip()
                
                # 세 번째 셀: 날짜
                date = cells[2].text.strip()
                
                # PDF URL이 유효한 경우에만 추가
                if pdf_url and "common.do?cmd=down" in pdf_url:
                    # 절대 URL로 변환
                    if pdf_url.startswith('/'):
                        pdf_url = f"https://www.samsungpop.com{pdf_url}"
                    
                    # 종목명 추출 (제목에서 괄호 안의 종목코드 앞 부분 추출)
                    stock_name = ""
                    if "(" in title:
                        # 괄호 앞 부분에서 종목명 추출
                        before_paren = title.split("(")[0].strip()
                        # 작성자명 제거
                        if author and author in before_paren:
                            stock_name = before_paren.replace(f"({author})", "").replace(author, "").strip()
                        else:
                            stock_name = before_paren
                    
                    # 리포트 정보 저장
                    reports.append({
                        "title": title,
                        "author": author,
                        "date": date,
                        "pdf_url": pdf_url,
                        "stock_name": stock_name
                    })
                    
                    log_message(f"리포트 추출: {title[:50]}... - {author}")
                    
            except Exception as e:
                log_message(f"리포트 행 처리 중 오류: {str(e)}")
                continue
                
        return reports
        
    except Exception as e:
        log_message(f"리포트 정보 추출 중 오류: {str(e)}")
        return []

def navigate_to_next_page(driver, current_start_count):
    """다음 페이지로 이동"""
    next_start_count = current_start_count + 7  # 페이지당 7개 리포트
    
    try:
        log_message(f"다음 페이지로 이동 중... (startCount: {next_start_count})")
        
        # doPaging JavaScript 함수 실행
        driver.execute_script(f"doPaging({next_start_count})")
        
        time.sleep(3)  # 페이지 로드 대기
        
        # 페이지 로드 확인
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.tbl-type.board"))
        )
        
        log_message(f"페이지 이동 완료 (startCount: {next_start_count})")
        return True, next_start_count
        
    except Exception as e:
        log_message(f"다음 페이지 이동 중 오류: {str(e)}")
        return False, current_start_count

def download_pdf(pdf_url, report):
    """PDF 다운로드"""
    if not pdf_url:
        log_message(f"PDF URL 없음: {report['title']}")
        return False
    
    log_message(f"PDF 다운로드 중: {pdf_url}")
    
    try:
        # 날짜 파싱 및 정리
        date_str = report["date"]
        try:
            # 날짜 형식을 표준화 (YYYY-MM-DD 형식으로 변환)
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
        
        # 파일명 생성 (삼성증권_제목_날짜.pdf)
        def sanitize_filename(filename):
            return re.sub(r'[\\/*?:"<>|]', "_", filename)
        
        sanitized_title = sanitize_filename(report['title'])
        
        # 제목이 너무 긴 경우 줄이기
        if len(sanitized_title) > 100:
            sanitized_title = sanitized_title[:100]
        
        file_name = f"삼성증권_{sanitized_title}_{formatted_date}.pdf"
        save_path = os.path.join(DOWNLOAD_DIR, file_name)
        
        # 이미 파일이 존재하는 경우 스킵
        if os.path.exists(save_path):
            log_message(f"이미 존재하는 파일 건너뛰기: {save_path}")
            return True
        
        # PDF 다운로드
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
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

def save_metadata(reports):
    """메타데이터 저장"""
    if not reports:
        log_message("저장할 리포트 메타데이터가 없음")
        return None
        
    log_message(f"{len(reports)}개 리포트의 메타데이터 저장 중...")
    df = pd.DataFrame(reports)
    
    # CSV로 저장
    metadata_path = os.path.join(DOWNLOAD_DIR, "samsung_consensus_reports.csv")
    df.to_csv(metadata_path, index=False, encoding="utf-8-sig")
    log_message(f"메타데이터 저장 완료: {metadata_path}")
    
    return df

def main():
    """메인 실행 함수"""
    # 시작 시간 기록
    start_time = datetime.now()
    log_message(f"삼성증권 크롤링 시작: {start_time}")
    
    # 다운로드 디렉토리 생성
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    driver = None
    try:
        # 웹 드라이버 설정
        driver = setup_driver()
        
        # 전체 리포트 목록
        all_reports = []
        current_start_count = 0
        max_pages = 20  # 최대 20페이지까지 크롤링 (140개 리포트)
        page_num = 1
        
        while page_num <= max_pages:
            log_message(f"페이지 {page_num} 처리 중... (startCount: {current_start_count})")
            
            # 현재 페이지로 이동
            if not navigate_to_reports(driver, current_start_count):
                log_message(f"페이지 {page_num} 로딩 실패. 크롤링 종료.")
                break
            
            # 현재 페이지에서 리포트 추출
            reports = extract_reports_from_page(driver)
            
            if not reports:
                log_message(f"페이지 {page_num}에서 리포트를 찾을 수 없습니다.")
                break
            
            all_reports.extend(reports)
            log_message(f"페이지 {page_num}에서 {len(reports)}개 리포트 추출")
            
            # 다음 페이지로 이동 (마지막 페이지가 아닌 경우)
            if page_num < max_pages:
                success, current_start_count = navigate_to_next_page(driver, current_start_count)
                if not success:
                    log_message("더 이상 페이지가 없습니다.")
                    break
            
            page_num += 1
            
            # 서버 부하 방지
            time.sleep(2)
        
        log_message(f"총 {len(all_reports)}개의 리포트를 찾았습니다.")
        
        # 메타데이터 저장
        save_metadata(all_reports)
        
        # PDF 다운로드
        log_message("PDF 다운로드 시작...")
        success_count = 0
        
        for i, report in enumerate(all_reports):
            log_message(f"다운로드 진행: {i+1}/{len(all_reports)}")
            
            pdf_url = report.get("pdf_url")
            if pdf_url:
                if download_pdf(pdf_url, report):
                    success_count += 1
                
            # 서버 부하 방지를 위한 대기
            time.sleep(2)
        
        # 완료 시간 및 소요 시간 기록
        end_time = datetime.now()
        duration = end_time - start_time
        log_message(f"크롤링 완료: {end_time}")
        log_message(f"총 소요 시간: {duration}")
        log_message(f"총 {len(all_reports)}개 리포트 중 {success_count}개 다운로드 완료")
        
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
