import time
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from urllib.parse import urljoin, urlparse, parse_qs

# 다운로드 경로 설정 (다른 크롤링 코드와 일치)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
download_path = os.path.join(PARENT_DIR, "consensus", "paxnet")
os.makedirs(download_path, exist_ok=True)

class PaxnetPDFDownloader:
    def __init__(self, download_path=None):
        """
        팍스넷 PDF 다운로더 초기화
        """
        if download_path is None:
            download_path = os.path.join(PARENT_DIR, "consensus", "paxnet")
        
        self.download_path = os.path.abspath(download_path)
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        
        # Chrome 옵션 설정
        self.chrome_options = Options()
        self.chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True
        })
        
        # 헤드리스 모드 옵션 (필요시 주석 해제)
        # self.chrome_options.add_argument('--headless')
        
    def download_from_list_page(self, list_url):
        """
        리스트 페이지에서 모든 리포트 PDF 다운로드
        
        Args:
            list_url: 리포트 목록 페이지 URL
        """
        driver = webdriver.Chrome(options=self.chrome_options)
        downloaded_files = []
        
        try:
            print(f"리스트 페이지 접속: {list_url}")
            driver.get(list_url)
            
            # 페이지가 완전히 로드될 때까지 대기
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.board-list"))
            )
            time.sleep(3)
            
            # 팍스넷 리포트 목록 찾기 - 스크린샷에서 확인된 구조
            report_links = driver.find_elements(By.CSS_SELECTOR, "ul.board-list li a[href*='javascript:selectView']")
            
            if not report_links:
                print("리포트 목록을 찾을 수 없습니다.")
                return downloaded_files
            
            print(f"총 {len(report_links)}개의 리포트 발견")
            
            # 각 리포트 처리
            processed = 0
            for i in range(len(report_links)):
                try:
                    # 매번 새로 찾기 (DOM이 변경될 수 있으므로)
                    report_links = driver.find_elements(By.CSS_SELECTOR, "ul.board-list li a[href*='javascript:selectView']")
                    if i >= len(report_links):
                        break
                    
                    link = report_links[i]
                    title = link.text.strip()
                    
                    if not title:
                        continue
                    
                    print(f"\n[{processed+1}/{len(report_links)}] 리포트: {title[:60]}...")
                    
                    # href에서 reportId 추출
                    href = link.get_attribute('href')
                    if href:
                        match = re.search(r"selectView\('(\d+)'\)", href)
                        
                        if match:
                            report_id = match.group(1)
                            report_url = f"https://www.paxnet.co.kr/stock/report/reportView?menuCode=2222&reportId={report_id}"
                            
                            # 새 탭에서 열기
                            driver.execute_script("window.open('');")
                            driver.switch_to.window(driver.window_handles[-1])
                            driver.get(report_url)
                            time.sleep(3)
                            
                            # PDF 다운로드
                            pdf_file = self._download_pdf_from_detail_page(driver, title)
                            if pdf_file:
                                downloaded_files.append(pdf_file)
                                processed += 1
                            
                            # 탭 닫고 원래 탭으로 돌아가기
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                            time.sleep(1)
                    
                except Exception as e:
                    print(f"  오류 발생: {e}")
                    # 오류 발생 시에도 원래 탭으로 돌아가기
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    continue
                    
        except Exception as e:
            print(f"전체 프로세스 오류: {e}")
            
        finally:
            driver.quit()
            
        print(f"\n총 {len(downloaded_files)}개의 PDF 다운로드 완료")
        return downloaded_files
    
    def _download_pdf_from_detail_page(self, driver, title):
        """
        상세 페이지에서 PDF 다운로드 처리
        """
        try:
            # 페이지 로딩 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)
            
            # PDF 파일 링크 찾기 - 여러 패턴 시도
            pdf_link = None
            pdf_url = None
            
            # 1. 직접적인 PDF 링크 찾기
            pdf_selectors = [
                "a[href*='.pdf']",
                "a[href*='.PDF']",
                "a[onclick*='pdf']",
                "a[onclick*='PDF']",
                "a[onclick*='download']",
                "a[onclick*='Download']"
            ]
            
            for selector in pdf_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        href = elem.get_attribute('href') or ''
                        onclick = elem.get_attribute('onclick') or ''
                        text = elem.text.strip().lower()
                        
                        # PDF 관련 텍스트나 링크 확인
                        if 'pdf' in href.lower() or 'pdf' in onclick.lower() or 'pdf' in text:
                            pdf_link = elem
                            if href and 'javascript:' not in href:
                                pdf_url = href
                            break
                    
                    if pdf_link:
                        break
                except:
                    continue
            
            # 2. iframe 내부 확인
            if not pdf_link:
                try:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        driver.switch_to.frame(iframe)
                        try:
                            pdf_link = driver.find_element(By.CSS_SELECTOR, "a[href*='.pdf']")
                            pdf_url = pdf_link.get_attribute('href')
                            driver.switch_to.default_content()
                            break
                        except:
                            driver.switch_to.default_content()
                            continue
                except:
                    driver.switch_to.default_content()
            
            # 3. onclick 함수 실행이 필요한 경우
            if pdf_link and not pdf_url:
                onclick = pdf_link.get_attribute('onclick')
                if onclick:
                    # JavaScript 실행
                    try:
                        driver.execute_script(onclick)
                        time.sleep(3)
                        
                        # 새 창 확인
                        if len(driver.window_handles) > 1:
                            original_window = driver.current_window_handle
                            driver.switch_to.window(driver.window_handles[-1])
                            
                            if '.pdf' in driver.current_url.lower():
                                pdf_url = driver.current_url
                                driver.close()
                                driver.switch_to.window(original_window)
                    except:
                        pass
            
            # PDF URL이 있으면 다운로드
            if pdf_url:
                print(f"  PDF URL 발견: {pdf_url}")
                pdf_file = self._download_pdf_direct(pdf_url, title)
                if pdf_file:
                    return pdf_file
            
            # 4. 페이지에 embed나 object로 PDF가 포함된 경우
            if not pdf_url:
                try:
                    # embed 태그 확인
                    embed = driver.find_element(By.CSS_SELECTOR, "embed[type*='pdf']")
                    pdf_url = embed.get_attribute('src')
                except:
                    try:
                        # object 태그 확인
                        obj = driver.find_element(By.CSS_SELECTOR, "object[type*='pdf']")
                        pdf_url = obj.get_attribute('data')
                    except:
                        pass
                
                if pdf_url:
                    print(f"  임베디드 PDF URL 발견: {pdf_url}")
                    pdf_file = self._download_pdf_direct(pdf_url, title)
                    if pdf_file:
                        return pdf_file
            
            # PDF를 찾지 못한 경우
            print("  PDF 링크를 찾을 수 없습니다.")
            
            # 디버깅: 페이지 내용 확인
            try:
                # 파일 관련 영역 찾기
                file_areas = driver.find_elements(By.CSS_SELECTOR, "[class*='file'], [class*='download'], [class*='attach']")
                if file_areas:
                    print(f"  파일 관련 영역 {len(file_areas)}개 발견")
                    for area in file_areas[:3]:
                        print(f"    - {area.get_attribute('class')}: {area.text[:50]}")
            except:
                pass
            
            return None
            
        except Exception as e:
            print(f"  PDF 다운로드 실패: {e}")
            return None
    
    def _download_pdf_direct(self, pdf_url, title):
        """
        URL로 직접 PDF 다운로드
        """
        try:
            # 상대 경로 처리
            if not pdf_url.startswith('http'):
                pdf_url = urljoin('https://www.paxnet.co.kr', pdf_url)
            
            # 파일명 생성
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)[:80]
            
            # URL에서 원본 파일명 추출 시도
            url_path = urlparse(pdf_url).path
            original_filename = os.path.basename(url_path)
            
            if original_filename and original_filename.endswith('.pdf'):
                # 원본 파일명이 너무 길면 축약
                if len(original_filename) > 100:
                    name, ext = os.path.splitext(original_filename)
                    original_filename = name[:80] + ext
                filename = original_filename
            else:
                filename = f"{safe_title}.pdf"
            
            filepath = os.path.join(self.download_path, filename)
            
            # 이미 존재하는 파일 처리
            if os.path.exists(filepath):
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(filepath):
                    filename = f"{base}_{counter}{ext}"
                    filepath = os.path.join(self.download_path, filename)
                    counter += 1
            
            # 다운로드
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.paxnet.co.kr/',
                'Accept': 'application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            # SSL 검증 비활성화 (필요시)
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            response = requests.get(pdf_url, headers=headers, stream=True, verify=False, timeout=30)
            
            if response.status_code == 200:
                # Content-Type 확인
                content_type = response.headers.get('Content-Type', '')
                
                # 파일 저장
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # 파일 크기 확인
                file_size = os.path.getsize(filepath)
                if file_size < 1000:  # 1KB 미만이면 문제가 있을 가능성
                    print(f"  경고: 파일 크기가 너무 작음 ({file_size} bytes)")
                    os.remove(filepath)
                    return None
                
                print(f"  다운로드 완료: {filename} ({file_size/1024:.1f} KB)")
                return filepath
            else:
                print(f"  다운로드 실패 (상태 코드: {response.status_code})")
                return None
                
        except Exception as e:
            print(f"  직접 다운로드 실패: {e}")
            return None

# 사용 예시
if __name__ == "__main__":
    # 다운로더 초기화
    downloader = PaxnetPDFDownloader()
    
    # 리스트 페이지에서 모든 리포트 다운로드
    list_url = "https://www.paxnet.co.kr/stock/report/report?menuCode=2222&currentPageNo=1"
    downloaded_files = downloader.download_from_list_page(list_url)
    
    # 다운로드된 파일 목록 출력
    print("\n다운로드된 파일:")
    for file in downloaded_files:
        print(f"- {file}")
