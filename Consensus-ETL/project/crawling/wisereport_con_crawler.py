# -*- coding: utf-8 -*-
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
download_path = os.path.join(PARENT_DIR, "consensus", "wisereport")
os.makedirs(download_path, exist_ok=True)

class WiseReportCrawler:
    def __init__(self, base_dir=download_path):
        self.base_url = "https://comp.wisereport.co.kr/wiseReport/summary/ReportSummary.aspx"
        self.params = {
            'cmp_cd': '005930'  # 삼성전자
        }
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
        url_params = '&'.join([f"{k}={v}" for k, v in self.params.items()])
        full_url = f"{self.base_url}?{url_params}"
        
        try:
            self.driver.get(full_url)
            print(f"페이지 URL: {full_url}")
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
    
    def download_excel(self):
        """Excel 파일 다운로드"""
        try:
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
                
                # 다운로드된 파일 확인
                files = os.listdir(self.base_dir)
                excel_files = [f for f in files if f.endswith(('.xls', '.xlsx'))]
                
                if excel_files:
                    print(f"다운로드 완료: {excel_files}")
                    return excel_files
                else:
                    print("Excel 파일이 다운로드되지 않았습니다.")
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
    
    def crawl_reports(self):
        """WiseReport 리포트 크롤링"""
        try:
            print("WiseReport 리포트 크롤링 시작")
            
            # 페이지 이동
            self.navigate_to_page()
            
            # Excel 다운로드
            downloaded_files = self.download_excel()
            
            if downloaded_files:
                print(f"총 {len(downloaded_files)}개 파일 다운로드 완료")
                return downloaded_files
            else:
                print("다운로드된 파일이 없습니다.")
                return []
                
        except Exception as e:
            print(f"크롤링 실패: {e}")
            return []
    
    def run(self):
        """크롤링 실행"""
        print("WiseReport 리포트 크롤링 시작")
        
        try:
            downloaded_files = self.crawl_reports()
            
            if downloaded_files:
                print("\n=== 크롤링 결과 요약 ===")
                print(f"다운로드된 파일 수: {len(downloaded_files)}")
                print(f"다운로드 경로: {self.base_dir}")
                print(f"파일 목록: {downloaded_files}")
            else:
                print("크롤링된 데이터가 없습니다.")
                
        except Exception as e:
            print(f"실행 중 오류 발생: {e}")

if __name__ == "__main__":
    crawler = WiseReportCrawler()
    crawler.run()
