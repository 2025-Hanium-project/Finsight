
import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin

# 유진투자증권 기업분석 리포트 페이지 URL
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
response = session.get(url, headers=headers)
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

# PDF 파일 다운로드
for idx, (title, pdf_url) in enumerate(pdf_links, 1):
    try:
        print(f"[{idx}/{len(pdf_links)}] 다운로드 중: {title}")
        
        # PDF 파일 요청
        pdf_response = session.get(pdf_url, headers=headers)
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

print("모든 PDF 다운로드 완료!")
