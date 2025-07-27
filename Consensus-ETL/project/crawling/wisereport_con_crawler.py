# -*- coding: utf-8 -*-
import time
import os
import pandas as pd
import re
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
download_path = os.path.join(PARENT_DIR, "consensus", "wisereport")
os.makedirs(download_path, exist_ok=True)

class WiseReportCrawler:
    def __init__(self, base_dir=download_path):
        self.base_url = "https://comp.wisereport.co.kr/wiseReport/summary/ReportSummary.aspx"
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
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # 웹드라이버 초기화
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def __del__(self):
        """소멸자: 웹드라이버 종료"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def navigate_to_page(self):
        """페이지로 이동"""
        try:
            self.driver.get(self.base_url)
            print(f"페이지 URL: {self.base_url}")
            time.sleep(3)  # 페이지 로딩 대기
        except Exception as e:
            print(f"페이지 로드 실패: {e}")
            raise
    
    def find_excel_button(self):
        """Excel 다운로드 버튼 찾기"""
        excel_button = None
        
        # 방법 1: class name으로 찾기
        try:
            excel_button = self.wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btn_etc"))
            )
            print("Excel 버튼을 class name으로 찾았습니다.")
            return excel_button
        except:
            pass
        
        # 방법 2: Excel 텍스트를 포함한 링크 찾기
        try:
            excel_button = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Excel')]")
            print("Excel 버튼을 텍스트로 찾았습니다.")
            return excel_button
        except:
            pass
        
        # 방법 3: icon-excel 클래스를 가진 span의 부모 요소 찾기
        try:
            excel_icon = self.driver.find_element(By.CLASS_NAME, "icon-excel")
            excel_button = excel_icon.find_element(By.XPATH, "./..")
            print("Excel 버튼을 아이콘으로 찾았습니다.")
            return excel_button
        except:
            pass
        
        # 방법 4: 스타일 속성으로 찾기
        try:
            excel_button = self.driver.find_element(
                By.CSS_SELECTOR, 
                "a[style*='background-color:#0DADEF']"
            )
            print("Excel 버튼을 스타일로 찾았습니다.")
            return excel_button
        except:
            pass
        
        return None
    
    def get_available_dates(self):
        """사용 가능한 날짜 목록 가져오기"""
        try:
            date_select = self.wait.until(
                EC.presence_of_element_located((By.ID, "ddlDate"))
            )
            
            options = date_select.find_elements(By.TAG_NAME, "option")
            available_dates = []
            
            for option in options:
                date_value = option.get_attribute("value")
                date_text = option.text
                if date_value and len(date_value) == 8:  # YYYYMMDD 형식
                    available_dates.append({
                        'value': date_value,
                        'text': date_text,
                        'element': option
                    })
            
            print(f"사용 가능한 날짜: {len(available_dates)}개")
            return available_dates
            
        except Exception as e:
            print(f"날짜 목록 가져오기 실패: {e}")
            return []
    
    def select_date_and_search(self, date_value):
        """날짜 선택하고 검색"""
        try:
            print(f"날짜 선택 중: {date_value}")
            
            # 날짜 선택
            date_select = self.driver.find_element(By.ID, "ddlDate")
            
            # JavaScript로 날짜 선택
            self.driver.execute_script(f"document.getElementById('ddlDate').value = '{date_value}';")
            time.sleep(1)
            
            # 검색 버튼 클릭
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "btnsubmit"))
            )
            search_button.click()
            print(f"날짜 {date_value} 검색 완료")
            
            # 페이지 로딩 대기
            time.sleep(3)
            return True
            
        except Exception as e:
            print(f"날짜 선택 및 검색 실패: {e}")
            return False
    
    def check_data_availability(self):
        """데이터 유무 확인"""
        try:
            # 데이터가 없을 때 나타나는 메시지 확인
            no_data_selectors = [
                "//td[contains(text(), '데이터가 없습니다')]",
                "//div[contains(text(), '데이터가 없습니다')]",
                "//span[contains(text(), '데이터가 없습니다')]",
                "//td[contains(text(), '조회된 데이터가 없습니다')]",
                ".no-data",
                ".empty-data"
            ]
            
            for selector in no_data_selectors:
                try:
                    if selector.startswith('//'):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        print("데이터가 없습니다.")
                        return False
                except:
                    continue
            
            # Excel 버튼이 있는지 확인
            excel_button = self.find_excel_button()
            if excel_button:
                print("데이터가 있습니다.")
                return True
            else:
                print("Excel 버튼을 찾을 수 없어 데이터 없음으로 판단")
                return False
                
        except Exception as e:
            print(f"데이터 유무 확인 중 오류: {e}")
            return False
    
    def download_excel(self):
        """Excel 파일 다운로드"""
        try:
            # 다운로드 전 기존 파일 목록 저장
            files_before = set(os.listdir(self.base_dir)) if os.path.exists(self.base_dir) else set()
            
            # Excel 버튼 찾기
            excel_button = self.find_excel_button()
            
            if excel_button:
                # 버튼이 보이도록 스크롤
                self.driver.execute_script("arguments[0].scrollIntoView(true);", excel_button)
                time.sleep(1)
                
                # 버튼 클릭
                excel_button.click()
                print("Excel 다운로드 버튼을 클릭했습니다.")
                
                # 다운로드 완료 대기
                time.sleep(5)
                
                # 새로 다운로드된 파일만 확인
                files_after = set(os.listdir(self.base_dir)) if os.path.exists(self.base_dir) else set()
                new_files = files_after - files_before
                excel_files = [f for f in new_files if f.endswith(('.xls', '.xlsx'))]
                
                if excel_files:
                    print(f"새로 다운로드된 파일: {list(excel_files)}")
                    return list(excel_files)
                else:
                    print("새로운 Excel 파일이 다운로드되지 않았습니다.")
                    return []
            else:
                print("Excel 버튼을 찾을 수 없습니다.")
                
                # 페이지 소스 일부 출력하여 디버깅
                print("\n현재 페이지의 버튼 관련 요소들:")
                buttons = self.driver.find_elements(By.TAG_NAME, "a")
                for btn in buttons[:10]:  # 처음 10개만 출력
                    print(f"Text: {btn.text}, Class: {btn.get_attribute('class')}")
                
                return []
                
        except Exception as e:
            print(f"Excel 다운로드 중 오류 발생: {e}")
            return []
    
    def crawl_reports_for_date(self, date_value):
        """특정 날짜의 리포트 크롤링"""
        try:
            # 날짜 선택하고 검색
            if not self.select_date_and_search(date_value):
                return []
            
            # 데이터 유무 확인
            if not self.check_data_availability():
                print(f"날짜 {date_value}에 데이터가 없습니다.")
                return []
            
            # Excel 다운로드
            downloaded_files = self.download_excel()
            
            if downloaded_files:
                # 새로 다운로드된 파일만 필터링하여 파일명 변경
                renamed_files = []
                for file in downloaded_files:
                    old_path = os.path.join(self.base_dir, file)
                    
                    # 이미 wisereport_ 접두사가 있는 파일은 건너뛰기
                    if file.startswith("wisereport_"):
                        continue
                    
                    if os.path.exists(old_path):
                        name, ext = os.path.splitext(file)
                        new_name = f"wisereport_{date_value}_{name}{ext}"
                        new_path = os.path.join(self.base_dir, new_name)
                        
                        # 같은 이름의 파일이 이미 있으면 건너뛰기
                        if os.path.exists(new_path):
                            print(f"파일이 이미 존재함: {new_name}")
                            continue
                        
                        try:
                            os.rename(old_path, new_path)
                            renamed_files.append(new_name)
                            print(f"파일명 변경: {file} -> {new_name}")
                        except Exception as e:
                            print(f"파일명 변경 실패: {file}, 오류: {e}")
                            renamed_files.append(file)
                    else:
                        renamed_files.append(file)
                
                return renamed_files
            else:
                print(f"날짜 {date_value}에 다운로드된 파일이 없습니다.")
                return []
                
        except Exception as e:
            print(f"날짜 {date_value} 크롤링 실패: {e}")
            return []
    
    def crawl_reports(self, days=7):
        """WiseReport 리포트 크롤링 (최근 N일)"""
        try:
            print(f"WiseReport 리포트 크롤링 시작 - 최근 {days}일")
            
            # 페이지 이동
            self.navigate_to_page()
            
            # 사용 가능한 날짜 목록 가져오기
            available_dates = self.get_available_dates()
            
            if not available_dates:
                print("사용 가능한 날짜가 없습니다.")
                return []
            
            # 최근 N일 날짜만 필터링
            target_dates = []
            today = datetime.now()
            
            for date_info in available_dates:
                try:
                    date_obj = datetime.strptime(date_info['value'], '%Y%m%d')
                    days_diff = (today - date_obj).days
                    
                    if 0 <= days_diff <= days:
                        target_dates.append(date_info)
                except:
                    continue
            
            print(f"수집 대상 날짜: {len(target_dates)}개")
            
            all_downloaded_files = []
            
            for i, date_info in enumerate(target_dates, 1):
                print(f"\n[{i}/{len(target_dates)}] 날짜 {date_info['text']} 처리 중...")
                
                downloaded_files = self.crawl_reports_for_date(date_info['value'])
                all_downloaded_files.extend(downloaded_files)
                
                # 서버 부하 방지
                if i < len(target_dates):
                    time.sleep(2)
            
            return all_downloaded_files
                
        except Exception as e:
            print(f"크롤링 실패: {e}")
            return []
    
    def run(self, days=7):
        """크롤링 실행"""
        print(f"WiseReport 리포트 크롤링 시작 - 최근 {days}일")
        
        try:
            downloaded_files = self.crawl_reports(days)
            
            if downloaded_files:
                print("\n=== 크롤링 결과 요약 ===")
                print(f"수집 기간: 최근 {days}일")
                print(f"다운로드된 파일 수: {len(downloaded_files)}")
                print(f"다운로드 경로: {self.base_dir}")
                print(f"파일 목록:")
                for file in downloaded_files:
                    print(f"  - {file}")
                return True
            else:
                print("크롤링된 데이터가 없습니다.")
                return False
                
        except Exception as e:
            print(f"실행 중 오류 발생: {e}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='WiseReport 리포트 크롤러')
    parser.add_argument('--days', type=int, default=7, help='수집할 최근 일수 (기본: 7일)')
    
    args = parser.parse_args()
    
    try:
        crawler = WiseReportCrawler()
        result = crawler.run(days=args.days)
        
        if not result:
            print("데이터 수집에 실패했습니다.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"오류 발생: {e}")
        sys.exit(1)
