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
    
    def extract_stock_info(self, text):
        """상상인증권 PDF에서 종목 정보 추출"""
        print(f"\n=== 종목 정보 추출 ===")
        
        lines = text.split('\n')
        stock_name = None
        stock_code = None
        
        # 첫 번째 줄에서 종목명 추출 (상상인증권 특징)
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if line and len(line) > 0:
                # 한글 기업명 패턴 찾기
                korean_match = re.search(r'([가-힣A-Za-z&\-\.]+)', line)
                if korean_match:
                    candidate = korean_match.group(1)
                    if self.is_valid_stock_name(candidate):
                        stock_name = candidate
                        print(f"✓ 종목명 발견 (줄 {i+1}): {stock_name}")
                        break
        
        # 전체 텍스트에서 종목코드 찾기
        # 6자리 숫자 패턴 (상상인증권은 괄호 없이 나타날 수 있음)
        code_patterns = [
            r'종목코드[:\s]*(\d{6})',
            r'코드[:\s]*(\d{6})',
            r'\b(\d{6})\b',  # 단순 6자리 숫자
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 가장 가능성 높은 종목코드 선택 (000000~999999 범위)
                for code in matches:
                    if code.startswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                        stock_code = code
                        print(f"✓ 종목코드 발견: {stock_code}")
                        break
            if stock_code:
                break
        
        # 기본값 설정
        if not stock_name:
            stock_name = "Unknown"
        if not stock_code:
            stock_code = "000000"
        
        print(f"최종 결과: {stock_name} ({stock_code})")
        return stock_name, stock_code
    
    def is_valid_stock_name(self, candidate):
        """유효한 종목명인지 확인"""
        if not candidate or len(candidate) < 2:
            return False
        
        # 길이 제한
        if len(candidate) > 30:
            return False
        
        # 제외할 단어들
        excluded_words = [
            '상상인증권', '리서치', '분석', '보고서', '투자', '의견', '등급',
            '목표', '주가', '현재', '기준', '매수', '매도', '중립',
            '상승', '하락', '전망', '예상', '기대', '실적', '매출',
            '영업', '이익', '손실', '증가', '감소', '성장', '개선',
            '당사', '동사', '회사', '기업', '업체', '사업', '부문',
            '시장', '산업', '분야', '영역', '부분', '측면', '관점'
        ]
        
        candidate_lower = candidate.lower()
        for excluded in excluded_words:
            if excluded in candidate_lower:
                return False
        
        # 숫자만 있는 경우 제외
        if re.match(r'^\d+$', candidate):
            return False
        
        # 특수문자만 있는 경우 제외
        if re.match(r'^[^\w가-힣]+$', candidate):
            return False
        
        return True
    
    def extract_price_info(self, text):
        """가격 정보 추출"""
        print(f"\n=== 가격 정보 추출 ===")
        
        # 현재가/종가 추출
        current_price_patterns = [
            r'종가[:\s]*\([^)]+\)[:\s]*([0-9,]+)원?',
            r'현재가[:\s]*\([^)]+\)[:\s]*([0-9,]+)원?',
            r'종가[:\s]*([0-9,]+)원?',
            r'현재가[:\s]*([0-9,]+)원?',
        ]
        
        current_price = None
        for pattern in current_price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                current_price = int(matches[0].replace(',', ''))
                print(f"✓ 현재가: {current_price:,}원")
                break
        
        # 목표가 추출
        target_price_patterns = [
            r'목표주가[:\s]*([0-9,]+)원?',
            r'목표가[:\s]*([0-9,]+)원?',
            r'Target Price[:\s]*([0-9,]+)원?',
        ]
        
        target_price = None
        for pattern in target_price_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                target_price = int(matches[0].replace(',', ''))
                print(f"✓ 목표가: {target_price:,}원")
                break
        
        # 상승여력 추출 또는 계산
        upside_potential = None
        
        # 직접 상승여력 찾기
        upside_patterns = [
            r'상승여력[:\s]*([0-9\.\-]+)%',
            r'상승률[:\s]*([0-9\.\-]+)%',
        ]
        
        for pattern in upside_patterns:
            matches = re.findall(pattern, text)
            if matches:
                upside_str = matches[0]
                if upside_str != '-':
                    upside_potential = float(upside_str)
                    print(f"✓ 상승여력: {upside_potential}%")
                break
        
        # 계산으로 상승여력 구하기
        if upside_potential is None and current_price and target_price:
            upside_potential = round(((target_price - current_price) / current_price) * 100, 1)
            print(f"✓ 상승여력 (계산): {upside_potential}%")
        
        return current_price, target_price, upside_potential
    
    def extract_rating_info(self, text):
        """투자등급 정보 추출"""
        print(f"\n=== 투자등급 정보 추출 ===")
        
        # 투자의견 추출
        rating_patterns = [
            r'투자의견[:\s]*(매수|매도|중립|BUY|SELL|HOLD)',
            r'투자등급[:\s]*(매수|매도|중립|BUY|SELL|HOLD)',
            r'등급[:\s]*(매수|매도|중립|BUY|SELL|HOLD)',
        ]
        
        rating = None
        for pattern in rating_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                rating_text = matches[0].upper()
                if rating_text in ['BUY', '매수']:
                    rating = '매수'
                elif rating_text in ['SELL', '매도']:
                    rating = '매도'
                elif rating_text in ['HOLD', '중립']:
                    rating = '중립'
                
                print(f"✓ 투자의견: {rating}")
                break
        
        # 의견변경 추출
        opinion_change_patterns = [
            r'의견변경[:\s]*(유지|상향|하향|신규)',
            r'등급변경[:\s]*(유지|상향|하향|신규)',
        ]
        
        opinion_change = None
        for pattern in opinion_change_patterns:
            matches = re.findall(pattern, text)
            if matches:
                opinion_change = matches[0]
                print(f"✓ 의견변경: {opinion_change}")
                break
        
        # 기본값 설정
        if not rating:
            rating = "매수"  # 상상인증권 기본값
        if not opinion_change:
            opinion_change = "유지"
        
        return rating, opinion_change
    
    def extract_analyst_info(self, text):
        """애널리스트 정보 추출"""
        print(f"\n=== 애널리스트 정보 추출 ===")
        
        # 애널리스트명 추출
        analyst_patterns = [
            r'애널리스트[:\s]*([가-힣]{2,4})',
            r'작성자[:\s]*([가-힣]{2,4})',
            r'연구원[:\s]*([가-힣]{2,4})',
            r'([가-힣]{2,4})\s*애널리스트',
            r'([가-힣]{2,4})\s*연구원',
        ]
        
        analyst_name = None
        for pattern in analyst_patterns:
            matches = re.findall(pattern, text)
            if matches:
                analyst_name = matches[0]
                print(f"✓ 애널리스트: {analyst_name}")
                break
        
        # 상상인증권으로 고정
        company_name = '상상인증권'
        
        return analyst_name, company_name
    
    def extract_report_title(self, text, pdf_path):
        """리포트 제목 추출"""
        print(f"\n=== 리포트 제목 추출 ===")
        
        lines = text.split('\n')
        
        # 종목명 다음 줄들에서 제목 찾기
        for i, line in enumerate(lines[:10]):
            line = line.strip()
            if line and len(line) > 5 and len(line) < 100:
                # 제목으로 보이는 패턴들
                if (not re.search(r'(상상인증권|종가|현재가|목표|주가|원|%|pt|억원)', line) and
                    not re.match(r'^\d+$', line) and
                    not re.match(r'^\d{4}[\.\-]\d{2}[\.\-]\d{2}', line)):
                    print(f"✓ 제목 발견: {line}")
                    return line
        
        # 파일명에서 제목 추출 시도
        filename = os.path.basename(pdf_path)
        if filename.endswith('.pdf'):
            filename = filename[:-4]
        
        return filename
    
    def extract_investment_rationale(self, text):
        """투자 근거 추출"""
        print(f"\n=== 투자 근거 추출 ===")
        
        # 전체 텍스트에서 투자 근거 부분 찾기
        lines = text.split('\n')
        rationale_lines = []
        
        # 의미있는 내용이 있는 줄들 수집
        for line in lines:
            line = line.strip()
            if (line and len(line) > 20 and
                not re.search(r'(상상인증권|종가|현재가|목표|주가|^\d+$|^[\d\.\-]+%$)', line)):
                rationale_lines.append(line)
        
        if rationale_lines:
            # 처음 몇 줄을 합쳐서 투자 근거로 사용
            rationale_text = ' '.join(rationale_lines[:5])
            
            # 길이 제한
            if len(rationale_text) > 500:
                rationale_text = rationale_text[:500] + "..."
            
            print(f"✓ 투자 근거 추출 완료 (길이: {len(rationale_text)})")
            return rationale_text
        
        return "투자 근거 정보 없음"
    
    def extract_report_date(self, text, filename):
        """리포트 날짜 추출"""
        print(f"\n=== 리포트 날짜 추출 ===")
        
        # 텍스트에서 날짜 찾기
        date_patterns = [
            r'(\d{4})\s*[\.\-]\s*(\d{1,2})\s*[\.\-]\s*(\d{1,2})',
            r'(\d{2})[\.\-](\d{1,2})[\.\-](\d{1,2})',
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                year, month, day = matches[0]
                if len(year) == 2:
                    year = '20' + year
                
                try:
                    date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    print(f"✓ 날짜 발견: {date_str}")
                    return date_str
                except:
                    continue
        
        # 파일명에서 날짜 추출 시도
        filename_date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
        if filename_date_match:
            date_str = filename_date_match.group(0)
            print(f"✓ 파일명에서 날짜 발견: {date_str}")
            return date_str
        
        # 기본값: 오늘 날짜
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"✓ 기본 날짜 사용: {today}")
        return today
    
    def parse_pdf(self, pdf_path):
        """PDF 파싱 메인 함수"""
        print(f"\n{'='*80}")
        print(f"상상인증권 PDF 파싱 시작: {os.path.basename(pdf_path)}")
        print(f"{'='*80}")
        
        # 텍스트 추출
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            print("텍스트 추출 실패")
            return None
        
        filename = os.path.basename(pdf_path)
        
        # 정보 추출
        stock_name, stock_code = self.extract_stock_info(text)
        current_price, target_price, upside_potential = self.extract_price_info(text)
        rating, opinion_change = self.extract_rating_info(text)
        analyst_name, company_name = self.extract_analyst_info(text)
        report_title = self.extract_report_title(text, pdf_path)
        report_date = self.extract_report_date(text, filename)
        investment_rationale = self.extract_investment_rationale(text)
        
        # 데이터 구성
        data = {
            'report_id': str(uuid.uuid4()),
            'stock_code': stock_code,
            'stock_name': stock_name,
            'report_title': report_title,
            'report_date': report_date,
            'report_type': '기업분석',
            'analyst_name': analyst_name or 'Unknown',
            'company_name': company_name,
            'rating': rating,
            'opinion_change': opinion_change,
            'target_price': target_price,
            'current_price': current_price,
            'upside_potential': upside_potential,
            'investment_rationale': investment_rationale,
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
        
        for i, pdf_file in enumerate(pdf_files):
            pdf_path = os.path.join(pdf_folder_path, pdf_file)
            print(f"\n처리 중 ({i+1}/{len(pdf_files)}): {pdf_file}")
            
            try:
                result = self.parse_pdf(pdf_path)
                if result:
                    success_count += 1
                    print(f"✓ 성공: {pdf_file}")
                else:
                    error_count += 1
                    print(f"✗ 실패: {pdf_file}")
            except Exception as e:
                error_count += 1
                print(f"✗ 오류: {pdf_file} - {str(e)}")
        
        print(f"\n{'='*80}")
        print(f"처리 완료")
        print(f"성공: {success_count}개")
        print(f"실패: {error_count}개")
        print(f"총 데이터: {len(self.data_list)}개")
        print(f"{'='*80}")

def main():
    """메인 실행 함수"""
    parser = SangsanginConsensusParser()
    
    # 현재 파일의 디렉토리 경로를 기준으로 상대경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # PDF 폴더 경로 설정
    pdf_folder_path = os.path.join(current_dir, "..", "consensus", "sangsangin")
    
    # CSV 출력 경로 설정
    output_path = os.path.join(current_dir, "..", "consensus_parsed", "sangsangin_consensus_reports.csv")
    
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
                if data['target_price']:
                    print(f"   투자의견: {data['rating']}, 목표가: {data['target_price']:,}원")
                else:
                    print(f"   투자의견: {data['rating']}, 목표가: None")
                if data.get('investment_rationale') and data['investment_rationale'] != '투자 근거 정보 없음':
                    rationale_preview = data['investment_rationale'][:100] + "..." if len(data['investment_rationale']) > 100 else data['investment_rationale']
                    print(f"   투자근거: {rationale_preview}")
            
            # CSV 저장
            parser.save_to_csv(output_path)
            
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
