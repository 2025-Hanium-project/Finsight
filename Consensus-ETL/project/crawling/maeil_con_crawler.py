import time
import os
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import requests
from urllib.parse import urljoin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
download_path = os.path.join(PARENT_DIR, "consensus", "maeil")
os.makedirs(download_path, exist_ok=True)

class MaeilEconomyCrawler:
    def __init__(self, base_dir=download_path):
        self.base_url = "https://stock.mk.co.kr"
        self.base_dir = base_dir
        Path(base_dir).mkdir(parents=True, exist_ok=True)
        
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # 다운로드 설정
        prefs = {
            "download.default_directory": os.path.abspath(base_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 웹드라이버 초기화
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # HTTP 요청용 헤더
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def __del__(self):
        """소멸자: 드라이버 종료"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def crawl_reports(self, date="2025-07-19", page=1, stock_code=""):
        """매일경제 증권사 리포트 크롤링"""
        try:
            url = f"{self.base_url}/price/report?stock_code={stock_code}&day={date}&page={page}"
            print(f"페이지 URL: {url}")
            
            # 페이지 접속
            self.driver.get(url)
            time.sleep(3)
            
            # 페이지 로딩 대기
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
            except TimeoutException:
                print("리포트 테이블을 찾을 수 없습니다.")
                return []
            
            # 리포트 데이터 파싱
            reports = self._parse_report_table()
            
            print(f"발견된 리포트 수: {len(reports)}")
            return reports
            
        except Exception as e:
            print(f"크롤링 중 오류 발생: {e}")
            return []
    
    def _parse_report_table(self):
        """리포트 테이블에서 데이터 추출"""
        reports = []
        
        try:
            report_rows = self.driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            
            for row in report_rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 5:
                        title = cells[0].text.strip()
                        category = cells[1].text.strip()
                        analyst = cells[2].text.strip()
                        company = cells[3].text.strip()
                        date_text = cells[4].text.strip()
                        
                        # 헤더 행이나 빈 행 필터링
                        if (not title or title in ['0', '제목', 'title'] or 
                            not company or company in ['0', '증권사', 'company'] or
                            title.startswith('0 ') or '0.00%' in title):
                            continue
                        
                        # 다운로드 링크 찾기 (조용히 처리)
                        download_link = self._find_download_link(row)
                        
                        report_entry = {
                            'date': self._format_date(date_text),
                            'title': title,
                            'category': category,
                            'analyst': analyst,
                            'company': company,
                            'download_link': download_link,
                            'filename': self._generate_filename(title, company, date_text)
                        }
                        
                        reports.append(report_entry)
                        
                except Exception as e:
                    # 조용히 넘어가기 (헤더 행 등에서 발생하는 정상적인 오류)
                    continue
            
        except Exception as e:
            print(f"데이터 파싱 중 오류 발생: {e}")
        
        return reports
    
    def _find_download_link(self, row_element):
        """PDF 다운로드 링크 찾기 - 매일경제 웹사이트 구조에 맞게 개선"""
        try:
            # 방법 1: 제목 링크 클릭하여 상세 페이지로 이동
            try:
                title_link = row_element.find_element(By.CSS_SELECTOR, "td:first-child a")
                if title_link:
                    detail_url = title_link.get_attribute("href")
                    if detail_url:
                        return self._get_pdf_from_detail_page(detail_url)
            except:
                # 링크가 없는 행은 조용히 넘어가기
                pass
            
            # 방법 2: onclick 이벤트에서 직접 PDF URL 추출
            onclick_elements = row_element.find_elements(By.CSS_SELECTOR, "[onclick]")
            for element in onclick_elements:
                onclick = element.get_attribute("onclick")
                if onclick:
                    # JavaScript에서 PDF URL 패턴 찾기
                    patterns = [
                        r"window\.open\(['\"]([^'\"]*\.pdf[^'\"]*)['\"]",
                        r"location\.href\s*=\s*['\"]([^'\"]*\.pdf[^'\"]*)['\"]",
                        r"download\(['\"]([^'\"]*)['\"]",
                        r"['\"]([^'\"]*\/download\/[^'\"]*)['\"]",
                        r"['\"]([^'\"]*\.pdf[^'\"]*)['\"]"
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, onclick)
                        if match:
                            url = match.group(1)
                            if not url.startswith('http'):
                                url = urljoin(self.base_url, url)
                            return url
            
            # 방법 3: 다운로드 아이콘이나 버튼 찾기
            download_elements = row_element.find_elements(By.CSS_SELECTOR, 
                "img[src*='download'], img[alt*='다운로드'], img[title*='다운로드'], "
                "a[title*='다운로드'], button[title*='다운로드'], "
                ".download, .btn-download, [class*='download']")
            
            for element in download_elements:
                # 부모 요소에서 링크 찾기
                parent = element.find_element(By.XPATH, "..")
                if parent.tag_name == 'a':
                    href = parent.get_attribute("href")
                    if href:
                        return href
                
                # onclick 이벤트 확인
                onclick = element.get_attribute("onclick")
                if onclick:
                    url_match = re.search(r"['\"]([^'\"]*(?:\.pdf|download)[^'\"]*)['\"]", onclick)
                    if url_match:
                        url = url_match.group(1)
                        if not url.startswith('http'):
                            url = urljoin(self.base_url, url)
                        return url
            
        except Exception as e:
            # 조용히 처리 (헤더 행이나 링크가 없는 행에서 발생하는 정상적인 상황)
            pass
        
        return None
    
    def _get_pdf_from_detail_page(self, detail_url):
        """상세 페이지에서 PDF 다운로드 링크 찾기"""
        try:
            # 새 탭에서 상세 페이지 열기
            original_window = self.driver.current_window_handle
            self.driver.execute_script("window.open(arguments[0]);", detail_url)
            
            # 새 탭으로 전환
            new_window = [window for window in self.driver.window_handles if window != original_window][0]
            self.driver.switch_to.window(new_window)
            
            time.sleep(2)  # 페이지 로딩 대기
            
            # 다운로드 버튼/링크 찾기
            download_selectors = [
                "a[href*='.pdf']",
                "a[href*='download']", 
                "button[onclick*='pdf']",
                "button[onclick*='download']",
                ".btn-download",
                ".download-btn",
                "img[src*='download']",
                "a[title*='다운로드']",
                "button[title*='다운로드']",
                "[class*='download'][href]",
                "[onclick*='pdf']",
                "[onclick*='download']"
            ]
            
            for selector in download_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        # href 속성 확인
                        href = element.get_attribute("href")
                        if href and ('.pdf' in href.lower() or 'download' in href.lower()):
                            # 원래 탭으로 돌아가기
                            self.driver.close()
                            self.driver.switch_to.window(original_window)
                            return href
                        
                        # onclick 이벤트 확인
                        onclick = element.get_attribute("onclick")
                        if onclick:
                            url_patterns = [
                                r"window\.open\(['\"]([^'\"]*)['\"]",
                                r"location\.href\s*=\s*['\"]([^'\"]*)['\"]",
                                r"download\(['\"]([^'\"]*)['\"]",
                                r"['\"]([^'\"]*\.pdf[^'\"]*)['\"]"
                            ]
                            
                            for pattern in url_patterns:
                                match = re.search(pattern, onclick)
                                if match:
                                    url = match.group(1)
                                    if not url.startswith('http'):
                                        url = urljoin(self.base_url, url)
                                    # 원래 탭으로 돌아가기
                                    self.driver.close()
                                    self.driver.switch_to.window(original_window)
                                    return url
                except:
                    continue
            
            # PDF 직접 링크가 있는지 페이지 소스에서 검색
            page_source = self.driver.page_source
            pdf_patterns = [
                r'href=["\']([^"\']*\.pdf[^"\']*)["\']',
                r'src=["\']([^"\']*\.pdf[^"\']*)["\']',
                r'url\(["\']([^"\']*\.pdf[^"\']*)["\']',
                r'["\']([^"\']*\/download\/[^"\']*\.pdf[^"\']*)["\']'
            ]
            
            for pattern in pdf_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    url = matches[0]
                    if not url.startswith('http'):
                        url = urljoin(self.base_url, url)
                    # 원래 탭으로 돌아가기
                    self.driver.close()
                    self.driver.switch_to.window(original_window)
                    return url
            
            # 원래 탭으로 돌아가기
            self.driver.close()
            self.driver.switch_to.window(original_window)
            
        except Exception as e:
            print(f"상세 페이지에서 PDF 링크 찾기 중 오류: {e}")
            # 오류 시에도 원래 탭으로 돌아가기
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(original_window)
            except:
                pass
        
        return None
    
    def _format_date(self, date_text):
        """날짜 형식 정리"""
        if not date_text:
            return datetime.now().strftime('%Y-%m-%d')
        
        # 날짜 패턴 정리 (예: 2025.07.19 -> 2025-07-19)
        date_text = re.sub(r'(\d{4})\.(\d{2})\.(\d{2})', r'\1-\2-\3', date_text)
        date_text = re.sub(r'(\d{4})-(\d{1})-(\d{1})', r'\1-0\2-0\3', date_text)  # 한자리 월/일 처리
        date_text = re.sub(r'(\d{4})-(\d{2})-(\d{1})', r'\1-\2-0\3', date_text)
        date_text = re.sub(r'(\d{4})-(\d{1})-(\d{2})', r'\1-0\2-\3', date_text)
        
        return date_text if re.match(r'\d{4}-\d{2}-\d{2}', date_text) else datetime.now().strftime('%Y-%m-%d')
    
    def _generate_filename(self, title, company, date):
        """파일명 생성"""
        safe_title = re.sub(r'[\\/*?:"<>|]', '_', title)
        safe_company = re.sub(r'[\\/*?:"<>|]', '_', company)
        date_str = self._format_date(date).replace('-', '')
        return f"{date_str}_{safe_company}_{safe_title}.pdf"
    
    def download_pdf(self, download_url, filename):
        """PDF 파일 다운로드 - 개선된 버전"""
        try:
            # 파일이 이미 존재하면 건너뛰기
            filepath = os.path.join(self.base_dir, filename)
            if os.path.exists(filepath):
                print(f"파일이 이미 존재함: {filename}")
                return filepath
            
            print(f"다운로드 시도: {download_url}")
            
            # 세션을 사용하여 쿠키 유지
            session = requests.Session()
            session.headers.update(self.headers)
            
            # 첫 번째 요청으로 페이지 접근 (세션 설정)
            try:
                initial_response = session.get(download_url, timeout=10)
                initial_response.raise_for_status()
                
                # Content-Type 확인
                content_type = initial_response.headers.get('Content-Type', '').lower()
                
                if 'application/pdf' in content_type:
                    # 직접 PDF 파일인 경우
                    with open(filepath, 'wb') as f:
                        f.write(initial_response.content)
                    
                    file_size = os.path.getsize(filepath)
                    if file_size > 1000:  # 1KB 이상
                        print(f"다운로드 완료: {filename} ({file_size} bytes)")
                        return filepath
                    else:
                        os.remove(filepath)
                        print(f"파일 크기가 너무 작음: {file_size} bytes")
                        return None
                
                elif 'text/html' in content_type:
                    # HTML 페이지인 경우, PDF 링크 찾기
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(initial_response.content, 'html.parser')
                    
                    # PDF 직접 링크 찾기
                    pdf_links = soup.find_all('a', href=re.compile(r'.*\.pdf.*', re.I))
                    for link in pdf_links:
                        pdf_url = link.get('href')
                        if pdf_url:
                            if not pdf_url.startswith('http'):
                                pdf_url = urljoin(download_url, pdf_url)
                            
                            pdf_response = session.get(pdf_url, timeout=10)
                            if pdf_response.status_code == 200:
                                with open(filepath, 'wb') as f:
                                    f.write(pdf_response.content)
                                
                                file_size = os.path.getsize(filepath)
                                if file_size > 1000:
                                    print(f"다운로드 완료: {filename} ({file_size} bytes)")
                                    return filepath
                                else:
                                    os.remove(filepath)
                    
                    # 다운로드 버튼이나 스크립트 찾기
                    download_scripts = soup.find_all(string=re.compile(r'.*\.pdf.*|.*download.*', re.I))
                    for script in download_scripts:
                        url_match = re.search(r'["\']([^"\']*\.pdf[^"\']*)["\']', script)
                        if url_match:
                            pdf_url = url_match.group(1)
                            if not pdf_url.startswith('http'):
                                pdf_url = urljoin(download_url, pdf_url)
                            
                            try:
                                pdf_response = session.get(pdf_url, timeout=10)
                                if pdf_response.status_code == 200 and 'application/pdf' in pdf_response.headers.get('Content-Type', ''):
                                    with open(filepath, 'wb') as f:
                                        f.write(pdf_response.content)
                                    
                                    file_size = os.path.getsize(filepath)
                                    if file_size > 1000:
                                        print(f"다운로드 완료: {filename} ({file_size} bytes)")
                                        return filepath
                                    else:
                                        os.remove(filepath)
                            except:
                                continue
                
            except requests.RequestException as e:
                print(f"다운로드 요청 실패: {e}")
                return None
            
        except Exception as e:
            print(f"PDF 다운로드 중 오류: {e}")
            return None
        
        print(f"PDF 다운로드 실패: {filename}")
        return None
    
    def save_to_csv(self, reports, filename="maeil_consensus.csv"):
        """데이터를 CSV 파일로 저장"""
        if not reports:
            print("저장할 데이터가 없습니다.")
            return None
        
        df = pd.DataFrame(reports)
        
        # CSV 파일로 저장
        file_path = os.path.join(self.base_dir, filename)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        
        print(f"데이터가 {file_path}에 성공적으로 저장되었습니다.")
        print(f"저장된 데이터: {len(df)}행 × {len(df.columns)}열")
        
        return df
    
    def download_reports(self, reports, max_downloads=None):
        """리포트 목록에서 PDF 파일 다운로드"""
        downloaded_files = []
        
        # max_downloads가 None이면 모든 리포트 다운로드
        if max_downloads is None:
            reports_to_download = reports
        else:
            reports_to_download = reports[:max_downloads]
        
        for i, report in enumerate(reports_to_download, 1):
            try:
                print(f"[{i}/{len(reports_to_download)}] 다운로드 시도: {report['title']}")
                
                if report['download_link']:
                    filepath = self.download_pdf(report['download_link'], report['filename'])
                    if filepath:
                        downloaded_files.append(filepath)
                else:
                    print(f"다운로드 링크가 없습니다: {report['title']}")
                
                time.sleep(1)  # 서버 부하 방지
                
            except Exception as e:
                print(f"리포트 {report['title']} 다운로드 중 오류: {e}")
                continue
        
        return downloaded_files
    
    def run(self, date="2025-07-19", max_pages=3, stock_code=""):
        """크롤러 실행"""
        print("매일경제 리포트 크롤링 시작")
        
        all_reports = []
        
        for page in range(1, max_pages + 1):
            print(f"페이지 {page} 크롤링 중...")
            reports = self.crawl_reports(date=date, page=page, stock_code=stock_code)
            
            if not reports:
                print(f"페이지 {page}에서 리포트를 찾을 수 없습니다.")
                break
                
            all_reports.extend(reports)
            time.sleep(2)  # 페이지 간 대기
        
        if all_reports:
            # CSV 저장
            df = self.save_to_csv(all_reports)
            
            # PDF 다운로드 (모든 리포트)
            downloaded = self.download_reports(all_reports, max_downloads=None)
            
            if df is not None:
                print("\n=== 크롤링 결과 요약 ===")
                print(f"총 리포트 수: {len(df)}")
                print(f"다운로드된 파일 수: {len(downloaded)}")
                print(f"컬럼: {list(df.columns)}")
        else:
            print("크롤링된 데이터가 없습니다.")

if __name__ == "__main__":
    crawler = MaeilEconomyCrawler()
    # 첫 페이지만 테스트하고, 처음 3개 리포트만 다운로드 시도
    crawler.run(date="2025-07-19", max_pages=1)
