
import requests
from bs4 import BeautifulSoup
import os
import sys
import time
from urllib.parse import urljoin

# 유진투자증권 기업분석 리포트 페이지 URL
#
# 주의: 이 페이지는 현재 로그인 페이지(lo10r.do)로 리다이렉트되어 비로그인 수집이 불가능하다.
#       PC 신버전(www.eugenefn.com/ingo/igii/igii400.do)의 목록도 서버 오류를 반환한다.
#       유진투자증권 리포트는 한경컨센서스 크롤러(hk_con_crawler.py)가 이미 수집하고 있으므로
#       계정을 확보해 로그인 처리를 붙이거나, DAG에서 이 크롤러를 제외하는 것을 검토할 것.
url = "https://m.eugenefn.com/ii30r.do"

# 저장할 디렉토리 생성 (project/consensus/yj)
project_root = os.path.join(os.path.dirname(__file__), "..", "..")  # project 폴더로 이동
save_dir = os.path.join(project_root, "project", "consensus", "yj")
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# 세션 생성 (쿠키 및 헤더 유지)
session = requests.Session()

# User-Agent 설정 (서버가 정상적인 브라우저로 인식하도록)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

# 메인 페이지 접속
response = session.get(url, headers=headers, timeout=30)
response.raise_for_status()  # 오류 발생 시 예외 발생

# HTML 파싱
soup = BeautifulSoup(response.text, "html.parser")

# PDF 링크 추출
pdf_links = []
for link in soup.find_all("a", href=True):
    href = link["href"]
    if href.endswith(".pdf") and "amail" in href:
        # 상대 URL을 절대 URL로 변환
        full_url = urljoin("https://www.eugenefn.com/", href)
        pdf_links.append((link.text.strip(), full_url))

print(f"총 {len(pdf_links)}개의 PDF 파일을 찾았습니다.")

# 링크를 하나도 찾지 못하면 조용히 성공하지 말고 실패로 끝낸다.
# (예전에는 0건이어도 exit 0이라 DAG가 계속 성공으로 집계했다)
if not pdf_links:
    print(
        "PDF 링크를 찾지 못했습니다. 로그인 페이지로 리다이렉트되었을 가능성이 높습니다. "
        f"확인 URL: {response.url}",
        file=sys.stderr,
    )
    sys.exit(1)

# PDF 파일 다운로드
failed_downloads = 0
for idx, (title, pdf_url) in enumerate(pdf_links, 1):
    try:
        print(f"[{idx}/{len(pdf_links)}] 다운로드 중: {title}")
        
        # PDF 파일 요청
        pdf_response = session.get(pdf_url, headers=headers, timeout=30)
        pdf_response.raise_for_status()
        
        # 파일명 생성 (URL에서 추출)
        filename = pdf_url.split("/")[-1]
        
        # 파일 저장
        filepath = os.path.join(save_dir, filename)
        with open(filepath, "wb") as f:
            f.write(pdf_response.content)
        
        print(f"  → 저장 완료: {filepath}")
        
        # 서버 부하 방지를 위한 딜레이
        time.sleep(1)
        
    except Exception as e:
        print(f"  → 오류 발생: {e}")
        failed_downloads += 1

if failed_downloads:
    print(
        f"{failed_downloads}/{len(pdf_links)}개 PDF 다운로드에 실패했습니다.",
        file=sys.stderr,
    )
    sys.exit(1)

print("모든 PDF 다운로드 완료!")
