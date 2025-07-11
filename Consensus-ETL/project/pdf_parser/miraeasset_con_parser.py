import os
import pdfplumber
import pandas as pd
import re
import time
import easyocr
import difflib

def parse_filename(filename):
    result = {}
    base = os.path.basename(filename)
    # 종목명
    m = re.match(r'^\d{4}-\d{2}-\d{2}_(.+?)\s*\(', base)
    if m:
        result['종목명'] = m.group(1).strip()
    # 종목코드, 투자의견
    m = re.search(r'\((\d{5,6})_ ?(매수|매도|중립|Not Rated)\)', base)
    if m:
        result['종목코드'] = m.group(1)
        result['투자의견'] = m.group(2)
    # 애널리스트
    m = re.search(r'_([^_]+)_미래에셋증권', base)
    if m:
        name_block = m.group(1).strip()
        if '외' in name_block:
            result['애널리스트 이름'] = name_block[:3]
        else:
            result['애널리스트 이름'] = name_block
    return result

def extract_opinion_from_filename(filename):
    base = os.path.basename(filename)
    m = re.search(r'\((\d{5,6})_ ?(매수|매도|중립|Not Rated)\)', base)
    if m:
        return m.group(2)
    m2 = re.search(r'_(매수|매도|중립|Not Rated)[\)\._ ]', base)
    if m2:
        return m2.group(1)
    return ''


def parse_plumber_text(text):
    result = {
        '리포트생성날짜': '', '분야': '', '컨센서스 제목': '', '목표주가': '',
        '현재주가': '', '상승여력': ''
    }
    if filename:
        opinion = extract_opinion_from_filename(filename)
        if opinion:
            result['투자의견'] = opinion

    m = re.search(r'(\d{5,6})\s*[·•]\s*([가-힣A-Za-z\/&]+)', text)
    if m:
        result['종목코드'] = m.group(1)
        result['분야'] = m.group(2)
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if result.get('종목코드') and result['종목코드'] in line:
            if i+1 < len(lines):
                result['종목명'] = lines[i+1].strip()
            if i+2 < len(lines):
                result['컨센서스 제목'] = lines[i+2].strip()
            break
    m = re.search(r'(\d{4}\.\d{1,2}\.\d{1,2})', text)
    if m:
        result['리포트생성날짜'] = m.group(1).replace('.', '-')
    m = re.search(r'투자의견[^\n]*(매수|매도|중립|Not Rated)', text)
    if not result['투자의견']:
        m = re.search(r'투자의견[^\n]*(매수|매도|중립|Not Rated)', text)
        if m:
            result['투자의견'] = m.group(1)
            
    m = re.search(r'목표주가[^\d\-]*([-\d,]+)원', text)
    if m:
        val = m.group(1).replace(',', '')
        if val and val != '-':
            result['목표주가'] = f"{int(val):,}원"
    m = re.search(r'현재주가[^(]*\([^)]+\)\s*([,\d]+)원', text)
    if m:
        result['현재주가'] = m.group(1) + "원"
    m = re.search(r'상승여력\s*([+-]?\d+\.?\d*)%', text)
    if m:
        result['상승여력'] = m.group(1) + '%'
    return result

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
    result = {
        '리포트생성날짜': '', '분야': '', '컨센서스 제목': '',
        '목표주가': '', '현재주가': '', '상승여력': ''
    }
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    m = re.search(r'(\d{4}\.\d{1,2}\.\d{1,2})', text)
    if m:
        result['리포트생성날짜'] = m.group(1).replace('.', '-')
    if lines:
        m = re.match(r'(\d{5,6})\s+([가-힣A-Za-z\/&]+)', lines[0])
        if m:
            result['분야'] = m.group(2)

    if lines and file_stock_name:
        first_line = lines[0]
        idx = first_line.find(file_stock_name[-1])
        if idx != -1:
            title_start = idx + 1
            while title_start < len(first_line) and first_line[title_start] == ' ':
                title_start += 1
            result['컨센서스 제목'] = first_line[title_start:].strip()
        # 2차: 빈 문자열이면 유사도 기반 적용
        if not result['컨센서스 제목']:
            result['컨센서스 제목'] = get_title_by_fuzzy_match(first_line, file_stock_name, min_ratio=0.6)
            
    m = re.search(r'목표주가[^\d\-]*([-\d,]+)원', text)
    if m:
        val = m.group(1).replace(',', '')
        if val and val != '-':
            result['목표주가'] = f"{int(val):,}원"
    for i, line in enumerate(lines):
        if '상승여력' in line:
            m1 = re.search(r'([+-]?\d+\.?\d*)\s*%', line)
            if m1:
                result['상승여력'] = m1.group(1) + '%'
            if not result['현재주가'] and i > 0:
                prev_line = lines[i-1]
                m2 = re.search(r'([,\d]+)\s*원', prev_line)
                if m2:
                    result['현재주가'] = m2.group(1) + "원"
            break
    return result

# ---- 메인 루프 ----
pdf_dir = '../consensus/miraeasset_consensus'
results = []
reader = easyocr.Reader(['ko', 'en'])
pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
total = len(pdf_files)
total_start = time.time()

for idx, filename in enumerate(pdf_files, 1):
    file_start = time.time()
    pdf_path = os.path.join(pdf_dir, filename)
    # 1. 파일명 정보로 result를 우선 생성
    result = {
        '리포트생성날짜': '',
        '종목코드': '',
        '분야': '',
        '종목명': '',
        '컨센서스 제목': '',
        '투자의견': '',
        '목표주가': '',
        '현재주가': '',
        '상승여력': '',
        '애널리스트 이름': ''
    }
    filename_info = parse_filename(filename)
    for k, v in filename_info.items():
        result[k] = v

    # 2. plumber 텍스트 기반 값 보완
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        plumber_text = page.extract_text()
    plumber_result = parse_plumber_text(plumber_text if plumber_text else "")
    for k, v in plumber_result.items():
        if v: result[k] = v

    # 3. plumber로 '리포트생성날짜' 없으면 easyocr
    if not result['리포트생성날짜']:
        with pdfplumber.open(pdf_path) as pdf:
            pil_image = pdf.pages[0].to_image(resolution=300).original
            pil_image.save('temp.png')
            ocr_text = '\n'.join(reader.readtext('temp.png', detail=0, paragraph=True))
            os.remove('temp.png')
        ocr_result = parse_easyocr_text(ocr_text, file_stock_name=result['종목명'])
        for k, v in ocr_result.items():
            if v: result[k] = v

    results.append(result)
    file_end = time.time()
    print(f"[{idx}/{total}] {filename}: {file_end-file_start:.2f}초")

total_end = time.time()
print(f"\n전체 파싱 완료! ({total_end-total_start:.1f}초, {total}개 파일)")

df = pd.DataFrame(results)
output_dir = '../consensus_csv'
output_path = os.path.join(output_dir, 'miraeasset_consensus_reports.csv')
df.to_csv(output_path, index=False, encoding='utf-8-sig')
print(f"csv 파일 저장 완료: {output_path}")

