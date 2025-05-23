
import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime
import logging
import re
import pytesseract
from PIL import Image
import cv2
import numpy as np

# Tesseract OCR 경로 설정 (Windows의 경우)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# Mac이나 Linux의 경우 주석 처리

# 로깅 설정
def setup_logger():
    # 로그 파일 경로
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # 현재 시간으로 로그 파일명 생성
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'{log_dir}/crawling_log_{current_time}.log'
    
    # 로거 설정
    logger = logging.getLogger('heungkuk_crawler')
    logger.setLevel(logging.INFO)
    
    # 파일 핸들러
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 포맷 설정
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 이미지에서 텍스트 추출 함수
def extract_text_from_image(image_path):
    try:
        # 이미지 읽기
        img = cv2.imread(image_path)
        
        # 이미지 전처리 (선명도 향상)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        # OCR 처리 (한국어 인식 포함)
        # 한국어와 영어 모두 인식하도록 설정
        custom_config = r'--oem 3 --psm 6 -l kor+eng'
        text = pytesseract.image_to_string(img, config=custom_config)
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from image {image_path}: {e}")
        return ""

# 로거 초기화
logger = setup_logger()

# 헤더 설정
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.heungkuksec.co.kr/'
}

# 크롤링할 페이지 수 설정
start_page = 1
end_page = 5  # 필요에 따라 조정

# 메인 저장 디렉토리
base_save_dir = 'heungkuk_reports'
os.makedirs(base_save_dir, exist_ok=True)

# 처리된 보고서 ID를 저장할 집합 (중복 방지)
processed_reports = set()

# 크롤링 시작 로그
logger.info(f"Started crawling Heungkuk Securities reports from page {start_page} to {end_page}")

for page in range(start_page, end_page + 1):
    # 목록 페이지 URL (페이지네이션 파라미터 추가)
    list_url = f'https://www.heungkuksec.co.kr/research/company/list.do?currentPage={page}'
    
    try:
        # 목록 페이지 요청
        logger.info(f"Requesting list page {page}: {list_url}")
        response = requests.get(list_url, headers=headers)
        response.raise_for_status()
        
        # HTML 파싱
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 보고서 목록에서 각 행 추출 (테이블 행 형태로 있음)
        report_rows = soup.select('table tr')
        logger.info(f"Found {len(report_rows)} rows in page {page}")
        
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
                    logger.warning(f"Could not extract report ID from link: {href}")
                    continue
                
                # 이미 처리한 보고서는 건너뛰기
                if report_id in processed_reports:
                    logger.debug(f"Skipping already processed report ID: {report_id}")
                    continue
                
                processed_reports.add(report_id)
                logger.info(f"Processing report ID: {report_id}")
                
                # 보고서 페이지 URL 구성
                detail_url = f'https://www.heungkuksec.co.kr/research/company/view.do?key={report_id}'
                
                try:
                    # 상세 페이지 요청
                    logger.info(f"Requesting detail page: {detail_url}")
                    detail_response = requests.get(detail_url, headers=headers)
                    detail_response.raise_for_status()
                    
                    # 상세 페이지 HTML 파싱
                    detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
                    
                    logger.info(f"Report info - Title: {title_text}, Author: {analyst}, Date: {date_str}")
                    
                    # 날짜 파싱 및 폴더 이름 생성
                    try:
                        # 날짜 형식이 'YYYY-MM-DD'라고 가정
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        date_folder_name = date_obj.strftime('%Y%m%d')
                    except ValueError:
                        # 날짜 파싱 실패 시 'Unknown_Date'로 설정
                        logger.warning(f"Failed to parse date: {date_str}, using 'Unknown_Date'")
                        date_folder_name = 'Unknown_Date'
                    
                    # 날짜별 폴더 생성
                    date_folder_path = os.path.join(base_save_dir, date_folder_name)
                    os.makedirs(date_folder_path, exist_ok=True)
                    
                    # 유효한 파일명으로 변환
                    valid_title = ''.join(c if c.isalnum() or c in [' ', '-', '_'] else '_' for c in title_text)
                    valid_title = valid_title[:100]  # 파일명 길이 제한
                    
                    # 보고서 이미지 URL 추출
                    img_elements = detail_soup.select('table tr td img[src^="http://www.heungkuksec.co.kr/upload/"]')
                    logger.info(f"Found {len(img_elements)} image(s) in report ID: {report_id}")
                    
                    # 보고서에서 추출한 모든 텍스트를 저장할 변수
                    all_extracted_text = ""
                    
                    # 이미지 저장 및 OCR 처리
                    for i, img in enumerate(img_elements):
                        img_url = img['src']
                        try:
                            logger.info(f"Downloading image {i+1}/{len(img_elements)}: {img_url}")
                            img_response = requests.get(img_url, headers=headers)
                            img_response.raise_for_status()
                            
                            # 이미지 저장
                            img_filename = f'{date_folder_path}/{valid_title}_report_{report_id}_{i+1}.jpg'
                            with open(img_filename, 'wb') as f:
                                f.write(img_response.content)
                            
                            logger.info(f"Downloaded image: {img_filename}")
                            
                            # OCR 처리
                            logger.info(f"Extracting text from image: {img_filename}")
                            extracted_text = extract_text_from_image(img_filename)
                            
                            # 텍스트 저장
                            text_filename = f'{date_folder_path}/{valid_title}_report_{report_id}_{i+1}_text.txt'
                            with open(text_filename, 'w', encoding='utf-8') as f:
                                f.write(extracted_text)
                            
                            # 모든 텍스트 합치기
                            all_extracted_text += f"\n\n--- Image {i+1} ---\n\n"
                            all_extracted_text += extracted_text
                            
                            logger.info(f"Extracted and saved text from image {i+1}")
                            
                        except Exception as e:
                            logger.error(f"Error processing image {img_url}: {e}")
                    
                    # 전체 추출 텍스트 저장
                    if all_extracted_text:
                        full_text_filename = f'{date_folder_path}/{valid_title}_report_{report_id}_full_text.txt'
                        with open(full_text_filename, 'w', encoding='utf-8') as f:
                            f.write(all_extracted_text)
                        logger.info(f"Saved combined text from all images: {full_text_filename}")
                    
                    # 보고서 메타데이터 저장 (제목, 작성자, 날짜 등)
                    meta_filename = f'{date_folder_path}/{valid_title}_report_{report_id}_meta.txt'
                    
                    # 메타데이터 저장
                    with open(meta_filename, 'w', encoding='utf-8') as f:
                        f.write(f'Title: {title_text}\n')
                        f.write(f'Report ID: {report_id}\n')
                        f.write(f'Author: {analyst}\n')
                        f.write(f'Date: {date_str}\n')
                        f.write(f'URL: {detail_url}\n')
                    
                    logger.info(f"Saved metadata: {meta_filename}")
                    
                    # 서버 부하 방지를 위한 딜레이
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing report {report_id}: {e}")
            
            except Exception as e:
                logger.error(f"Error parsing row: {e}")
                continue
        
        # 페이지 간 딜레이
        logger.info(f"Completed page {page}, waiting before next page...")
        time.sleep(2)
        
    except Exception as e:
        logger.error(f"Error processing page {page}: {e}")

logger.info(f"Completed downloading {len(processed_reports)} reports.")
logger.info("Crawling process finished.")
