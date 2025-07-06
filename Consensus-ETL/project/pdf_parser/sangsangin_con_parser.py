#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pdfplumber
import pandas as pd
import re
import uuid
from datetime import datetime
import os
import logging
logging.getLogger("pdfminer").setLevel(logging.ERROR)

class SangsanginConsensusParser:
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
        return text
    
    def check_consensus_report(self, pdf_path):
        """상상인증권 컨센서스 리포트 판별"""
        print(f"\n=== 컨센서스 리포트 판별 시작 ===")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[0]  # 첫 번째 페이지
                
                # 전체 페이지 텍스트 추출
                full_text = page.extract_text()
                
                if not full_text:
                    print("페이지에서 텍스트가 추출되지 않음")
                    return False, None, None
                
                print(f"추출된 텍스트 일부:")
                print("-" * 30)
                print(full_text[:500])  # 처음 500자만 출력
                print("-" * 30)
                
                # 상상인증권 리포트 특징 확인
                sangsangin_keywords = ['상상인증권', 'SANGSANGIN', '상상인', '투자의견', '목표주가']
                has_sangsangin = any(keyword in full_text for keyword in sangsangin_keywords)
                
                if not has_sangsangin:
                    print("상상인증권 리포트가 아님")
                    return False, None, None
                
                # 종목코드 패턴 찾기 (6자리 숫자)
                stock_code_patterns = [
                    r'\((\d{6})\)',  # (123456) 형태
                    r'(\d{6})',      # 123456 형태
                    r'A(\d{6})',     # A123456 형태
                ]
                
                stock_code = None
                for pattern in stock_code_patterns:
                    matches = re.findall(pattern, full_text)
                    if matches:
                        # 첫 번째로 발견된 종목코드 사용
                        stock_code = matches[0]
                        print(f"✓ 종목코드 발견: {stock_code}")
                        break
                
                if not stock_code:
                    print("종목코드를 찾을 수 없음")
                    return False, None, None
                
                # 종목명 찾기
                stock_name_patterns = [
                    r'([가-힣A-Za-z0-9&\s\.\-]+?)\s*\((\d{6})\)',  # "종목명 (종목코드)" 형태
                    r'\((\d{6})\)\s*([가-힣A-Za-z0-9&\s\.\-]+)',  # "(종목코드) 종목명" 형태
                    r'기업명[:\s]*([가-힣A-Za-z0-9&\.\-]+)',
                    r'종목명[:\s]*([가-힣A-Za-z0-9&\.\-]+)',
                    r'회사명[:\s]*([가-힣A-Za-z0-9&\.\-]+)',
                ]
                
                stock_name = None
                for pattern in stock_name_patterns:
                    matches = re.findall(pattern, full_text)
                    for match in matches:
                        if isinstance(match, tuple):
                            # 패턴에 따라 종목명과 코드 위치 결정
                            if len(match) == 2:
                                if match[1] == stock_code:  # 종목명 (코드)
                                    candidate = match[0].strip()
                                elif match[0] == stock_code:  # (코드) 종목명
                                    candidate = match[1].strip()
                                else:
                                    continue
                            else:
                                continue
                        else:
                            candidate = match.strip()
                        
                        # 유효한 종목명인지 확인
                        if self.is_valid_stock_name(candidate):
                            stock_name = self.clean_stock_name(candidate)
                            print(f"✓ 종목명 발견: {stock_name}")
                            break
                    if stock_name:
                        break
                
                # 여전히 못 찾은 경우 좀 더 관대한 검사
                if not stock_name:
                    # 한글 기업명 패턴으로 재검사
                    korean_company_patterns = [
                        r'([가-힣]{2,15})\s*\(',  # 한글 기업명 다음에 괄호
                        r'([가-힣]{2,15})\s*투자의견',  # 한글 기업명 다음에 '투자의견'
                        r'([가-힣]{2,15})\s*목표주가',  # 한글 기업명 다음에 '목표주가'
                    ]
                    
                    for pattern in korean_company_patterns:
                        matches = re.findall(pattern, full_text)
                        for match in matches:
                            candidate = match.strip()
                            if self.is_valid_stock_name(candidate):
                                stock_name = self.clean_stock_name(candidate)
                                print(f"✓ 종목명 발견 (한글 패턴): {stock_name}")
                                break
                        if stock_name:
                            break
                
                if not stock_name:
                    print("종목명을 찾을 수 없음 - 기본값 사용")
                    stock_name = "Unknown"
                
                print(f"✅ 컨센서스 리포트 확인: {stock_name} ({stock_code})")
                return True, stock_name, stock_code
                
        except Exception as e:
            print(f"컨센서스 리포트 판별 오류: {e}")
            return False, None, None
    
    def is_valid_stock_name(self, candidate):
        """유효한 종목명인지 확인"""
        if not candidate or len(candidate) < 2:
            return False
        
        # 길이 제한
        if len(candidate) > 30:
            return False
        
        # 기본 패턴 확인 (한글, 영어, 숫자, &, ., - 허용)
        if not re.match(r'^[가-힣A-Za-z0-9&\.\-\s]+$', candidate):
            return False
        
        # 제외할 단어들
        excluded_words = [
            '상상인증권', '상상인', '리서치', '분석', '보고서', 'analyst', 'research',
            'buy', 'sell', 'hold', '매수', '매도', '중립', 'rating', 'sangsangin',
            'target', 'price', '목표', '주가', '현재', '기준', '투자', '의견',
            '등급', '상향', '하향', '유지', '신규', '종목', '기업', '회사',
            'maintain', 'upgrade', 'downgrade', 'initiate', 'company'
        ]
        
        candidate_lower = candidate.lower()
        for excluded in excluded_words:
            if excluded in candidate_lower:
                return False
        
        # 숫자만 있는 경우 제외
        if re.match(r'^\d+$', candidate):
            return False
        
        # 너무 짧은 영어 단어 제외 (2글자 이하)
        if re.match(r'^[A-Za-z]{1,2}$', candidate):
            return False
        
        # 한글이 포함된 경우 (한글+영어 조합 포함) 더 관대하게 처리
        if re.search(r'[가-힣]', candidate):
            return True
        
        # 영어만 있는 경우 3글자 이상이어야 함
        if re.match(r'^[A-Za-z]+$', candidate) and len(candidate) >= 3:
            return True
        
        # 영어+숫자 조합
        if re.match(r'^[A-Za-z]+[0-9]+$', candidate) and len(candidate) >= 3:
            return True
        
        return False
    
    def clean_stock_name(self, stock_name):
        """종목명 정리"""
        if not stock_name:
            return stock_name
        
        # 기본 정리
        stock_name = stock_name.strip()
        
        # 불필요한 문구 제거
        unwanted_patterns = [
            r'\s*Not\s+Rated\s*',
            r'\s*(BUY|SELL|HOLD|매수|매도|중립)\s*',
            r'\s*(Analyst|애널리스트|연구원)\s*',
            r'\s*(주식회사|㈜|\(주\))\s*',
            r'\s*(Target|목표)\s*',
            r'\s*(Price|주가)\s*',
            r'\s*(투자의견|투자등급)\s*',
            r'\s*(기업명|종목명|회사명)\s*'
        ]
        
        for pattern in unwanted_patterns:
            stock_name = re.sub(pattern, ' ', stock_name, flags=re.IGNORECASE)
        
        # 연속된 공백 정리
        stock_name = re.sub(r'\s+', '', stock_name)
        
        return stock_name.strip()
    
    def parse_stock_info(self, text, pre_stock_name=None, pre_stock_code=None):
        """주식 정보 파싱 (사전 확인된 정보 우선 사용)"""
        print(f"\n=== 종목 정보 파싱 ===")
        
        # 사전 확인된 정보가 있으면 우선 사용
        if pre_stock_name and pre_stock_code:
            print(f"사전 확인된 정보 사용: {pre_stock_name} ({pre_stock_code})")
            return pre_stock_name, pre_stock_code
        
        # 종목명과 코드 추출
        stock_patterns = [
            r'([가-힣A-Za-z0-9&\s\.\-]+?)\s*\((\d{6})\)',  # "종목명 (123456)" 형태
            r'\((\d{6})\)\s*([가-힣A-Za-z0-9&\s\.\-]+)',  # "(123456) 종목명" 형태
        ]
        
        stock_name = None
        stock_code = None
        
        for i, pattern in enumerate(stock_patterns):
            match = re.search(pattern, text)
            if match:
                if i == 0:  # 첫 번째 패턴: 종목명 (코드)
                    raw_name = match.group(1).strip()
                    stock_code = match.group(2)
                else:  # 두 번째 패턴: (코드) 종목명
                    stock_code = match.group(1)
                    raw_name = match.group(2).strip()
                
                # 종목명 정리
                if raw_name and self.is_valid_stock_name(raw_name):
                    stock_name = self.clean_stock_name(raw_name)
                    print(f"패턴 {i+1}에서 발견: {stock_name} ({stock_code})")
                    break
        
        # 여전히 찾지 못한 경우 기본값
        if not stock_name:
            stock_name = "Unknown"
        if not stock_code:
            stock_code = "000000"
        
        print(f"최종 결과: {stock_name} ({stock_code})")
        return stock_name, stock_code
    
    def parse_price_info(self, text):
        """가격 정보 파싱"""
        print(f"\n=== 가격 정보 파싱 시작 ===")
        
        # 목표가 추출
        target_price_patterns = [
            r'목표주가[:\s]*([0-9,]+)원?',
            r'Target Price[:\s]*([0-9,]+)원?',
            r'목표가[:\s]*([0-9,]+)원?',
            r'TP[:\s]*([0-9,]+)원?',
            r'목표주가:\s*([0-9,]+)원?',
            r'목표주가\s+([0-9,]+)원?'
        ]
        
        target_price = None
        for i, pattern in enumerate(target_price_patterns):
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    target_price = int(matches[0].replace(',', ''))
                    print(f"✓ 목표가 발견 (패턴 {i+1}): {target_price:,}원")
                    break
                except:
                    continue
        
        # 현재가 추출
        current_price_patterns = [
            r'현재가[:\s]*([0-9,]+)원?',
            r'기준가[:\s]*([0-9,]+)원?',
            r'주가[:\s]*([0-9,]+)원?(?!.*목표)',
            r'현재주가[:\s]*([0-9,]+)원?',
            r'기준주가[:\s]*([0-9,]+)원?',
            r'주가\(([^)]+)\)[:\s]*([0-9,]+)원?',
        ]
        
        current_price = None
        for i, pattern in enumerate(current_price_patterns):
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    if isinstance(matches[0], tuple):
                        current_price = int(matches[0][1].replace(',', ''))
                        print(f"✓ 현재가 발견 ({matches[0][0]}): {current_price:,}원")
                    else:
                        current_price = int(matches[0].replace(',', ''))
                        print(f"✓ 현재가 발견: {current_price:,}원")
                    break
                except:
                    continue
        
        # 상승여력 계산
        upside_potential = None
        if current_price and target_price:
            upside_potential = round(((target_price - current_price) / current_price) * 100, 1)
            print(f"✓ 상승여력 계산: {upside_potential}%")
        
        return current_price, target_price, upside_potential
    
    def parse_analyst_info(self, text, pdf_path=None):
        """애널리스트 정보 파싱"""
        print(f"\n=== 애널리스트 정보 파싱 시작 ===")
        
        analyst_patterns = [
            r'Analyst[:\s]*([가-힣]{2,4})',
            r'애널리스트[:\s]*([가-힣]{2,4})',
            r'작성자[:\s]*([가-힣]{2,4})',
            r'연구원[:\s]*([가-힣]{2,4})',
            r'([가-힣]{2,4})\s*애널리스트',
            r'([가-힣]{2,4})\s*연구원',
            r'담당[:\s]*([가-힣]{2,4})',
            r'리서치[:\s]*([가-힣]{2,4})',
        ]
        
        analyst_name = None
        for i, pattern in enumerate(analyst_patterns):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                # 일반적인 한국 이름 패턴 확인
                if len(candidate) >= 2 and re.match(r'^[가-힣]+$', candidate):
                    analyst_name = candidate
                    print(f"✓ 애널리스트 발견: '{analyst_name}'")
                    break
        
        # 증권사명은 상상인증권으로 고정
        company_name = '상상인증권'
        print(f"✓ 증권사: '{company_name}'")
        
        return analyst_name, company_name
    
    def parse_rating_info(self, text):
        """투자등급 정보 파싱"""
        print(f"\n=== 투자등급 정보 파싱 ===")
        
        lines = text.split('\n')
        rating = None
        opinion_change = None
        
        # 투자의견 찾기
        rating_patterns = [
            r'투자의견[:\s]*(BUY|SELL|HOLD|매수|매도|중립|Strong Buy|Strong Sell)',
            r'투자등급[:\s]*(BUY|SELL|HOLD|매수|매도|중립|Strong Buy|Strong Sell)',
            r'Rating[:\s]*(BUY|SELL|HOLD|매수|매도|중립|Strong Buy|Strong Sell)',
            r'(BUY|SELL|HOLD|매수|매도|중립|Strong Buy|Strong Sell)',
        ]
        
        for pattern in rating_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                rating_text = matches[0].upper()
                if rating_text in ['BUY', 'STRONG BUY', '매수']:
                    rating = '매수'
                elif rating_text in ['SELL', 'STRONG SELL', '매도']:
                    rating = '매도'
                elif rating_text in ['HOLD', '중립']:
                    rating = '중립'
                
                print(f"✓ 투자의견 발견: {rating}")
                break
        
        # 의견변경 정보 찾기
        change_patterns = [
            r'(유지|상향|하향|신규|Maintain|Upgrade|Downgrade|Initiate|New)',
        ]
        
        for pattern in change_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                change_text = matches[0].lower()
                if change_text in ['maintain', '유지']:
                    opinion_change = '유지'
                elif change_text in ['upgrade', '상향']:
                    opinion_change = '상향'
                elif change_text in ['downgrade', '하향']:
                    opinion_change = '하향'
                elif change_text in ['initiate', 'new', '신규']:
                    opinion_change = '신규'
                
                print(f"✓ 의견변경 발견: {opinion_change}")
                break
        
        # 기본값 설정
        if not rating:
            rating = '매수'
        if not opinion_change:
            opinion_change = '유지'
        
        return rating, opinion_change
    
    def extract_investment_rationale(self, pdf_path):
        """투자 의견 근거 추출"""
        print(f"\n=== 투자 근거 추출 시작 ===")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[0]  # 첫 번째 페이지에서 추출
                
                # 전체 텍스트 추출
                full_text = page.extract_text()
                
                if full_text:
                    print(f"추출된 원본 텍스트 길이: {len(full_text)}")
                    cleaned_text = self.clean_rationale_text(full_text)
                    
                    if cleaned_text and len(cleaned_text) > 20:
                        print(f"정리된 텍스트 길이: {len(cleaned_text)}")
                        return cleaned_text
                    else:
                        print("정리 후 유효한 투자 근거가 없습니다.")
                        return None
                else:
                    print("텍스트를 추출할 수 없습니다.")
                    return None
                    
        except Exception as e:
            print(f"투자 근거 추출 오류: {e}")
            return None
    
    def clean_rationale_text(self, text):
        """투자 근거 텍스트 정리"""
        if not text:
            return None
        
        # 기본 정리
        text = text.strip()
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # 불필요한 정보 제거
        unwanted_patterns = [
            r'상상인증권.*?\d{4}\.\s*\d{1,2}\.\s*\d{1,2}',
            r'SANGSANGIN.*?\d{4}\.\s*\d{1,2}\.\s*\d{1,2}',
            r'Analyst.*?CFA',
            r'KOSPI\s+[\d,\.]+pt',
            r'KOSDAQ\s+[\d,\.]+pt',
            r'시가총액\s+[\d,]+억\s*원',
            r'발행주식수\s+[\d,]+천주',
            r'외국인\s+지분율\s+[\d\.]+%',
            r'배당수익률.*?[\d\.]+%',
            r'CM\d+_\d+_\d+\.pdf',
        ]
        
        for pattern in unwanted_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # 연속된 공백 정리
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 너무 짧은 텍스트 제외
        if len(text) < 30:
            return None
        
        # 의미 있는 투자 근거 키워드 확인
        meaningful_keywords = [
            '매수', '투자', '성장', '실적', '수익', '영업', '매출', '이익',
            '전망', '예상', '기대', '개선', '증가', '상승', '긍정', '호조',
            '경쟁력', '시장', '사업', '부문', '확대', '기회', '잠재력',
            '강세', '회복', '확장', '혁신', '우수', '경영', '관리'
        ]
        
        keyword_count = sum(1 for keyword in meaningful_keywords if keyword in text)
        if keyword_count < 2:
            return None
        
        return text.strip()
    
    def extract_report_title(self, text, pdf_path):
        """리포트 제목 추출"""
        print(f"\n=== 리포트 제목 추출 ===")
        
        # 파일명에서 제목 추출 시도
        filename = os.path.basename(pdf_path)
        if filename and filename.endswith('.pdf'):
            # 파일명에서 의미있는 제목 찾기
            title_from_filename = filename.replace('.pdf', '').replace('_', ' ')
            if len(title_from_filename) > 3:
                print(f"✓ 파일명 기반 제목: {title_from_filename}")
                return title_from_filename
        
        # 텍스트에서 제목 패턴 찾기
        lines = text.split('\n')
        
        # 제목으로 보이는 패턴들
        title_keywords = ['전망', '분석', '리뷰', '업데이트', '노트', '탐방', '실적', '성장', '개선', '기대', '추천', '리포트']
        
        for line in lines[:20]:  # 처음 20줄에서 찾기
            line = line.strip()
            if (len(line) > 8 and len(line) < 80 and
                any(keyword in line for keyword in title_keywords) and
                not re.search(r'상상인증권|analyst|페이지|page|@|tel|email|CM\d+', line, re.IGNORECASE)):
                print(f"✓ 키워드 기반 제목 발견: {line}")
                return line
        
        # 종목코드 다음에 나오는 제목 찾기
        for i, line in enumerate(lines):
            line = line.strip()
            if re.search(r'\(\d{6}\)', line):  # 종목코드가 포함된 줄
                # 다음 몇 줄에서 제목 찾기
                for j in range(i+1, min(i+5, len(lines))):
                    title_line = lines[j].strip()
                    if (title_line and 
                        len(title_line) > 5 and len(title_line) < 100 and
                        not re.search(r'상상인증권|analyst|페이지|page|^\d+$|@|tel|email|CM\d+', title_line, re.IGNORECASE) and
                        not re.match(r'^\d{4}[\.\-]\d{2}[\.\-]\d{2}', title_line)):
                        print(f"✓ 제목 발견: {title_line}")
                        return title_line
        
        return "제목 미상"
    
    def parse_report_info(self, text, filename, pdf_path):
        """리포트 정보 파싱"""
        report_title = self.extract_report_title(text, pdf_path)
        
        # 날짜 추출 (텍스트에서 먼저 시도)
        date_patterns = [
            r'(\d{4})\s*[\.\-/]\s*(\d{1,2})\s*[\.\-/]\s*(\d{1,2})',
            r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',
            r'(\d{2})\s*[\.\-/]\s*(\d{1,2})\s*[\.\-/]\s*(\d{1,2})',
        ]
        
        report_date = None
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    match = matches[0]
                    if len(match[0]) == 4:  # YYYY-MM-DD 형태
                        year, month, day = match
                    else:  # YY-MM-DD 형태
                        year = "20" + match[0]
                        month, day = match[1], match[2]
                    
                    report_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    print(f"✓ 날짜 발견: {report_date}")
                    break
                except:
                    continue
        
        # 날짜를 찾지 못한 경우 현재 날짜 사용
        if not report_date:
            report_date = datetime.now().strftime('%Y-%m-%d')
            print(f"✓ 기본 날짜 사용: {report_date}")
        
        return report_title, report_date
    
    def parse_pdf(self, pdf_path):
        """PDF 파싱 메인 함수"""
        print(f"\n{'='*80}")
        print(f"PDF 파싱 시작: {os.path.basename(pdf_path)}")
        print(f"{'='*80}")
        
        # 1단계: 컨센서스 리포트 여부 확인
        is_consensus, pre_stock_name, pre_stock_code = self.check_consensus_report(pdf_path)
        if not is_consensus:
            print(f"❌ 컨센서스 리포트가 아님 - 파싱 건너뜀")
            return None
        
        # 2단계: PDF에서 텍스트 추출
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            print("텍스트 추출 실패")
            return None
        
        filename = os.path.basename(pdf_path)
        
        # 3단계: 정보 추출
        stock_name, stock_code = self.parse_stock_info(text, pre_stock_name, pre_stock_code)
        current_price, target_price, upside_potential = self.parse_price_info(text)
        analyst_name, company_name = self.parse_analyst_info(text, pdf_path)
        rating, opinion_change = self.parse_rating_info(text)
        report_title, report_date = self.parse_report_info(text, filename, pdf_path)
        investment_rationale = self.extract_investment_rationale(pdf_path)
        
        # 4단계: 데이터 구성
        data = {
            'report_id': str(uuid.uuid4()),
            'stock_code': stock_code,
            'stock_name': stock_name,
            'report_title': report_title or f"{stock_name} 분석리포트",
            'report_date': report_date,
            'report_type': '기업분석',
            'analyst_name': analyst_name or 'Unknown',
            'company_name': company_name or '상상인증권',
            'rating': rating or '매수',
            'opinion_change': opinion_change or '유지',
            'target_price': target_price,
            'current_price': current_price,
            'upside_potential': upside_potential,
            'investment_rationale': investment_rationale or '투자 근거 정보 없음',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.data_list.append(data)
        print(f"✅ 파싱 완료: {stock_name} ({stock_code})")
        return data
    
    def save_to_csv(self, output_path):
        """CSV 파일로 저장"""
        if not self.data_list:
            print("저장할 데이터가 없습니다.")
            return
        
        df = pd.DataFrame(self.data_list)
        df['stock_code'] = df['stock_code'].astype(str)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"CSV 파일 저장 완료: {output_path}")
        print(f"총 {len(self.data_list)}개 리포트 저장")
    
    def save_to_json(self, output_path):
        """JSON 파일로 저장"""
        if not self.data_list:
            print("저장할 데이터가 없습니다.")
            return
        
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data_list, f, ensure_ascii=False, indent=2)
        
        print(f"JSON 파일 저장 완료: {output_path}")
        print(f"총 {len(self.data_list)}개 리포트 저장")
    
    def process_all_pdfs(self, pdf_folder_path):
        """폴더 내 모든 PDF 파일 처리"""
        print(f"PDF 폴더 스캔 시작: {pdf_folder_path}")
        
        if not os.path.exists(pdf_folder_path):
            print(f"폴더가 존재하지 않습니다: {pdf_folder_path}")
            return
        
        pdf_files = [f for f in os.listdir(pdf_folder_path) if f.endswith('.pdf')]
        
        if not pdf_files:
            print("PDF 파일이 없습니다.")
            return
        
        print(f"발견된 PDF 파일: {len(pdf_files)}개")
        
        # 각 PDF 파일 처리
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        for i, pdf_file in enumerate(pdf_files):
            pdf_path = os.path.join(pdf_folder_path, pdf_file)
            print(f"\n처리 중 ({i+1}/{len(pdf_files)}): {pdf_file}")
            
            try:
                result = self.parse_pdf(pdf_path)
                if result:
                    success_count += 1
                    print(f"✓ 성공: {pdf_file}")
                else:
                    skipped_count += 1
                    print(f"⊘ 건너뜀: {pdf_file} (컨센서스 리포트 아님)")
            except Exception as e:
                error_count += 1
                print(f"✗ 오류: {pdf_file} - {str(e)}")
        
        print(f"\n{'='*80}")
        print(f"처리 완료")
        print(f"성공: {success_count}개")
        print(f"건너뜀: {skipped_count}개 (컨센서스 리포트 아님)")
        print(f"실패: {error_count}개")
        print(f"총 데이터: {len(self.data_list)}개")
        print(f"{'='*80}")

def main():
    """메인 실행 함수"""
    parser = SangsanginConsensusParser()
    
    # 현재 파일의 디렉토리 경로를 기준으로 상대경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # PDF 폴더 경로 설정 (상대경로)
    pdf_folder_path = os.path.join(current_dir, "..", "consensus", "sangsangin")
    
    # CSV 출력 경로 설정 (상대경로)
    csv_output_path = os.path.join(current_dir, "..", "consensus_parsed", "sangsangin_consensus_reports.csv")
    json_output_path = os.path.join(current_dir, "..", "consensus_parsed", "sangsangin_consensus_reports.json")
    
    # 출력 디렉토리 생성
    os.makedirs(os.path.dirname(csv_output_path), exist_ok=True)
    
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
            
            # CSV 및 JSON 저장
            parser.save_to_csv(csv_output_path)
            parser.save_to_json(json_output_path)
            
            # 요약 통계
            print(f"\n{'='*80}")
            print("요약 통계:")
            print(f"{'='*80}")
            
            ratings = {}
            for data in parser.data_list:
                rating = data['rating']
                ratings[rating] = ratings.get(rating, 0) + 1
            
            print("투자의견별 분포:")
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
