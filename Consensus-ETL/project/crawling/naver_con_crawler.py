import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import sys
import time
from datetime import datetime
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='naver_finance_crawler.log'
)
logger = logging.getLogger('naver_finance_crawler')

class NaverFinanceCrawler:
    def __init__(self, download_path=None):
        self.base_url = "https://finance.naver.com"
        self.research_url = "https://finance.naver.com/research/"
        
        # 저장 경로 설정 (project/consensus/naver)
        if download_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            download_path = os.path.join(base_dir, "project", "consensus", "naver")
        
        self.download_path = download_path
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        }
        
        # 다운로드 디렉토리 생성
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
            print(f"네이버 크롤러 저장 경로 생성: {self.download_path}")
            
        # 셀레니움 설정
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 헤드리스 모드
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument(f"--user-agent={self.headers['User-Agent']}")
        
        # 다운로드 경로 설정
        prefs = {"download.default_directory": os.path.abspath(self.download_path)}
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
    def __del__(self):
        """소멸자: 드라이버 종료"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def get_stock_list(self):
        """네이버 금융에서 종목 리스트 가져오기"""
        try:
            response = requests.get("https://finance.naver.com/sise/sise_market_sum.nhn", headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            stock_list = []
            for tr in soup.select('table.type_2 tr'):
                if tr.select('td.no'):
                    code = tr.select('td:nth-child(2) a')[0]['href'].split('=')[-1]
                    name = tr.select('td:nth-child(2) a')[0].text.strip()
                    stock_list.append({'code': code, 'name': name})
            
            logger.info(f"총 {len(stock_list)}개 종목 정보 수집 완료")
            return stock_list
        except Exception as e:
            logger.error(f"종목 리스트 가져오기 실패: {str(e)}")
            return []
    
    def get_research_list(self, page=1, max_pages=10):
        """리서치 리포트 목록 가져오기 (실제 사이트 구조 반영)"""
        all_reports = []
        try:
            for page_num in range(page, page + max_pages):
                url = f"https://finance.naver.com/research/company_list.naver?page={page_num}"
                logger.info(f"리포트 목록 페이지 크롤링: {url}")
                self.driver.get(url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'table.type_1'))
                )
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                trs = soup.select('table.type_1 > tbody > tr')

                for tr in trs:
                    tds = tr.find_all('td')
                    if len(tds) < 5:
                        continue  # 유효하지 않은 행 스킵

                    stock_name = tds[0].get_text(strip=True)
                    stock_code = ""
                    stock_a = tds[0].find('a')
                    if stock_a and 'code=' in stock_a['href']:
                        stock_code = stock_a['href'].split('code=')[-1]

                    title = tds[1].get_text(strip=True)
                    report_url = self.base_url + tds[1].find('a')['href'] if tds[1].find('a') else ""
                    company = tds[2].get_text(strip=True)
                    date = tds[4].get_text(strip=True)

                    # PDF 링크 확인 및 추출
                    pdf_link = ""
                    pdf_tag = tds[3].find('a', href=True)
                    if pdf_tag and '.pdf' in pdf_tag['href']:
                        pdf_link = pdf_tag['href']
                        if not pdf_link.startswith('http'):
                            pdf_link = self.base_url + pdf_link

                    all_reports.append({
                        'title': title,
                        'url': report_url,
                        'date': date,
                        'company': company,
                        'stock_name': stock_name,
                        'stock_code': stock_code,
                        'pdf_link': pdf_link
                    })

                next_page = soup.select_one('td.pgRR a')
                if not next_page or page_num == page + max_pages - 1:
                    break


            logger.info(f"총 {len(all_reports)}개 리포트 목록 수집 완료")
            return all_reports
        except Exception as e:
            logger.error(f"리포트 목록 가져오기 실패: {str(e)}")
            return []
    
    def download_pdf(self, report_info):
        """첨부 PDF 직접 다운로드 (Content-Type 검사 완화, 실제 PDF 여부로 판별)"""
        try:
            pdf_url = report_info.get('pdf_link', '')
            if not pdf_url or not pdf_url.endswith('.pdf'):
                logger.warning(f"PDF 링크 없음 또는 잘못됨: {pdf_url}")
                # 첨부가 없는 목록 행은 다운로드 실패가 아니므로 skip으로 구분한다
                return {'success': False, 'error': 'PDF 링크 없음', 'skip': True}
            # 파일명 생성
            date_str = report_info['date'].replace('.', '')
            safe_title = ''.join(c for c in report_info['title'] if c.isalnum() or c in ' _-')[:50]
            file_name = f"{report_info['company']}_{report_info['stock_name']}_{date_str}_{safe_title}.pdf"
            file_path = os.path.join(self.download_path, file_name)
            # 이미 다운로드된 파일이면 스킵
            if os.path.exists(file_path):
                logger.info(f"이미 다운로드된 파일: {file_name}")
                return {'success': True, 'path': file_path, 'skip': True}
            # PDF 파일 다운로드 (User-Agent, Referer 추가)
            logger.info(f"PDF 다운로드 시도: {pdf_url}")
            headers = {
                'User-Agent': self.headers['User-Agent'],
                'Referer': 'https://finance.naver.com/research/company_list.naver'
            }
            response = requests.get(pdf_url, headers=headers)
            if response.status_code == 200:
                # PDF 파일인지 간단히 확인
                if response.content[:4] == b'%PDF':
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"PDF 다운로드 완료: {file_name}")
                    return {'success': True, 'path': file_path}
                else:
                    # 실패한 응답 저장
                    debug_path = os.path.join(self.download_path, 'fail_debug.html')
                    with open(debug_path, 'wb') as f:
                        f.write(response.content)
                    logger.error(f"PDF 다운로드 실패(실제 PDF 아님): {pdf_url} (응답 저장: {debug_path})")
                    return {'success': False, 'error': 'PDF 다운로드 실패'}
            else:
                # 실패한 응답 저장
                debug_path = os.path.join(self.download_path, 'fail_debug.html')
                with open(debug_path, 'wb') as f:
                    f.write(response.content)
                logger.error(f"PDF 다운로드 실패(HTTP 오류): {pdf_url} (응답 저장: {debug_path})")
                return {'success': False, 'error': 'PDF 다운로드 실패'}
        except Exception as e:
            logger.error(f"PDF 다운로드 처리 중 오류: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def run_crawler(self, days_limit=7, max_reports=100, stock_filter=None):
        """종목별 리포트 크롤링 실행

        Returns:
            int: 종료 코드 (0=성공, 1=실패). Airflow가 재시도할 수 있게 전파한다.
        """
        try:
            # 1. 모든 리포트 목록 가져오기
            all_reports = self.get_research_list(max_pages=20)

            # 목록이 비면 사이트 구조 변경으로 보고 실패로 끝낸다
            if not all_reports:
                logger.error("수집된 리포트가 없습니다. 목록 페이지 구조를 확인하세요.")
                return 1

            # 2. 날짜 필터링 (최근 days_limit일 내의 리포트만)
            if days_limit > 0:
                today = datetime.now()
                filtered_reports = []
                
                for report in all_reports:
                    try:
                        report_date = datetime.strptime(report['date'], '%Y.%m.%d')
                        days_diff = (today - report_date).days
                        
                        if days_diff <= days_limit:
                            filtered_reports.append(report)
                    except:
                        # 날짜 형식이 다를 경우 무시
                        pass
                
                all_reports = filtered_reports
            
            # 3. 종목 필터링 (특정 종목 코드만 포함)
            if stock_filter:
                all_reports = [r for r in all_reports if r['stock_code'] in stock_filter]
            
            # 4. 최대 개수 제한
            all_reports = all_reports[:max_reports]
            
            # 5. PDF 다운로드
            results = []
            failed_count = 0
            for report in all_reports:
                result = self.download_pdf(report)

                # 이미 받은 파일과 첨부 없는 행(skip)은 실패로 세지 않는다
                if not result['success'] and not result.get('skip'):
                    failed_count += 1

                # 결과 저장
                report_result = {**report, **result}
                results.append(report_result)

            # 6. 결과 저장 (동일 폴더에 저장)
            result_file = os.path.join(self.download_path, f'naver_finance_reports_{datetime.now().strftime("%Y%m%d")}.csv')
            result_df = pd.DataFrame(results)
            result_df.to_csv(result_file, index=False, encoding='utf-8-sig')
            logger.info(f"크롤링 완료: 총 {len(results)}개 리포트 처리")
            logger.info(f"결과 저장: {result_file}")

            if failed_count:
                logger.error(f"{failed_count}/{len(results)}개 PDF 다운로드에 실패했습니다.")
                return 1
            return 0

        except Exception as e:
            logger.error(f"크롤링 실행 중 오류: {str(e)}")
            return 1

if __name__ == "__main__":
    crawler = NaverFinanceCrawler()
    sys.exit(crawler.run_crawler(days_limit=0, max_reports=20))
