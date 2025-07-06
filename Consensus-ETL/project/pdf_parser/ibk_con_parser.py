#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ibk 는 json 이랑 csv로 둘다 저장해서 이 부분 알아둘 것
import os
import re
import uuid
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import pdfplumber
import logging
import warnings

# PDF 파싱 관련 경고 무시
warnings.filterwarnings("ignore", category=UserWarning, module="pdfplumber")
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IBKConsensusParser:
    def __init__(self, pdf_folder_path, output_dir):
        self.pdf_folder_path = Path(pdf_folder_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def parse_filename(self, filename):
        """파일명에서 기본 정보 추출 - 모든 PDF 파일 처리"""
        # PDF 파일인지 확인
        if not filename.lower().endswith('.pdf'):
            return None, None
        
        # 파일명에서 .pdf 제거
        basename = filename[:-4]
        
        # 패턴 1: {종목명}_{YYYYMMDD}.pdf 형식
        pattern1 = r'(.+)_(\d{8})$'
        match1 = re.match(pattern1, basename)
        if match1:
            stock_name = match1.group(1)
            date_str = match1.group(2)
            # YYYYMMDD -> YYYY-MM-DD 형식으로 변환
            report_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            return stock_name, report_date
        
        # 패턴 2: {종목명}_{YYYY.MM.DD}.pdf 형식
        pattern2 = r'(.+)_(\d{4}\.\d{2}\.\d{2})$'
        match2 = re.match(pattern2, basename)
        if match2:
            stock_name = match2.group(1)
            date_str = match2.group(2)
            # YYYY.MM.DD -> YYYY-MM-DD 형식으로 변환
            report_date = date_str.replace('.', '-')
            return stock_name, report_date
        
        # 패턴 3: 날짜 정보가 없는 경우, 스마트 종목명 추출 사용
        stock_name = self.extract_stock_name_from_filename(filename)
        report_date = datetime.now().strftime('%Y-%m-%d')
        
        return stock_name, report_date
    
    def extract_text_from_pdf(self, pdf_path):
        """PDF에서 텍스트 추출"""
        try:
            full_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
            return full_text
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패 {pdf_path}: {e}")
            return ""
    
    def extract_stock_name_from_content(self, text):
        """PDF 내용에서 종목명 추출"""
        lines = text.split('\n')
        
        # 패턴 1: Company Update 다음에 나오는 종목명
        for i, line in enumerate(lines):
            line = line.strip()
            if line == "Company Update" and i+1 < len(lines):
                stock_name = lines[i+1].strip()
                # 종목코드가 바로 다음에 있는지 확인
                if i+2 < len(lines) and re.match(r'^\(\d{6}\)$', lines[i+2].strip()):
                    return stock_name
        
        # 패턴 2: 대괄호 안의 종목명 [종목명]
        bracket_matches = re.findall(r'\[([^\]]+)\]', text)
        for match in bracket_matches:
            # 숫자나 특수문자만 있는 것은 제외
            if not re.match(r'^[\d\s\-\.]+$', match) and len(match) > 1:
                # 일반적이지 않은 패턴 제외
                if not any(word in match.lower() for word in ['company', 'update', 'report', 'ibk', '투자증권', '리서치']):
                    return match.strip()
        
        # 패턴 3: 종목코드 앞에 나오는 종목명
        for i, line in enumerate(lines):
            line = line.strip()
            # 종목코드 패턴 찾기
            if re.match(r'^\(\d{6}\)$', line) and i > 0:
                # 종목코드 앞 줄들을 확인
                for j in range(max(0, i-3), i):
                    prev_line = lines[j].strip()
                    if (prev_line and 
                        len(prev_line) > 1 and len(prev_line) < 30 and
                        not re.search(r'update|report|company|analyst|페이지|page|ibk|투자증권', prev_line, re.IGNORECASE) and
                        not re.match(r'^[\d\s\-\.]+$', prev_line)):
                        return prev_line
        
        # 패턴 4: 첫 번째 페이지에서 한글 기업명 패턴 찾기
        first_lines = lines[:20]  # 첫 20줄만 확인
        for line in first_lines:
            line = line.strip()
            # 한글로 된 기업명 패턴 (2-10글자)
            korean_pattern = re.match(r'^([가-힣]{2,10})$', line)
            if korean_pattern:
                stock_name = korean_pattern.group(1)
                if stock_name not in ['기업분석', '투자의견', '애널리스트', '보고서', '리포트']:
                    return stock_name
        
        return None
    
    def extract_report_title_improved(self, text):
        """개선된 리포트 제목 추출"""
        lines = text.split('\n')
        
        # 패턴 1: Company Update -> 종목명 -> 종목코드 -> 제목 순서
        for i, line in enumerate(lines):
            line = line.strip()
            if line == "Company Update" and i+3 < len(lines):
                # Company Update 다음이 종목명, 그 다음이 종목코드인지 확인
                stock_line = lines[i+1].strip()
                code_line = lines[i+2].strip()
                
                if re.match(r'^\(\d{6}\)$', code_line):
                    # 종목코드 다음 줄부터 제목 찾기
                    for j in range(i+3, min(i+8, len(lines))):
                        title_line = lines[j].strip()
                        if (title_line and 
                            len(title_line) > 5 and len(title_line) < 100 and
                            not re.search(r'ibk|투자증권|analyst|페이지|page|^\d+$|@|tel|email', title_line, re.IGNORECASE) and
                            not title_line.startswith('02)') and
                            '리서치' not in title_line):
                            return title_line
        
        # 패턴 2: 종목코드 바로 다음에 나오는 제목
        for i, line in enumerate(lines):
            line = line.strip()
            if re.match(r'^\(\d{6}\)$', line):
                # 종목코드 다음 줄들을 확인
                for j in range(i+1, min(i+6, len(lines))):
                    next_line = lines[j].strip()
                    if (next_line and 
                        len(next_line) > 5 and len(next_line) < 100 and
                        not re.search(r'ibk|투자증권|analyst|페이지|page|^\d+$|@|tel|email|리서치', next_line, re.IGNORECASE) and
                        not next_line.startswith('02)') and
                        not re.match(r'^\d{4}[\.\-]\d{2}[\.\-]\d{2}', next_line)):  # 날짜 패턴 제외
                        return next_line
        
        # 패턴 3: 제목으로 보이는 패턴들 (특정 키워드 포함)
        title_keywords = ['전망', '분석', '리뷰', '업데이트', '노트', '탐방', '실적', '성장', '개선', '기대', '확대', '전환', '회복']
        for line in lines[:30]:  # 첫 30줄에서만 찾기
            line = line.strip()
            if (len(line) > 8 and len(line) < 80 and
                any(keyword in line for keyword in title_keywords) and
                not re.search(r'ibk|투자증권|analyst|페이지|page|@|tel|email', line, re.IGNORECASE)):
                return line
        
        # 패턴 4: 대괄호로 시작하지 않는 첫 번째 의미있는 문장
        for line in lines[:20]:
            line = line.strip()
            if (line and 
                not line.startswith('[') and 
                len(line) > 10 and len(line) < 80 and
                not re.search(r'company|update|ibk|투자증권|analyst|페이지|page|^\d+$|@|tel|email|리서치', line, re.IGNORECASE) and
                not re.match(r'^\(\d{6}\)$', line) and
                not re.match(r'^[가-힣]{2,10}$', line)):  # 단순 종목명 제외
                return line
        
        return "제목 미상"
    
    def extract_stock_code(self, text):
        """텍스트에서 종목코드 추출"""
        # 6자리 숫자 패턴 찾기
        patterns = [
            r'\((\d{6})\)',  # (123456)
            r'종목코드[\s:]*(\d{6})',
            r'Stock Code[\s:]*(\d{6})',
            r'CODE[\s:]*(\d{6})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
        
    def extract_analyst_name(self, text):
        """애널리스트 이름 추출"""
        patterns = [
            r'애널리스트[\s:]*([가-힣]{2,4})',
            r'분석자[\s:]*([가-힣]{2,4})',
            r'작성자[\s:]*([가-힣]{2,4})',
            r'Analyst[\s:]*([가-힣]{2,4})',
            r'([가-힣]{2,4})[\s]*애널리스트',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def extract_rating(self, text):
        """투자의견 추출"""
        patterns = [
            r'투자의견[\s:]*([^\n\r]+)',
            r'투자등급[\s:]*([^\n\r]+)',
            r'Rating[\s:]*([^\n\r]+)',
            r'(매수|매도|보유|중립|Buy|Sell|Hold|강력매수)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rating = match.group(1).strip()
                # 표준화
                if any(word in rating.lower() for word in ['buy', '매수', '강력매수']):
                    return '매수'
                elif any(word in rating.lower() for word in ['hold', '보유', '중립']):
                    return '보유'
                elif any(word in rating.lower() for word in ['sell', '매도']):
                    return '매도'
                return rating
        
        return None
    
    def extract_target_price(self, text):
        """목표주가 추출"""
        patterns = [
            r'목표주?가[\s:]*([0-9,]+)원?',
            r'Target\s*Price[\s:]*([0-9,]+)',
            r'TP[\s:]*([0-9,]+)',
            r'목표가[\s:]*([0-9,]+)원?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    if 100 <= price <= 10000000:
                        return price
                except ValueError:
                    continue
        
        return None
    
    def extract_current_price(self, text):
        """현재주가 추출"""
        patterns = [
            r'현재주?가[\s:]*([0-9,]+)원?',
            r'주가[\s:]*([0-9,]+)원?',
            r'Current\s*Price[\s:]*([0-9,]+)',
            r'종가[\s:]*([0-9,]+)원?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    if 100 <= price <= 10000000:
                        return price
                except ValueError:
                    continue
        
        return None
    
    def extract_report_title(self, text):
        """개선된 리포트 제목 추출 - 새로운 로직 사용"""
        return self.extract_report_title_improved(text)
    
    def extract_investment_rationale(self, pdf_path):
        """투자의견 근거 추출 - y좌표 607까지"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[0]  # 첫 번째 페이지
                page_width = page.width
                page_height = page.height
                
                # y좌표 607까지의 영역 설정 (상단부터 607까지)
                rationale_bbox = (0, 0, page_width, 607)
                
                # 해당 영역에서 텍스트 추출
                cropped_page = page.crop(rationale_bbox)
                text = cropped_page.extract_text()
                
                if not text:
                    return "투자의견 근거 추출 실패 - 해당 영역에 텍스트 없음"
                
                # 텍스트 정리
                cleaned_text = self.clean_rationale_text(text)
                return cleaned_text
                
        except Exception as e:
            logger.warning(f"좌표 기반 추출 실패: {e}")
            return "투자의견 근거 추출 실패"
    
    def clean_rationale_text(self, text):
        """투자의견 근거 텍스트 정리"""
        if not text:
            return "투자의견 근거 없음"
        
        lines = text.split('\n')
        cleaned_lines = []
        
        # 제외할 패턴들
        exclude_patterns = [
            'ibk투자증권', 'ibk증권', 'ibk research', 'ibk 리서치',
            '면책조항', '고지사항', '투자권고', '투자위험', '투자결정',
            'copyright', '저작권', '무단복제', '전재금지',
            '본 자료는', '당사는', '면책', '리스크', 'risk',
            '연구원', 'analyst', '@', 'tel:', 'email:',
            '발행일', '작성일', '보고서', 'report'
        ]
        
        # 투자 관련 키워드 (이 중 하나라도 포함되어야 유효한 투자 근거로 인정)
        investment_keywords = [
            '실적', '매출', '영업이익', '순이익', '성장', '전망', '예상',
            '투자포인트', '투자요약', '핵심', '주요', '포인트',
            '사업', '시장', '경쟁', '수익', '이익', '부문', '제품',
            '개선', '확대', '증가', '감소', '상승', '하락',
            '1Q', '2Q', '3Q', '4Q', '분기', '연간', '목표',
            '밸류에이션', '주가', 'P/E', 'P/B', 'ROE', 'EBITDA'
        ]
        
        has_investment_content = False
        
        for line in lines:
            line = line.strip()
            
            # 너무 짧은 라인 제외
            if len(line) < 10:
                continue
            
            # 제외 패턴 체크
            line_lower = line.lower()
            if any(pattern in line_lower for pattern in exclude_patterns):
                continue
            
            # 투자 관련 키워드가 포함된 라인인지 확인
            if any(keyword in line for keyword in investment_keywords):
                has_investment_content = True
                cleaned_lines.append(line)
            elif has_investment_content and len(line) > 20:
                # 이미 투자 관련 내용이 시작된 후의 긴 문장들
                cleaned_lines.append(line)
        
        # 결과 정리
        if not cleaned_lines:
            return "투자의견 근거 추출 실패 - 적절한 투자 근거 내용 없음"
        
        result = ' '.join(cleaned_lines)
        
        # 길이 제한 (너무 긴 경우 문장 단위로 자르기)
        if len(result) > 2000:
            sentences = result.split('. ')
            trimmed = ""
            for sentence in sentences:
                if len(trimmed + sentence) < 1800:
                    trimmed += sentence + ". "
                else:
                    break
            result = trimmed.rstrip()
            if not result.endswith('.'):
                result += "..."
        
        return result
    
    def extract_stock_name_from_filename(self, filename):
        """파일명에서 종목명 추출 - 다양한 패턴 지원"""
        # PDF 확장자 제거
        basename = filename.replace('.pdf', '')
        
        # 특수문자 및 숫자 패턴 제거
        # 예: "CJ프레시웨이_20250704" -> "CJ프레시웨이"
        # 예: "[삼성전자]_분석보고서" -> "삼성전자"
        
        # 대괄호 안의 종목명 추출
        bracket_match = re.search(r'\[([^\]]+)\]', basename)
        if bracket_match:
            return bracket_match.group(1).strip()
        
        # 언더스코어 앞의 종목명 추출
        if '_' in basename:
            parts = basename.split('_')
            stock_name = parts[0]
            
            # 숫자나 특수문자 제거
            stock_name = re.sub(r'[0-9\-\.]', '', stock_name).strip()
            
            if stock_name:
                return stock_name
        
        # 날짜 패턴 제거
        cleaned_name = re.sub(r'\d{4}[\.\-]\d{2}[\.\-]\d{2}', '', basename)
        cleaned_name = re.sub(r'\d{8}', '', cleaned_name)
        cleaned_name = re.sub(r'[_\-\.]', ' ', cleaned_name).strip()
        
        # 너무 긴 경우 첫 번째 단어만 사용
        words = cleaned_name.split()
        if words:
            return words[0]
        
        return basename  # 마지막 수단으로 원본 파일명 사용
    
    def parse_single_pdf(self, pdf_path):
        """단일 PDF 파일 파싱"""
        logger.info(f"파싱 중: {pdf_path.name}")
        
        # PDF 텍스트 추출 (먼저 수행)
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning(f"텍스트 추출 실패: {pdf_path.name}")
            return None
        
        # PDF 내용에서 종목명 추출 (우선)
        stock_name_from_content = self.extract_stock_name_from_content(text)
        
        # 파일명에서 기본 정보 추출 (보조)
        stock_name_from_filename, report_date = self.parse_filename(pdf_path.name)
        
        # 종목명 결정 (PDF 내용 우선, 없으면 파일명, 그것도 없으면 기본값)
        if stock_name_from_content:
            stock_name = stock_name_from_content
            logger.info(f"PDF 내용에서 종목명 추출: {stock_name}")
        elif stock_name_from_filename:
            stock_name = stock_name_from_filename
            logger.info(f"파일명에서 종목명 추출: {stock_name}")
        else:
            stock_name = "종목명 미상"
            logger.warning(f"종목명 추출 실패: {pdf_path.name}")
        
        # 날짜 처리
        if not report_date:
            report_date = datetime.now().strftime('%Y-%m-%d')
            logger.warning(f"파일명에서 날짜 추출 실패, 현재 날짜 사용: {pdf_path.name}")
        
        # 정보 추출
        stock_code = self.extract_stock_code(text)
        analyst_name = self.extract_analyst_name(text)
        rating = self.extract_rating(text)
        target_price = self.extract_target_price(text)
        current_price = self.extract_current_price(text)
        report_title = self.extract_report_title(text)
        investment_rationale = self.extract_investment_rationale(pdf_path)  # pdf_path 전달
        
        # 상승여력 계산
        upside_potential = None
        if target_price and current_price and current_price > 0:
            upside_potential = round(((target_price - current_price) / current_price) * 100, 1)
        
        # 결과 데이터
        result = {
            'report_id': str(uuid.uuid4()),
            'stock_code': stock_code,
            'stock_name': stock_name,
            'report_title': report_title,
            'report_date': report_date,
            'report_type': '기업분석',
            'analyst_name': analyst_name,
            'company_name': 'IBK투자증권',
            'rating': rating,
            'opinion_change': '유지',  # 기본값
            'target_price': target_price,
            'current_price': current_price,
            'upside_potential': upside_potential,
            'investment_rationale': investment_rationale,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return result
    
    def parse_all_pdfs(self):
        """모든 PDF 파일 파싱"""
        results = []
        
        # PDF 파일 찾기
        pdf_files = list(self.pdf_folder_path.glob("*.pdf"))
        logger.info(f"총 {len(pdf_files)}개 PDF 파일 발견")
        
        for pdf_file in pdf_files:
            try:
                result = self.parse_single_pdf(pdf_file)
                if result:
                    results.append(result)
                    logger.info(f"성공: {pdf_file.name}")
                    
                    # 추출된 정보 출력
                    print(f"\n=== {pdf_file.name} 파싱 결과 ===")
                    print(f"종목코드: {result['stock_code']}")
                    print(f"종목명: {result['stock_name']}")
                    print(f"제목: {result['report_title']}")
                    print(f"애널리스트: {result['analyst_name']}")
                    print(f"투자의견: {result['rating']}")
                    print(f"현재주가: {result['current_price']}")
                    print(f"목표주가: {result['target_price']}")
                    
                else:
                    logger.warning(f"파싱 실패: {pdf_file.name}")
            except Exception as e:
                logger.error(f"오류 발생 {pdf_file.name}: {e}")
        
        # 전체 결과를 CSV와 JSON으로 저장
        if results:
            # CSV 저장
            df = pd.DataFrame(results)
            csv_path = self.output_dir / "ibk_consensus_reports_complete.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            # JSON 저장
            json_path = self.output_dir / "ibk_consensus_reports_complete.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"총 {len(results)}개 레포트 파싱 완료")
            logger.info(f"CSV 저장: {csv_path}")
            logger.info(f"JSON 저장: {json_path}")
            
            # 결과 요약 출력
            self.print_summary(df)
        else:
            logger.warning("파싱된 결과가 없습니다.")
        
        return results
    
    def print_summary(self, df):
        """파싱 결과 요약 출력"""
        print("\n=== 파싱 결과 요약 ===")
        print(f"총 레포트 수: {len(df)}")
        print(f"종목 수: {df['stock_name'].nunique()}")
        if 'analyst_name' in df.columns and not df['analyst_name'].isna().all():
            print(f"애널리스트 수: {df['analyst_name'].nunique()}")
        if 'rating' in df.columns and not df['rating'].isna().all():
            print(f"투자의견 분포:")
            print(df['rating'].value_counts())
        print(f"\n종목별 레포트 수:")
        print(df['stock_name'].value_counts())

def main():
    # 경로 설정 - 상대 경로 사용
    current_dir = Path(__file__).parent  # 현재 파일(ibk_con_parser.py)이 있는 디렉토리
    project_dir = current_dir.parent      # project 디렉토리
    
    pdf_folder = project_dir / "consensus" / "ibks"
    output_dir = project_dir / "consensus_parsed"
    
    # 파서 실행
    parser = IBKConsensusParser(pdf_folder, output_dir)
    results = parser.parse_all_pdfs()
    
    return results

if __name__ == "__main__":
    main()
