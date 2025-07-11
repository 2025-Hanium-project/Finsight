import os
import pdfplumber
import pandas as pd
import re
import time
import glob
import easyocr

def parse_daishin_page1_text(text, filename=None):
    result = {
        '리포트생성날짜': '',
        '종목코드': '',
        '분야': '',
        '종목명': '',
        '컨센서스 제목': '',
        '투자의견': '',
        '목표주가': '',
        '현재주가': '',
        '애널리스트 이름': ''
    }
    # 1. 파일명에서 날짜, 종목명 추출
    if filename:
        base = os.path.basename(filename)
        # 날짜
        m_date = re.match(r'^(\d{4}-\d{2}-\d{2})_', base)
        if m_date:
            result['리포트생성날짜'] = m_date.group(1)
        # 종목명
        m_name = re.match(r'^\d{4}-\d{2}-\d{2}_(.+?)\.pdf', base)
        if m_name:
            result['종목명'] = m_name.group(1).strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # 2. 본문에서 날짜(파일명에 없으면만)
    if not result['리포트생성날짜']:
        m = re.search(r'(\d{4})[./\-](\d{1,2})[./\-](\d{1,2})', text)
        if m:
            result['리포트생성날짜'] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    # 3. 나머지 항목
    m = re.search(r'([0-9]{2,6})', text)
    if m:
        result['종목코드'] = m.group(1).zfill(6)
    m = re.search(r'BUY|매수|중립|비중확대|비중유지|매도|Not Rated|Buy|Overweight|Neutral|Reduce|Sell|Marketperform|N.R', text, re.I)
    if m:
        result['투자의견'] = m.group(0).upper()
    m = re.search(r'목표주가[^\d\-]*([-\d,]+)원', text)
    if not m:
        m = re.search(r'목표주가\s*([-\d,]+)', text)
    if not m:
        m = re.search(r'Target Price[^\d\-]*([-\d,]+)', text, re.I)
    if m:
        val = m.group(1).replace(',', '')
        if val and val != '-':
            result['목표주가'] = f"{int(val):,}원"
    m = re.search(r'현재주가[^\d\-]*([-\d,]+)원', text)
    if not m:
        m = re.search(r'현재주가\s*([-\d,]+)', text)
    if not m:
        m = re.search(r'Current Price[^\d\-]*([-\d,]+)', text, re.I)
    if m:
        val = m.group(1).replace(',', '')
        if val and val != '-':
            result['현재주가'] = f"{int(val):,}원"
    m = re.search(r'([가-힣]{2,4})\s+[A-Za-z0-9._%+-]+@daishin\.com', text)
    if m:
        result['애널리스트 이름'] = m.group(1)
    for line in lines:
        if '업종' in line:
            m = re.search(r'([가-힣A-Za-z]+)업종', line)
            if m:
                result['분야'] = m.group(1) + "업종"
            else:
                result['분야'] = "업종"
            break
    for line in lines[:8]:
        if not result['컨센서스 제목'] and len(line) > 10 and ("후기" in line or "분석" in line):
            result['컨센서스 제목'] = line.strip()
    if not result['컨센서스 제목'] and lines:
        if len(lines) > 2:
            result['컨센서스 제목'] = lines[1]
    return result

# ---- 메인 루프 ----
pdf_dir = '../consensus/daishin'
pdf_files = sorted(glob.glob(os.path.join(pdf_dir, '*.pdf')))
results = []

for idx, pdf_path in enumerate(pdf_files, 1):
    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]
        page1_text = first_page.extract_text() or ""

    # "투자의견"이 포함되어 있으면 파싱
    if "투자의견" in page1_text:
        parsed = parse_daishin_page1_text(page1_text, filename=pdf_path)
        if parsed is not None:
            results.append(parsed)
        print(f"[{idx}] {os.path.basename(pdf_path)}: 파싱 완료")
    else:
        print(f"[{idx}] {os.path.basename(pdf_path)}: '투자의견' 없음, 패스")

# DataFrame & CSV 저장
if results:
    df = pd.DataFrame(results)
    os.makedirs('../consensus_csv', exist_ok=True)
    df.to_csv('../consensus_csv/daishin_consensus_reports.csv', index=False, encoding='utf-8-sig')
    print("csv 파일 저장 완료: daishin_consensus_reports.csv")
else:
    print("파싱 결과가 없습니다.")