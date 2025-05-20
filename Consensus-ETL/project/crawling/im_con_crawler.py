
import requests
from bs4 import BeautifulSoup
import os
import logging
import datetime
import time
import random
import re
from urllib.parse import urljoin
import json

# 로깅 설정
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"im_securities_crawler_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
download_dir = os.path.join(PARENT_DIR, "consensus", "im_securities")

# 저장 디렉토리 설정
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

# 세션 생성
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://m.imfnsec.com:442/mobile/research/rs01.jsp'
})

# 기본 URL
base_url = "https://m.imfnsec.com:442"
report_list_url = f"{base_url}/mobile/research/rs01.jsp"

def extract_pdf_path(onclick_attr):
    """
    JavaScript onclick 속성에서 PDF 파일 경로 추출
    """
    if not onclick_attr:
        return None
    
    # javascript:view_pdf('/upload/R_E08/2025/05/[09170431]_011780.pdf') 패턴 추출
    pdf_match = re.search(r"view_pdf\('([^']+)'\)", onclick_attr)
    if pdf_match:
        return pdf_match.group(1)
    return None

def get_report_list(page=1):
    """
    특정 페이지의 리포트 목록을 가져오는 함수
    구조 분석 결과에 맞게 수정
    """
    try:
        logger.info(f"페이지 {page} 리포트 목록 가져오기 시작")
        
        # 페이지 매개변수 설정
        params = {}
        if page > 1:
            params = {"page": page}
            
        response = session.get(report_list_url, params=params)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 구조 분석 결과에 맞게 리포트 항목 선택
        report_items = soup.select('tr')
        
        logger.info(f"발견된 tr 태그 수: {len(report_items)}")
        
        reports = []
        for item in report_items:
            try:
                # 제목과 날짜가 포함된 a 태그 찾기
                link_elem = item.select_one('td.tal a')
                if not link_elem:
                    continue
                
                # PDF 파일 경로 추출
                onclick = link_elem.get('href', '')
                pdf_path = extract_pdf_path(onclick)
                if not pdf_path:
                    continue
                
                # 제목과 날짜 추출
                title_elem = link_elem.select_one('p:not(.d)')
                date_elem = link_elem.select_one('p.d')
                
                if not title_elem or not date_elem:
                    continue
                
                title_text = title_elem.get_text().strip()
                date_text = date_elem.get_text().strip()
                
                # PDF 다운로드 URL 구성
                pdf_url = urljoin(base_url, pdf_path)
                
                # 리포트 정보 추가
                reports.append({
                    'title': title_text,
                    'date': date_text,
                    'pdf_url': pdf_url,
                    'pdf_path': pdf_path
                })
                logger.info(f"리포트 추가: {title_text} ({date_text})")
            except Exception as e:
                logger.error(f"리포트 항목 처리 중 오류: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        logger.info(f"페이지 {page}에서 {len(reports)}개 리포트 목록 추출 완료")
        return reports
    
    except Exception as e:
        logger.error(f"페이지 {page} 리포트 목록 가져오기 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def download_report(report):
    """
    리포트 PDF 파일 다운로드 함수
    """
    if not report.get('pdf_url'):
        logger.warning(f"PDF URL이 없음: {report['title']}")
        return False
    
    try:
        logger.info(f"리포트 다운로드 시작: {report['title']}")
        
        # PDF 파일 다운로드
        pdf_url = report['pdf_url']
        
        # 파일명 생성 (날짜_제목.pdf)
        date_str = report['date'].replace('/', '')
        
        # 파일명에 사용할 수 없는 문자 제거
        safe_title = ''.join(c if c.isalnum() or c in ' .-_' else '_' for c in report['title'])
        
        # PDF 파일 경로에서 원본 파일명 추출 (옵션)
        original_filename = os.path.basename(report['pdf_path'])
        filename = f"{date_str}_{safe_title}_{original_filename}"
        filepath = os.path.join(download_dir, filename)
        
        # PDF 파일 다운로드
        pdf_response = session.get(pdf_url, stream=True)
        pdf_response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in pdf_response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"리포트 다운로드 완료: {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"리포트 다운로드 실패: {report['title']} - {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """
    메인 함수 - 모든 페이지의 리포트를 날짜별로 크롤링
    """
    try:
        logger.info("아이엠증권 리서치 리포트 크롤링 시작")
        
        # 1. 시작 페이지부터 모든 페이지 순회
        page = 1
        max_pages = 20  # 안전장치: 최대 페이지 수 제한
        all_reports = []
        
        while page <= max_pages:
            reports = get_report_list(page)
            
            if not reports:
                logger.info(f"페이지 {page}에서 리포트가 없거나 마지막 페이지에 도달")
                break
            
            all_reports.extend(reports)
            logger.info(f"현재까지 총 {len(all_reports)}개 리포트 항목 수집")
            
            # 다음 페이지로 이동
            page += 1
            
            # 서버 부하 방지를 위한 대기
            time.sleep(random.uniform(1.5, 3.0))
        
        # 리포트가 없는 경우
        if not all_reports:
            logger.warning("수집된 리포트가 없습니다. 웹사이트 구조를 확인하세요.")
            return
        
        # 2. 날짜별로 리포트 정렬
        def get_date_for_sorting(report):
            try:
                date_str = report['date']
                
                # 날짜 형식 분석 (YYYY/MM/DD)
                date_match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
                if date_match:
                    year = int(date_match.group(1))
                    month = int(date_match.group(2))
                    day = int(date_match.group(3))
                    return datetime.datetime(year, month, day)
                
                return datetime.datetime(1900, 1, 1)  # 날짜 파싱 실패 시 가장 오래된 날짜로
            except:
                return datetime.datetime(1900, 1, 1)
                
        all_reports.sort(key=get_date_for_sorting, reverse=True)  # 최신순 정렬
        
        # 3. 정렬된 리포트 목록을 파일로 저장
        report_list_file = os.path.join(download_dir, "report_list.txt")
        with open(report_list_file, 'w', encoding='utf-8') as f:
            for report in all_reports:
                f.write(f"{report['date']} - {report['title']} - {os.path.basename(report['pdf_path'])}\n")
        
        # JSON 형식으로도 저장
        report_list_json = os.path.join(download_dir, "report_list.json")
        with open(report_list_json, 'w', encoding='utf-8') as f:
            json.dump(all_reports, f, ensure_ascii=False, indent=2)
        
        logger.info(f"리포트 목록 파일 저장 완료: {report_list_file}, {report_list_json}")
        
        # 4. 각 리포트 다운로드
        download_count = 0
        for report in all_reports:
            if download_report(report):
                download_count += 1
            
            # 서버 부하 방지를 위한 대기
            time.sleep(random.uniform(1.0, 2.0))
        
        logger.info(f"총 {download_count}/{len(all_reports)}개 리포트 다운로드 완료")
        
    except Exception as e:
        logger.error(f"크롤링 중 예상치 못한 오류 발생: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        logger.info("아이엠증권 리서치 리포트 크롤링 종료")

if __name__ == "__main__":
    main()
