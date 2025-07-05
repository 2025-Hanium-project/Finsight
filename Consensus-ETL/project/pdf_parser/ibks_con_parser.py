#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import pandas as pd
import json
import pdfplumber
from datetime import datetime
from pathlib import Path
import uuid
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IBKSConsensusParser:
    def __init__(self, pdf_folder_path, output_dir):
        self.pdf_folder_path = Path(pdf_folder_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def parse_filename(self, filename):
        """파일명에서 기본 정보 추출"""
        # 예: 삼양식품_20250516.pdf
        pattern = r'(.+)_(\d{8})\.pdf'
        match = re.match(pattern, filename)
        
        if match:
            stock_name = match.group(1)
            date_str = match.group(2)
            # YYYYMMDD -> YYYY-MM-DD 형식으로 변환
            report_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            return report_date, stock_name
        return None, None
    
    def extract_text_from_pdf(self, pdf_path):
        """PDF에서 텍스트 추출"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                return full_text
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패 {pdf_path}: {e}")
            return ""
    
    def extract_stock_code(self, text):
        """텍스트에서 종목코드 추출"""
        # IBK증권 리포트에서 종목코드 패턴 찾기
        patterns = [
            r'종목코드[\s:]*(\d{6})',
            r'Stock Code[\s:]*(\d{6})',
            r'\((\d{6})\)',  # (039840) 형태
            r'코드[\s:]*(\d{6})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def extract_analyst_name(self, text):
        """애널리스트 이름 추출"""
        patterns = [
            r'애널리스트[\s:]*([가-힣]{2,4})',
            r'Analyst[\s:]*([가-힣]{2,4})',
            r'분석자[\s:]*([가-힣]{2,4})',
            r'작성자[\s:]*([가-힣]{2,4})',
            r'연구원[\s:]*([가-힣]{2,4})',
            r'리서치[\s:]*([가-힣]{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def extract_rating(self, text):
        """투자의견 추출"""
        patterns = [
            r'투자의견[\s:]*([가-힣A-Za-z\s]+)',
            r'투자등급[\s:]*([가-힣A-Za-z\s]+)',
            r'Rating[\s:]*([A-Za-z\s]+)',
            r'Opinion[\s:]*([A-Za-z\s]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
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
            r'목표가[\s:]*([0-9,]+)',
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
            r'Current\s*Price[\s:]*([0-9,]+)',
            r'주가[\s:]*([0-9,]+)원?',
            r'종가[\s:]*([0-9,]+)원?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        
        return None
    
    def extract_report_title(self, text):
        """리포트 제목 추출"""
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            # 의미있는 제목 찾기 (종목명 다음에 오는 긴 텍스트)
            if len(line) > 10 and len(line) < 100:
                # 제외할 패턴들
                exclude_patterns = ['종목코드', '애널리스트', '투자의견', '목표주가', '현재주가']
                if not any(pattern in line for pattern in exclude_patterns):
                    # 한글이 포함되고 적당한 길이인 경우 제목으로 인식
                    if re.search(r'[가-힣]', line) and 5 < len(line) < 80:
                        return line
        
        return "제목 미상"
    
    def extract_investment_rationale(self, text):
        """투자의견 근거 추출"""
        lines = text.split('\n')
        content_lines = []
        
        # 제외할 패턴들
        exclude_patterns = [
            '종목코드', '애널리스트', '투자의견', '목표주가', '현재주가',
            '리서치', '증권', '당사는', '면책조항', '고지사항',
            '이 자료는', '본 보고서', '투자 권유', '투자 판단',
            '----------------------------------------',
            '========================================',
        ]
        
        # 시작할 수 있는 키워드들
        start_keywords = [
            '실적', '매출', '영업이익', '당기순이익', '전망', '예상',
            '성장', '확장', '투자', '사업', '개발', '시장', '경쟁',
            '플랫폼', '정상화', '본격화', '핵심', '분기', '연간',
            'Q1', 'Q2', 'Q3', 'Q4', '1Q', '2Q', '3Q', '4Q'
        ]
        
        start_collecting = False
        
        for line in lines:
            line = line.strip()
            
            # 빈 줄이나 너무 짧은 줄 건너뛰기
            if len(line) < 20:
                continue
            
            # 제외할 패턴 확인
            if any(pattern in line for pattern in exclude_patterns):
                # 고지사항이나 면책조항 시작되면 중단
                if any(stop_word in line for stop_word in ['당사는', '면책조항', '고지사항', '이 자료는']):
                    break
                continue
            
            # 수집 시작 조건
            if not start_collecting:
                if (any(keyword in line for keyword in start_keywords) and len(line) > 30) or \
                   (len(line) > 50 and any(ending in line for ending in ['다.', '습니다.', '됩니다.', '예정입니다.', '것으로', '있습니다.'])):
                    start_collecting = True
            
            if start_collecting:
                # 의미있는 내용만 수집
                if len(line) > 20:
                    content_lines.append(line)
                    
                    # 충분히 수집했으면 중단
                    if len(' '.join(content_lines)) > 2500:
                        break
        
        # 수집된 내용이 없거나 너무 적으면 전체에서 의미있는 문장 추출
        if len(content_lines) < 3 or len(' '.join(content_lines)) < 200:
            content_lines = []
            for line in lines:
                line = line.strip()
                if (len(line) > 40 and 
                    not any(pattern in line for pattern in exclude_patterns) and
                    any(keyword in line for keyword in start_keywords)):
                    content_lines.append(line)
                    if len(content_lines) > 15:
                        break
        
        # 최종 결과 정리
        rationale = ' '.join(content_lines)
        
        # 길이 조정
        if len(rationale) > 2500:
            sentences = rationale.split('. ')
            result = ""
            for sentence in sentences:
                if len(result + sentence) < 2000:
                    result += sentence + ". "
                else:
                    break
            rationale = result.rstrip()
            if not rationale.endswith('.'):
                rationale += "..."
        elif len(rationale) < 100:
            rationale = "투자의견 근거 추출 실패 - 적절한 본문 내용을 찾을 수 없음"
        
        return rationale
    
    def parse_single_pdf(self, pdf_path):
        """단일 PDF 파일 파싱"""
        logger.info(f"파싱 중: {pdf_path.name}")
        
        # 파일명에서 기본 정보 추출
        report_date, stock_name = self.parse_filename(pdf_path.name)
        if not report_date or not stock_name:
            logger.warning(f"파일명 파싱 실패: {pdf_path.name}")
            return None
        
        # PDF 텍스트 추출
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning(f"텍스트 추출 실패: {pdf_path.name}")
            return None
        
        # 정보 추출
        stock_code = self.extract_stock_code(text)
        analyst_name = self.extract_analyst_name(text)
        rating = self.extract_rating(text)
        target_price = self.extract_target_price(text)
        current_price = self.extract_current_price(text)
        report_title = self.extract_report_title(text)
        investment_rationale = self.extract_investment_rationale(text)
        
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
        
        # 결과를 CSV와 JSON으로 저장
        if results:
            # CSV 저장
            df = pd.DataFrame(results)
            csv_path = self.output_dir / "ibks_consensus_reports_complete.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            # JSON 저장
            json_path = self.output_dir / "ibks_consensus_reports_complete.json"
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
        print("\n=== IBK투자증권 파싱 결과 요약 ===")
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
    # 경로 설정
    pdf_folder = r"c:\Users\jse\Desktop\vscode\hanium_project\Finsight-service\Consensus-ETL\project\consensus\ibks"
    output_dir = r"c:\Users\jse\Desktop\vscode\hanium_project\Finsight-service\Consensus-ETL\project\consensus_parsed"
    
    # 파서 실행
    parser = IBKSConsensusParser(pdf_folder, output_dir)
    results = parser.parse_all_pdfs()
    
    return results

if __name__ == "__main__":
    main()
