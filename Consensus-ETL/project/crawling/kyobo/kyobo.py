import os
import re
import time
import logging
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import PyPDF2
import shutil

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("kyobo_crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("KyoboCrawler")

class KyoboSecuritiesReportCrawler:
    def __init__(self, base_url="https://m.iprovest.com", save_dir="reports", download_dir=None):
        self.base_url = base_url
        self.report_list_url = f"{base_url}/weblogic/ResearchServlet/newReports"
        
        # 저장 디렉토리 구조 생성
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        # 다운로드 디렉토리 설정
        self.download_dir = download_dir if download_dir else os.path.join(os.getcwd(), "downloads")
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        
        # Selenium 설정 및 초기화
        self.setup_driver()
        
        # 수집된 데이터를 저장할 DataFrame
        self.reports_data = pd.DataFrame(
            columns=['제목', '종목명', '분석가', '날짜', '분류', 'PDF경로', '원문내용', '수집일자']
        )
    
    def setup_driver(self):
        """Selenium WebDriver 설정"""
        chrome_options = Options()
        
        # 다운로드 디렉토리 설정
        prefs = {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,  # PDF를 외부 뷰어로 열지 않고 다운로드
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 필요한 옵션 설정
        # chrome_options.add_argument('--headless')  # 실행 과정을 확인하기 위해 주석 처리
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--start-maximized')  # 브라우저 최대화
        
        # 웹드라이버 초기화
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
    
    def crawl_reports(self, max_pages=3):
        """리포트 크롤링 실행"""
        logger.info(f"크롤링 시작")
        
        try:
            # 메인 페이지 접속
            self.driver.get(self.report_list_url)
            logger.info("메인 페이지 접속 완료")
            
            # 페이지 로딩 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # 이미지에 표시된 다운로드 버튼 분석을 위한 디버깅
            self.debug_page_elements()
            
            # 페이지별 처리
            for page in range(1, max_pages + 1):
                logger.info(f"페이지 {page} 처리 중...")
                
                # 첫 페이지 이후에는 페이지 번호 클릭
                if page > 1:
                    if not self.navigate_to_page(page):
                        break
                
                # 현재 페이지의 모든 "다운로드" 버튼 찾기
                self.process_current_page_reports()
                
            # 결과 저장
            self.save_data_to_csv()
            
        except Exception as e:
            logger.error(f"크롤링 중 오류 발생: {e}")
            self.driver.save_screenshot("error.png")
        finally:
            # WebDriver 종료
            self.driver.quit()
        
        return self.reports_data
    
    def debug_page_elements(self):
        """페이지 요소 디버깅"""
        try:
            # 페이지 스크린샷
            self.driver.save_screenshot("full_page.png")
            logger.info("전체 페이지 스크린샷 저장: full_page.png")
            
            # 모든 버튼 로깅
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            logger.info(f"페이지에서 {len(buttons)}개 버튼 발견")
            
            for i, btn in enumerate(buttons[:10]):  # 처음 10개만
                try:
                    text = btn.text
                    class_name = btn.get_attribute("class")
                    logger.info(f"버튼 {i+1}: 텍스트={text}, 클래스={class_name}")
                except:
                    pass
            
            # 모든 링크 로깅
            links = self.driver.find_elements(By.TAG_NAME, "a")
            logger.info(f"페이지에서 {len(links)}개 링크 발견")
            
            for i, link in enumerate(links[:10]):  # 처음 10개만
                try:
                    text = link.text
                    href = link.get_attribute("href")
                    class_name = link.get_attribute("class")
                    logger.info(f"링크 {i+1}: 텍스트={text}, href={href}, 클래스={class_name}")
                except:
                    pass
            
            # 이미지에서 보이는 다운로드 버튼과 유사한 요소 찾기
            download_elements = self.driver.find_elements(
                By.XPATH, 
                "//button[contains(text(), '다운로드')] | //a[contains(text(), '다운로드')] | //a[contains(@class, 'download')] | //img[contains(@alt, '다운로드')]/parent::*"
            )
            
            logger.info(f"다운로드 관련 요소 {len(download_elements)}개 발견")
            
            for i, elem in enumerate(download_elements):
                try:
                    html = elem.get_attribute("outerHTML")
                    logger.info(f"다운로드 요소 {i+1} HTML: {html}")
                    
                    # 요소 스크린샷
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                    time.sleep(0.5)
                    self.driver.save_screenshot(f"download_element_{i+1}.png")
                except:
                    pass
        
        except Exception as e:
            logger.error(f"디버깅 중 오류: {e}")
    
    def navigate_to_page(self, page_num):
        """특정 페이지로 이동"""
        try:
            # 페이지 번호 요소 찾기
            page_elements = self.driver.find_elements(By.XPATH, f"//a[text()='{page_num}']")
            
            if not page_elements:
                logger.warning(f"페이지 {page_num} 링크를 찾을 수 없습니다.")
                return False
            
            # 페이지 번호 클릭
            page_elements[0].click()
            logger.info(f"페이지 {page_num}로 이동 완료")
            
            # 페이지 로딩 대기
            time.sleep(3)
            return True
            
        except Exception as e:
            logger.error(f"페이지 {page_num}로 이동 중 오류: {e}")
            return False
    
    def process_current_page_reports(self):
        """현재 페이지의 모든 리포트 처리"""
        try:
            # 이미지에서 보이는 구조에 맞게 리포트 항목 찾기
            items = self.driver.find_elements(By.CSS_SELECTOR, "ul > li")
            
            if not items:
                logger.warning("리포트 항목을 찾을 수 없습니다.")
                return
            
            logger.info(f"{len(items)}개 리포트 항목 발견")
            
            for idx, item in enumerate(items):
                try:
                    # 항목 텍스트 로깅
                    item_text = item.text
                    if not item_text or len(item_text) < 5:  # 빈 항목이나 너무 짧은 항목 무시
                        continue
                    
                    logger.info(f"리포트 항목 {idx+1} 텍스트: {item_text[:100]}")
                    
                    # 제목 추출
                    title_elem = None
                    try:
                        title_elem = item.find_element(By.CSS_SELECTOR, "h4, h3, strong")
                        title = title_elem.text.strip()
                    except NoSuchElementException:
                        # 제목 요소를 찾을 수 없는 경우 첫 번째 행을 제목으로 사용
                        lines = item_text.split('\n')
                        title = lines[0] if lines else f"리포트_{idx+1}"
                    
                    # 항목의 모든 버튼 요소 찾기
                    buttons = item.find_elements(By.TAG_NAME, "button")
                    download_button = None
                    
                    # 다운로드 버튼 찾기
                    for btn in buttons:
                        if '다운로드' in btn.text:
                            download_button = btn
                            break
                    
                    # 다운로드 버튼을 찾지 못한 경우 a 태그 확인
                    if not download_button:
                        links = item.find_elements(By.TAG_NAME, "a")
                        for link in links:
                            if '다운로드' in link.text or 'download' in link.get_attribute("class").lower():
                                download_button = link
                                break
                    
                    # 이미지 확인 (이미지에서 보이는 다운로드 버튼 형태)
                    if not download_button:
                        # 이미지를 통한 다운로드 버튼 찾기
                        try:
                            download_images = item.find_elements(
                                By.XPATH, 
                                ".//img[contains(@src, 'download') or contains(@alt, '다운로드')]"
                            )
                            if download_images:
                                # 이미지의 부모 요소 (a 태그)가 다운로드 버튼일 가능성
                                parent = self.driver.execute_script("return arguments[0].parentNode;", download_images[0])
                                if parent.tag_name.lower() == 'a':
                                    download_button = parent
                        except:
                            pass
                    
                    # 다운로드 버튼 찾았을 때 처리
                    if download_button:
                        logger.info(f"다운로드 버튼 발견: {title}")
                        
                        # 메타데이터 추출
                        date = None
                        stock_name = None
                        analyst = None
                        category = None
                        
                        # 날짜 추출
                        date_match = re.search(r'(\d{4}/\d{2}/\d{2})', item_text)
                        if date_match:
                            date = date_match.group(1)
                        
                        # 카테고리, 종목명, 분석가 추출
                        lines = item_text.split('\n')
                        for line in lines:
                            if '기업분석' in line or '산업분석' in line or '채권전략' in line:
                                parts = line.split()
                                if len(parts) >= 1:
                                    category = parts[0]
                                if len(parts) >= 3:
                                    stock_name = parts[-2]
                                    analyst = parts[-1]
                        
                        # 버튼 스크린샷
                        self.driver.save_screenshot(f"before_click_{idx}.png")
                        
                        # 버튼 위치로 스크롤
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_button)
                        time.sleep(1)
                        
                        # 버튼 클릭
                        try:
                            download_button.click()
                            logger.info(f"다운로드 버튼 클릭 성공: {title}")
                        except Exception as e:
                            # JavaScript로 클릭 시도
                            try:
                                self.driver.execute_script("arguments[0].click();", download_button)
                                logger.info(f"JavaScript로 다운로드 버튼 클릭 성공: {title}")
                            except Exception as js_e:
                                logger.error(f"다운로드 버튼 클릭 실패: {e}, JS 오류: {js_e}")
                                continue
                        
                        # 다운로드 완료 대기
                        time.sleep(3)
                        
                        # 다운로드된 파일 찾기 및 처리
                        self.process_downloaded_file(title, date, stock_name, analyst, category)
                    else:
                        logger.warning(f"다운로드 버튼을 찾을 수 없음: {title}")
                
                except Exception as e:
                    logger.error(f"리포트 항목 {idx+1} 처리 중 오류: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"현재 페이지 처리 중 오류: {e}")
    
    def process_downloaded_file(self, title, date, stock_name, analyst, category):
        """다운로드된 파일 찾기 및 처리"""
        try:
            # 다운로드 디렉토리에서 가장 최근 파일 찾기
            max_wait = 10
            downloaded_file = None
            
            for _ in range(max_wait):
                files = os.listdir(self.download_dir)
                pdf_files = [f for f in files if f.endswith('.pdf') and not f.startswith('._')]
                
                if pdf_files:
                    # 가장 최근에 다운로드된 파일 선택
                    latest_file = max(pdf_files, key=lambda f: os.path.getmtime(os.path.join(self.download_dir, f)))
                    downloaded_file = os.path.join(self.download_dir, latest_file)
                    break
                
                time.sleep(1)
            
            if not downloaded_file:
                logger.warning(f"다운로드된 PDF 파일을 찾을 수 없습니다: {title}")
                return False
            
            logger.info(f"다운로드된 파일: {downloaded_file}")
            
            # 날짜 정보 파싱
            if not date:
                logger.warning(f"날짜 정보가 없습니다. 현재 날짜를 사용합니다.")
                date_obj = datetime.now()
            else:
                try:
                    # 날짜 형식에 맞게 파싱
                    if '/' in date:
                        date_obj = datetime.strptime(date, '%Y/%m/%d')
                    elif '-' in date:
                        date_obj = datetime.strptime(date, '%Y-%m-%d')
                    else:
                        date_obj = datetime.now()
                except:
                    date_obj = datetime.now()
            
            # 파일 저장 경로 생성
            year_dir = os.path.join(self.save_dir, str(date_obj.year))
            if not os.path.exists(year_dir):
                os.makedirs(year_dir)
                
            month_dir = os.path.join(year_dir, f"{date_obj.month:02d}")
            if not os.path.exists(month_dir):
                os.makedirs(month_dir)
                
            day_dir = os.path.join(month_dir, f"{date_obj.day:02d}")
            if not os.path.exists(day_dir):
                os.makedirs(day_dir)
            
            # 파일명 생성
            stock_name_clean = (stock_name or "").replace('/', '_').strip()
            title_clean = title.replace('/', '_').strip()
            date_for_filename = date_obj.strftime('%Y%m%d')
            
            if stock_name_clean:
                filename = f"{stock_name_clean}_{title_clean}_{date_for_filename}.pdf"
            else:
                filename = f"{title_clean}_{date_for_filename}.pdf"
            
            # 특수문자 제거 및 파일명 정리
            filename = re.sub(r'[\\/:*?"<>|]', '', filename)
            filename = filename[:150] + '.pdf' if len(filename) > 150 else filename
            
            target_path = os.path.join(day_dir, filename)
            
            # 파일 복사
            shutil.copy2(downloaded_file, target_path)
            logger.info(f"파일 저장 완료: {target_path}")
            
            # PDF 내용 추출 시도
            pdf_content = None
            try:
                pdf_content = self.extract_pdf_content(downloaded_file)
            except Exception as e:
                logger.error(f"PDF 내용 추출 실패: {e}")
            
            # 데이터프레임에 추가
            report_data = {
                '제목': title,
                '종목명': stock_name,
                '분석가': analyst,
                '날짜': date,
                '분류': category,
                'PDF경로': target_path,
                '원문내용': pdf_content,
                '수집일자': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.reports_data = pd.concat([
                self.reports_data, 
                pd.DataFrame([report_data])
            ], ignore_index=True)
            
            logger.info(f"리포트 데이터 추가 완료: {title}")
            
            return True
        
        except Exception as e:
            logger.error(f"다운로드 파일 처리 실패: {e}")
            return False
    
    def extract_pdf_content(self, pdf_path):
        """PDF 파일에서 텍스트 내용 추출"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                max_pages = min(len(pdf_reader.pages), 5)  # 처음 5페이지만 추출
                for page_num in range(max_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패: {e}")
            return None
    
    def save_data_to_csv(self):
        """수집된 데이터를 CSV 파일로 저장"""
        if not self.reports_data.empty:
            csv_path = os.path.join(self.save_dir, f"kyobo_reports_{datetime.now().strftime('%Y%m%d')}.csv")
            self.reports_data.to_csv(csv_path, index=False, encoding='utf-8-sig')
            logger.info(f"데이터 CSV 저장 완료: {csv_path}")
            return csv_path
        else:
            logger.warning("수집된 데이터가 없습니다.")
        return None

# 사용 예시
if __name__ == "__main__":
    # 저장 디렉토리 설정
    save_dir = "kyobo_reports"
    download_dir = "downloads"
    
    # 크롤러 객체 생성
    crawler = KyoboSecuritiesReportCrawler(save_dir=save_dir, download_dir=download_dir)
    
    # 크롤링 실행
    crawler.crawl_reports(max_pages=1)  # 첫 페이지만 테스트
    
    print(f"크롤링 완료! 저장 경로: {os.path.abspath(save_dir)}")
