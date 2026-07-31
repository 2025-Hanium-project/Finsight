import os
import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import logging
import time
import urllib.parse

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ds_report_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
download_path = os.path.join(PARENT_DIR, "consensus", "DS_investment")
if not os.path.exists(download_path):
    os.makedirs(download_path)
os.makedirs(download_path, exist_ok=True)

# 종료 코드 판정용 오류 집계 (목록/상세 파싱 실패)
error_count = 0
# # 다운로드 폴더 생성
# def create_folders():
#     base_dir = os.path.join(os.getcwd(), 'DS_Reports')
#     if not os.path.exists(base_dir):
#         os.makedirs(base_dir)
#     return base_dir


# 리포트 목록 페이지에서 리포트 ID 및 정보 가져오기
def get_report_list(page_num=1, max_pages=10):
    global error_count
    all_reports = []
    
    for page in range(1, max_pages + 1):
        url = f"https://www.ds-sec.co.kr/bbs/board.php?bo_table=sub03_02&page={page}"
        try:
            logger.info(f"페이지 {page} 요청 중...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.ds-sec.co.kr/'
            }
            
            # 세션 생성 및 유지
            session = requests.Session()
            response = session.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 리포트 항목 찾기 (페이지 구조에 맞게 수정)
            report_items = soup.select('table.board_list tr:not(:first-child)')
            
            if not report_items:
                logger.warning(f"페이지 {page}에서 리포트 목록을 찾을 수 없습니다. 다른 선택자로 시도합니다.")
                report_items = soup.select('tr')
            
            logger.info(f"찾은 항목 수: {len(report_items)}")
            
            for item in report_items:
                try:
                    # 번호, 제목, 날짜 등 추출
                    cols = item.select('td')
                    if len(cols) < 3:  # 최소한 번호, 제목, 날짜 열이 있어야 함
                        continue
                    
                    # 1. 번호/ID 추출
                    num_col = cols[0].text.strip()
                    if not num_col.isdigit():
                        continue  # 번호가 숫자가 아니면 헤더 행일 수 있음
                    
                    # 2. 제목과 링크 추출
                    title_link = cols[1].select_one('a')
                    if not title_link:
                        continue
                        
                    title = title_link.text.strip()
                    href = title_link.get('href', '')
                    
                    # href에서 wr_id 추출
                    wr_id_match = re.search(r'wr_id=(\d+)', href)
                    if not wr_id_match:
                        continue
                    
                    wr_id = wr_id_match.group(1)
                    
                    # 3. 날짜 추출 (페이지에서 보이는 날짜 위치에 따라 조정)
                    date_str = cols[3].text.strip() if len(cols) > 3 else ""
                    
                    # 4. 조회수 추출 (필요시)
                    views = cols[4].text.strip() if len(cols) > 4 else "0"
                    
                    all_reports.append({
                        'id': num_col,
                        'title': title,
                        'date': date_str,
                        'views': views,
                        'wr_id': wr_id
                    })
                    
                    logger.info(f"항목 추출: {title} (ID: {num_col}, 날짜: {date_str}, 조회수: {views}, wr_id: {wr_id})")
                    
                except Exception as e:
                    logger.error(f"항목 처리 중 오류: {str(e)}")
                    error_count += 1
                    continue
            
            if page < max_pages:
                logger.info(f"다음 페이지로 이동하기 전 2초 대기...")
                time.sleep(2)
            
        except Exception as e:
            logger.error(f"페이지 {page} 처리 중 오류 발생: {str(e)}")
            error_count += 1
            break
    
    logger.info(f"총 {len(all_reports)}개 리포트 정보 수집 완료")
    return all_reports

# 리포트 상세 페이지에서 첨부파일 정보 가져오기
def get_report_attachments(wr_id, session=None):
    global error_count
    if session is None:
        session = requests.Session()
        
    url = f"https://www.ds-sec.co.kr/bbs/board.php?bo_table=sub03_02&wr_id={wr_id}"
    attachments = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.ds-sec.co.kr/bbs/board.php?bo_table=sub03_02'
        }
        
        response = session.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 첨부파일 정보 찾기
        file_links = soup.select('section#bo_v_file a')
        
        if not file_links:
            logger.warning(f"리포트 ID {wr_id}에서 첨부파일 섹션을 찾을 수 없습니다. 다른 선택자로 시도합니다.")
            file_links = soup.select('a[href*="download.php"]')
        
        logger.info(f"리포트 ID {wr_id}에서 찾은 파일 링크 수: {len(file_links)}")
        
        for link in file_links:
            # 파일명은 링크 텍스트에서 추출
            file_name = link.text.strip()
            if not file_name:
                spans = link.select('span')
                file_name = ' '.join([span.text.strip() for span in spans if span.text.strip()])
            
            # 파일 크기 등의 정보 제거
            file_name = re.sub(r'\([^)]*\)', '', file_name).strip()
            
            # 파일 URL
            file_url = link.get('href')
            if not file_url:
                continue
                
            # URL이 상대 경로인 경우 절대 경로로 변환
            if not file_url.startswith('http'):
                file_url = urllib.parse.urljoin('https://www.ds-sec.co.kr/', file_url)
            
            # 파일명이 없으면 URL에서 추출
            if not file_name:
                file_name_match = re.search(r'no=(\d+)', file_url)
                if file_name_match:
                    file_name = f"report_{wr_id}_{file_name_match.group(1)}.pdf"
                else:
                    file_name = f"report_{wr_id}.pdf"
            
            # 파일명이 pdf로 끝나지 않으면 확장자 추가
            if not file_name.lower().endswith('.pdf'):
                file_name += '.pdf'
            
            attachments.append({
                'name': file_name,
                'url': file_url
            })
            
            logger.info(f"첨부파일 발견: {file_name} ({file_url})")
        
        return attachments
        
    except Exception as e:
        logger.error(f"리포트 ID {wr_id} 처리 중 오류 발생: {str(e)}")
        error_count += 1
        return []

# 파일 다운로드 함수
def download_file(url, save_path, session=None):
    if session is None:
        session = requests.Session()
        
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.ds-sec.co.kr/bbs/board.php?bo_table=sub03_02'
        }
        
        # 쿠키 확인
        cookies = session.cookies.get_dict()
        logger.info(f"요청 시 쿠키: {cookies}")
        
        # 먼저 HEAD 요청으로 Content-Type 확인
        head_response = session.head(url, headers=headers)
        content_type = head_response.headers.get('Content-Type', '')
        
        logger.info(f"파일 헤더 확인 - Content-Type: {content_type}")
        
        # 다운로드 요청
        response = session.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        # 실제 받은 Content-Type 확인
        actual_content_type = response.headers.get('Content-Type', '')
        logger.info(f"다운로드 응답 - Content-Type: {actual_content_type}")
        
        # Content-Disposition 헤더에서 파일명 확인
        content_disposition = response.headers.get('Content-Disposition', '')
        if content_disposition:
            logger.info(f"Content-Disposition: {content_disposition}")
            filename_match = re.search(r'filename=["\'](.*?)["\']', content_disposition)
            if filename_match:
                suggested_filename = filename_match.group(1)
                logger.info(f"서버가 제안한 파일명: {suggested_filename}")
        
        # 파일 저장
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # 파일 크기 확인
        file_size = os.path.getsize(save_path)
        logger.info(f"다운로드 완료: {save_path} ({file_size} bytes)")
        
        # 작은 파일 내용 확인
        if file_size < 10000:  # 10KB 미만이면 의심
            logger.warning(f"파일 크기가 작습니다: {file_size} bytes")
            
            # 파일 내용 확인 (HTML인지)
            with open(save_path, 'r', encoding='utf-8', errors='ignore') as f:
                try:
                    first_line = f.readline().strip()
                    logger.info(f"파일 첫 줄: {first_line}")
                    
                    # HTML로 시작하면 PDF가 아닐 가능성이 높음
                    if first_line.startswith('<!DOCTYPE') or first_line.startswith('<html'):
                        logger.error(f"다운로드된 파일이 HTML입니다. PDF가 아닙니다.")
                        
                        # HTML 파일로 저장
                        html_path = save_path + ".html"
                        os.rename(save_path, html_path)
                        logger.info(f"HTML 파일로 저장됨: {html_path}")
                        
                        return False
                except:
                    pass
        
        return True
        
    except Exception as e:
        logger.error(f"파일 다운로드 중 오류 발생: {url}, {str(e)}")
        return False

# 메인 함수
def main():
    """크롤러 실행

    Returns:
        int: 종료 코드 (0=성공, 1=실패). Airflow가 재시도할 수 있게 전파한다.
    """
    start_time = datetime.now()
    logger.info(f"크롤링 시작: {start_time}")
    
    # 폴더 생성
    base_dir = download_path
    
    # 세션 유지
    session = requests.Session()
    
    # 리포트 목록 가져오기
    reports = get_report_list(max_pages=3)  # 테스트를 위해 3페이지만
    logger.info(f"총 {len(reports)}개 리포트 정보 수집 완료")
    
    if not reports:
        logger.warning("수집된 리포트가 없습니다. 크롤링을 종료합니다.")
        end_time = datetime.now()
        logger.info(f"크롤링 완료: {end_time}")
        logger.info(f"총 소요 시간: {end_time - start_time}")
        return 1

    # 리포트 정보를 담을 데이터프레임 생성
    report_data = []

    # 종료 코드 판정용 집계
    saved_count = 0
    failed_count = 0
    
    # 각 리포트별 첨부파일 다운로드
    for idx, report in enumerate(reports):
        logger.info(f"리포트 처리 중 ({idx+1}/{len(reports)}): {report['title']}")
        
        # 날짜 정보 추출 및 폴더 생성
        date_str = report['date'].replace('.', '-')  # 날짜 형식 변환 (필요시)
        
        # 첨부파일 정보 가져오기
        attachments = get_report_attachments(report['wr_id'], session)
        
        if not attachments:
            logger.warning(f"리포트 ID {report['wr_id']} ({report['title']})에 첨부파일이 없습니다.")
            continue
        
        # 첨부파일 다운로드
        for attachment in attachments:
            file_name = attachment['name']
            file_url = attachment['url']
            
            save_path = os.path.join(base_dir, file_name)
            
            download_success = download_file(file_url, save_path, session)
            status = "성공" if download_success else "실패"

            if download_success:
                saved_count += 1
            else:
                failed_count += 1

            report_data.append({
                'ID': report['id'],
                '제목': report['title'],
                '날짜': report['date'],
                '파일명': file_name,
                '다운로드 상태': status,
                '저장 경로': save_path if download_success else "",
                '조회수': report.get('views', '0')
            })
            
            logger.info(f"파일 다운로드 {status}: {file_name}")
        
        # 과도한 요청 방지를 위한 딜레이
        time.sleep(2)
    
    # 결과 저장
    if report_data:
        df = pd.DataFrame(report_data)
        excel_path = os.path.join(base_dir, f"DS_Reports_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        df.to_excel(excel_path, index=False)
        logger.info(f"다운로드 로그가 저장되었습니다: {excel_path}")
    
    end_time = datetime.now()
    logger.info(f"크롤링 완료: {end_time}")
    logger.info(f"총 소요 시간: {end_time - start_time}")

    # 조용히 성공하지 않는다. 한 건도 못 받았거나 오류가 있으면 Airflow에 실패로 알린다.
    if not saved_count:
        logger.error("다운로드된 리포트가 없습니다. 사이트 구조를 확인하세요.")
        return 1
    if failed_count or error_count:
        logger.error(f"{failed_count + error_count}건의 오류가 발생했습니다.")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
