
import requests
from bs4 import BeautifulSoup
import os
import logging
import datetime
import time
import random
import re
import sys
import tempfile
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


def is_complete_pdf(filepath):
    """완료된 PDF인지 최소한의 구조를 확인한다."""
    try:
        if os.path.getsize(filepath) < 1024:
            return False
        with open(filepath, 'rb') as f:
            if f.read(5) != b'%PDF-':
                return False
            f.seek(max(0, os.path.getsize(filepath) - 4096))
            return b'%%EOF' in f.read()
    except OSError:
        return False


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

# 목록 페이지 custom 폼의 기본값 (첫 요청 시 채워진다)
_list_form_defaults = None


def _extract_form_defaults(soup):
    """목록 페이지 custom 폼의 hidden input 기본값 추출"""
    form = soup.find('form', attrs={'name': 'custom'})
    if not form:
        return None
    return {
        inp.get('name'): (inp.get('value') or '')
        for inp in form.find_all('input') if inp.get('name')
    }


def fetch_list_page(page):
    """
    목록 페이지 HTML을 가져와 BeautifulSoup으로 반환.

    페이지 이동은 쿼리스트링이 아니라 custom 폼 POST로 이루어진다
    (page() 자바스크립트가 cur_page를 채우고 f.submit() 한다).
    GET ?page=N 은 서버가 무시하고 항상 1페이지를 돌려주므로 사용하면 안 된다.
    """
    global _list_form_defaults

    # 1페이지이거나 폼 기본값을 아직 모르면 GET으로 시작
    if page <= 1 or _list_form_defaults is None:
        response = session.get(report_list_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        _list_form_defaults = _extract_form_defaults(soup)

        if page <= 1:
            return soup
        if _list_form_defaults is None:
            logger.warning("목록 폼(custom)을 찾지 못해 페이지 이동 불가")
            return soup

    form_data = dict(_list_form_defaults)
    form_data['cur_page'] = str(page)

    response = session.post(
        f"{report_list_url}?bid={form_data.get('bid', '')}",
        data=form_data,
        headers={'Referer': report_list_url},
        timeout=30,
    )
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')


def get_report_list(page=1):
    """
    특정 페이지의 리포트 목록을 가져오는 함수
    구조 분석 결과에 맞게 수정
    """
    try:
        logger.info(f"페이지 {page} 리포트 목록 가져오기 시작")

        soup = fetch_list_page(page)

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
        raise

def download_report(report):
    """
    리포트 PDF 파일 다운로드 함수
    """
    if not report.get('pdf_url'):
        logger.warning(f"PDF URL이 없음: {report['title']}")
        return False
    
    try:
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

        # 완전히 받은 리포트만 건너뛴다. 이전 실행이 남긴 부분 파일은 다시 받는다.
        if os.path.exists(filepath) and is_complete_pdf(filepath):
            logger.info(f"이미 존재하는 파일 건너뛰기: {filename}")
            return None
        if os.path.exists(filepath):
            logger.warning(f"불완전한 기존 파일을 다시 다운로드합니다: {filename}")

        logger.info(f"리포트 다운로드 시작: {report['title']}")

        # 같은 디렉토리의 임시 파일에 기록한 뒤 검증과 원자적 교체를 수행한다.
        # 연결이 끊겨도 최종 경로에는 부분 PDF가 남지 않는다.
        temp_fd, temp_filepath = tempfile.mkstemp(
            prefix=".im_report_",
            suffix=".part",
            dir=download_dir,
        )
        os.close(temp_fd)
        try:
            with session.get(pdf_url, stream=True, timeout=(10, 60)) as pdf_response:
                pdf_response.raise_for_status()

                with open(temp_filepath, 'wb') as f:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())

            if not is_complete_pdf(temp_filepath):
                raise ValueError("다운로드 결과가 완전한 PDF가 아닙니다.")

            os.replace(temp_filepath, filepath)
        finally:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
        
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
        # 일 1회 실행 기준 증분 수집 (1페이지 = 20건, 최근 며칠치를 충분히 덮는다).
        # 과거분 백필이 필요하면 이 값을 임시로 올려서 별도 실행할 것.
        max_pages = 5
        all_reports = []
        
        seen_pdf_urls = set()

        while page <= max_pages:
            reports = get_report_list(page)

            if not reports:
                logger.info(f"페이지 {page}에서 리포트가 없거나 마지막 페이지에 도달")
                break

            # 같은 리포트를 여러 번 받는 경우 방지 (페이지 이동 실패 시 안전장치)
            new_reports = [r for r in reports if r['pdf_url'] not in seen_pdf_urls]
            seen_pdf_urls.update(r['pdf_url'] for r in new_reports)

            if not new_reports:
                logger.info(f"페이지 {page}가 이전 페이지와 동일 - 수집 종료")
                break

            all_reports.extend(new_reports)
            logger.info(f"현재까지 총 {len(all_reports)}개 리포트 항목 수집")
            
            # 다음 페이지로 이동
            page += 1
            
            # 서버 부하 방지를 위한 대기
            time.sleep(random.uniform(1.5, 3.0))
        
        # 리포트가 없는 경우
        if not all_reports:
            logger.warning("수집된 리포트가 없습니다. 웹사이트 구조를 확인하세요.")
            return 1
        
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
        
        # 기존 목록과 합쳐 최근 5페이지 수집이 과거 manifest를 축소하지 않게 한다.
        report_list_json = os.path.join(download_dir, "report_list.json")
        manifest_reports = list(all_reports)
        manifest_urls = {report['pdf_url'] for report in manifest_reports}
        if os.path.exists(report_list_json):
            try:
                with open(report_list_json, 'r', encoding='utf-8') as f:
                    previous_reports = json.load(f)
                if not isinstance(previous_reports, list):
                    raise ValueError("기존 JSON의 최상위 값이 목록이 아닙니다.")
                for report in previous_reports:
                    if not isinstance(report, dict):
                        continue
                    pdf_url = report.get('pdf_url')
                    if pdf_url and pdf_url not in manifest_urls:
                        manifest_reports.append(report)
                        manifest_urls.add(pdf_url)
            except (OSError, ValueError, TypeError) as e:
                logger.warning(f"기존 리포트 목록을 읽지 못해 새 목록으로 교체합니다: {e}")

        # 3. 정렬된 리포트 목록을 파일로 저장
        report_list_file = os.path.join(download_dir, "report_list.txt")
        with open(report_list_file, 'w', encoding='utf-8') as f:
            for report in manifest_reports:
                f.write(f"{report['date']} - {report['title']} - {os.path.basename(report['pdf_path'])}\n")
        
        # JSON 형식으로도 저장
        with open(report_list_json, 'w', encoding='utf-8') as f:
            json.dump(manifest_reports, f, ensure_ascii=False, indent=2)
        
        logger.info(f"리포트 목록 파일 저장 완료: {report_list_file}, {report_list_json}")
        
        # 4. 각 리포트 다운로드
        download_count = 0
        failed_count = 0
        for report in all_reports:
            result = download_report(report)
            if result is None:
                continue
            if result:
                download_count += 1
            else:
                failed_count += 1

            # 서버 부하 방지를 위한 대기
            time.sleep(random.uniform(1.0, 2.0))
        
        logger.info(f"총 {download_count}/{len(all_reports)}개 리포트 다운로드 완료")
        if failed_count:
            raise RuntimeError(f"{failed_count}개 리포트 다운로드 실패")
        return 0
        
    except Exception as e:
        logger.error(f"크롤링 중 예상치 못한 오류 발생: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    finally:
        logger.info("아이엠증권 리서치 리포트 크롤링 종료")

if __name__ == "__main__":
    sys.exit(main())
