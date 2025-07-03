# import PyPDF2
import pdfplumber
import pandas as pd
import re
import uuid
from datetime import datetime
import os
import logging
logging.getLogger("pdfminer").setLevel(logging.ERROR)

class KiwoomConsensusParser:
    def __init__(self):
        self.data_list = []
        
    def extract_text_from_pdf(self, pdf_path):
        """PDF에서 텍스트 추출"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"PDF 읽기 오류: {e}")
            return None
        # 디버깅용 출력
        # print(text[:1000])
        return text
    
    def parse_stock_info(self, text):
        """주식 정보 파싱 (개선된 버전)"""
        print(f"\n=== 종목 정보 파싱 ===")
          # 종목명과 코드 추출 (괄호 안의 6자리 숫자)
        stock_patterns = [
            r'([가-힣A-Za-z\s&]+)\s*\((\d{6})\)',  # "SK이노베이션 (096770)" 형태
            r'\((\d{6})\)\s*([가-힣A-Za-z\s&]+)',  # "(096770) SK이노베이션" 형태
        ]
        
        stock_name = None
        stock_code = None
        
        for i, pattern in enumerate(stock_patterns):
            match = re.search(pattern, text)
            if match:
                if i == 0:  # 첫 번째 패턴: 종목명 (코드)
                    stock_name = match.group(1).strip()
                    stock_code = match.group(2)  # 문자열로 유지
                else:  # 두 번째 패턴: (코드) 종목명
                    stock_code = match.group(1)  # 문자열로 유지
                    stock_name = match.group(2).strip()
                  # 종목명 정리 - 더 강화된 버전
                if stock_name:
                    # "Not Rated" 제거 (앞뒤 공백 포함)
                    stock_name = re.sub(r'\s*Not\s+Rated\s*', ' ', stock_name, flags=re.IGNORECASE)
                    # 줄바꿈 문자 제거
                    stock_name = re.sub(r'[\n\r]+', ' ', stock_name)
                    # 분석가 관련 단어 제거
                    stock_name = re.sub(r'(Analyst|애널리스트|연구원|스몰캡)', '', stock_name, flags=re.IGNORECASE)
                    # 투자의견 제거
                    stock_name = re.sub(r'(BUY|SELL|HOLD|매수|매도|중립)', '', stock_name, flags=re.IGNORECASE)
                    # 기타 불필요한 텍스트 제거
                    stock_name = re.sub(r'(주식회사|㈜|\(주\))', '', stock_name, flags=re.IGNORECASE)
                    # 여러 공백을 하나로 정리하고 앞뒤 공백 제거
                    stock_name = re.sub(r'\s+', ' ', stock_name).strip()
        
                print(f"패턴 {i+1}에서 발견: {stock_name} ({stock_code})")
                break
    
        # 종목 정보를 찾지 못한 경우 줄별 검색
        if not stock_name or not stock_code:
            print("기본 패턴으로 찾지 못함. 줄별 검색...")
            lines = text.split('\n')
            
            for i, line in enumerate(lines[:15]):
                line = line.strip()
                print(f"줄 {i+1}: '{line}'")
                
                # 6자리 종목코드 찾기
                code_match = re.search(r'\((\d{6})\)', line)
                if code_match:
                    stock_code = code_match.group(1)  # 문자열로 유지 (007660 그대로)
                      # 같은 줄에서 종목명 찾기
                    line_without_code = re.sub(r'\(\d{6}\)', '', line).strip()
                    if line_without_code and len(line_without_code) > 1:                        # 날짜나 기타 정보 제거
                        clean_name = re.sub(r'\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}', '', line_without_code)
                        clean_name = re.sub(r'(BUY|SELL|HOLD|매수|매도|중립)', '', clean_name, flags=re.IGNORECASE)
                        # "Not Rated" 제거 (강화된 버전)
                        clean_name = re.sub(r'\s*Not\s+Rated\s*', ' ', clean_name, flags=re.IGNORECASE)
                        # 줄바꿈 문자 제거
                        clean_name = re.sub(r'[\n\r]+', ' ', clean_name)
                        # 증권사명 제거 (확장된 목록)
                        clean_name = re.sub(r'(삼성증권|키움증권|미래에셋증권|NH투자증권|한국투자증권|대신증권|하나증권|IBK투자증권|KB증권|신한투자증권)', '', clean_name, flags=re.IGNORECASE)
                        # 분석가 관련 단어 제거
                        clean_name = re.sub(r'(Analyst|애널리스트|연구원|스몰캡)', '', clean_name, flags=re.IGNORECASE)
                        # 기타 불필요한 텍스트 제거
                        clean_name = re.sub(r'(주식회사|㈜|\(주\))', '', clean_name, flags=re.IGNORECASE)
                        # 여러 공백을 하나로 정리
                        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
                        # 앞뒤 공백 및 특수문자 정리
                        clean_name = clean_name.strip(' \t\n\r')
                        
                        if clean_name and len(clean_name) >= 2:
                            stock_name = clean_name
                            print(f"✓ 발견: {stock_name} ({stock_code})")
                            break
    
        # 여전히 찾지 못한 경우 기본값
        if not stock_name:
            stock_name = "Unknown"
        if not stock_code:
            stock_code = "000000"  # 문자열로 기본값 설정
    
        print(f"최종 결과: {stock_name} ({stock_code})")
        return stock_name, stock_code
    
    def parse_price_info(self, text):
        """가격 정보 파싱"""
        print(f"\n=== 가격 정보 파싱 시작 ===")
        
        # 텍스트를 줄별로 분석
        lines = text.split('\n')
        print(f"첫 10줄에서 가격 정보 찾기:")
        for i, line in enumerate(lines[:10]):
            print(f"줄 {i+1}: '{line.strip()}'")
        
        # 목표가 추출 (더 구체적인 패턴 사용)
        target_price_patterns = [
            r'목표주가[:\s]*([0-9,]+)원?',
            r'Target Price[:\s]*([0-9,]+)원?',
            r'목표가[:\s]*([0-9,]+)원?',
            r'목표주가:\s*([0-9,]+)원?'
        ]
        
        target_price = None
        for i, pattern in enumerate(target_price_patterns):
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # 첫 번째 매치를 목표가로 사용
                target_price = int(matches[0].replace(',', ''))
                print(f"목표가 패턴 {i+1} '{pattern}' 매치: {matches}")
                print(f"✓ 목표가: {target_price:,}원")
                break
            else:
                print(f"목표가 패턴 {i+1} '{pattern}': 매치 없음")
        
        # 현재가 추출 (목표가와 다른 패턴 사용)
        current_price_patterns = [
            r'주가\(([^)]+)\)[:\s]*([0-9,]+)원?',  # "주가(5/15): 53,600원" 패턴
            r'현재가[:\s]*([0-9,]+)원?',
            r'기준가[:\s]*([0-9,]+)원?',
            r'주가[:\s]*([0-9,]+)원?(?!.*목표)',  # 목표가 아닌 주가
        ]
        
        current_price = None
        for i, pattern in enumerate(current_price_patterns):
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # 괄호 안에 날짜가 있는 경우 (예: 주가(5/15): 53,600원)
                    current_price = int(matches[0][1].replace(',', ''))
                    print(f"현재가 패턴 {i+1} '{pattern}' 매치: {matches}")
                    print(f"✓ 현재가 ({matches[0][0]}): {current_price:,}원")
                else:
                    current_price = int(matches[0].replace(',', ''))
                    print(f"현재가 패턴 {i+1} '{pattern}' 매치: {matches}")
                    print(f"✓ 현재가: {current_price:,}원")
                break
            else:
                print(f"현재가 패턴 {i+1} '{pattern}': 매치 없음")
        
        # 줄별로 분석해서 가격 정보 찾기 (fallback)
        if not target_price or not current_price:
            print(f"\n=== 줄별 가격 정보 분석 ===")
            for i, line in enumerate(lines[:15]):
                line = line.strip()
                if not line:
                    continue
                
                print(f"줄 {i+1}: '{line}'")
                
                # 목표주가 줄 찾기
                if '목표주가' in line and not target_price:
                    price_match = re.search(r'([0-9,]+)원?', line)
                    if price_match:
                        target_price = int(price_match.group(1).replace(',', ''))
                        print(f"  ✓ 목표주가 발견: {target_price:,}원")
                
                # 주가 줄 찾기 (목표주가가 아닌)
                if '주가(' in line and not current_price:
                    price_match = re.search(r'주가\([^)]+\):\s*([0-9,]+)원?', line)
                    if price_match:
                        current_price = int(price_match.group(1).replace(',', ''))
                        print(f"  ✓ 현재주가 발견: {current_price:,}원")
        
        # 수동으로 텍스트에서 특정 패턴 찾기 (최종 시도)
        if not target_price or not current_price:
            print(f"\n=== 수동 패턴 매칭 ===")
            
            # "목표주가: 70,000원" 형태 찾기
            target_match = re.search(r'목표주가[:\s]*([0-9,]+)', text)
            if target_match and not target_price:
                target_price = int(target_match.group(1).replace(',', ''))
                print(f"수동 매칭 - 목표주가: {target_price:,}원")
            
            # "주가(날짜): 금액" 형태 찾기
            current_match = re.search(r'주가\([^)]+\):\s*([0-9,]+)', text)
            if current_match and not current_price:
                current_price = int(current_match.group(1).replace(',', ''))
                print(f"수동 매칭 - 현재주가: {current_price:,}원")
        
        # 상승여력 계산
        upside_potential = None
        if current_price and target_price:
            upside_potential = round(((target_price - current_price) / current_price) * 100, 1)
            print(f"\n=== 상승여력 계산 ===")
            print(f"목표주가: {target_price:,}원")
            print(f"현재주가: {current_price:,}원")
            print(f"상승여력: {upside_potential}%")
        
        print(f"\n=== 가격 정보 파싱 결과 ===")
        print(f"현재가: {current_price:,}원" if current_price else "현재가: None")
        print(f"목표가: {target_price:,}원" if target_price else "목표가: None")
        print(f"상승여력: {upside_potential}%" if upside_potential else "상승여력: None")
        print("=" * 50)
        
        return current_price, target_price, upside_potential
    
    def parse_analyst_info(self, text, pdf_path=None):
        """애널리스트 정보 파싱 (extract_words 보조)"""
        print(f"\n=== 애널리스트 정보 파싱 시작 ===")
        analyst_patterns = [
            r'Analyst[\s\n:]*([가-힣]{2,4})',
            r'Analyst[\s\n:]*([가-힣]{2,4}),',
            r'Analyst[\s\n:]*([가-힣]{2,4})[ ,]',
            r'Analyst[\s\n:]*([가-힣]{2,4})[A-Za-z@]',
            r'A\s*n\s*a\s*l\s*y\s*s\s*t\s*([가-힣]{2,4})',  # "A nalyst" 처럼 공백이 중간에 있는 경우
            r'A\s*n\s*a\s*l\s*y\s*s\s*t\s*([가-힣]{2,4}),',  # "A nalyst 박상준," 패턴
            r'A\s*n\s*a\s*l\s*y\s*s\s*t\s*([가-힣]{2,4})\s*,\s*([A-Za-z]+)',  # "A nalyst 박상준, CFA" 패턴
            r'애널리스트[:\s]*([가-힣]{2,4})',
            r'작성자[:\s]*([가-힣]{2,4})',
            r'Research[:\s]*([가-힣]{2,4})',
            r'연구원[:\s]*([가-힣]{2,4})',
            r'([가-힣]{2,4})\s*애널리스트',
            r'([가-힣]{2,4})\s*연구원'
        ]
        analyst_name = None
        for i, pattern in enumerate(analyst_patterns):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                analyst_name = match.group(1)
                print(f"패턴 {i+1} '{pattern}'로 애널리스트 발견: '{analyst_name}'")
                break
            else:
                print(f"패턴 {i+1} '{pattern}': 매치 없음")
        
        # 특정 패턴 직접 검색 (예: "A nalyst 박상준, CFA" 패턴)
        if not analyst_name:
            special_match = re.search(r'A\s+nalyst\s+([가-힣]{2,4})', text)
            if special_match:
                analyst_name = special_match.group(1)
                print(f"특수 패턴 'A nalyst'로 애널리스트 발견: '{analyst_name}'")
        
        # extract_words()로 보조 추출
        if not analyst_name and pdf_path:
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    page = pdf.pages[0]
                    words = page.extract_words()
                    
                    # "A" 다음에 "nalyst"가 있고, 그 뒤에 한글 이름이 있는지 확인
                    for i, word in enumerate(words):
                        if i+2 < len(words) and word['text'] == 'A' and 'nalyst' in words[i+1]['text']:
                            if re.match(r'^[가-힣]{2,4}$', words[i+2]['text']):
                                analyst_name = words[i+2]['text']
                                print(f"extract_words()로 'A nalyst' 패턴에서 애널리스트 발견: '{analyst_name}'")
                                break
                        
                        # 일반 "Analyst" 패턴도 체크
                        if 'Analyst' in word['text']:
                            if i+1 < len(words) and re.match(r'^[가-힣]{2,4}$', words[i+1]['text']):
                                analyst_name = words[i+1]['text']
                                print(f"extract_words()로 'Analyst' 패턴에서 애널리스트 발견: '{analyst_name}'")
                                break
            except Exception as e:
                print(f"extract_words() 애널리스트 추출 오류: {e}")
        
        # 증권사명 추출
        print(f"\n=== 증권사명 추출 ===")
        company_patterns = [
            r'(삼성증권|키움증권|미래에셋증권|NH투자증권|한국투자증권|대신증권|하나증권|유진투자증권)',
            r'([가-힣]+증권)',
            r'(삼성|키움|미래에셋|NH투자|한국투자|대신|하나|유진투자)\s*증권?'
        ]
        
        company_name = None
        for i, pattern in enumerate(company_patterns):
            match = re.search(pattern, text)
            if match:
                company_name = match.group(1)
                if not company_name.endswith('증권'):
                    company_name += '증권'
                print(f"패턴 {i+1} '{pattern}'로 증권사 발견: '{company_name}'")
                break
            else:
                print(f"패턴 {i+1} '{pattern}': 매치 없음")
        
        # 텍스트 첫 부분에서 증권사 직접 검색
        if not company_name:
            print("기본 패턴으로 찾지 못함. 줄별 검색 시작...")
            lines = text.split('\n')
            for i, line in enumerate(lines[:10]):  # 처음 10줄에서 검색
                line = line.strip()
                print(f"줄 {i+1}: '{line}'")
                
                # 알려진 증권사명이 포함된 경우
                securities = ['삼성증권', '키움증권', '미래에셋증권', 'NH투자증권', '한국투자증권', 
                             '대신증권', '하나증권', '유진투자증권']
                for sec in securities:
                    if sec in line:
                        company_name = sec
                        print(f"✓ 줄에서 증권사 발견: '{company_name}'")
                        break
                if company_name:
                    break
        
        print(f"\n=== 애널리스트 정보 파싱 결과 ===")
        print(f"애널리스트: '{analyst_name}'")
        print(f"증권사: '{company_name}'")
        print("=" * 50)
        
        return analyst_name, company_name
    
    def parse_rating_info(self, text):
        """투자등급 정보 파싱 (개선된 버전)"""
        print(f"\n=== 투자등급 정보 파싱 ===")
        
        # 투자의견 추출 (줄별로 찾기)
        lines = text.split('\n')
        rating = None
        opinion_change = None
        
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            print(f"줄 {i+1}: '{line}'")
            
            # BUY, SELL 등이 포함된 줄에서 투자의견 추출
            if re.search(r'(BUY|SELL|HOLD|매수|매도|중립)', line, re.IGNORECASE):
                rating_match = re.search(r'(BUY|SELL|HOLD|매수|매도|중립)', line, re.IGNORECASE)
                if rating_match:
                    rating_text = rating_match.group(1).upper()
                    if rating_text in ['BUY', '매수']:
                        rating = '매수'
                    elif rating_text in ['SELL', '매도']:
                        rating = '매도'
                    elif rating_text in ['HOLD', '중립']:
                        rating = '중립'
                
                print(f"✓ 투자의견 발견: {rating}")
                
                # 같은 줄에서 의견변경 정보 찾기
                if 'Maintain' in line or '유지' in line:
                    opinion_change = '유지'
                elif '상향' in line or 'UP' in line.upper():
                    opinion_change = '상향'
                elif '하향' in line or 'DOWN' in line.upper():
                    opinion_change = '하향'
                elif '신규' in line or 'NEW' in line.upper():
                    opinion_change = '신규'
                else:
                    # 괄호 안의 정보에서 추출
                    change_match = re.search(r'\((Maintain|상향|하향|유지|신규)\)', line, re.IGNORECASE)
                    if change_match:
                        change_text = change_match.group(1)
                        if change_text.lower() == 'maintain' or change_text == '유지':
                            opinion_change = '유지'
                        else:
                            opinion_change = change_text
                
                if opinion_change:
                    print(f"✓ 의견변경 발견: {opinion_change}")
                break
        
        # 기본값 설정
        if not rating:
            rating = '매수'  # 기본값
        if not opinion_change:
            opinion_change = '유지'  # 기본값
        
        print(f"최종 결과: 투자의견={rating}, 의견변경={opinion_change}")
        return rating, opinion_change
    
    def extract_investment_rationale(self, pdf_path):
        """좌표 기반으로 투자 의견 근거 추출 (키움증권 리포트 전용)"""
        print(f"\n=== 투자 근거 추출 시작 (좌표 기반) ===")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[0]  # 첫 번째 페이지에서 추출
                
                # 페이지 크기 정보
                page_width = page.width
                page_height = page.height
                print(f"페이지 크기: {page_width} x {page_height}")
                
                # 키움증권 리포트의 투자 근거 영역 좌표 설정
                # GUI 도구로 확인한 정확한 좌표 사용: x=232, y=165부터 문서 끝까지
                rationale_bbox = (232, 165, page_width, page_height)  # (x0, y0, x1, y1)
                print(f"투자 근거 추출 영역: x={rationale_bbox[0]}~{rationale_bbox[2]}, y={rationale_bbox[1]}~{rationale_bbox[3]}")
                
                # 지정된 좌표 영역에서 텍스트 추출
                cropped_page = page.crop(rationale_bbox)
                rationale_text = cropped_page.extract_text()
                
                if rationale_text:
                    print(f"추출된 원본 텍스트 길이: {len(rationale_text)}")
                    print(f"원본 텍스트 미리보기:")
                    print("-" * 50)
                    print(rationale_text[:500])
                    print("-" * 50)
                    
                    # 텍스트 정리 및 필터링
                    cleaned_text = self.clean_rationale_text(rationale_text)
                    
                    if cleaned_text and len(cleaned_text) > 20:
                        print(f"\n=== 정리된 투자 근거 ===")
                        print(f"정리된 텍스트 길이: {len(cleaned_text)}")
                        print(f"정리된 내용 미리보기:")
                        print("-" * 50)
                        print(cleaned_text[:300])
                        if len(cleaned_text) > 300:
                            print("...")
                        print("-" * 50)
                        return cleaned_text
                    else:
                        print("정리 후 유효한 투자 근거가 없습니다.")
                        return None
                else:
                    print("지정된 좌표 영역에서 텍스트를 추출할 수 없습니다.")
                    return None
                    
        except Exception as e:
            print(f"투자 근거 추출 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def clean_rationale_text(self, text):
        """투자 근거 텍스트 정리 (키움증권 전용)"""
        if not text:
            return None
        
        # 기본 정리
        text = text.strip()
        
        # 줄바꿈을 공백으로 변경하되 단락 구분은 유지
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 연속된 줄바꿈은 단락 구분으로 유지
        text = re.sub(r'\n', ' ', text)  # 단일 줄바꿈은 공백으로
        text = re.sub(r'\s+', ' ', text)  # 연속된 공백을 하나로
        
        # 키움증권 리포트에서 불필요한 헤더/푸터 정보 제거
        unwanted_patterns = [
            r'키움증권.*?\d{4}\.\s*\d{1,2}\.\s*\d{1,2}',  # "키움증권 2025. 5. 16" 형태
            r'Analyst.*?CFA',  # 애널리스트 정보
            r'Stock Data.*?(?=\w)',  # Stock Data 섹션 시작 부분
            r'Company Data.*?(?=\w)',  # Company Data 섹션 시작 부분
            r'KOSPI\s+[\d,\.]+pt',  # KOSPI 지수 정보
            r'시가총액\s+[\d,]+억\s*원',  # 시가총액 정보
            r'\d+주\s+일평균\s+거래량',  # 거래량 정보
            r'최고가\s+최저가',  # 주가 정보 헤더
            r'[\d,]+원\s+[\d,]+원',  # 연속된 가격 정보
            r'발행주식수\s+[\d,]+천주',  # 발행주식수
            r'외국인\s+지분율\s+[\d\.]+%',  # 외국인 지분율
            r'배당수익률.*?[\d\.]+%',  # 배당수익률
            r'BPS.*?[\d,]+원',  # BPS 정보
        ]
        
        for pattern in unwanted_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # 연속된 숫자와 % 조합 정리 (재무 데이터)
        text = re.sub(r'\d+%\s*\(\s*YoY\s*\)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\d+%\s*\(\s*\w+\s*\)', '', text, flags=re.IGNORECASE)
        
        # 테이블 형태의 데이터 제거 (숫자와 단위가 반복되는 패턴)
        text = re.sub(r'(\d+[,\.]\d+\s*){3,}', ' ', text)
        text = re.sub(r'([\d,]+억\s*){2,}', ' ', text)
        
        # 특수 문자 정리 (한글, 영문, 숫자, 기본 문장부호만 유지)
        text = re.sub(r'[^\w\s가-힣.,!?()%-]', ' ', text)
        
        # 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 너무 짧은 텍스트 제외
        if len(text) < 20:
            return None
        
        # 의미 있는 투자 근거 문장이 포함되어 있는지 확인
        meaningful_keywords = [
            '매수', '투자', '성장', '실적', '수익', '영업', '매출', '이익',
            '전망', '예상', '기대', '개선', '증가', '상승', '긍정', '호조',
            '경쟁력', '시장', '사업', '부문', '확대', '기회', '잠재력'
        ]
        
        keyword_count = sum(1 for keyword in meaningful_keywords if keyword in text)
        if keyword_count < 2:  # 의미 있는 키워드가 2개 미만이면 제외
            return None
        
        # 최종 길이 체크
        if len(text) < 30:
            return None
        
        return text.strip()

    def extract_report_title_by_color(self, pdf_path):
        """Extract report title by joining all chars with the target color on the first page, grouped by y (top) position."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[0]
                target_color = (0.745, 0.38, 0.522)
                # 색상 일치하는 문자만 추출
                color_chars = [char for char in page.chars if char.get("non_stroking_color") == target_color]
                if not color_chars:
                    return None
                # y(top) 좌표별로 그룹화
                from collections import defaultdict
                lines = defaultdict(list)
                for char in color_chars:
                    y = round(char["top"], 1)  # y좌표를 반올림해서 같은 줄로 묶음
                    lines[y].append(char)
                # 각 줄을 x0 기준 정렬 후 텍스트로 합침
                line_texts = []
                for y, chars in lines.items():
                    sorted_chars = sorted(chars, key=lambda c: c["x0"])
                    text = "".join([c["text"] for c in sorted_chars]).strip()
                    if text:
                        line_texts.append((y, text))
                if not line_texts:
                    return None
                # 가장 긴 줄(혹은 가장 위에 있는 줄)을 제목으로 선택
                # 우선 길이순, 길이 같으면 y좌표가 큰(아래쪽) 것 우선
                line_texts.sort(key=lambda x: (-len(x[1]), x[0]))
                return line_texts[0][1]
        except Exception as e:
            print(f"Error extracting report title by color: {e}")
        return None

    def parse_report_info(self, text, filename, pdf_path):
        """리포트 정보 파싱"""
        report_title = self.extract_report_title_by_color(pdf_path)
        if not report_title:
            # Fallback to the 6th line logic if no title is found by color
            lines = text.split('\n')
            if len(lines) >= 6:
                sixth_line = lines[5].strip()
                if (len(sixth_line) >= 3 and 
                    re.search(r'[가-힣]', sixth_line) and  # 한글 포함
                    not re.search(r'^\d+$', sixth_line) and  # 숫자만 아님
                    not re.search(r'\d{4}[-./]\d{1,2}[-./]\d{1,2}', sixth_line) and  # 날짜 아님
                    not re.search(r'^\d{1,3}(,\d{3})*원?$', sixth_line)):  # 가격 정보 아님
                    report_title = sixth_line
        
        # 날짜 추출 (파일명에서)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        report_date = date_match.group(1) if date_match else datetime.now().strftime('%Y-%m-%d')

        return report_title, report_date    
    def parse_pdf(self, pdf_path):
        """PDF 파싱 메인 함수"""
        print(f"PDF 파싱 시작: {pdf_path}")
        
        # PDF에서 텍스트 추출
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            print("텍스트 추출 실패")
            return None
        
        filename = os.path.basename(pdf_path)
        
        # 정보 추출
        stock_name, stock_code = self.parse_stock_info(text)
        current_price, target_price, upside_potential = self.parse_price_info(text)
        analyst_name, company_name = self.parse_analyst_info(text, pdf_path) # pdf_path 인자 추가
        rating, opinion_change = self.parse_rating_info(text)
        report_title, report_date = self.parse_report_info(text, filename, pdf_path)
        investment_rationale = self.extract_investment_rationale(pdf_path)  # 투자 근거 추출
        
        # 데이터 구성
        data = {
            'report_id': str(uuid.uuid4()),
            'stock_code': stock_code,  # 이미 문자열이므로 그대로 사용
            'stock_name': stock_name,
            'report_title': report_title or f"{stock_name} 분석리포트",
            'report_date': report_date,
            'report_type': '기업분석',
            'analyst_name': analyst_name or 'Unknown',
            'company_name': company_name or 'Unknown',
            'rating': rating or 'Unknown',
            'opinion_change': opinion_change or '유지',
            'target_price': target_price,
            'current_price': current_price,
            'upside_potential': upside_potential,
            'investment_rationale': investment_rationale or '투자 근거 정보 없음',  # 투자 근거 추가
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.data_list.append(data)
        print(f"파싱 완료: {stock_name} ({stock_code})")
        return data
    
    def save_to_csv(self, output_path):
        """CSV 파일로 저장"""
        if not self.data_list:
            print("저장할 데이터가 없습니다.")
            return
        
        df = pd.DataFrame(self.data_list)
        
        # 종목코드를 문자열로 명시적으로 변환 (앞의 0 보존)
        df['stock_code'] = df['stock_code'].astype(str)
        
        # CSV 저장 시 종목코드 컬럼이 숫자로 해석되지 않도록 처리
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"CSV 파일 저장 완료: {output_path}")
        print(f"총 {len(self.data_list)}개 리포트 저장")
        
        # 저장된 데이터 확인
        print(f"\n=== 저장된 종목코드 확인 ===")
        for data in self.data_list:
            print(f"{data['stock_name']}: {data['stock_code']} (타입: {type(data['stock_code'])})")
    
    def process_all_pdfs(self, pdf_folder_path):
        """폴더 내 모든 PDF 파일 처리"""
        print(f"PDF 폴더 스캔 시작: {pdf_folder_path}")
        
        # PDF 파일 목록 가져오기
        if not os.path.exists(pdf_folder_path):
            print(f"폴더가 존재하지 않습니다: {pdf_folder_path}")
            return
        
        pdf_files = [f for f in os.listdir(pdf_folder_path) if f.endswith('.pdf')]
        
        if not pdf_files:
            print("PDF 파일이 없습니다.")
            return
        
        print(f"발견된 PDF 파일: {len(pdf_files)}개")
        for i, pdf_file in enumerate(pdf_files):
            print(f"{i+1}. {pdf_file}")
        
        # 각 PDF 파일 처리
        success_count = 0
        error_count = 0
        
        for i, pdf_file in enumerate(pdf_files):
            pdf_path = os.path.join(pdf_folder_path, pdf_file)
            print(f"\n{'='*80}")
            print(f"처리 중 ({i+1}/{len(pdf_files)}): {pdf_file}")
            print(f"{'='*80}")
            
            try:
                result = self.parse_pdf(pdf_path)
                if result:
                    success_count += 1
                    print(f"✓ 성공: {pdf_file}")
                else:
                    error_count += 1
                    print(f"✗ 실패: {pdf_file} (파싱 결과 없음)")
            except Exception as e:
                error_count += 1
                print(f"✗ 오류: {pdf_file} - {str(e)}")
        
        print(f"\n{'='*80}")
        print(f"처리 완료 - 성공: {success_count}개, 실패: {error_count}개")
        print(f"총 데이터: {len(self.data_list)}개")
        print(f"{'='*80}")

def main():
    """메인 실행 함수"""
    parser = KiwoomConsensusParser()
    
    # 현재 파일의 디렉토리 경로를 기준으로 상대경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # PDF 폴더 경로 설정 (상대경로)
    pdf_folder_path = os.path.join(current_dir, "..", "consensus", "kiwoom")
    
    # CSV 출력 경로 설정 (상대경로)
    output_path = os.path.join(current_dir, "..", "consensus_parsed", "kiwoom_consensus_reports.csv")
    
    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        # 폴더 내 모든 PDF 파일 처리
        parser.process_all_pdfs(pdf_folder_path)
        
        # 처리 결과 출력
        if parser.data_list:
            print(f"\n{'='*80}")
            print("전체 파싱 결과:")
            print(f"{'='*80}")
            
            for i, data in enumerate(parser.data_list):
                print(f"{i+1}. {data['stock_name']} ({data['stock_code']}) - {data['report_title']}")
                print(f"   증권사: {data['company_name']}, 애널리스트: {data['analyst_name']}")
                print(f"   투자의견: {data['rating']}, 목표가: {data['target_price']:,}원" if data['target_price'] else f"   투자의견: {data['rating']}, 목표가: None")
                if data.get('investment_rationale') and data['investment_rationale'] != '투자 근거 정보 없음':
                    rationale_preview = data['investment_rationale'][:100] + "..." if len(data['investment_rationale']) > 100 else data['investment_rationale']
                    print(f"   투자근거: {rationale_preview}")
            
            # CSV 저장
            parser.save_to_csv(output_path)
            
            # 요약 통계
            print(f"\n{'='*80}")
            print("요약 통계:")
            print(f"{'='*80}")
            
            # 증권사별 통계
            companies = {}
            ratings = {}
            
            for data in parser.data_list:
                company = data['company_name']
                rating = data['rating']
                
                companies[company] = companies.get(company, 0) + 1
                ratings[rating] = ratings.get(rating, 0) + 1
            
            print("증권사별 리포트 수:")
            for company, count in companies.items():
                print(f"  {company}: {count}개")
            
            print("\n투자의견별 분포:")
            for rating, count in ratings.items():
                print(f"  {rating}: {count}개")
                
        else:
            print("처리된 데이터가 없습니다.")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()