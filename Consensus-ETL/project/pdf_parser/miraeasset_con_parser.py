import os
import pdfplumber
import pandas as pd
import re
import time
import easyocr
import difflib

# -------------------------------
# 파일명 기반 정보 추출
# -------------------------------
def parse_filename(filename):
    result = {}
    base = os.path.basename(filename)
    # 종목명
    m = re.match(r'^\d{4}-\d{2}-\d{2}_(.+?)\s*\(', base)
    if m:
        result['stock_name'] = m.group(1).strip()
    # 종목코드, 투자의견
    m = re.search(r'\((\d{5,6})_ ?(매수|매도|중립|Not Rated)\)', base)
    if m:
        result['stock_code'] = m.group(1)
        result['rating'] = m.group(2)
    # 애널리스트 이름
    m = re.search(r'_([^_]+)_미래에셋증권', base)
    if m:
        name_block = m.group(1).strip()
        if '외' in name_block:
            result['analyst_name'] = name_block[:3]
        else:
            result['analyst_name'] = name_block
    return result

# -------------------------------
# plumber 기반 텍스트 파싱
# -------------------------------
def parse_plumber_text(text):
    result = {}
    # 날짜
    m = re.search(r'(\d{4}\.\d{1,2}\.\d{1,2})', text)
    if m:
        result['report_date'] = m.group(1).replace('.', '-')
    # 종목코드 / 분야
    m = re.search(r'(\d{5,6})\s*[·•]\s*([가-힣A-Za-z\/&]+)', text)
    if m:
        result['stock_code'] = m.group(1)
        result['report_type'] = m.group(2)
    # 제목
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if result.get('stock_code') and result['stock_code'] in line:
            if i+2 < len(lines):
                result['report_title'] = lines[i+2].strip()
            break
    # 투자의견
    m = re.search(r'투자의견[^\n]*(매수|매도|중립|Not Rated)', text)
    if m:
        result['rating'] = m.group(1)
    # 투자의견 변화
    m = re.search(r'투자의견\s*\((상향|하향|유지)\)', text)
    if m:
        result['opinion_change'] = m.group(1)
    # 목표주가
    m = re.search(r'목표주가[^\d\-]*([-\d,]+)원', text)
    if m:
        val = m.group(1).replace(',', '')
        if val and val != '-':
            result['target_price'] = f"{int(val):,}원"
    # 목표주가 변화
    m = re.search(r'목표주가[^\n]*(상향|하향)\s*\(([^)]+)\)', text)
    if m:
        result['target_price_change'] = m.group(2)
    # 현재주가
    m = re.search(r'현재주가[^(]*\([^)]+\)\s*([,\d]+)원', text)
    if m:
        result['현재주가'] = m.group(1) + "원"
    # 투자 근거
    m = re.search(r'(투자\s*포인트|투자\s*근거|Investment\s*Rationale)\s*:?(.+)', text)
    if m:
        result['investment_rationale'] = m.group(2).strip()
    return result

# -------------------------------
# EasyOCR 보완 파싱
# -------------------------------
def get_title_by_fuzzy_match(first_line, file_stock_name, min_ratio=0.6):
    n = len(file_stock_name)
    best_ratio = 0
    best_idx = -1
    for i in range(len(first_line) - n + 1):
        candidate = first_line[i:i+n]
        ratio = difflib.SequenceMatcher(None, candidate, file_stock_name).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_idx = i
    if best_ratio >= min_ratio and best_idx != -1:
        title_start = best_idx + n
        while title_start < len(first_line) and first_line[title_start] == ' ':
            title_start += 1
        return first_line[title_start:].strip()
    return ""

def parse_easyocr_text(text, file_stock_name=""):
    result = {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    # 날짜
    m = re.search(r'(\d{4}\.\d{1,2}\.\d{1,2})', text)
    if m:
        result['report_date'] = m.group(1).replace('.', '-')
    # 분야
    if lines:
        m = re.match(r'(\d{5,6})\s+([가-힣A-Za-z\/&]+)', lines[0])
        if m:
            result['report_type'] = m.group(2)
    # 제목
    if lines and file_stock_name:
        first_line = lines[0]
        result['report_title'] = get_title_by_fuzzy_match(first_line, file_stock_name)
    # 목표주가
    m = re.search(r'목표주가[^\d\-]*([-\d,]+)원', text)
    if m:
        val = m.group(1).replace(',', '')
        if val and val != '-':
            result['target_price'] = f"{int(val):,}원"
    # 상승여력
    m = re.search(r'상승여력\s*([+-]?\d+\.?\d*)%', text)
    if m:
        result['상승여력'] = m.group(1) + '%'
    return result

# -------------------------------
# 메인 처리
# -------------------------------
pdf_dir = '../consensus/miraeasset'
results = []
reader = easyocr.Reader(['ko', 'en'])
pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
total = len(pdf_files)
total_start = time.time()

for idx, filename in enumerate(pdf_files, 1):
    file_start = time.time()
    pdf_path = os.path.join(pdf_dir, filename)

    # 초기 result
    result = {
        'stock_code': '',
        'stock_name': '',
        'report_title': '',
        'report_date': '',
        'report_type': '',
        'analyst_name': '',
        'company_name': '미래에셋증권',
        'rating': '',
        'opinion_change': '',
        'target_price': '',
        'target_price_change': '',
        'investment_rationale': ''
    }

    # 1. 파일명 기반 추출
    filename_info = parse_filename(filename)
    result.update({k: v for k, v in filename_info.items() if v})

    # 2. pdfplumber 파싱
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        plumber_text = page.extract_text() or ""
    plumber_result = parse_plumber_text(plumber_text)
    result.update({k: v for k, v in plumber_result.items() if v})

    # 3. 보완: EasyOCR
    if not result['report_date']:
        with pdfplumber.open(pdf_path) as pdf:
            pil_image = pdf.pages[0].to_image(resolution=300).original
            pil_image.save('temp.png')
            ocr_text = '\n'.join(reader.readtext('temp.png', detail=0, paragraph=True))
            os.remove('temp.png')
        ocr_result = parse_easyocr_text(ocr_text, file_stock_name=result.get('stock_name', ''))
        result.update({k: v for k, v in ocr_result.items() if v})

    results.append(result)
    print(f"[{idx}/{total}] {filename} 처리 완료 ({time.time()-file_start:.2f}초)")

# -------------------------------
# CSV 저장
# -------------------------------
output_dir = '../consensus_csv'
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, 'miraeasset_consensus_reports.csv')
df = pd.DataFrame(results)
df.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"\n전체 파싱 완료! ({time.time()-total_start:.1f}초, {total}개 파일)")
print(f"CSV 저장: {output_path}")
