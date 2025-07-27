import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from datetime import datetime, timedelta
import os
import logging
import argparse

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 다운로드 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
DOWNLOAD_DIR = os.path.join(PARENT_DIR, "consensus", "fnguide")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class FnGuideCrawler:
    def __init__(self, download_dir=None, headless=True):
        """
        FnGuide 크롤러 초기화

        Args:
            download_dir (str): 데이터를 저장할 디렉토리 (기본값: project/consensus/fnguide)
            headless (bool): 브라우저를 백그라운드에서 실행할지 여부
        """
        if download_dir is None:
            download_dir = DOWNLOAD_DIR

        self.download_dir = os.path.abspath(download_dir)
        os.makedirs(self.download_dir, exist_ok=True)
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def get_yesterday_date(self):
        """어제 날짜를 YYYY/MM/DD 형식으로 반환"""
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime("%Y/%m/%d")
    
    def is_weekend(self, date_str):
        """주말 여부 확인"""
        try:
            date_obj = datetime.strptime(date_str, "%Y/%m/%d")
            return date_obj.weekday() >= 5  # 5=토요일, 6=일요일
        except:
            return False
    
    def get_date_range(self, start_date, end_date):
        """날짜 범위 생성 및 검증"""
        try:
            start = datetime.strptime(start_date, "%Y/%m/%d")
            end = datetime.strptime(end_date, "%Y/%m/%d")
            
            if start > end:
                raise ValueError("시작일이 종료일보다 늦습니다.")
            
            dates = []
            current = start
            while current <= end:
                date_str = current.strftime("%Y/%m/%d")
                # 주말 제외
                if not self.is_weekend(date_str):
                    dates.append(date_str)
                current += timedelta(days=1)
            
            return dates
        except Exception as e:
            logger.error(f"날짜 범위 생성 오류: {e}")
            return []

    def setup_driver(self):
        """Chrome 드라이버 설정"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # 다운로드 설정 (다른 크롤러와 일치)
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)

    def close_driver(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()

    def crawl_reports(self, start_date="2025/07/13", end_date="2025/07/20"):
        """
        FnGuide 리포트 요약 데이터를 크롤링합니다.

        Args:
            start_date (str): 시작일 (YYYY/MM/DD)
            end_date (str): 종료일 (YYYY/MM/DD)

        Returns:
            pandas.DataFrame: 크롤링된 리포트 데이터
        """
        try:
            if not self.driver:
                self.setup_driver()

            logger.info(f"크롤링 시작: {start_date} ~ {end_date}")

            # FnGuide 리포트 요약 페이지 접속
            url = "https://comp.fnguide.com/SVO2/ASP/SVD_Report_Summary.asp"
            if self.driver:
                self.driver.get(url)
            else:
                logger.error("드라이버가 초기화되지 않았습니다.")
                return pd.DataFrame()

            logger.info("페이지 로딩 대기...")
            time.sleep(3)

            # 페이지 제목 확인
            if self.driver:
                logger.info(f"페이지 제목: {self.driver.title}")

            # 날짜 입력 필드 찾기 및 설정
            try:
                # JavaScript로 날짜 설정 시도
                start_date_js = start_date.replace("/", "")
                end_date_js = end_date.replace("/", "")

                # JavaScript 실행으로 날짜 설정
                if self.driver:
                    self.driver.execute_script(
                        f"""
                    if(document.getElementById('inFromDate')) {{
                        document.getElementById('inFromDate').value = '{start_date}';
                    }}
                    if(document.getElementById('inToDate')) {{
                        document.getElementById('inToDate').value = '{end_date}';
                    }}
                    if(document.getElementById('startdt')) {{
                        document.getElementById('startdt').value = '{start_date_js}';
                    }}
                    if(document.getElementById('enddt')) {{
                        document.getElementById('enddt').value = '{end_date_js}';
                    }}
                """
                    )

                logger.info("JavaScript로 날짜 설정 완료")

                # 조회 버튼 클릭
                search_selectors = ["#btnSearch", "a[href*='javascript:void(0)']", ".us_btn_ty1", "input[value='조회']"]

                search_clicked = False
                for selector in search_selectors:
                    try:
                        if not self.driver:
                            break
                        search_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if search_button.is_displayed():
                            search_button.click()
                            logger.info(f"'{selector}' 버튼 클릭 완료")
                            search_clicked = True
                            break
                    except:
                        continue

                if not search_clicked:
                    # JavaScript로 직접 검색 함수 호출
                    logger.info("JavaScript로 검색 함수 직접 호출")
                    if self.driver:
                        self.driver.execute_script(
                            """
                        if(typeof btnSearch_Click === 'function') {
                            btnSearch_Click();
                        } else if(typeof searchReport === 'function') {
                            searchReport();
                        } else {
                            // 폼 제출
                            var form = document.getElementById('param');
                            if(form) form.submit();
                        }
                    """
                        )

                logger.info("데이터 로딩 대기...")
                time.sleep(5)

                # GridBody에 데이터가 로드될 때까지 대기
                data_loaded = False
                for i in range(10):  # 최대 10초 대기
                    if not self.driver:
                        break
                    tbody = self.driver.find_element(By.ID, "GridBody")
                    if tbody.find_elements(By.TAG_NAME, "tr"):
                        logger.info(f"{i+1}초 후 데이터 로드 확인")
                        data_loaded = True
                        break
                    time.sleep(1)
                else:
                    logger.warning("데이터 로딩 시간 초과")
                
                # 데이터가 없으면 조기 종료
                if not data_loaded:
                    logger.info("해당 날짜에 데이터가 없습니다. 크롤링을 종료합니다.")
                    return pd.DataFrame()

            except (TimeoutException, NoSuchElementException) as e:
                logger.error(f"날짜 설정 실패: {e}")
                logger.info("기본 페이지 데이터 추출 시도...")

            # 테이블 데이터 추출
            data_list = []

            # FnGuide 테이블 선택자 (실제 구조에 맞춤)
            table_selectors = [
                "table.us_table_ty1",
                "table[class*='table']",
                "table[class*='grid']",
                "#gridTable",
                ".us_table_ty1",
                "table tbody",
                "table",
            ]

            table_found = False
            for selector in table_selectors:
                try:
                    if not self.driver:
                        break
                    tables = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if tables:
                        logger.info(f"'{selector}' 선택자로 {len(tables)}개 테이블 발견")

                        # 가장 많은 행을 가진 테이블 선택
                        target_table = None
                        max_rows = 0

                        for table in tables:
                            rows = table.find_elements(By.TAG_NAME, "tr")
                            if len(rows) > max_rows:
                                max_rows = len(rows)
                                target_table = table

                        if target_table and max_rows > 1:
                            logger.info(f"선택된 테이블: {max_rows}개 행")

                            rows = target_table.find_elements(By.TAG_NAME, "tr")

                            # 헤더 확인
                            if rows:
                                header_cells = rows[0].find_elements(By.TAG_NAME, "th")
                                if not header_cells:
                                    header_cells = rows[0].find_elements(By.TAG_NAME, "td")
                                headers = [cell.text.strip() for cell in header_cells]
                                logger.info(f"헤더: {headers}")

                            # 데이터 행 추출 (헤더 제외)
                            data_rows = rows[1:] if len(rows) > 1 else rows
                            for i, row in enumerate(data_rows, 1):
                                try:
                                    cells = row.find_elements(By.TAG_NAME, "td")
                                    if len(cells) >= 4:  # FnGuide 테이블은 최소 4개 컬럼
                                        row_data = [cell.text.strip() for cell in cells]

                                        # 의미있는 데이터가 있는지 확인 (날짜, 종목명, 투자의견 중 최소 2개)
                                        meaningful_data = [
                                            data
                                            for data in row_data
                                            if data and len(data.strip()) > 0 and data.strip() != "-"
                                        ]
                                        if len(meaningful_data) >= 2:
                                            # 헤더 행이나 빈 행 필터링
                                            if not any(
                                                keyword in str(row_data[0]).lower()
                                                for keyword in ["일자", "날짜", "date", "no", "번호"]
                                            ):
                                                data_list.append(row_data)
                                                if i <= 3:  # 처음 3행만 출력
                                                    logger.info(f"행 {i}: {row_data}")

                                except Exception as e:
                                    logger.debug(f"행 {i} 처리 중 오류: {e}")
                                    continue

                            table_found = True
                            break

                except Exception as e:
                    logger.debug(f"'{selector}' 테이블 검색 중 오류: {e}")
                    continue

            if not table_found:
                logger.error("테이블을 찾을 수 없습니다.")
                # 페이지 소스 일부 출력
                if self.driver:
                    logger.debug("페이지 소스 일부:")
                    logger.debug(self.driver.page_source[:1000])
                return pd.DataFrame()

            if not data_list:
                logger.info("해당 날짜에 데이터가 없습니다. 크롤링을 종료합니다.")
                return pd.DataFrame()

            # DataFrame 생성 - 실제 FnGuide 테이블 구조에 맞춤
            columns = ["일자", "종목명_리포트요약", "투자의견", "목표주가", "전일종가", "제공처_작성자"]

            # 실제 컬럼 수에 맞춰 조정
            max_cols = max(len(row) for row in data_list) if data_list else 0
            if max_cols > len(columns):
                columns.extend([f"추가컬럼{i}" for i in range(len(columns), max_cols)])

            # 모든 행의 길이를 최대 컬럼 수에 맞춰 조정
            for i, row in enumerate(data_list):
                if len(row) < max_cols:
                    data_list[i].extend([""] * (max_cols - len(row)))
                elif len(row) > max_cols:
                    data_list[i] = row[:max_cols]

            df = pd.DataFrame(data_list, columns=columns[:max_cols])
            logger.info(f"추출된 데이터 행 수: {len(df)}")

            return df

        except Exception as e:
            logger.error(f"크롤링 중 오류 발생: {e}")
            import traceback

            traceback.print_exc()
            return pd.DataFrame()

    def clean_data(self, df):
        """데이터 정리"""
        if df.empty:
            return df

        # 빈 행 제거
        df = df.dropna(how="all")

        # 목표주가와 전일종가에서 숫자 추출
        if "목표주가" in df.columns:
            df["목표주가"] = df["목표주가"].str.replace(",", "").str.extract(r"(\d+)")[0]
        if "전일종가" in df.columns:
            df["전일종가"] = df["전일종가"].str.replace(",", "").str.extract(r"(\d+)")[0]

        # 날짜 형식 정리
        if "일자" in df.columns:
            df["일자"] = pd.to_datetime(df["일자"], errors="coerce")

        return df

    def save_to_csv(self, df, filename=None, date_str=None):
        """CSV 파일로 저장"""
        if df.empty:
            logger.warning("저장할 데이터가 없습니다.")
            return None

        if filename is None:
            if date_str:
                # 날짜별 파일명 (백필용)
                date_formatted = date_str.replace('/', '')
                filename = f"fnguide_reports_{date_formatted}.csv"
            else:
                # 일반 파일명
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"fnguide_reports_{timestamp}.csv"

        filepath = os.path.join(self.download_dir, filename)
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        logger.info(f"데이터가 '{filepath}' 파일로 저장되었습니다.")
        return filepath

    def run(self, start_date=None, end_date=None, filename=None):
        """전체 크롤링 프로세스 실행"""
        try:
            # 날짜가 지정되지 않으면 어제 날짜 사용
            if start_date is None or end_date is None:
                yesterday = self.get_yesterday_date()
                start_date = end_date = yesterday
                logger.info(f"어제 날짜로 설정: {yesterday}")
            
            logger.info("=" * 50)
            logger.info("FnGuide 크롤링 시작")
            logger.info("=" * 50)

            # 드라이버 설정
            self.setup_driver()

            # 데이터 크롤링
            df = self.crawl_reports(start_date, end_date)

            if df.empty:
                logger.info("해당 날짜에 데이터가 없어 크롤링을 종료합니다.")
                return pd.DataFrame()

            # 데이터 정리
            df_cleaned = self.clean_data(df)

            # CSV 저장
            self.save_to_csv(df_cleaned, filename, start_date if start_date == end_date else None)

            logger.info("=" * 50)
            logger.info("크롤링 완료")
            logger.info("=" * 50)

            return df_cleaned

        finally:
            # 드라이버 종료
            self.close_driver()
    
    def backfill_data(self, start_date, end_date):
        """데이터 백필 실행"""
        logger.info("=" * 50)
        logger.info(f"데이터 백필 시작: {start_date} ~ {end_date}")
        logger.info("=" * 50)
        
        # 날짜 범위 생성 (주말 제외)
        dates = self.get_date_range(start_date, end_date)
        
        if not dates:
            logger.error("유효한 날짜 범위가 없습니다.")
            return []
        
        logger.info(f"총 {len(dates)}개 날짜 백필 예정 (주말 제외)")
        logger.info(f"백필 대상 날짜: {dates[0]} ~ {dates[-1]}")
        
        successful_files = []
        failed_dates = []
        
        try:
            # 드라이버 설정
            self.setup_driver()
            
            for i, date in enumerate(dates, 1):
                try:
                    logger.info(f"\n[{i}/{len(dates)}] {date} 백필 시작...")
                    
                    # 해당 날짜 데이터 크롤링
                    df = self.crawl_reports(date, date)
                    
                    if df.empty:
                        logger.info(f"{date}: 데이터 없음 (스킵)")
                        continue
                    
                    # 데이터 정리 및 저장
                    df_cleaned = self.clean_data(df)
                    filepath = self.save_to_csv(df_cleaned, date_str=date)
                    
                    if filepath:
                        successful_files.append(filepath)
                        logger.info(f"{date}: 성공 ({len(df_cleaned)}개 데이터)")
                    
                    # 서버 부하 방지를 위한 짧은 대기
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"{date}: 실패 - {e}")
                    failed_dates.append(date)
                    continue
            
            # 결과 요약
            logger.info("\n" + "=" * 50)
            logger.info("백필 결과 요약")
            logger.info("=" * 50)
            logger.info(f"성공: {len(successful_files)}개 파일")
            logger.info(f"실패: {len(failed_dates)}개 날짜")
            
            if successful_files:
                logger.info("\n성공한 파일들:")
                for filepath in successful_files:
                    logger.info(f"  - {os.path.basename(filepath)}")
            
            if failed_dates:
                logger.warning("\n실패한 날짜들:")
                for date in failed_dates:
                    logger.warning(f"  - {date}")
                logger.info("\n실패한 날짜는 다시 실행해주세요.")
            
            return successful_files
            
        finally:
            # 드라이버 종료
            self.close_driver()


def parse_args():
    """명령행 인수 파싱"""
    parser = argparse.ArgumentParser(
        description='FnGuide 리포트 데이터 크롤러',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python fnguide_con_crawler.py                                    # 어제 날짜 크롤링
  python fnguide_con_crawler.py --backfill --start 2025/07/01 --end 2025/07/26  # 백필
  python fnguide_con_crawler.py --headless                        # 백그라운드 실행
"""
    )
    
    parser.add_argument('--backfill', action='store_true',
                       help='백필 모드 실행')
    parser.add_argument('--start', '--start-date', type=str,
                       help='시작일 (YYYY/MM/DD 형식)')
    parser.add_argument('--end', '--end-date', type=str,
                       help='종료일 (YYYY/MM/DD 형식)')
    parser.add_argument('--headless', action='store_true',
                       help='백그라운드에서 실행')
    
    return parser.parse_args()

def main():
    """메인 실행 함수"""
    args = parse_args()
    
    # FnGuide 크롤러 생성
    crawler = FnGuideCrawler(headless=args.headless)
    
    try:
        if args.backfill:
            # 백필 모드
            if not args.start or not args.end:
                logger.error("백필 실행시 --start와 --end 날짜를 모두 지정해주세요.")
                return
            
            successful_files = crawler.backfill_data(args.start, args.end)
            
            if successful_files:
                logger.info(f"\n백필 완료: {len(successful_files)}개 파일 생성")
            else:
                logger.warning("\n백필 완료: 생성된 파일 없음")
        else:
            # 일반 모드 (어제 날짜 크롤링)
            df = crawler.run(args.start, args.end)
            
            # 결과 출력
            if df is not None and not df.empty:
                logger.info("\n크롤링된 데이터 미리보기:")
                print(df.head())
                logger.info(f"\n총 {len(df)}개의 리포트가 수집되었습니다.")
            else:
                logger.info("\n수집된 데이터가 없습니다.")
            
    except KeyboardInterrupt:
        logger.info("\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        logger.error(f"\n예상치 못한 오류: {e}")
    finally:
        crawler.close_driver()


# 사용 예시
if __name__ == "__main__":
    main()
