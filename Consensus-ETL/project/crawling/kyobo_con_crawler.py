
import os
import re
import sys
import time
import logging
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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
    def __init__(self, base_url="https://m.iprovest.com", save_dir=None, download_dir=None):
        self.base_url = base_url
        self.report_list_url = f"{base_url}/weblogic/ResearchServlet/newReports"
        
        # 저장 디렉토리 구조 생성 (project/consensus/kyobo)
        if save_dir is None:
            # 현재 파일 위치: Consensus-ETL/project/crawling/kyobo_con_crawler.py
            CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # crawling 폴더
            PROJECT_DIR = os.path.dirname(CURRENT_DIR)  # project 폴더
            self.save_dir = os.path.join(PROJECT_DIR, "consensus", "kyobo")
        else:
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

        # 종료 코드 판정용 집계
        self.saved_count = 0
        self.failed_count = 0

    def setup_driver(self):
        """Selenium WebDriver 설정"""
        chrome_options = Options()
        
        # 다운로드 디렉토리 설정
        prefs = {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True  # PDF를 외부 뷰어로 열지 않고 다운로드
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 필요한 옵션 설정
        chrome_options.add_argument('--headless')  # 실행 과정을 확인하기 위해 주석 처리
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # 웹드라이버 초기화
        # 드라이버를 PATH에서 찾으면 낡은 chromedriver를 집어 Chrome 버전과 충돌한다.
        # bnk/yuanta와 동일하게 설치된 Chrome에 맞는 드라이버를 받아서 쓴다.
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=chrome_options
        )
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
            
            # 디버깅 파일 생성 제거
            # 페이지 소스 저장 제거
            # 스크린샷 저장 제거
            logger.info("메인 페이지 접속 및 로딩 완료")
            
            # 현재 페이지의 모든 요소 찾기를 시도
            self.find_all_elements_debug()

            for page in range(1, max_pages + 1):
                if page > 1 and not self.goto_page(page):
                    break

                logger.info(f"=== 페이지 {page} 처리 중 ===")

                # 모든 다운로드 버튼 직접 찾기
                download_buttons = self.find_all_download_buttons()

                if not download_buttons:
                    logger.warning(f"페이지 {page}에서 다운로드 버튼을 찾을 수 없습니다.")
                    # 1페이지에도 버튼이 없으면 사이트 구조가 바뀐 것으로 보고 실패 처리
                    if page == 1:
                        self.failed_count += 1
                    break

                logger.info(f"총 {len(download_buttons)}개의 다운로드 버튼을 찾았습니다.")

                # 각 다운로드 버튼에 대해 작업 수행
                for idx, button in enumerate(download_buttons):
                    try:
                        # 버튼의 위치로 스크롤
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(1)

                        # 스크린샷 제거

                        # 버튼 주변 요소에서 필요한 정보 추출
                        report_info = self.extract_report_info_from_button(button, idx)

                        # 이미 받은 리포트는 다시 받지 않는다.
                        # DAG가 retries=3으로 돌기 때문에 없으면 같은 파일을 세 번 내려받는다.
                        if report_info and os.path.exists(self.target_path(**report_info)):
                            logger.info(f"이미 존재하는 리포트 건너뛰기: {report_info['title']}")
                            continue

                        # 새로 생긴 파일만 골라내기 위해 클릭 직전 상태를 기록
                        before_files = set(os.listdir(self.download_dir))

                        # 버튼 클릭
                        logger.info(f"다운로드 버튼 {idx+1} 클릭 시도")
                        try:
                            button.click()
                        except:
                            # JavaScript로 클릭
                            self.driver.execute_script("arguments[0].click();", button)

                        # 다운로드된 파일 처리
                        if report_info:
                            if self.process_downloaded_file(before_files, **report_info):
                                self.saved_count += 1
                            else:
                                self.failed_count += 1

                    except Exception as e:
                        logger.error(f"버튼 {idx+1} 처리 중 오류: {e}")
                        self.failed_count += 1
                        continue

            # 결과 저장
            # self.save_data_to_csv()
            
        except Exception as e:
            logger.error(f"크롤링 중 오류 발생: {e}")
            self.failed_count += 1
            # 오류 스크린샷 제거
        finally:
            # WebDriver 종료
            self.driver.quit()

        return self.reports_data
    
    def goto_page(self, page_num):
        """목록의 지정 페이지로 이동.

        페이저(div.board_paging)의 각 링크는 _href 속성에 pageNum을 담고 있다.
        다운로드 버튼을 클릭하면 목록 페이지를 벗어나므로, 링크를 클릭하는 대신
        같은 형식의 URL로 직접 이동한다.
        """
        try:
            self.driver.get(
                f"{self.report_list_url}"
                f"?scr_id=null&srch_db=0&QU=&DT1=&DT2=&provestz=&menuCode=1&pageNum={page_num}"
            )
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.board_paging"))
            )
            time.sleep(2)

            # 요청한 페이지가 실제로 열렸는지 확인 (마지막 페이지를 넘어가면 유지되지 않는다)
            current = self.driver.find_elements(By.CSS_SELECTOR, "div.board_paging a.pageOn span")
            if current and current[0].text.strip() != str(page_num):
                logger.info(f"페이지 {page_num} 없음 - 마지막 페이지로 판단")
                return False

            logger.info(f"페이지 {page_num}로 이동 성공")
            return True
        except Exception as e:
            logger.info(f"페이지 {page_num} 이동 실패 - 수집 종료 ({e})")
            return False

    def find_all_elements_debug(self):
        """디버깅을 위해 페이지의 모든 요소 유형을 찾고 기록"""
        try:
            # 다양한 태그의 요소 수 확인
            tags_to_check = ["article", "li", "button", "a", "h4", "div", "span", "img"]
            
            for tag in tags_to_check:
                elements = self.driver.find_elements(By.TAG_NAME, tag)
                logger.info(f"{tag} 태그 요소 수: {len(elements)}")
                
                # 처음 발견된 몇 개 요소의 클래스와 텍스트 로깅
                for i, elem in enumerate(elements[:5]):
                    try:
                        class_name = elem.get_attribute("class") or "없음"
                        text = elem.text or "없음"
                        logger.info(f"{tag} #{i+1} - 클래스: {class_name}, 텍스트: {text[:30]}")
                    except:
                        pass
                    
                    if i >= 4:  # 처음 5개만 로깅
                        break
            
            # 특정 클래스 이름으로 요소 찾기
            class_names = ["download", "btn", "ico", "report", "list"]
            for class_name in class_names:
                elements = self.driver.find_elements(By.CSS_SELECTOR, f"[class*='{class_name}']")
                logger.info(f"클래스 '{class_name}' 포함 요소 수: {len(elements)}")
            
        except Exception as e:
            logger.error(f"요소 디버깅 중 오류: {e}")
    
    def find_all_download_buttons(self):
        """가능한 모든 방법으로 다운로드 버튼 찾기"""
        all_buttons = []
        
        try:
            # 방법 1: 클래스 이름으로 찾기
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "a.ico_download, a.btn_download")
            if buttons:
                logger.info(f"클래스 이름으로 {len(buttons)}개 버튼 발견")
                all_buttons.extend(buttons)
            
            # 방법 2: 다운로드 텍스트로 찾기
            text_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), '다운로드')] | //a[contains(text(), '다운로드')]")
            if text_buttons:
                logger.info(f"텍스트로 {len(text_buttons)}개 버튼 발견")
                all_buttons.extend([b for b in text_buttons if b not in all_buttons])
            
            # 방법 3: 일반적인 버튼 태그 찾기
            all_a_tags = self.driver.find_elements(By.TAG_NAME, "a")
            download_links = []
            
            for a in all_a_tags:
                try:
                    html = a.get_attribute("outerHTML")
                    if "download" in html.lower() or "ico_download" in html:
                        download_links.append(a)
                except:
                    continue
            
            if download_links:
                logger.info(f"HTML로 {len(download_links)}개 버튼 발견")
                all_buttons.extend([b for b in download_links if b not in all_buttons])
            
            # 방법 4: 이미지 기준으로 찾기
            try:
                img_buttons = self.driver.find_elements(By.XPATH, "//img[contains(@src, 'download') or contains(@alt, 'download')]/parent::a")
                if img_buttons:
                    logger.info(f"이미지로 {len(img_buttons)}개 버튼 발견")
                    all_buttons.extend([b for b in img_buttons if b not in all_buttons])
            except:
                pass
            
            # 중복 제거
            unique_buttons = []
            for button in all_buttons:
                if button not in unique_buttons:
                    unique_buttons.append(button)

            # 페이지 하단의 '보호금융상품등록부'도 RSDownloadServlet을 사용해
            # 위의 광범위한 탐색에 포함된다. 실제 리서치 리포트 경로만 남긴다.
            report_buttons = []
            for button in unique_buttons:
                # 초기 HTML은 표준 href를 사용하지만 페이지의 스크립트가 로딩 후
                # href를 "javascript:"로 바꾸고 원래 경로를 _href로 옮긴다.
                # 두 상태 모두에서 동작하도록 어느 한 속성에 경로가 있으면 남긴다.
                download_paths = (
                    button.get_attribute("href") or "",
                    button.get_attribute("_href") or "",
                )
                if any("/research/report/" in path for path in download_paths):
                    report_buttons.append(button)

            excluded_count = len(unique_buttons) - len(report_buttons)
            if excluded_count:
                logger.info(f"리포트가 아닌 다운로드 링크 {excluded_count}개 제외")
            
            # 각 버튼 로깅
            for i, btn in enumerate(report_buttons):
                try:
                    html = btn.get_attribute("outerHTML")
                    logger.info(f"버튼 {i+1} HTML: {html}")
                except:
                    pass
            
            return report_buttons
            
        except Exception as e:
            logger.error(f"다운로드 버튼 찾기 오류: {e}")
            return []
    
    def extract_report_info_from_button(self, button, idx):
        """다운로드 버튼으로부터 보고서 정보 추출"""
        try:
            # 버튼의 부모 요소 (리포트 컨테이너)
            parent = None
            try:
                # 버튼에서 가장 가까운 li 또는 article 찾기
                parent = button
                for _ in range(5):  # 최대 5단계 상위로 올라가기
                    parent = self.driver.execute_script("return arguments[0].parentNode;", parent)
                    tag_name = self.driver.execute_script("return arguments[0].tagName.toLowerCase();", parent)
                    if tag_name in ["li", "article"]:
                        break
            except:
                logger.warning(f"버튼 {idx+1}의 부모 요소를 찾을 수 없습니다.")
            
            # 제목, 날짜, 종목명, 분석가 찾기
            title = None
            date = None
            stock_name = None
            analyst = None
            category = None
            
            # 부모 요소가 있다면 정보 추출 시도
            if parent:
                # 부모 요소 스크린샷 제거
                
                # 제목 추출
                try:
                    title_elem = parent.find_element(By.CSS_SELECTOR, "h4, h3, .title, strong")
                    title = title_elem.text.strip()
                except:
                    # 직접 텍스트에서 추출 시도
                    parent_text = parent.text
                    lines = parent_text.split('\n')
                    if lines:
                        title = lines[0].strip()
                
                # 날짜 추출
                parent_text = parent.text
                date_match = re.search(r'(\d{4}/\d{2}/\d{2})', parent_text)
                if date_match:
                    date = date_match.group(1)
                
                # 종목명, 분석가 추출
                lines = parent_text.split('\n')
                for line in lines:
                    if '기업분석' in line or '산업분석' in line or '채권전략' in line:
                        parts = line.split()
                        if parts and parts[0] in ['기업분석', '산업분석', '채권전략', '투자전략']:
                            category = parts[0]
                        if len(parts) >= 3:
                            stock_name = parts[-2]
                            analyst = parts[-1]
            
            # 제목이 없으면 대체 이름을 쓴다.
            # 시:분:초를 넣으면 실행마다 파일명이 달라져 중복 검사가 무력화되므로 넣지 않는다.
            if not title:
                title = f"리포트_{idx+1}"
            
            logger.info(f"추출된 정보: 제목={title}, 날짜={date}, 종목명={stock_name}, 분석가={analyst}, 분류={category}")
            
            return {
                'title': title,
                'date': date,
                'stock_name': stock_name,
                'analyst': analyst,
                'category': category
            }
            
        except Exception as e:
            logger.error(f"보고서 정보 추출 오류: {e}")
            # 최소한의 정보라도 반환
            return {
                'title': f"리포트_{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'date': None,
                'stock_name': None,
                'analyst': None,
                'category': None
            }
    
    def target_path(self, title, date, stock_name, **_):
        """리포트 정보로 최종 저장 경로를 만든다 (다운로드 전 중복 확인에도 사용)."""
        # 날짜 정보 파싱
        if not date:
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

        # 날짜별 폴더 구조 제거 - 직접 save_dir에 저장
        # 파일명 생성
        stock_name_clean = stock_name.replace('/', '_').strip() if stock_name else ""
        title_clean = title.replace('/', '_').strip()
        date_for_filename = date_obj.strftime('%Y%m%d')

        if stock_name_clean:
            filename = f"{stock_name_clean}_{title_clean}_{date_for_filename}.pdf"
        else:
            filename = f"{title_clean}_{date_for_filename}.pdf"

        # 특수문자 제거 및 파일명 정리
        filename = re.sub(r'[\\/:*?"<>|]', '', filename)
        filename = filename[:150] + '.pdf' if len(filename) > 150 else filename

        return os.path.join(self.save_dir, filename)

    def wait_for_download(self, before_files, timeout=30):
        """클릭 이후 새로 생긴 PDF를 기다린다.

        이전에는 다운로드 폴더에서 mtime이 가장 최신인 PDF를 골랐는데,
        다운로드가 제때 끝나지 않으면 직전 리포트를 다른 이름으로 다시
        저장해 버렸다. 클릭 전후 목록 차이로 실제 새 파일만 집는다.
        """
        # 클릭 전부터 받는 중이던 파일(앞 리포트가 타임아웃으로 남긴 것)은
        # 완성되는 순간 새 이름으로 나타난다. 우리 것이 아니므로 미리 제외한다.
        suffix = '.crdownload'
        pending = {f[:-len(suffix)] for f in before_files if f.endswith(suffix)}

        deadline = time.time() + timeout
        while time.time() < deadline:
            new_files = set(os.listdir(self.download_dir)) - before_files - pending
            # 크롬이 받는 중이면 .crdownload가 남아 있다
            if not any(f.endswith(suffix) for f in new_files):
                new_pdfs = [f for f in new_files
                            if f.endswith('.pdf') and not f.startswith('._')]
                if len(new_pdfs) == 1:
                    return os.path.join(self.download_dir, new_pdfs[0])
                if len(new_pdfs) > 1:
                    # 어느 것이 이 리포트인지 알 수 없다. 잘못된 PDF를 저장하느니 실패로 둔다.
                    logger.warning(f"새 PDF가 여러 개라 특정할 수 없습니다: {sorted(new_pdfs)}")
                    return None
            time.sleep(0.5)
        return None

    def process_downloaded_file(self, before_files, title, date, stock_name, analyst, category):
        """다운로드된 파일 처리 및 정리"""
        try:
            downloaded_file = self.wait_for_download(before_files)

            if not downloaded_file:
                logger.warning(f"다운로드된 PDF 파일이 없습니다: {title}")
                return False

            logger.info(f"다운로드된 파일: {downloaded_file}")

            target_path = self.target_path(title, date, stock_name)

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
    
    # def save_data_to_csv(self):
    #     """수집된 데이터를 CSV 파일로 저장"""
    #     if not self.reports_data.empty:
    #         csv_path = os.path.join(self.save_dir, f"kyobo_reports_{datetime.now().strftime('%Y%m%d')}.csv")
    #         self.reports_data.to_csv(csv_path, index=False, encoding='utf-8-sig')
    #         logger.info(f"데이터 CSV 저장 완료: {csv_path}")
    #         return csv_path
    #     return None

# 사용 예시
if __name__ == "__main__":
    # 크롤러 객체 생성 (저장 경로를 기본값으로 사용)
    crawler = KyoboSecuritiesReportCrawler()
    
    # 크롤링 실행
    crawler.crawl_reports(max_pages=3)  # 일 1회 실행 기준, 재실행 여유분 포함

    print(f"크롤링 완료! 저장 경로: {os.path.abspath(crawler.save_dir)}")
    print(f"신규 저장 {crawler.saved_count}건, 실패 {crawler.failed_count}건")

    # 실패가 있으면 Airflow가 재시도/알림할 수 있도록 실패로 끝낸다
    sys.exit(1 if crawler.failed_count else 0)
