import os
import re
import pandas as pd
import json
from datetime import datetime
from docling.document_converter import DocumentConverter
from pathlib import Path
import uuid
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KiwoomImprovedParser:
    def __init__(self, pdf_folder_path, output_dir):
        self.pdf_folder_path = Path(pdf_folder_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.converter = DocumentConverter()
        
    def extract_text_from_pdf(self, pdf_path):
        """PDF에서 텍스트 추출"""
        try:
            result = self.converter.convert(pdf_path)
            return result.document.export_to_markdown(), result.document
        except Exception as e:
            logger.error(f"PDF 텍스트 추출 실패 {pdf_path}: {e}")
            return "", None
    
    def parse_filename(self, filename):
        """파일명에서 기본 정보 추출"""
        # 예: 2025-05-15_디오_키움증권.pdf
        pattern = r'(\d{4}-\d{2}-\d{2})_(.+)_키움증권\.pdf'
        match = re.match(pattern, filename)
        
        if match:
            report_date = match.group(1)
            stock_name = match.group(2)
            return report_date, stock_name
        return None, None
    
    def extract_stock_code(self, text):
        """텍스트에서 종목코드 추출"""
        # "## 디오 (039840)" 패턴 찾기
        pattern = r'##\s*([^(]+)\s*\((\d{6})\)'
        match = re.search(pattern, text)
        if match:
            return match.group(2)
        
        # 다른 패턴들도 시도
        patterns = [
            r'\((\d{6})\)',  # (039840)
            r'종목코드[\s:]*(\d{6})',
            r'Stock Code[\s:]*(\d{6})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def extract_analyst_name(self, text):
        """애널리스트 이름 추출"""
        # "의료기기 Analyst 신민수 alstn0527@kiwoom.com" 패턴
        pattern = r'Analyst\s+([가-힣]{2,4})\s+[a-zA-Z0-9_.+-]+@kiwoom\.com'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        
        # 다른 패턴들
        patterns = [
            r'애널리스트[\s:]*([가-힣]{2,4})',
            r'분석자[\s:]*([가-힣]{2,4})',
            r'작성자[\s:]*([가-힣]{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def extract_rating(self, text):
        """투자의견 추출"""
        # "## Not Rated" 패턴에서 추출
        pattern = r'##\s*(Not\s*Rated|Buy|매수|Sell|매도|Hold|보유|Strong\s*Buy|Outperform|Underperform)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            rating = match.group(1).strip()
            if 'not rated' in rating.lower():
                return 'Not Rated'
            elif any(word in rating.lower() for word in ['buy', '매수', 'strong']):
                return '매수'
            elif any(word in rating.lower() for word in ['hold', '보유']):
                return '보유'
            elif any(word in rating.lower() for word in ['sell', '매도']):
                return '매도'
            return rating
        
        return None
    
    def extract_target_price(self, text):
        """목표주가 추출"""
        # 투자지표 테이블에서 찾기나 별도 목표주가 표시
        patterns = [
            r'목표주?가[\s:]*([0-9,]+)원?',
            r'Target\s*Price[\s:]*([0-9,]+)',
            r'TP[\s:]*([0-9,]+)',
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
        # "주가(5/14): 20,950원" 패턴
        pattern = r'주가\([^)]*\)[\s:]*([0-9,]+)원?'
        match = re.search(pattern, text)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return float(price_str)
            except ValueError:
                pass
        
        return None
    
    def extract_report_title(self, text):
        """리포트 제목 추출"""
        # "## 수비 후 공격 위한 미드필더들의 부단한 노력" 같은 패턴
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            # ## 헤더 중에서 의미있는 제목 찾기
            if line.startswith('##') and len(line) > 5:
                title = line.replace('##', '').strip()
                # 제외할 헤더들
                exclude_keywords = ['not rated', 'stock data', 'company data', '투자지표', 'price trend']
                if not any(keyword in title.lower() for keyword in exclude_keywords):
                    # 종목코드가 포함된 헤더가 아니고, 의미있는 제목인지 확인
                    if not re.search(r'\(\d{6}\)', title) and len(title) > 3:
                        return title
        
        return "제목 미상"
    
    def extract_investment_rationale(self, text):
        """투자의견 근거 추출 - ## 제목 이후 다음 헤더나 제외 패턴 전까지의 내용 추출 (개선된 버전)"""
        lines = text.split('\n')
        content_lines = []
        
        # 제외할 패턴들 (더 포괄적으로)
        exclude_patterns = [
            'analyst', '@kiwoom.com', '자료:', 'fnguide', '키움증권 리서치센터',
            'compliance notice', '고지사항', '투자의견 및 적용기준', '투자등급 비율',
            '포괄손익계산서', '현금흐름표', '재무상태표', '(단위:', '십억 원)',
            '당사는', '발행주식을', '보유하고 있지', '사전 제공한 사실이', 
            '금융투자분석사는', '외부의 부당한', '조사분석자료는', '유가증권 투자를',
            '무단으로 인용', '저작권을 침해하는', '등급 추세:', 'universe:', 'msci'
        ]
        
        # ## 헤더(제목) 찾기 - 종목코드가 없는 의미있는 제목
        title_found = False
        start_collecting = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # ## 헤더 찾기 (종목코드가 포함된 헤더가 아닌 것)
            if line.startswith('##') and not title_found:
                title = line.replace('##', '').strip()
                # 제외할 헤더들
                exclude_headers = ['not rated', 'stock data', 'company data', '투자지표', 'price trend',
                                 'compliance notice', '고지사항', '목표주가', '주가(', '시가총액']
                
                # 종목코드가 포함되지 않고, 제외 헤더가 아닌 경우 제목으로 인식
                if (not re.search(r'\(\d{6}\)', title) and 
                    not any(keyword in title.lower() for keyword in exclude_headers) and 
                    len(title) > 5):
                    title_found = True
                    start_collecting = True
                    continue
            
            # 제목 이후부터 수집 시작
            if start_collecting:
                # <!-- image --> 만나면 중단
                if '<!-- image -->' in line:
                    break
                
                # 다른 ## 헤더 만나면 중단 (새로운 섹션 시작)
                if line.startswith('##'):
                    break
                
                # 제외 패턴 체크 (소문자로 변환해서)
                line_lower = line.lower()
                if any(pattern in line_lower for pattern in exclude_patterns):
                    break  # 고지사항이나 메타데이터 시작되면 완전히 중단
                
                # 테이블 형태 데이터 제외
                if line.count('|') > 2 or line.startswith('|'):
                    continue
                
                # 짧은 메타데이터성 정보 제외
                if (line_lower.startswith('목표주가') or line_lower.startswith('주가(') or 
                    line_lower.startswith('시가총액') or line_lower.startswith('buy(') or
                    line_lower.startswith('not rated')):
                    continue
                
                # 의미있는 내용만 수집 (빈 줄이 아니고 너무 짧지 않은 것)
                if len(line) > 20:
                    content_lines.append(line)
        
        # 수집된 내용이 없거나 너무 적으면 다른 방법 시도
        if len(content_lines) < 2:
            # 전체 텍스트에서 실적/분석 관련 긴 문장들만 추출
            for line in lines:
                line = line.strip()
                line_lower = line.lower()
                
                # 고지사항이나 메타데이터 제외
                if any(pattern in line_lower for pattern in exclude_patterns):
                    continue
                
                # 실적이나 분석 내용이 포함된 긴 문장 수집
                if (len(line) > 50 and 
                    not line.startswith('##') and
                    not line.startswith('|') and
                    '<!-- image -->' not in line and
                    any(keyword in line_lower for keyword in 
                        ['실적', '매출', '영업이익', '분기', '전망', '예상', '성장', '사업', '투자', '개선', '증가', '감소'])):
                    content_lines.append(line)
                    
                    # 충분히 수집했으면 중단
                    if len(content_lines) > 15:
                        break
        
        # 최종 결과 정리
        rationale = ' '.join(content_lines)
        
        # 길이 조정 및 정리
        if len(rationale) > 2000:
            sentences = rationale.split('. ')
            result = ""
            for sentence in sentences:
                if len(result + sentence) < 1800:
                    result += sentence + ". "
                else:
                    break
            rationale = result.rstrip()
            if not rationale.endswith('.'):
                rationale += "..."
        elif len(rationale) < 100:
            rationale = "투자의견 근거 추출 실패 - 적절한 본문 내용을 찾을 수 없음"
        
        return rationale

    def extract_investment_rationale_from_chunks(self, doc):
        """doc.chunks를 활용한 투자의견 근거 추출 - 개선된 버전"""
        if not doc or not hasattr(doc, 'chunks'):
            return "문서 구조를 읽을 수 없습니다"
            
        content_parts = []
        collecting = False
        found_main_title = False
        
        # 제외할 패턴들 (더 포괄적으로)
        exclude_patterns = [
            'analyst', '@kiwoom.com', '자료:', 'fnguide', '키움증권 리서치센터',
            'compliance notice', '고지사항', '투자의견 및 적용기준', '투자등급 비율',
            '포괄손익계산서', '현금흐름표', '재무상태표', '(단위:', '십억 원)',
            '당사는', '발행주식을', '보유하고 있지', '사전 제공한 사실이', 
            '금융투자분석사는', '외부의 부당한', '조사분석자료는', '유가증권 투자를',
            '무단으로 인용', '저작권을 침해하는', 'buy(maintain)', 'buy (maintain)',
            '목표주가:', '주가(', '시가총액:', 'not rated', 'stock data', 'company data',
            '등급 추세:', 'universe:', 'msci', '상향 ▲', '하향 ▼'
        ]
        
        for chunk in doc.chunks:
            if hasattr(chunk, 'text') and chunk.text:
                text = chunk.text.strip()
                
                if not text or len(text) < 10:
                    continue
                
                # 소문자로 변환해서 패턴 체크
                text_lower = text.lower()
                
                # 제외할 패턴 체크
                if any(pattern in text_lower for pattern in exclude_patterns):
                    continue
                
                # 헤딩 타입 확인
                is_heading = (text.startswith('##') or 
                             len(text) < 100 and text.count('\n') == 0 and len(text.split()) < 15)
                
                if is_heading:
                    # 종목코드가 포함된 메인 제목 찾기
                    if re.search(r'\(\d{6}\)', text):
                        found_main_title = True
                        continue
                    
                    # 메인 제목 이후의 의미있는 서브 제목 찾기
                    if found_main_title and not collecting:
                        title = text.replace('##', '').strip()
                        
                        # 의미있는 제목인지 확인 (길이와 내용으로 판단)
                        if (len(title) > 8 and 
                            not any(exclude_word in title.lower() for exclude_word in 
                                   ['not rated', 'stock data', 'company data', '투자지표', 'price trend',
                                    'compliance', '고지사항', '목표주가', '주가(', '시가총액']) and
                            not re.search(r'\(\d{6}\)', title)):
                            collecting = True
                            continue
                    
                    # 다른 헤딩을 만나면 수집 중단
                    elif collecting and len(text) > 5:
                        break
                
                # 본문 텍스트 수집
                elif collecting and not is_heading:
                    # 테이블 데이터나 단순 나열 제외
                    if (text.count('|') > 3 or text.count('\t') > 5 or
                        text_lower.startswith('주)') or text_lower.startswith('note:')):
                        continue
                    
                    # 짧은 단순 문구들 제외
                    if len(text) < 30:
                        continue
                    
                    # 숫자만 있는 라인 제외
                    if text.replace('.', '').replace(',', '').replace('%', '').replace(' ', '').isdigit():
                        continue
                    
                    # 의미있는 본문만 수집
                    content_parts.append(text)
                    
                    # 충분히 수집했으면 중단
                    if len(' '.join(content_parts)) > 2500:
                        break
        
        # chunks 방법으로 충분한 내용을 얻지 못했으면 마크다운 텍스트 기반 백업 방법 사용
        if len(content_parts) < 2 or len(' '.join(content_parts)) < 200:
            return self.extract_investment_rationale_fallback(doc)
        
        # 결과 정리
        rationale = ' '.join(content_parts)
        
        # 추가 정리 (문장 끝에서 자르기)
        if len(rationale) > 2000:
            sentences = rationale.split('. ')
            result = ""
            for sentence in sentences:
                if len(result + sentence) < 1800:
                    result += sentence + ". "
                else:
                    break
            rationale = result.rstrip()
            if not rationale.endswith('.'):
                rationale += "..."
        
        return rationale

    def extract_investment_rationale_fallback(self, doc):
        """chunks 방법 실패 시 백업용 추출 방법"""
        try:
            text = doc.export_to_markdown()
            return self.extract_investment_rationale(text)
        except:
            return "투자의견 근거 추출 실패 - chunks 및 백업 방법 모두 실패"
    
    def parse_single_pdf(self, pdf_path):
        """단일 PDF 파일 파싱"""
        logger.info(f"파싱 중: {pdf_path.name}")
        
        # 파일명에서 기본 정보 추출
        report_date, stock_name = self.parse_filename(pdf_path.name)
        if not report_date or not stock_name:
            logger.warning(f"파일명 파싱 실패: {pdf_path.name}")
            return None
        
        # PDF 텍스트 추출
        text, doc = self.extract_text_from_pdf(pdf_path)
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
        
        # chunks를 사용한 investment_rationale 추출 시도, 실패시 기존 방법 사용
        if doc:
            investment_rationale = self.extract_investment_rationale_from_chunks(doc)
            # chunks 방법이 실패했으면 기존 방법 사용
            if "추출 실패" in investment_rationale or len(investment_rationale) < 100:
                investment_rationale = self.extract_investment_rationale(text)
        else:
            investment_rationale = self.extract_investment_rationale(text)
        
        # 상승여력 계산
        upside_potential = None
        if target_price and current_price and current_price > 0:
            upside_potential = round(((target_price - current_price) / current_price) * 100, 1)
        
        # 결과 데이터 (원래 요청한 필드 순서대로)
        result = {
            'report_id': str(uuid.uuid4()),
            'stock_code': stock_code,
            'stock_name': stock_name,
            'report_title': report_title,
            'report_date': report_date,
            'report_type': '기업분석',
            'analyst_name': analyst_name,
            'company_name': '키움증권',
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
        
        # 전체 결과를 CSV와 JSON으로 저장 (하나의 파일에)
        if results:
            # CSV 저장 (원래 요청한 필드 순서대로)
            df = pd.DataFrame(results)
            csv_path = self.output_dir / "kiwoom_consensus_reports_complete.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            # 전체 JSON 저장 (하나의 파일에 모든 레포트)
            json_path = self.output_dir / "kiwoom_consensus_reports_complete.json"
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
        print(f"애널리스트 수: {df['analyst_name'].nunique()}")
        if 'rating' in df.columns and not df['rating'].isna().all():
            print(f"투자의견 분포:")
            print(df['rating'].value_counts())
        print(f"\n종목별 레포트 수:")
        print(df['stock_name'].value_counts())

def main():
    # 경로 설정
    pdf_folder = r"c:\Users\jse\Desktop\vscode\hanium_project\Finsight-service\Consensus-ETL\project\consensus\kiwoom"
    output_dir = r"c:\Users\jse\Desktop\vscode\hanium_project\Finsight-service\Consensus-ETL\project\consensus_parsed"
    
    # 파서 실행
    parser = KiwoomImprovedParser(pdf_folder, output_dir)
    results = parser.parse_all_pdfs()
    
    return results

if __name__ == "__main__":
    main()
