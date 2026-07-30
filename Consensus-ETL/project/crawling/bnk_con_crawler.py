import requests
from bs4 import BeautifulSoup
import os
import logging
from datetime import datetime
import time
import pandas as pd
import re
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import sys

# 로깅 설정
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'bnk_download_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 콘솔에도 로그 출력
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

class BNKReportCrawler:
    def __init__(self, download_dir='bnk_reports', max_pages=3, max_reports=10, headless=True):
        """
        BNK투자증권 리포트 크롤러 초기화
        
        Args:
            download_dir (str): PDF 파일 다운로드 디렉토리
            max_pages (int): 크롤링할 최대 페이지 수
            max_reports (int): 다운로드할 최대 리포트 수
            headless (bool): 헤드리스 모드 사용 여부 (화면 표시 없음)
        """
        self.base_url = 'https://www.bnkfn.co.kr'
        self.list_url = 'https://www.bnkfn.co.kr/research/analysingCompany.jspx'
        self.download_dir = download_dir
        self.max_pages = max_pages
        self.max_reports = max_reports
        self.headless = headless
        self.session = requests.Session()

        # 종료 코드 판정용 실패 집계
        self.failed_count = 0

        # User-Agent 설정 (크롤링 차단 방지)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # 다운로드 디렉토리 생성
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 기존 다운로드 기록 (중복 다운로드 방지)
        self.download_history = self._load_download_history()
        
        # Selenium 브라우저 설정
        self.driver = None
        
    def _setup_driver(self):
        """Selenium 웹 드라이버 설정"""
        if self.driver:
            return
            
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--mute-audio")
            chrome_options.add_argument(f"--user-agent={self.headers['User-Agent']}")
            
            # PDF 뷰어 비활성화 (다운로드 위해)
            prefs = {
                "download.default_directory": os.path.abspath(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True,
                "profile.default_content_setting_values.automatic_downloads": 1
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # 웹 드라이버 설정 및 실행
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logging.info("Selenium 웹 드라이버가 성공적으로 설정되었습니다.")
        
        except Exception as e:
            logging.error(f"Selenium 웹 드라이버 설정 중 오류: {e}")
            raise
    
    def _close_driver(self):
        """Selenium 웹 드라이버 종료"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logging.info("Selenium 웹 드라이버가 종료되었습니다.")
            except Exception as e:
                logging.error(f"Selenium 웹 드라이버 종료 중 오류: {e}")
        
    def _load_download_history(self):
        """기존에 다운로드한 리포트 목록 로드"""
        history_file = os.path.join(self.download_dir, 'download_history.csv')
        if os.path.exists(history_file):
            try:
                return pd.read_csv(history_file)
            except Exception as e:
                logging.error(f"다운로드 기록 로드 중 오류: {e}")
                return pd.DataFrame(columns=['report_no', 'title', 'date', 'author', 'filename', 'download_method'])
        return pd.DataFrame(columns=['report_no', 'title', 'date', 'author', 'filename', 'download_method'])
    
    def _save_download_history(self, report_info):
        """다운로드 기록 저장"""
        history_file = os.path.join(self.download_dir, 'download_history.csv')
        
        # 새 데이터 프레임 생성
        new_row = pd.DataFrame([report_info])
        
        # 기존 기록에 추가
        self.download_history = pd.concat([self.download_history, new_row], ignore_index=True)
        
        # CSV 파일로 저장
        self.download_history.to_csv(history_file, index=False, encoding='utf-8-sig')
    
    def _generate_filename(self, title, date):
        match = re.search(r'\((.*?)\)', title)
        corp_name = re.sub(r'[\\/*?:"<>|]', '_', match.group(1)) if match else "미상"
        safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)
        return f"{date.replace('.', '')}_{safe_title}_{corp_name}.pdf"

    def get_report_list(self):
        """
        BNK투자증권 웹사이트에서 리포트 목록 가져오기
        
        Returns:
            list: 리포트 정보 딕셔너리 목록
        """
        all_reports = []
        
        # 브라우저 설정
        self._setup_driver()
        
        for page in range(1, self.max_pages + 1):
            logging.info(f"페이지 {page} 크롤링 중...")
            
            # 페이지 URL 구성
            page_url = f"{self.list_url}?page={page}" if page > 1 else self.list_url
            
            try:
                # Selenium으로 페이지 로드
                self.driver.get(page_url)
                
                # 페이지 로딩 대기
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                
                # 페이지 소스 가져오기
                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                # 리포트 테이블 찾기
                table = soup.find('table')
                if not table:
                    logging.warning(f"페이지 {page}에서 테이블을 찾을 수 없습니다.")
                    continue
                
                # 리포트 행 추출
                rows = table.find_all('tr')[1:]  # 헤더 행 제외
                
                if not rows:
                    logging.warning(f"페이지 {page}에서 리포트 행을 찾을 수 없습니다.")
                    break  # 더 이상 페이지가 없는 경우
                
                # 각 행에서 리포트 정보 추출
                for row in rows:
                    try:
                        # 각 열(td) 추출
                        columns = row.find_all('td')
                        
                        if len(columns) < 6:
                            continue
                        
                        # 리포트 번호
                        report_no = columns[0].text.strip()
                        
                        # 리포트 제목
                        title_element = columns[1]
                        title = title_element.text.strip()
                        
                        # 제목 링크 확인
                        title_link = title_element.find('a')
                        has_link = bool(title_link)
                        
                        # onclick 속성 추출 (JavaScript 호출 정보)
                        onclick_attr = ''
                        if title_link and 'onclick' in title_link.attrs:
                            onclick_attr = title_link['onclick']
                        
                        # 작성자
                        author = columns[2].text.strip()
                        
                        # 첨부 파일 확인
                        has_attachment = bool(columns[3].find('img'))
                        
                        # 작성일
                        date = columns[4].text.strip()
                        
                        # 조회수
                        views = columns[5].text.strip()
                        
                        # 이미 다운로드한 리포트인지 확인
                        if report_no in self.download_history['report_no'].values:
                            logging.info(f"이미 다운로드한 리포트: {report_no} - {title}")
                            continue
                        
                        # 리포트 정보 저장 (링크가 있는 리포트만)
                        if has_link or has_attachment:
                            report_info = {
                                'no': report_no,
                                'title': title,
                                'author': author,
                                'date': date,
                                'views': views,
                                'onclick': onclick_attr
                            }
                            all_reports.append(report_info)
                            
                            # 최대 리포트 수 도달 시 종료
                            if len(all_reports) >= self.max_reports:
                                logging.info(f"최대 리포트 수({self.max_reports})에 도달하여 크롤링 종료")
                                return all_reports
                    
                    except Exception as e:
                        logging.error(f"행 파싱 중 오류: {e}")
                        continue
                
                # 페이지 사이 대기 (서버 부하 방지)
                time.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logging.error(f"페이지 {page} 크롤링 중 오류: {e}")
                continue
        
        return all_reports
    
    def download_report_using_selenium(self, report):
        """
        Selenium을 사용하여 리포트 다운로드
        
        Args:
            report (dict): 리포트 정보 딕셔너리
            
        Returns:
            bool: 다운로드 성공 여부
        """
        report_no = report['no']
        title = report['title']
        
        try:
            # 리스트 페이지 로드
            self.driver.get(self.list_url)
            
            # 페이지 로딩 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # 리포트 행 찾기
            report_rows = self.driver.find_elements(By.TAG_NAME, "tr")
            
            # 해당 리포트의 행 찾기
            target_row = None
            for row in report_rows:
                try:
                    if report_no in row.text:
                        # 번호와 제목 모두 확인
                        if title in row.text:
                            target_row = row
                            break
                except:
                    continue
            
            if not target_row:
                logging.warning(f"Selenium에서 리포트를 찾을 수 없습니다: {report_no} - {title}")
                return False
            
            # 다운로드 방법 1: 제목 링크 클릭
            try:
                # 해당 행에서 제목 링크 찾기
                title_link = target_row.find_element(By.CSS_SELECTOR, "td:nth-child(2) a")
                
                # 새 창에서 열리지 않도록 JavaScript로 클릭 효과 직접 실행
                self.driver.execute_script("arguments[0].click();", title_link)
                
                # PDF 로딩 대기 (PDF가 iframe이나 object 태그로 표시될 수 있음)
                time.sleep(5)  # PDF 로딩 대기
                
                # 현재 URL 확인 (PDF URL로 리디렉션 된 경우)
                current_url = self.driver.current_url
                
                if '.pdf' in current_url:
                    # PDF URL로 리디렉션 된 경우, 직접 다운로드
                    self._download_pdf_from_url(current_url, report)
                    return True
                
                # 브라우저에서 PDF 뷰어나 다운로드 버튼 확인
                pdf_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "iframe[src*='.pdf'], object[data*='.pdf'], embed[src*='.pdf'], a[href*='.pdf']")
                
                if pdf_elements:
                    for elem in pdf_elements:
                        pdf_url = None
                        if elem.tag_name == 'iframe':
                            pdf_url = elem.get_attribute('src')
                        elif elem.tag_name == 'object':
                            pdf_url = elem.get_attribute('data')
                        elif elem.tag_name == 'embed':
                            pdf_url = elem.get_attribute('src')
                        elif elem.tag_name == 'a':
                            pdf_url = elem.get_attribute('href')
                        
                        if pdf_url and '.pdf' in pdf_url:
                            if not pdf_url.startswith('http'):
                                pdf_url = f"{self.base_url}{pdf_url}" if not pdf_url.startswith('/') else f"{self.base_url}{pdf_url}"
                            
                            # PDF URL 발견, 다운로드
                            logging.info(f"PDF URL 발견: {pdf_url}")
                            self._download_pdf_from_url(pdf_url, report)
                            return True
                
                # 다운로드 버튼 찾기
                download_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                    "a[href*='download'], button[onclick*='download'], a[onclick*='download']")
                
                if download_buttons:
                    for button in download_buttons:
                        try:
                            # 다운로드 버튼 클릭
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)  # 다운로드 시작 대기
                            
                            # 다운로드 파일 확인
                            if self._check_download_completed(report):
                                return True
                        except:
                            continue
            
            except Exception as e:
                logging.error(f"제목 링크 클릭 방식 다운로드 중 오류: {e}")
            
            # 다운로드 방법 2: 첨부 파일 아이콘 클릭
            try:
                # 리스트 페이지로 돌아가기
                self.driver.get(self.list_url)
                
                # 페이지 로딩 대기
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                
                # 리포트 행 다시 찾기
                report_rows = self.driver.find_elements(By.TAG_NAME, "tr")
                target_row = None
                for row in report_rows:
                    try:
                        if report_no in row.text and title in row.text:
                            target_row = row
                            break
                    except:
                        continue
                
                if target_row:
                    # 첨부 파일 아이콘 찾기
                    attachment_icon = target_row.find_element(By.CSS_SELECTOR, "td:nth-child(4) img")
                    
                    # 클릭
                    self.driver.execute_script("arguments[0].click();", attachment_icon)
                    time.sleep(3)  # 다운로드 시작 대기
                    
                    # 다운로드 파일 확인
                    if self._check_download_completed(report):
                        return True
            
            except Exception as e:
                logging.error(f"첨부 파일 아이콘 클릭 방식 다운로드 중 오류: {e}")
            
            # 다운로드 방법 3: 네트워크 모니터링을 통한 PDF URL 추적
            try:
                # 브라우저의 네트워크 요청 로그 확인
                pdf_urls = []
                for request in self.driver.execute_script("return window.performance.getEntries();"):
                    url = request.get('name', '')
                    if '.pdf' in url:
                        pdf_urls.append(url)
                
                if pdf_urls:
                    for pdf_url in pdf_urls:
                        try:
                            self._download_pdf_from_url(pdf_url, report)
                            return True
                        except:
                            continue
            
            except Exception as e:
                logging.error(f"네트워크 모니터링 방식 다운로드 중 오류: {e}")
            
            # 모든 방법 실패
            return False
            
        except Exception as e:
            logging.error(f"Selenium을 사용한 리포트 다운로드 중 오류: {e}")
            return False
    
    def _check_download_completed(self, report):
        time.sleep(5)

        # 다운로드 디렉토리에서 가장 최근 PDF 파일을 찾음
        downloaded_files = os.listdir(self.download_dir)
        pdf_files = [f for f in downloaded_files if f.endswith('.pdf')]

        if not pdf_files:
            return False

        pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.download_dir, x)), reverse=True)
        latest_pdf = pdf_files[0]
        file_path = os.path.join(self.download_dir, latest_pdf)

        file_size = os.path.getsize(file_path)
        if file_size < 1000:
            return False

        try:
            self._save_download_history({
                'report_no': report['no'],
                'title': report['title'],
                'date': report['date'],
                'author': report['author'],
                'filename': latest_pdf,
                'download_method': 'selenium'
            })
            logging.info(f"다운로드 성공: {latest_pdf} ({file_size} bytes)")
            return True
        except Exception as e:
            logging.error(f"다운로드 기록 저장 실패: {e}")
            return False

    def _download_pdf_from_url(self, pdf_url, report):
        """
        PDF URL에서 직접 다운로드 (원본 파일명으로 저장)
        """
        try:
            # PDF 파일 다운로드
            response = requests.get(pdf_url, headers=self.headers, stream=True, timeout=10)

            if response.status_code == 200:
                # Content-Type 확인
                content_type = response.headers.get('Content-Type', '')
                is_pdf = 'pdf' in content_type.lower() or 'application/octet-stream' in content_type.lower()

                if not is_pdf and len(response.content) < 1000:
                    logging.warning(f"PDF가 아닌 것 같습니다: {content_type}")
                    return False

                # 파일명 추출 (URL에서)
                url_filename = pdf_url.split('/')[-1].split('?')[0]
                file_path = os.path.join(self.download_dir, url_filename)

                # 파일이 이미 존재하면 다운로드하지 않음
                if os.path.exists(file_path):
                    logging.info(f"이미 파일이 존재하여 다운로드를 건너뜀: {url_filename}")
                    return True

                # 파일 저장
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # 파일 크기 확인
                file_size = os.path.getsize(file_path)
                if file_size < 1000:
                    logging.warning(f"파일 크기가 너무 작습니다 ({file_size} bytes). 다운로드 실패 의심.")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return False

                # 다운로드 기록 저장
                self._save_download_history({
                    'report_no': report['no'],
                    'title': report['title'],
                    'date': report['date'],
                    'author': report['author'],
                    'filename': url_filename,
                    'download_method': 'direct_url'
                })

                logging.info(f"URL에서 직접 다운로드 성공: {url_filename} ({file_size} bytes)")
                return True

            else:
                logging.warning(f"PDF URL 요청 실패: HTTP {response.status_code}")
                return False

        except Exception as e:
            logging.error(f"PDF URL에서 직접 다운로드 중 오류: {e}")
            return False
    
    def download_reports(self, reports):
        """
        리포트 목록에서 PDF 파일 다운로드
        
        Args:
            reports (list): 리포트 정보 딕셔너리 목록
        """
        # 작성일 기준으로 정렬 (최신순)
        sorted_reports = sorted(reports, key=lambda x: x['date'], reverse=True)
        
        logging.info(f"총 {len(sorted_reports)}개의 리포트 다운로드 시작")
        
        # Selenium 드라이버 설정
        self._setup_driver()
        
        for idx, report in enumerate(sorted_reports, 1):
            try:
                report_no = report['no']
                title = report['title']
                
                logging.info(f"[{idx}/{len(sorted_reports)}] 리포트 다운로드 시도: {report_no} - {title}")
                
                # Selenium을 사용하여 다운로드
                success = self.download_report_using_selenium(report)

                if not success:
                    logging.error(f"리포트 다운로드 실패: {report_no} - {title}")
                    self.failed_count += 1
                
                # 다운로드 간격 조절 (서버 부하 방지)
                time.sleep(random.uniform(1.5, 3.0))
                
            except Exception as e:
                logging.error(f"리포트 {report['no']} 처리 중 오류: {e}")
                self.failed_count += 1
                continue
    
#     def create_summary_report(self):
#         """다운로드한 파일들의 요약 보고서 생성"""
#         if self.download_history.empty:
#             logging.warning("다운로드 기록이 없어 요약 보고서를 생성할 수 없습니다.")
#             return
        
#         try:
#             # 요약 보고서 파일 경로
#             report_path = os.path.join(self.download_dir, 'summary_report.html')
            
#             # HTML 보고서 생성
#             html_content = """
            
            
            
                
                
                
                
            
            
                
# BNK투자증권 리포트 다운로드 요약

                

                    
# 총 다운로드 파일 수: {total_files}개


                    
# 최신 다운로드 날짜: {latest_date}


                    
# 대상 기간: {date_range}


                

                
                
# 작성일별 리포트 목록

#             """.format(
#                 total_files=len(self.download_history),
#                 latest_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                 date_range=f"{self.download_history['date'].min()} ~ {self.download_history['date'].max()}"
#             )
            
#             # 작성일 기준으로 정렬
#             sorted_history = self.download_history.sort_values(by='date', ascending=False)
            
#             # 작성일별로 그룹화
#             date_groups = sorted_history.groupby('date')
            
#             # 각 작성일별 테이블 생성
#             for date, group in date_groups:
#                 html_content += f"""
                

                    
# 작성일: {date}

                    
#                 """
                
#                 for _, row in group.iterrows():
#                     html_content += f"""
                        
#                     """
                
#                 html_content += """
                    
# 번호	제목	작성자	파일명	다운로드 방식
# {row['report_no']}	{row['title']}	{row['author']}	{row['filename']}	{row['download_method']}

                

#                 """
            
#             html_content += """
            
            
#             """
            
#             # HTML 파일로 저장
#             with open(report_path, 'w', encoding='utf-8') as f:
#                 f.write(html_content)
            
#             logging.info(f"요약 보고서가 생성되었습니다: {report_path}")
            
#         except Exception as e:
#             logging.error(f"요약 보고서 생성 중 오류: {e}")
    
    def run(self):
        """크롤러 실행

        Returns:
            int: 종료 코드 (0=성공, 1=실패). Airflow가 재시도할 수 있게 전파한다.
        """
        logging.info("BNK투자증권 리포트 크롤링 시작")

        try:
            # 리포트 목록 가져오기
            reports = self.get_report_list()

            if not reports:
                logging.warning("다운로드할 리포트가 없습니다.")
                return 1

            # 리포트 다운로드
            self.download_reports(reports)

            # 요약 보고서 생성
            # self.create_summary_report()

            # 드라이버 종료
            self._close_driver()

            logging.info("크롤링 완료")

            if self.failed_count:
                logging.error(f"{self.failed_count}개 리포트 다운로드 실패")
                return 1
            return 0

        except Exception as e:
            logging.error(f"크롤링 중 오류 발생: {e}")
            # 오류가 발생해도 드라이버는 종료
            self._close_driver()
            return 1


BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # 현재 파일 경로
PARENT_DIR = os.path.dirname(BASE_DIR)                         # 상위 디렉토리
DOWNLOAD_DIR = os.path.join(PARENT_DIR, "consensus", "bnk")    # 원하는 저장 위치
os.makedirs(DOWNLOAD_DIR, exist_ok=True)                       # 디렉토리 없으면 생성


if __name__ == "__main__":
    # 크롤러 설정 및 실행
    crawler = BNKReportCrawler(
        download_dir=DOWNLOAD_DIR,  # 다운로드 디렉토리
        max_pages=3,                 # 크롤링할 최대 페이지 수
        max_reports=50,              # 다운로드할 최대 리포트 수
        headless=True                # 헤드리스 모드 사용 (True: 브라우저 창 표시 안 함)
    )
    
    sys.exit(crawler.run())