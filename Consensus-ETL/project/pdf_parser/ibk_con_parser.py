#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
        """파일명에서 기본 정보 추출 - {종목명}_{YYYYMMDD}.pdf 형식"""
        pattern = r'(.+)_(\d{8})\.pdf'
        match = re.match(pattern, filename)
        
        if match:
            stock_name = match.group(1)
            date_str = match.group(2)
            # YYYYMMDD -> YYYY-MM-DD 형식으로 변환
            report_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            return stock_name, report_date
        return None, None
    
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
        """리포트 제목 추출"""
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # 의미있는 제목 찾기 (너무 짧지 않고, 특정 패턴이 아닌 것)
            if (len(line) > 10 and len(line) < 100 and
                not re.search(r'^\d+$', line) and  # 숫자만 있는 줄 제외
                not re.search(r'페이지|page', line, re.IGNORECASE) and
                not line.startswith('IBK') and
                '투자증권' not in line):
                # 한글이 포함되어 있으면 제목으로 판단
                if re.search(r'[가-힣]', line):
                    return line
        
        return "제목 미상"
    
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
    
    def parse_single_pdf(self, pdf_path):
        """단일 PDF 파일 파싱"""
        logger.info(f"파싱 중: {pdf_path.name}")
        
        # 파일명에서 기본 정보 추출
        stock_name, report_date = self.parse_filename(pdf_path.name)
        if not stock_name or not report_date:
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
    # 경로 설정
    pdf_folder = r"c:\Users\jse\Desktop\vscode\hanium_project\Finsight-service\Consensus-ETL\project\consensus\ibks"
    output_dir = r"c:\Users\jse\Desktop\vscode\hanium_project\Finsight-service\Consensus-ETL\project\consensus_parsed"
    
    # 파서 실행
    parser = IBKConsensusParser(pdf_folder, output_dir)
    results = parser.parse_all_pdfs()
    
    return results

if __name__ == "__main__":
    main()
