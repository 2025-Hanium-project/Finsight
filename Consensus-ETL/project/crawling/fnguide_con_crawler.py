import pandas as pd
import requests
import time
from datetime import datetime, timedelta
import os
import logging
import argparse
import sys

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 다운로드 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
DOWNLOAD_DIR = os.path.join(PARENT_DIR, "consensus", "fnguide")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class FnGuideCrawler:
    # 신버전(wcomp) 요약리포트 화면이 조회에 사용하는 API
    LIST_PAGE_URL = "https://wcomp.fnguide.com/Report/ReportSummary"
    API_URL = "https://wcomp.fnguide.com/Report/getRptSmrSummary"

    def __init__(self, download_dir=None, headless=True):
        """
        FnGuide 크롤러 초기화

        Args:
            download_dir (str): 데이터를 저장할 디렉토리 (기본값: project/consensus/fnguide)
            headless (bool): 남겨둔 인자 (더 이상 브라우저를 쓰지 않아 사용되지 않음)
        """
        if download_dir is None:
            download_dir = DOWNLOAD_DIR

        self.download_dir = os.path.abspath(download_dir)
        os.makedirs(self.download_dir, exist_ok=True)
        self.headless = headless

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
            ),
            "Referer": self.LIST_PAGE_URL,
            "X-Requested-With": "XMLHttpRequest",
        })

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
        """이전 버전 호환용 (더 이상 브라우저를 쓰지 않는다)"""
        return None

    def close_driver(self):
        """이전 버전 호환용 (더 이상 브라우저를 쓰지 않는다)"""
        return None

    def crawl_reports(self, start_date="2025/07/13", end_date="2025/07/20"):
        """
        FnGuide 리포트 요약 데이터를 크롤링합니다.

        기존 comp.fnguide.com/SVO2/ASP/SVD_Report_Summary.asp 페이지는 폐지되었고
        (접속 시 "페이지가 없습니다" 안내), 신버전 wcomp.fnguide.com 으로 이전되었다.
        신버전 화면이 조회에 사용하는 JSON API를 직접 호출하므로 브라우저가 필요 없다.

        Args:
            start_date (str): 시작일 (YYYY/MM/DD)
            end_date (str): 종료일 (YYYY/MM/DD)

        Returns:
            pandas.DataFrame: 크롤링된 리포트 데이터
        """
        sdt = start_date.replace("/", "").replace("-", "")
        edt = end_date.replace("/", "").replace("-", "")

        logger.info(f"조회 요청: {start_date} ~ {end_date}")

        try:
            response = self.session.get(
                self.API_URL,
                params={
                    "search_typ": "all",
                    "sdt": sdt,
                    "edt": edt,
                    "search": "",
                    "order_col": "0",
                    "order_typ": "D",
                },
                timeout=30,
            )
            response.raise_for_status()
            rows = response.json()["dataset"]["data"]
        except Exception as e:
            logger.error(f"리포트 조회 실패: {e}")
            raise RuntimeError("FnGuide API 조회에 실패했습니다.") from e

        if not rows:
            logger.info("해당 기간에 데이터가 없습니다.")
            return pd.DataFrame()

        records = [
            {
                "일자": row.get("DT"),
                "종목코드": row.get("CMP_CD"),
                "종목명": row.get("CMP_NM_KOR"),
                "리포트제목": row.get("RPT_TITLE"),
                "리포트요약": row.get("COMMENT"),
                "제공처": row.get("BRK_NM_KOR"),
                "작성자": row.get("ANL_NM_KOR"),
                "투자의견": row.get("RECOMM_NM"),
                "목표주가": row.get("TARGET_PRC"),
                "전일종가": row.get("CLOSE_PRC"),
                "리포트ID": row.get("RPT_ID"),
            }
            for row in rows
        ]

        df = pd.DataFrame(records)
        logger.info(f"{len(df)}개의 리포트를 수집했습니다.")
        return df

    def clean_data(self, df):
        """데이터 정리"""
        if df.empty:
            return df

        # 빈 행 제거
        df = df.dropna(how="all")

        # 목표주가와 전일종가에서 숫자 추출 (미제공 시 None이 올 수 있다)
        for col in ("목표주가", "전일종가"):
            if col in df.columns:
                df[col] = (
                    df[col].astype("string")
                    .str.replace(",", "", regex=False)
                    .str.extract(r"(\d+)")[0]
                )

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
                raise RuntimeError(f"{len(failed_dates)}개 날짜의 백필에 실패했습니다.")
            
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
                return 2
            
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
        return 130
    except Exception as e:
        logger.error(f"\n예상치 못한 오류: {e}")
        return 1
    finally:
        crawler.close_driver()

    return 0


# 사용 예시
if __name__ == "__main__":
    sys.exit(main())
