
import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime
import re

# 헤더 설정
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.heungkuksec.co.kr/'
}

# 크롤링할 페이지 수 설정
start_page = 1
end_page = 5  # 필요에 따라 조정

# 메인 저장 디렉토리 (project/consensus/hk)
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(script_dir))
base_save_dir = os.path.join(base_dir, "project", "consensus", "heungkuk")
os.makedirs(base_save_dir, exist_ok=True)

# 처리된 보고서 ID를 저장할 집합 (중복 방지)
processed_reports = set()

# 크롤링 시작
print(f"Started crawling Heungkuk Securities reports from page {start_page} to {end_page}")

for page in range(start_page, end_page + 1):
    # 목록 페이지 URL (페이지네이션 파라미터 추가)
    list_url = f'https://www.heungkuksec.co.kr/research/company/list.do?currentPage={page}'
    
    try:
        # 목록 페이지 요청
        print(f"Requesting list page {page}: {list_url}")
        response = requests.get(list_url, headers=headers)
        response.raise_for_status()
        
        # HTML 파싱
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 보고서 목록에서 각 행 추출 (테이블 행 형태로 있음)
        report_rows = soup.select('table tr')
        print(f"Found {len(report_rows)} rows in page {page}")
        
        for row in report_rows:
            try:
                # 보고서 제목 링크 찾기
                title_cell = row.select_one('td:nth-child(2)')
                if not title_cell:
                    continue
                
                # 직접 텍스트에서 정보 추출
                title_text = title_cell.text.strip()
                if not title_text:
                    continue
                
                # 애널리스트 정보
                analyst_cell = row.select_one('td:nth-child(3)')
                analyst = analyst_cell.text.strip() if analyst_cell else "Unknown"
                
                # 날짜 정보
                date_cell = row.select_one('td:nth-child(4)')
                date_str = date_cell.text.strip() if date_cell else "Unknown"
                
                # 보고서 ID 및 링크 추출 (현재는 td a 태그의 href 속성에서 가져옴)
                # 일단 a 태그를 찾아보고 없으면 건너뜀
                link_elem = row.select_one('a')
                if not link_elem:
                    continue
                
                href = link_elem.get('href', '')
                
                # href에서 key 값 추출 - 올바른 방식으로 파싱
                report_id = None
                if href and 'key=' in href:
                    # 정규식으로 key= 뒤의 숫자 추출
                    match = re.search(r'key=(\d+)', href)
                    if match:
                        report_id = match.group(1)
                
                # onclick 속성에서도 확인
                if not report_id:
                    onclick = link_elem.get('onclick', '')
                    if onclick and 'key=' in onclick:
                        match = re.search(r'key=(\d+)', onclick)
                        if match:
                            report_id = match.group(1)
                
                # 여전히 report_id가 없다면 건너뛰기
                if not report_id:
                    print(f"Could not extract report ID from link: {href}")
                    continue
                
                # 이미 처리한 보고서는 건너뛰기
                if report_id in processed_reports:
                    continue
                
                processed_reports.add(report_id)
                print(f"Processing report ID: {report_id}")
                
                # 보고서 페이지 URL 구성
                detail_url = f'https://www.heungkuksec.co.kr/research/company/view.do?key={report_id}'
                
                try:
                    # 상세 페이지 요청
                    print(f"Requesting detail page: {detail_url}")
                    detail_response = requests.get(detail_url, headers=headers)
                    detail_response.raise_for_status()
                    
                    # 상세 페이지 HTML 파싱
                    detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                    
                    print(f"Report info - Title: {title_text}, Author: {analyst}, Date: {date_str}")
                    
                    # 날짜 파싱 및 폴더 이름 생성
                    try:
                        # 날짜 형식이 'YYYY-MM-DD'라고 가정
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        date_folder_name = date_obj.strftime('%Y%m%d')
                    except ValueError:
                        # 날짜 파싱 실패 시 'Unknown_Date'로 설정
                        print(f"Failed to parse date: {date_str}, using 'Unknown_Date'")
                        date_folder_name = 'Unknown_Date'
                    
                    # 유효한 파일명으로 변환
                    valid_title = ''.join(c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in title_text)
                    valid_title = valid_title[:100]  # 파일명 길이 제한
                    
                    # 보고서 이미지 URL 추출
                    img_elements = detail_soup.select('table tr td img[src^="http://www.heungkuksec.co.kr/upload/"]')
                    print(f"Found {len(img_elements)} image(s) in report ID: {report_id}")
                    
                    # 이미지 저장
                    for i, img in enumerate(img_elements):
                        img_url = img['src']
                        try:
                            print(f"Downloading image {i+1}/{len(img_elements)}: {img_url}")
                            img_response = requests.get(img_url, headers=headers)
                            img_response.raise_for_status()
                            
                            # PNG 이미지 저장
                            img_filename = os.path.join(base_save_dir, f'{valid_title}_report_{report_id}_{i+1}.png')
                            with open(img_filename, 'wb') as f:
                                f.write(img_response.content)
                            
                            print(f"Downloaded image: {img_filename}")
                            
                        except Exception as e:
                            print(f"Error processing image {img_url}: {e}")
                    
                    # 서버 부하 방지를 위한 딜레이
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error processing report {report_id}: {e}")
            
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue
        
        # 페이지 간 딜레이
        print(f"Completed page {page}, waiting before next page...")
        time.sleep(2)
        
    except Exception as e:
        print(f"Error processing page {page}: {e}")

print(f"Completed downloading {len(processed_reports)} reports.")
print("Crawling process finished.")
