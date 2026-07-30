import os
import time
import re
import pandas as pd
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import pdfplumber
import logging
import urllib.parse
from bs4 import BeautifulSoup
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("yuanta_crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("yuanta_crawler")

class YuantaResearchCrawler:
    def __init__(self):
        # 기본 URL 및 설정
        self.base_url = "https://www.myasset.com/myasset/research/rs_list/rs_list.cmd?cd006=&cd007=RE01&cd008="
        self.file_base_url = "https://file.myasset.com/sitemanager/upload/"
        
        # 저장 디렉토리 설정 (project/consensus 폴더 기준)
        # 현재 파일 위치: Consensus-ETL/project/crawling/yuanta_con_crawler.py
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # crawling 폴더
        PROJECT_DIR = os.path.dirname(CURRENT_DIR)  # project 폴더
        self.base_dir = os.path.join(PROJECT_DIR, "consensus", "yuanta")
        self.pdf_dir = self.base_dir  # PDF 파일을 project/consensus/yuanta에 직접 저장
        self.data_dir = self.base_dir  # 메타데이터도 같은 폴더에 저장
        
        # 디렉토리 생성
        os.makedirs(self.pdf_dir, exist_ok=True)
        
        # 메타데이터 저장 파일
        self.metadata_file = os.path.join(self.data_dir, "reports_metadata.csv")
        self.structured_data_file = os.path.join(self.data_dir, "structured_data.csv")
        
        # 웹드라이버 설정
        self.setup_driver()
        
        # HTTP 세션 설정 (다운로드 속도 개선)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
        # 이미 다운로드한 파일 목록 (중복 방지)
        self.existing_files = self.load_existing_files()

    def setup_driver(self):
        """웹드라이버 설정"""
        # 크롬 옵션 설정
        chrome_options = Options()
        # 브라우저 창 숨기기 (헤드리스 모드)
        chrome_options.add_argument("--headless")  # 디버깅 시에는 주석 처리
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # User-Agent 설정
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # 웹드라이버 초기화
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.driver.implicitly_wait(3)  # 10초에서 5초로 단축
        self.driver.set_page_load_timeout(15)  # 30초에서 15초로 단축
        
        logger.info("웹드라이버 설정 완료")
    
    def load_existing_files(self):
        """이미 다운로드한 파일 목록 로드"""
        existing_files = set()
        
        # 메타데이터 파일에서 로드
        if os.path.exists(self.metadata_file):
            try:
                metadata = pd.read_csv(self.metadata_file)
                if 'pdf_filename' in metadata.columns:
                    existing_files.update(metadata['pdf_filename'].tolist())
            except Exception as e:
                logger.error(f"메타데이터 파일 로드 오류: {str(e)}")
        
        # 디렉토리에 있는 파일 목록도 확인
        if os.path.exists(self.pdf_dir):
            for filename in os.listdir(self.pdf_dir):
                if filename.endswith('.pdf'):
                    existing_files.add(filename)
        
        return existing_files
    
    def login(self, username=None, password=None):
        """로그인 처리 (필요한 경우)"""
        if not username or not password:
            logger.info("로그인 정보가 제공되지 않아 로그인 과정 건너뜀")
            return False
            
        try:
            # 로그인 페이지로 이동
            self.driver.get("https://www.myasset.com/myasset/login/LO_0100000_P1.cmd")
            
            # 사용자 이름 입력
            username_input = self.driver.find_element(By.ID, "LOGIN_ID")
            username_input.clear()
            username_input.send_keys(username)
            
            # 비밀번호 입력
            password_input = self.driver.find_element(By.ID, "PWD")
            password_input.clear()
            password_input.send_keys(password)
            
            # 로그인 버튼 클릭
            login_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            login_button.click()
            
            # 로그인 성공 여부 확인
            time.sleep(3)
            if "로그인" in self.driver.title:
                logger.error("로그인 실패")
                return False
            
            logger.info("로그인 성공")
            return True
        
        except Exception as e:
            logger.error(f"로그인 중 오류: {str(e)}")
            return False
    
    def crawl_reports(self, date_from=None, date_to=None, max_pages=5, username=None, password=None):
        """리포트 크롤링 시작"""
        try:
            logger.info("크롤링 시작")
            
            # 로그인 (필요한 경우)
            if username and password:
                self.login(username, password)
            
            # 페이지 접속
            try:
                self.driver.get(self.base_url)
                logger.info(f"페이지 접속: {self.base_url}")
                time.sleep(2)  # 5초에서 2초로 단축
            except TimeoutException:
                logger.error("페이지 로딩 시간 초과, 새로고침 시도")
                self.driver.refresh()
                time.sleep(2)  # 5초에서 2초로 단축
            
            # 메타데이터 저장 리스트
            reports_metadata = []
            
            # 페이지 수 확인
            total_pages = self.get_total_pages()
            pages_to_crawl = min(total_pages, max_pages)
            logger.info(f"총 {total_pages}페이지 중 {pages_to_crawl}페이지 크롤링 예정")
            
            # 각 페이지 처리
            for page in range(1, pages_to_crawl + 1):
                if page > 1:
                    # 페이지 이동
                    self.goto_page(page)
                
                logger.info(f"페이지 {page} 처리 중...")
                
                # 현재 페이지의 모든 리포트 행 찾기
                try:
                    WebDriverWait(self.driver, 10).until(  # 20초에서 10초로 단축
                        EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr"))
                    )
                    rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                except Exception as e:
                    logger.error(f"페이지 {page}에서 리포트 목록을 찾을 수 없음: {str(e)}")
                    continue
                
                logger.info(f"페이지 {page}에서 {len(rows)}개의 행 발견")
                
                # 빈 행이나 헤더 행 필터링
                valid_rows = []
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 5 and cells[0].text.strip():  # 날짜가 있는 행만 처리
                        valid_rows.append(row)
                
                logger.info(f"페이지 {page}에서 {len(valid_rows)}개의 유효한 행 처리 예정")
                
                for idx, row in enumerate(valid_rows):
                    try:
                        # 데이터 추출
                        report_data = self.extract_row_data(row)
                        
                        if not report_data:
                            continue
                        
                        # 중복 체크
                        if report_data['pdf_filename'] in self.existing_files:
                            logger.info(f"이미 다운로드된 파일 건너뛰기: {report_data['pdf_filename']}")
                            continue
                        
                        # PDF 파일 직접 다운로드
                        pdf_path = None
                        
                        # 1. 원본 파일명으로 URL 직접 구성하여 다운로드 시도
                        if 'original_filename' in report_data and report_data['original_filename']:
                            pdf_path = self.download_pdf_by_filename(report_data)
                        
                        # 2. 첫 번째 방법 실패 시에만 첨부 파일 직접 클릭하여 다운로드 시도
                        if not pdf_path:
                            pdf_path = self.download_pdf_direct(row, report_data)
                        
                        if pdf_path:
                            report_data['pdf_path'] = pdf_path
                            reports_metadata.append(report_data)
                            self.existing_files.add(report_data['pdf_filename'])
                            logger.info(f"진행률: {idx+1}/{len(valid_rows)} ({((idx+1)/len(valid_rows)*100):.1f}%)")
                        
                        # 건너뛰기 (디버깅용)
                        # if idx >= 2:  # 테스트를 위해 처음 2개만 처리
                        #     break
                    
                    except Exception as e:
                        logger.error(f"행 {idx+1} 처리 중 오류: {str(e)}")
                        continue
            
            # 메타데이터 저장
            self.save_metadata(reports_metadata)
            
            return reports_metadata
        
        except Exception as e:
            logger.error(f"크롤링 중 오류 발생: {str(e)}")
            return []
        
        finally:
            # 세션 종료
            if hasattr(self, 'session'):
                self.session.close()
            # 브라우저 종료
            self.driver.quit()
            logger.info("크롤링 완료 및 브라우저 종료")
    
    def get_total_pages(self):
        """총 페이지 수 확인"""
        try:
            # 페이지가 완전히 로드될 때까지 대기
            time.sleep(1)  # 3초에서 1초로 단축
            
            # 페이지네이션 요소 찾기
            pagination_selectors = [
                ".pagenation a",  # 실제 사용 중인 클래스 (사이트 표기가 pagenation)
                ".pagination a",  # 일반적인 페이지네이션
                "a[href*='javascript:goPage']",  # javascript 함수로 페이지 이동
                ".paging a",  # 다른 일반적인 페이지네이션 클래스
                "ul.pagination li a"  # Bootstrap 스타일 페이지네이션
            ]
            
            for selector in pagination_selectors:
                try:
                    pagination = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if pagination:
                        # 숫자만 있는 페이지 링크 찾기
                        page_numbers = []
                        for elem in pagination:
                            if elem.text.isdigit():
                                page_numbers.append(int(elem.text))
                        
                        if page_numbers:
                            return max(page_numbers)
                except:
                    continue
            
            # 페이지 번호를 찾지 못한 경우
            logger.warning("페이지 번호를 찾을 수 없음, 1페이지로 가정")
            return 1
        
        except Exception as e:
            logger.error(f"페이지 수 확인 중 오류: {str(e)}")
            return 1
    
    def goto_page(self, page_num):
        """특정 페이지로 이동"""
        try:
            # 다양한 페이지 이동 방식 시도
            selectors = [
                f"//a[text()='{page_num}']",  # 텍스트가 페이지 번호인 링크
                f"//a[contains(@href, 'javascript:goPage({page_num})')]",  # javascript 함수 호출
                f"//a[@data-page='{page_num}']",  # data-page 속성
                f"//li[@class='page-item']/a[text()='{page_num}']"  # Bootstrap 스타일
            ]
            
            for selector in selectors:
                try:
                    page_link = self.driver.find_element(By.XPATH, selector)
                    page_link.click()
                    time.sleep(2)  # 5초에서 2초로 단축
                    logger.info(f"페이지 {page_num}로 이동 성공")
                    return True
                except:
                    continue
            
            # 모든 시도가 실패한 경우
            logger.error(f"페이지 {page_num}로 이동 실패")
            return False
        
        except Exception as e:
            logger.error(f"페이지 {page_num}로 이동 중 오류: {str(e)}")
            return False
    
    def extract_row_data(self, row):
        """행에서 데이터 추출"""
        try:
            # 각 셀 데이터 추출
            cells = row.find_elements(By.TAG_NAME, "td")
            
            if len(cells) < 5:
                logger.warning(f"행에 충분한 셀이 없음: {len(cells)} cells")
                return None
            
            # 날짜, 종목, 투자의견, 제목 등 추출
            date = cells[0].text.strip()  # 예: 2025/05/09
            
            # 종목명이 비어있는지 확인
            stock = cells[1].text.strip() if len(cells) > 1 else "Unknown"
            
            # 투자의견 (Not Rated 등)
            opinion = cells[2].text.strip() if len(cells) > 2 else ""
            
            # 제목
            title = cells[3].text.strip() if len(cells) > 3 else "No Title"
            
            # 저자 (인덱스 확인 필요)
            author_idx = 6  # 일반적인 인덱스, 페이지 구조에 따라 조정 필요
            author = cells[author_idx].text.strip() if len(cells) > author_idx else "Unknown"
            
            # 첨부 파일 확인 (5번째 셀)
            attachment_cell = cells[4] if len(cells) > 4 else None
            pdf_filename = None
            pdf_link = None
            
            if attachment_cell:
                # 1. PDF 파일명이 표시된 경우 (이미지의 경우)
                try:
                    pdf_filename_element = attachment_cell.find_element(By.TAG_NAME, "a")
                    pdf_filename = pdf_filename_element.text.strip()
                    pdf_link = pdf_filename_element.get_attribute("href")
                    
                    if pdf_filename and pdf_filename.endswith('.pdf'):
                        logger.info(f"PDF 파일명 발견: {pdf_filename}")
                    else:
                        # a 태그 안에 있는 img 태그의 alt 속성 확인
                        img_element = pdf_filename_element.find_element(By.TAG_NAME, "img")
                        alt_text = img_element.get_attribute("alt")
                        if alt_text and "pdf" in alt_text.lower():
                            # 이미지에 "첨부파일" 등의 alt 텍스트가 있는 경우
                            pdf_filename = None
                except:
                    pdf_filename = None
                    pdf_link = None
                
                # 2. HTML 소스에서 직접 추출 시도
                if not pdf_filename or not pdf_filename.endswith('.pdf'):
                    try:
                        html_source = attachment_cell.get_attribute("innerHTML")
                        if '_0_ko.pdf' in html_source:
                            # 정규식으로 파일명 추출
                            filename_match = re.search(r'(\d+_\d+_ko\.pdf)', html_source)
                            if filename_match:
                                pdf_filename = filename_match.group(1)
                                logger.info(f"HTML에서 PDF 파일명 발견: {pdf_filename}")
                    except:
                        pass
            
            # PDF 파일명이 없는 경우 생성
            if not pdf_filename or not pdf_filename.endswith('.pdf'):
                date_str = date.replace('/', '')
                safe_stock = re.sub(r'[\\/*?:"<>|]', '_', stock)
                safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)[:50]
                pdf_filename = f"{date_str}_{safe_stock}_{safe_title}.pdf"
                logger.info(f"PDF 파일명 생성: {pdf_filename}")
            
            # 원본 파일명 보존
            original_filename = pdf_filename
            
            # 안전한 파일명으로 변환
            safe_pdf_filename = re.sub(r'[\\/*?:"<>|]', '_', pdf_filename)
            
            return {
                "date": date,
                "stock": stock,
                "opinion": opinion,
                "title": title,
                "author": author,
                "original_filename": original_filename,
                "pdf_filename": safe_pdf_filename,
                "pdf_link": pdf_link
            }
        
        except Exception as e:
            logger.error(f"행 데이터 추출 중 오류: {str(e)}")
            return None
    
    def download_pdf_by_filename(self, report_data):
        """파일명 패턴으로 직접 URL 구성하여 PDF 다운로드"""
        try:
            # 파일명 및 경로 설정
            filename = report_data['pdf_filename']
            filepath = os.path.join(self.pdf_dir, filename)
            
            # 이미 파일이 존재하는지 확인
            if os.path.exists(filepath):
                logger.info(f"파일이 이미 존재함: {filename}")
                return filepath
            
            # 원본 파일명 (이미지에서 볼 수 있는 형식)
            original_filename = report_data.get('original_filename')
            
            if original_filename and ('_0_ko.pdf' in original_filename or '_ko.pdf' in original_filename):
                # 파일명에서 연/월/일/시간 추출 시도
                date_match = re.match(r'(\d{4})(\d{2})(\d{2})(\d+)', original_filename)
                if date_match:
                    year, month, day, time_part = date_match.groups()
                    
                    # URL 구성 (이미지에서 본 패턴)
                    # 예: https://file.myasset.com/sitemanager/upload/2025/0509/174549/20250509174549443_0_ko.pdf
                    pdf_url = f"https://file.myasset.com/sitemanager/upload/{year}/{month}{day}/{time_part[:6]}/{original_filename}"
                    logger.info(f"파일명으로 URL 구성: {pdf_url}")
                    
                    # PDF 다운로드
                    response = self.session.get(  # requests.get 대신 세션 사용
                        pdf_url, 
                        stream=True,
                        timeout=15  # 30초에서 15초로 단축
                    )
                    
                    if response.status_code == 200:
                        # 청크 크기를 늘려서 다운로드 속도 개선
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=32768):  # 8192에서 32768로 증가
                                if chunk:
                                    f.write(chunk)
                        logger.info(f"PDF 다운로드 완료: {filename}")
                        return filepath
                    else:
                        logger.error(f"PDF 다운로드 실패 (상태 코드: {response.status_code})")
            
            return None
            
        except Exception as e:
            logger.error(f"파일명으로 PDF 다운로드 중 오류: {str(e)}")
            return None
    
    def download_pdf_direct(self, row, report_data):
        """첨부 파일 직접 다운로드"""
        try:
            # 파일명 및 경로 설정
            filename = report_data['pdf_filename']
            filepath = os.path.join(self.pdf_dir, filename)
            
            # 이미 파일이 존재하는지 확인
            if os.path.exists(filepath):
                logger.info(f"파일이 이미 존재함: {filename}")
                return filepath
            
            # 1. 첨부 파일 셀 찾기
            attachment_cell = row.find_elements(By.TAG_NAME, "td")[4]  # 첨부 파일 셀 (인덱스 확인 필요)
            
            try:
                # 2. 첨부 파일 링크 찾기
                attachment_link = attachment_cell.find_element(By.TAG_NAME, "a")
                
                # 안전하게 새 탭에서 열기
                self.driver.execute_script("window.open(arguments[0].href, '_blank');", attachment_link)
                time.sleep(1)  # 3초에서 1초로 단축
                
                # 새 탭이 열렸는지 확인
                if len(self.driver.window_handles) > 1:
                    # 새 탭으로 전환
                    new_tab = self.driver.window_handles[-1]
                    self.driver.switch_to.window(new_tab)
                    
                    # 현재 URL 확인
                    pdf_url = self.driver.current_url
                    logger.info(f"새 탭 URL: {pdf_url}")
                    
                    # PDF 다운로드
                    if pdf_url.endswith('.pdf') or 'file.myasset.com' in pdf_url:
                        logger.info(f"PDF URL 발견: {pdf_url}")
                        
                        # 안전한 다운로드 시도
                        try:
                            response = self.session.get(  # requests.get 대신 세션 사용
                                pdf_url, 
                                stream=True,
                                timeout=15  # 30초에서 15초로 단축
                            )
                            
                            if response.status_code == 200:
                                # 청크 크기를 늘려서 다운로드 속도 개선
                                with open(filepath, 'wb') as f:
                                    for chunk in response.iter_content(chunk_size=32768):  # 8192에서 32768로 증가
                                        if chunk:
                                            f.write(chunk)
                                logger.info(f"PDF 다운로드 완료: {filename}")
                            else:
                                logger.error(f"PDF 다운로드 실패 (상태 코드: {response.status_code})")
                        except Exception as e:
                            logger.error(f"PDF 다운로드 요청 중 오류: {str(e)}")
                    
                    # 탭 닫기
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                
                # 파일 존재 확인
                if os.path.exists(filepath):
                    return filepath
                
                # 파일이 없으면 원래 탭으로 돌아가기
                if self.driver.current_window_handle != self.driver.window_handles[0]:
                    self.driver.switch_to.window(self.driver.window_handles[0])
            
            except Exception as e:
                logger.error(f"첨부 파일 다운로드 중 오류: {str(e)}")
                
                # 탭 관리 복구 시도
                if len(self.driver.window_handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            
            logger.error(f"PDF 직접 다운로드 실패: {filename}")
            return None
        
        except Exception as e:
            logger.error(f"PDF 다운로드 중 오류: {str(e)}")
            return None
    
    def save_metadata(self, reports_metadata):
        """메타데이터 CSV로 저장"""
        try:
            if not reports_metadata:
                logger.warning("저장할 메타데이터 없음")
                return
            
            # 새 데이터프레임 생성
            new_df = pd.DataFrame(reports_metadata)
            
            # 기존 메타데이터와 병합
            if os.path.exists(self.metadata_file):
                try:
                    existing_df = pd.read_csv(self.metadata_file)
                    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                    # 중복 제거 (pdf_filename 기준)
                    combined_df = combined_df.drop_duplicates(subset=['pdf_filename'], keep='last')
                except Exception as e:
                    logger.error(f"기존 메타데이터 로드 중 오류: {str(e)}")
                    combined_df = new_df
            else:
                combined_df = new_df
            
            # CSV로 저장
            combined_df.to_csv(self.metadata_file, index=False, encoding="utf-8-sig")
            logger.info(f"메타데이터 저장 완료: {len(combined_df)}개 항목")
        
        except Exception as e:
            logger.error(f"메타데이터 저장 중 오류: {str(e)}")
    
    # parse_pdf_content 및 extract_pdf_data 메서드는 이전 코드와 동일하게 유지

def main():
    """메인 함수"""
    logger.info("유안타증권 리서치 크롤러 시작")
    
    try:
        # 크롤러 인스턴스 생성
        crawler = YuantaResearchCrawler()
        
        # 오늘 날짜
        today = datetime.now().strftime("%Y/%m/%d")
        # 30일 전 날짜 (기본 크롤링 범위)
        thirty_days_ago = (datetime.now() - pd.Timedelta(days=30)).strftime("%Y/%m/%d")
        
        # 리포트 크롤링 (매개변수 조정 - 더 적은 페이지, 타임아웃 문제 해결)
        reports = crawler.crawl_reports(max_pages=3)  # 일 1회 실행 기준, 재실행 여유분 포함
        
        # PDF 내용 파싱 (크롤링된 파일이 있는 경우)
        # if reports and len(reports) > 0:
        #     crawler.parse_pdf_content()
        
        logger.info("프로그램 정상 종료")
    
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {str(e)}")
        logger.info("프로그램 비정상 종료")

if __name__ == "__main__":
    main()
    sys.exit(0)
