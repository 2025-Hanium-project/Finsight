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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests

class HanaSecuritiesCrawler:
    def __init__(self, base_dir="./hana_reports"):
        self.base_url = "https://www.hanaw.com/main/research/research/list.cmd?pid=3&cid=2"
        self.base_dir = base_dir
        Path(base_dir).mkdir(parents=True, exist_ok=True)
        
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 화면 표시 없이 실행
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
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
    
    def crawl_page(self, page=1):
        """특정 페이지 크롤링"""
        try:
            # 페이지 URL 구성
            page_url = f"{self.base_url}&page={page}"
            print(f"페이지 URL: {page_url}")
            
            # 페이지 접속
            self.driver.get(page_url)
            
            # 페이지 로딩 대기
            time.sleep(5)  # 페이지 로딩을 위한 충분한 시간
            
            # 리포트 항목 찾기 - 실제 웹페이지 구조에 맞게 선택자 사용
            report_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.daily_bbs > ul > li")
            
            print(f"발견된 항목 수: {len(report_elements)}")
            
            reports = []
            for element in report_elements:
                try:
                    # 리포트 제목
                    title_elem = element.find_element(By.CSS_SELECTOR, "h3 > a.more_btn")
                    title = title_elem.text.strip()
                    if not title:
                        continue
                    
                    print(f"제목: {title}")
                    
                    # 종목코드/종목명 추출
                    stock_code_match = re.search(r'\((\d+)\.', title)
                    stock_code = stock_code_match.group(1) if stock_code_match else ""
                    
                    stock_name_match = re.search(r'^(.*?)\(', title)
                    stock_name = stock_name_match.group(1).strip() if stock_name_match else ""
                    
                    # 작성자
                    try:
                        author_elem = element.find_element(By.CSS_SELECTOR, "div.view > ul > li.view-txt")
                        author = author_elem.text.strip().split('&nbsp;')[-1]
                    except NoSuchElementException:
                        author = ""
                    
                    # 날짜
                    try:
                        date_elem = element.find_element(By.CSS_SELECTOR, "li.mb7.m-info.info > span.txtbasic")
                        date_text = date_elem.text.strip()
                        date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', date_text)
                        date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}" if date_match else ""
                    except NoSuchElementException:
                        date = ""
                    
                    # PDF 파일명 및 링크
                    try:
                        pdf_elem = element.find_element(By.CSS_SELECTOR, "div.pdf > a")
                        pdf_filename = pdf_elem.text.strip()
                        pdf_link = pdf_elem.get_attribute('href')
                    except NoSuchElementException:
                        pdf_filename = ""
                        pdf_link = ""
                    
                    # 투자의견 추출
                    opinion_match = re.search(r'/([^/)]+)', title)
                    opinion = opinion_match.group(1).strip() if opinion_match else ""
                    
                    # 목표가 추출
                    target_price_match = re.search(r'TP\s+([,\d]+)원', title)
                    target_price = target_price_match.group(1).replace(",", "") if target_price_match else ""
                    
                    reports.append({
                        "종목코드": stock_code,
                        "종목명": stock_name,
                        "리포트제목": title,
                        "작성자": author,
                        "작성일자": date,
                        "PDF파일명": pdf_filename,
                        "PDF링크": pdf_link,
                        "투자의견": opinion,
                        "목표가": target_price
                    })
                    print(f"리포트 정보 추출 성공: {stock_name} - {title}")
                    
                except Exception as e:
                    print(f"항목 처리 오류: {e}")
            
            return reports
            
        except Exception as e:
            print(f"페이지 크롤링 오류: {e}")
            return []
    
    def download_pdf(self, report):
        """PDF 파일 다운로드"""
        if not report.get("PDF파일명") or not report.get("PDF링크"):
            print(f"PDF 정보가 없습니다: {report.get('리포트제목', '제목 없음')}")
            return None
        
        try:
            # 날짜 정보 확인
            date_str = report.get("작성일자", "")
            if date_str and len(date_str.split("-")) == 3:
                year, month, day = date_str.split("-")
            else:
                # 현재 날짜 사용
                now = datetime.now()
                year, month, day = now.strftime("%Y"), now.strftime("%m"), now.strftime("%d")
            
            # 저장 경로 생성
            save_dir = Path(self.base_dir) / year / month / day
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # PDF 저장 경로
            pdf_filename = report["PDF파일명"]
            save_path = save_dir / pdf_filename
            
            # 이미 파일이 존재하면 다운로드 생략
            if save_path.exists():
                print(f"이미 존재하는 파일: {save_path}")
                return save_path
            
            # PDF 다운로드
            pdf_link = report["PDF링크"]
            print(f"PDF 다운로드 시도: {pdf_link}")
            
            # 직접 다운로드 링크로 접근
            self.driver.get(pdf_link)
            time.sleep(2)  # PDF 로드 대기
            
            # 페이지 소스 확인 (디버깅용)
            # print(f"PDF 페이지 소스: {self.driver.page_source[:500]}")
            
            # PDF 다운로드 (요청 방식 사용)
            response = requests.get(pdf_link, headers=self.headers, timeout=30)
            
            if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"PDF 다운로드 성공: {save_path}")
                return save_path
            else:
                print(f"PDF 다운로드 실패 (상태 코드: {response.status_code}): {pdf_link}")
                return None
            
        except Exception as e:
            print(f"PDF 다운로드 처리 오류: {e}")
            return None
    
    def crawl_reports(self, max_pages=3):
        """최대 페이지 수까지 크롤링 실행"""
        all_reports = []
        
        for page in range(1, max_pages + 1):
            print(f"\n페이지 {page} 크롤링 중...")
            reports = self.crawl_page(page)
            print(f"페이지 {page}에서 {len(reports)}개 리포트 발견")
            
            # 각 리포트 PDF 다운로드
            for report in reports:
                pdf_path = self.download_pdf(report)
                if pdf_path:
                    report["PDF저장경로"] = str(pdf_path)
                all_reports.append(report)
            
            # 서버 부하 방지를 위한 대기
            time.sleep(3)
        
        # 결과 데이터프레임 생성 및 CSV 저장
        if all_reports:
            df = pd.DataFrame(all_reports)
            csv_path = Path(self.base_dir) / "reports_database.csv"
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            print(f"총 {len(all_reports)}개 리포트 정보가 {csv_path}에 저장되었습니다.")
        else:
            print("수집된 리포트가 없습니다.")
        
        return all_reports
    
    def schedule_daily_crawl(self, hour=9, minute=0):
        """매일 정해진 시간에 크롤링 실행"""
        import schedule
        
        def job():
            print(f"{datetime.now()} - 정기 크롤링 시작")
            self.crawl_reports(max_pages=10)  # 10페이지까지 크롤링
        
        # 매일 지정된 시간에 실행
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(job)
        
        print(f"정기 크롤링 설정됨: 매일 {hour:02d}:{minute:02d}")
        while True:
            schedule.run_pending()
            time.sleep(60)

# 실행 코드
if __name__ == "__main__":
    crawler = HanaSecuritiesCrawler(base_dir="./hana_reports")
    reports = crawler.crawl_reports(max_pages=3)  # 처음 3페이지만 크롤링
    
    print(f"크롤링 완료: {len(reports)}개 리포트 정보 수집")
    
    # 정기 실행을 원한다면 주석 해제
    # crawler.schedule_daily_crawl(hour=9, minute=0)  # 매일 오전 9시에 실행
