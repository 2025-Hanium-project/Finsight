import os
import sys
import json
import argparse
import time
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
import warnings
import re
import glob
from pathlib import Path

# ============================================================================
# 🔑 Groq API 키 설정 (여기에 본인의 API 키를 입력하세요)
# ============================================================================
GROQ_API_KEY = "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"  # 여기에 실제 API 키 입력
# ============================================================================

def install_required_packages():
    """필요한 패키지들을 자동으로 설치합니다."""
    required_packages = {
        'fitz': 'PyMuPDF',
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'requests': 'requests',
        'pdfplumber': 'pdfplumber'  # Java 없이 표 추출 가능
    }
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"Installing {package_name}...")
            os.system(f"pip install {package_name}")

install_required_packages()

import fitz
import pandas as pd
import pdfplumber  # Java 없이 표 추출

warnings.filterwarnings('ignore')

class BatchSecuritiesParser:
    """일괄 증권사 리포트 파싱 클래스 (폴더 단위 처리)"""
    
    def __init__(self, input_folder: str, output_folder: str):
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.processed_files = []
        self.failed_files = []
        self.summary_data = []
        
        # 출력 폴더 생성
        os.makedirs(output_folder, exist_ok=True)
        
        print(f"📂 입력 폴더: {input_folder}")
        print(f"📁 출력 폴더: {output_folder}")
    
    def find_pdf_files(self) -> List[str]:
        """입력 폴더에서 PDF 파일들 찾기"""
        pdf_files = []
        
        # 다양한 패턴으로 PDF 파일 검색
        patterns = [
            os.path.join(self.input_folder, "*.pdf"),
            os.path.join(self.input_folder, "**", "*.pdf")  # 하위 폴더 포함
        ]
        
        for pattern in patterns:
            pdf_files.extend(glob.glob(pattern, recursive=True))
        
        # 중복 제거 및 정렬
        pdf_files = sorted(list(set(pdf_files)))
        
        print(f"🔍 발견된 PDF 파일: {len(pdf_files)}개")
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"  {i}. {os.path.basename(pdf_file)}")
        
        return pdf_files
    
    def create_output_subfolder(self, pdf_filename: str) -> str:
        """각 PDF 파일별 출력 하위 폴더 생성"""
        # 파일명에서 확장자 제거하고 안전한 폴더명 생성
        safe_name = os.path.splitext(pdf_filename)[0]
        # 특수문자를 안전한 문자로 변환
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', safe_name)
        safe_name = safe_name.replace(' ', '_')
        
        # 너무 긴 이름은 줄이기
        if len(safe_name) > 100:
            safe_name = safe_name[:100]
        
        subfolder = os.path.join(self.output_folder, safe_name)
        os.makedirs(subfolder, exist_ok=True)
        return subfolder
    
    def process_single_pdf(self, pdf_path: str, no_ai: bool = False, no_images: bool = False, image_analysis: bool = False) -> Dict:
        """개별 PDF 파일 처리 (AI 분석 간격 조절)"""
        pdf_filename = os.path.basename(pdf_path)
        print(f"\n{'='*60}")
        print(f"📄 처리 중: {pdf_filename}")
        print(f"{'='*60}")
        
        # 개별 파일용 출력 폴더 생성
        output_subfolder = self.create_output_subfolder(pdf_filename)
        
        try:
            # 파싱 실행
            parser = EnhancedSecuritiesParser(pdf_path, output_subfolder)
            results = parser.parse_complete_report(no_images, image_analysis)
            
            if results:
                # 결과 저장
                saved_files = parser.save_results()
                
                # AI 분석 (옵션 + 간격 조절)
                ai_analysis_path = None
                if not no_ai:
                    print("🤖 AI 분석 요청 중...")
                    
                    # 파일 간 처리 간격 추가 (Rate Limit 방지)
                    time.sleep(random.uniform(3, 8))  # 3-8초 랜덤 대기
                    
                    analyzer = GroqAnalyzer()
                    analysis = analyzer.analyze_report(results)
                    
                    if analysis and "API 키가 설정되지 않아" not in analysis and "분석 실패" not in analysis:
                        ai_analysis_path = os.path.join(output_subfolder, f"groq_analysis_{results['report_type']}.txt")
                        with open(ai_analysis_path, 'w', encoding='utf-8') as f:
                            f.write("# Groq API 분석 결과\n\n")
                            f.write(f"파일명: {pdf_filename}\n")
                            f.write(f"리포트 타입: {results['report_type']}\n")
                            f.write(f"분석 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                            f.write(analysis)
                        print("✅ AI 분석 완료 및 저장")
                    else:
                        print(f"⚠️ AI 분석 실패 또는 건너뜀: {analysis[:100]}...")
                
                # 성공 정보 기록
                success_info = {
                    'filename': pdf_filename,
                    'status': 'success',
                    'report_type': results['report_type'],
                    'output_folder': output_subfolder,
                    'parsing_info': results['parsing_info'],
                    'saved_files': saved_files,
                    'ai_analysis': ai_analysis_path,
                    'timestamp': datetime.now().isoformat()
                }
                
                # 종목/시장 정보 추가
                if results['report_type'] == 'stock_report' and results.get('stock_info'):
                    success_info['stock_info'] = results['stock_info']
                elif results['report_type'] == 'market_report' and results.get('market_info'):
                    success_info['market_info'] = {k: v for k, v in results['market_info'].items() if k != 'key_driver'}
                
                self.processed_files.append(success_info)
                self.summary_data.append(success_info)
                
                print(f"✅ 성공: {pdf_filename}")
                return success_info
                
            else:
                raise Exception("파싱 결과가 없습니다")
                
        except Exception as e:
            # 실패 정보 기록
            failure_info = {
                'filename': pdf_filename,
                'status': 'failed',
                'error': str(e),
                'output_folder': output_subfolder,
                'timestamp': datetime.now().isoformat()
            }
            
            self.failed_files.append(failure_info)
            self.summary_data.append(failure_info)
            
            print(f"❌ 실패: {pdf_filename} - {e}")
            return failure_info
    
    def process_all_pdfs(self, no_ai: bool = False, no_images: bool = False, image_analysis: bool = False) -> Dict:
        """모든 PDF 파일 일괄 처리"""
        pdf_files = self.find_pdf_files()
        
        if not pdf_files:
            print("❌ 처리할 PDF 파일이 없습니다.")
            return None
        
        print(f"\n🚀 일괄 처리 시작: {len(pdf_files)}개 파일")
        start_time = datetime.now()
        
        # 각 파일 처리
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"\n📊 진행률: {i}/{len(pdf_files)} ({i/len(pdf_files)*100:.1f}%)")
            self.process_single_pdf(pdf_path, no_ai, no_images, image_analysis)
        
        # 처리 완료
        end_time = datetime.now()
        processing_time = end_time - start_time
        
        # 전체 결과 요약
        summary = {
            'total_files': len(pdf_files),
            'successful': len(self.processed_files),
            'failed': len(self.failed_files),
            'processing_time': str(processing_time),
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'input_folder': self.input_folder,
            'output_folder': self.output_folder,
            'processed_files': self.processed_files,
            'failed_files': self.failed_files
        }
        
        # 요약 보고서 저장
        self.save_batch_summary(summary)
        
        # 결과 출력
        print(f"\n{'='*60}")
        print("📊 일괄 처리 완료!")
        print(f"{'='*60}")
        print(f"📂 총 파일 수: {summary['total_files']}")
        print(f"✅ 성공: {summary['successful']}")
        print(f"❌ 실패: {summary['failed']}")
        print(f"⏱️ 처리 시간: {processing_time}")
        print(f"📁 출력 폴더: {self.output_folder}")
        
        if self.failed_files:
            print(f"\n❌ 실패한 파일들:")
            for failed in self.failed_files:
                print(f"  - {failed['filename']}: {failed['error']}")
        
        return summary
    
    def save_batch_summary(self, summary: Dict):
        """일괄 처리 요약 보고서 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. JSON 요약 저장
        json_path = os.path.join(self.output_folder, f"batch_summary_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # 2. 텍스트 요약 저장
        txt_path = os.path.join(self.output_folder, f"batch_summary_{timestamp}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("# 증권사 리포트 일괄 처리 요약\n\n")
            f.write(f"처리 일시: {summary['start_time']} ~ {summary['end_time']}\n")
            f.write(f"처리 시간: {summary['processing_time']}\n")
            f.write(f"입력 폴더: {summary['input_folder']}\n")
            f.write(f"출력 폴더: {summary['output_folder']}\n\n")
            
            f.write("## 처리 결과\n")
            f.write(f"- 총 파일 수: {summary['total_files']}\n")
            f.write(f"- 성공: {summary['successful']}\n")
            f.write(f"- 실패: {summary['failed']}\n\n")
            
            if summary['processed_files']:
                f.write("## 성공한 파일들\n")
                for file_info in summary['processed_files']:
                    f.write(f"\n### {file_info['filename']}\n")
                    f.write(f"- 리포트 타입: {file_info['report_type']}\n")
                    f.write(f"- 출력 폴더: {file_info['output_folder']}\n")
                    f.write(f"- 텍스트 길이: {file_info['parsing_info']['text_length']:,}자\n")
                    f.write(f"- 페이지 이미지 개수: {file_info['parsing_info']['images_count']}개\n")
                    
                    if file_info.get('stock_info'):
                        f.write("- 종목 정보:\n")
                        for key, value in file_info['stock_info'].items():
                            f.write(f"  - {key}: {value}\n")
            
            if summary['failed_files']:
                f.write("\n## 실패한 파일들\n")
                for failed in summary['failed_files']:
                    f.write(f"- {failed['filename']}: {failed['error']}\n")
        
        # 3. Excel 요약 저장 (성공한 파일들의 정보)
        if summary['processed_files']:
            excel_path = os.path.join(self.output_folder, f"batch_summary_{timestamp}.xlsx")
            
            # 데이터 프레임 생성
            excel_data = []
            for file_info in summary['processed_files']:
                row = {
                    '파일명': file_info['filename'],
                    '리포트타입': file_info['report_type'],
                    '텍스트길이': file_info['parsing_info']['text_length'],
                    '페이지이미지개수': file_info['parsing_info']['images_count'],
                    '출력폴더': file_info['output_folder'],
                    '처리시간': file_info['timestamp']
                }
                
                # 종목 정보 추가
                if file_info.get('stock_info'):
                    row.update({
                        '종목명': file_info['stock_info'].get('stock_name', ''),
                        '종목코드': file_info['stock_info'].get('stock_code', ''),
                        '투자의견': file_info['stock_info'].get('investment_opinion', ''),
                        '목표주가': file_info['stock_info'].get('target_price', ''),
                        '현재주가': file_info['stock_info'].get('current_price', ''),
                        '상승여력': file_info['stock_info'].get('upside_potential', ''),
                        '애널리스트': file_info['stock_info'].get('analyst', ''),
                        '증권사': file_info['stock_info'].get('securities_firm', '')
                    })
                
                excel_data.append(row)
            
            df = pd.DataFrame(excel_data)
            df.to_excel(excel_path, index=False, engine='openpyxl')
        
        print(f"\n📊 요약 보고서 저장:")
        print(f"  - JSON: {json_path}")
        print(f"  - 텍스트: {txt_path}")
        if summary['processed_files']:
            print(f"  - Excel: {excel_path}")

class EnhancedSecuritiesParser:
    """개선된 증권사 리포트 파싱 클래스 (Java 없이 표 추출)"""
    
    def __init__(self, pdf_path: str, output_dir: str = "output"):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.doc = None
        self.report_type = None
        self.results = {
            'metadata': {},
            'report_type': '',
            'text': '',
            'images': [],
            'structure': {},
            'stock_info': {},
            'market_info': {},
            'parsing_info': {}
        }
        
        os.makedirs(output_dir, exist_ok=True)
    
    def open_pdf(self) -> bool:
        """PDF 파일 열기"""
        try:
            self.doc = fitz.open(self.pdf_path)
            print(f"✅ PDF 열기 성공: {len(self.doc)} 페이지")
            return True
        except Exception as e:
            print(f"❌ PDF 열기 실패: {e}")
            return False
    
    def detect_report_type(self, text: str) -> str:
        """리포트 타입 감지 (일일시황 vs 개별종목)"""
        stock_patterns = [
            r'COMPANY UPDATE',
            r'BUY|HOLD|SELL',
            r'목표주가',
            r'현재주가',
            r'투자의견',
            r'Senior Analyst',
            r'Research Associate',
            r'\(\d{6}\)',  # 종목코드 패턴
            r'Target Price',
            r'Investment Opinion'
        ]
        
        market_patterns = [
            r'마감시황',
            r'일일시황',
            r'데일리',
            r'KOSPI.*pt',
            r'KOSDAQ.*pt',
            r'주요 수급 동향',
            r'KEY DRIVER',
            r'업종별',
            r'산업 전망'
        ]
        
        stock_score = sum(1 for pattern in stock_patterns if re.search(pattern, text, re.IGNORECASE))
        market_score = sum(1 for pattern in market_patterns if re.search(pattern, text, re.IGNORECASE))
        
        print(f"📊 종목 리포트 점수: {stock_score}, 시장 리포트 점수: {market_score}")
        
        return 'stock_report' if stock_score > market_score else 'market_report'
    
    def parse_text(self) -> str:
        """텍스트 추출 (개선된 버전)"""
        if not self.doc:
            return ""
        
        print("📄 텍스트 추출 중...")
        text_content = ""
        
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            page_text = page.get_text()
            
            # 빈 페이지나 너무 짧은 텍스트 필터링
            if len(page_text.strip()) > 10:
                text_content += f"\n--- 페이지 {page_num + 1} ---\n"
                text_content += page_text
        
        self.results['text'] = text_content
        self.report_type = self.detect_report_type(text_content)
        self.results['report_type'] = self.report_type
        
        print(f"✅ 텍스트 추출 완료: {len(text_content)} 문자")
        print(f"📋 감지된 리포트 타입: {self.report_type}")
        
        return text_content
    
    def parse_stock_info(self, text: str, image_paths: List[str] = None) -> Dict:
        """개별 종목 정보 파싱 (텍스트 + 이미지 분석)"""
        if self.report_type != 'stock_report':
            return {}
        
        print("📈 종목 정보 추출 중...")
        stock_info = {}
        
        # 1. 텍스트에서 종목 정보 추출
        text_stock_info = self._extract_stock_info_from_text(text)
        stock_info.update(text_stock_info)
        
        # 2. 이미지에서 종목 정보 추출 (보완)
        if image_paths and self.results.get('images'):
            try:
                analyzer = GroqAnalyzer()
                image_stock_info = analyzer.analyze_images_for_stock_info(
                    [img['path'] for img in self.results['images']], 
                    self.report_type
                )
                
                # 이미지에서 추출한 정보로 텍스트 정보 보완
                for key, value in image_stock_info.items():
                    if value and (key not in stock_info or not stock_info[key]):
                        stock_info[key] = value
                        print(f"  📸 이미지에서 {key}: {value}")
                
            except Exception as e:
                print(f"⚠️ 이미지 분석 중 오류: {e}")
                # 이미지 분석 실패 시에도 계속 진행
                pass
        
        self.results['stock_info'] = stock_info
        print(f"✅ 종목 정보 추출 완료: {len(stock_info)}개 필드")
        
        # 추출된 정보 출력
        if stock_info:
            print("📊 추출된 종목 정보:")
            for key, value in stock_info.items():
                print(f"  - {key}: {value}")
        
        return stock_info
    
    def _extract_stock_info_from_text(self, text: str) -> Dict:
        """텍스트에서 종목 정보 추출"""
        stock_info = {}
        
        # 종목명과 코드 추출 (개선된 패턴)
        stock_patterns = [
            r'([가-힣A-Za-z]+[가-힣A-Za-z\s]*)\s*\((\d{6})\)',
            r'종목명[:\s]*([가-힣A-Za-z]+)\s*\(?(\d{6})?\)?',
            r'회사명[:\s]*([가-힣A-Za-z]+)\s*\(?(\d{6})?\)?',
            r'([가-힣A-Za-z]+)\s*\((\d{6})\)',  # 간단한 패턴
            r'([가-힣A-Za-z]+)\s*종목코드[:\s]*(\d{6})'
        ]
        
        for pattern in stock_patterns:
            match = re.search(pattern, text)
            if match:
                stock_name = match.group(1).strip()
                # 불필요한 텍스트 제거
                stock_name = re.sub(r'\b(com|Earnings Preview|Price Trend)\b', '', stock_name, flags=re.IGNORECASE).strip()
                if stock_name and len(stock_name) > 1:
                    stock_info['stock_name'] = stock_name
                if match.group(2):
                    stock_info['stock_code'] = match.group(2)
                break
        
        # 파일명에서 종목 정보 추출 (보조)
        filename = os.path.basename(self.pdf_path)
        filename_stock_match = re.search(r'([가-힣A-Za-z]+)\((\d{6})\)', filename)
        if filename_stock_match and 'stock_name' not in stock_info:
            stock_info['stock_name'] = filename_stock_match.group(1)
            stock_info['stock_code'] = filename_stock_match.group(2)
        
        # 투자의견 추출
        investment_patterns = [
            r'투자의견[:\s]*([A-Z]+)',
            r'Investment Opinion[:\s]*([A-Z]+)',
            r'추천[:\s]*([A-Z]+)',
            r'Rating[:\s]*([A-Z]+)',
            r'\b(BUY|HOLD|SELL)\b'
        ]
        for pattern in investment_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                opinion = match.group(1).upper()
                if opinion in ['BUY', 'HOLD', 'SELL']:
                    stock_info['investment_opinion'] = opinion
                    break
        
        # 목표주가 추출 (개선된 패턴)
        target_price_patterns = [
            r'목표주?가[:\s]*([0-9,]+)\s*원?',
            r'Target Price[:\s]*([0-9,]+)',
            r'목표가격[:\s]*([0-9,]+)\s*원?',
            r'TP[:\s]*([0-9,]+)',
            r'목표가[:\s]*([0-9,]+)',
            r'Target[:\s]*([0-9,]+)'
        ]
        for pattern in target_price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                # 유효한 가격인지 확인 (1000원 이상)
                try:
                    price = int(price_str)
                    if price >= 1000:
                        stock_info['target_price'] = price_str
                        break
                except ValueError:
                    continue
        
        # 현재주가 추출 (개선된 패턴)
        current_price_patterns = [
            r'현재주?가[:\s]*([0-9,]+)\s*원?',
            r'Current Price[:\s]*([0-9,]+)',
            r'주가[:\s]*([0-9,]+)\s*원?',
            r'Price[:\s]*([0-9,]+)',
            r'현재가[:\s]*([0-9,]+)',
            r'Current[:\s]*([0-9,]+)'
        ]
        for pattern in current_price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                # 유효한 가격인지 확인 (1000원 이상)
                try:
                    price = int(price_str)
                    if price >= 1000:
                        stock_info['current_price'] = price_str
                        break
                except ValueError:
                    continue
        
        # 상승여력 계산
        if 'target_price' in stock_info and 'current_price' in stock_info:
            try:
                target = float(stock_info['target_price'])
                current = float(stock_info['current_price'])
                if current > 0:
                    upside = ((target - current) / current) * 100
                    stock_info['upside_potential'] = f"{upside:.2f}%"
            except (ValueError, ZeroDivisionError):
                pass
        
        # 시가총액 추출
        market_cap_patterns = [
            r'시가총액[:\s]*([0-9,.]+조?\s*원?)',
            r'Market Cap[:\s]*([0-9,.]+)',
            r'시총[:\s]*([0-9,.]+조?\s*원?)'
        ]
        for pattern in market_cap_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                stock_info['market_cap'] = match.group(1)
                break
        
        # 애널리스트 정보 추출
        analyst_patterns = [
            r'([가-힣A-Za-z\s]+)\s*Senior Analyst',
            r'애널리스트[:\s]*([가-힣A-Za-z\s]+)',
            r'Analyst[:\s]*([가-힣A-Za-z\s]+)',
            r'분석가[:\s]*([가-힣A-Za-z\s]+)'
        ]
        for pattern in analyst_patterns:
            match = re.search(pattern, text)
            if match:
                stock_info['analyst'] = match.group(1).strip()
                break
        
        # 증권사 정보 (파일명에서 추출)
        filename = os.path.basename(self.pdf_path)
        securities_firms = {
            '삼성증권': ['삼성증권', '삼성'],
            '미래에셋증권': ['미래에셋', 'mirae'],
            'KB증권': ['KB증권', 'KB'],
            'NH투자증권': ['NH투자', 'NH'],
            '한국투자증권': ['한국투자', '한투'],
            '신한투자증권': ['신한투자', '신한'],
            'SK증권': ['SK증권', 'SK'],
            '대신증권': ['대신증권', '대신'],
            '현대차증권': ['현대차', '현대'],
            'DB금융투자': ['DB금융', 'DB']
        }
        
        for firm_name, keywords in securities_firms.items():
            if any(keyword in filename for keyword in keywords):
                stock_info['securities_firm'] = firm_name
                break
        
        # 발행일 추출
        date_patterns = [
            r'(\d{4}[-./]\d{1,2}[-./]\d{1,2})',
            r'(\d{4}\.\s*\d{1,2}\.\s*\d{1,2})',
            r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)',
            r'(\d{1,2}/\d{1,2}/\d{4})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                stock_info['report_date'] = match.group(1)
                break
        
        # 파일명에서 날짜 추출 (보조)
        filename_date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if filename_date_match and 'report_date' not in stock_info:
            stock_info['report_date'] = filename_date_match.group(1)
        
        return stock_info
    
    def parse_market_info(self, text: str) -> Dict:
        """시장 정보 파싱 (일일시황용)"""
        if self.report_type != 'market_report':
            return {}
        
        print("📊 시장 정보 추출 중...")
        market_info = {}
        
        # 주요 지수 추출
        indicators = {
            'KOSPI': r'KOSPI[^\d]*([\d,]+\.?\d*[^\d]*\([^)]+\))',
            'KOSDAQ': r'KOSDAQ[^\d]*([\d,]+\.?\d*[^\d]*\([^)]+\))',
            'KOSPI200': r'KOSPI200[^\d]*([\d,]+\.?\d*[^\d]*\([^)]+\))',
            'USD_KRW': r'달러[-\s]*원\s*환율[^\d]*([\d,]+\.?\d*[^\d]*\([^)]+\))',
            'KR_10Y': r'10\s*년물.*금리[^\d]*([\d.]+%[^\d]*\([^)]+\))',
            'SP500': r'S&P500[^\d]*([\d,]+\.?\d*[^\d]*\([^)]+\))'
        }
        
        for key, pattern in indicators.items():
            match = re.search(pattern, text)
            if match:
                market_info[key] = match.group(1).strip()
        
        # KEY DRIVER 추출
        key_driver_patterns = [
            r'KEY DRIVER(.*?)(?=출처:|$)',
            r'주요 동향(.*?)(?=출처:|$)',
            r'시장 동향(.*?)(?=출처:|$)'
        ]
        for pattern in key_driver_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                market_info['key_driver'] = match.group(1).strip()
                break
        
        self.results['market_info'] = market_info
        print(f"✅ 시장 정보 추출 완료: {len(market_info)}개 필드")
        return market_info
    

    
    def extract_page_images(self) -> List[Dict]:
        """PDF 페이지 전체를 이미지로 캡처"""
        if not self.doc:
            return []
        
        print("📄 페이지 캡처 중...")
        page_images = []
        
        for page_num in range(len(self.doc)):
            try:
                page = self.doc[page_num]
                
                # 페이지를 이미지로 렌더링 (고해상도)
                mat = fitz.Matrix(2.0, 2.0)  # 2배 확대로 고해상도
                pix = page.get_pixmap(matrix=mat)
                
                # 파일명 생성
                if self.report_type == 'stock_report':
                    img_filename = f"stock_page_{page_num+1:03d}.png"
                else:
                    img_filename = f"market_page_{page_num+1:03d}.png"
                
                img_path = os.path.join(self.output_dir, img_filename)
                pix.save(img_path)
                
                page_images.append({
                    'filename': img_filename,
                    'path': img_path,
                    'page': page_num + 1,
                    'size': (pix.width, pix.height),
                    'resolution': '2x'
                })
                print(f"  - {img_filename}: {pix.width}x{pix.height}")
                
                pix = None
                
            except Exception as e:
                print(f"  ⚠️ 페이지 {page_num+1} 캡처 실패: {e}")
        
        self.results['images'] = page_images
        print(f"✅ 페이지 캡처 완료: {len(page_images)}개")
        return page_images
    
    def analyze_structure(self) -> Dict:
        """문서 구조 분석"""
        print("🔍 문서 구조 분석 중...")
        text = self.results['text']
        structure = {'sections': [], 'title': '', 'date': ''}
        
        # 제목 추출
        lines = text.split('\n')
        for line in lines[:20]:  # 처음 20줄에서 제목 찾기
            line = line.strip()
            if len(line) > 5 and (
                '마감시황' in line or 
                'COMPANY UPDATE' in line or 
                '퓨처엠' in line or
                '리포트' in line or
                '분석' in line
            ):
                structure['title'] = line
                break
        
        # 파일명에서 제목 추출 (보조)
        if not structure['title']:
            filename = os.path.basename(self.pdf_path)
            title_match = re.search(r'([가-힣A-Za-z\s]+)', filename)
            if title_match:
                structure['title'] = title_match.group(1)
        
        # 날짜 추출
        date_patterns = [
            r'(\d{4}[-./]\d{1,2}[-./]\d{1,2})',
            r'(\d{4}\.\s*\d{1,2}\.\s*\d{1,2})',
            r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                structure['date'] = match.group(1)
                break
        
        # 섹션 식별
        if self.report_type == 'stock_report':
            section_patterns = [
                r'종목 정보',
                r'Investment Highlights',
                r'재무전망',
                r'Valuation',
                r'Risk Factors',
                r'투자포인트',
                r'실적전망'
            ]
        else:
            section_patterns = [
                r'업종별 순환매',
                r'주요지표 일간 변동',
                r'주요 수급 동향',
                r'KEY DRIVER',
                r'시장전망',
                r'산업동향'
            ]
        
        for pattern in section_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                structure['sections'].append(pattern)
        
        self.results['structure'] = structure
        print(f"✅ 구조 분석 완료: {len(structure['sections'])}개 섹션")
        return structure
    
    def parse_complete_report(self, no_images: bool = False, image_analysis: bool = False) -> Dict:
        """전체 리포트 파싱"""
        if not self.open_pdf():
            return None
        
        # 메타데이터 설정
        self.results['metadata'] = {
            'filename': os.path.basename(self.pdf_path),
            'pages': len(self.doc),
            'parsing_timestamp': datetime.now().isoformat()
        }
        
        # 각 단계 실행
        text_content = self.parse_text()
        if not no_images:
            self.extract_page_images()  # 페이지 전체 캡처
        self.analyze_structure()
        
        # 리포트 타입별 특화 파싱
        if self.report_type == 'stock_report':
            # 이미지 경로 전달 (이미지 분석이 활성화된 경우에만)
            image_paths = [img['path'] for img in self.results.get('images', [])] if image_analysis else None
            self.parse_stock_info(text_content, image_paths)
        else:
            self.parse_market_info(text_content)
        
        # 파싱 정보 추가
        self.results['parsing_info'] = {
            'text_length': len(self.results['text']),
            'images_count': len(self.results['images']),
            'sections_count': len(self.results['structure'].get('sections', []))
        }
        
        if self.doc:
            self.doc.close()
        
        return self.results
    
    def save_results(self, output_prefix: str = None) -> Dict[str, str]:
        """결과 저장"""
        if not output_prefix:
            if self.report_type == 'stock_report' and 'stock_info' in self.results:
                stock_name = self.results['stock_info'].get('stock_name', 'stock_report')
                output_prefix = f"{stock_name}_analysis"
            else:
                output_prefix = "market_report_analysis"
        
        saved_files = {}
        
        # 1. 통합 JSON 저장
        json_path = os.path.join(self.output_dir, f"{output_prefix}.json")
        json_data = self.results.copy()
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        saved_files['json'] = json_path
        
        # 2. 텍스트 저장
        text_path = os.path.join(self.output_dir, f"{output_prefix}_full_text.txt")
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(self.results['text'])
        saved_files['text'] = text_path
        

        
        # 4. 요약 정보 저장
        summary_path = os.path.join(self.output_dir, f"{output_prefix}_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"# {output_prefix.upper()} 요약\n\n")
            f.write(f"리포트 타입: {self.report_type}\n")
            f.write(f"파싱 일시: {self.results['metadata']['parsing_timestamp']}\n")
            f.write(f"파일명: {self.results['metadata']['filename']}\n")
            f.write(f"페이지 수: {self.results['metadata']['pages']}\n\n")
            
            if self.report_type == 'stock_report' and self.results['stock_info']:
                f.write("## 종목 정보\n")
                for key, value in self.results['stock_info'].items():
                    f.write(f"- {key}: {value}\n")
            elif self.report_type == 'market_report' and self.results['market_info']:
                f.write("## 시장 정보\n")
                for key, value in self.results['market_info'].items():
                    if key != 'key_driver':
                        f.write(f"- {key}: {value}\n")
            
            f.write(f"\n## 파싱 정보\n")
            f.write(f"- 텍스트 길이: {self.results['parsing_info']['text_length']:,}자\n")
            f.write(f"- 페이지 이미지 개수: {self.results['parsing_info']['images_count']}개\n")
            f.write(f"- 섹션 개수: {self.results['parsing_info']['sections_count']}개\n")
            
        saved_files['summary'] = summary_path
        
        return saved_files

class GroqAnalyzer:
    """Groq API를 사용한 리포트 분석 (Rate Limit 대응)"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GROQ_API_KEY or os.getenv('GROQ_API_KEY')
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
        if not self.api_key or self.api_key == "gsk_your_groq_api_key_here":
            self.api_key = None
    
    def analyze_images_for_stock_info(self, image_paths: List[str], report_type: str) -> Dict:
        """이미지에서 종목 정보 추출"""
        if not self.api_key or not image_paths:
            return {}
        
        print("🔍 이미지에서 종목 정보 추출 중...")
        
        # 첫 번째 이미지만 분석 (보통 첫 페이지에 종목 정보가 있음)
        first_image_path = image_paths[0] if image_paths else None
        if not first_image_path or not os.path.exists(first_image_path):
            return {}
        
        try:
            # 이미지를 base64로 인코딩
            import base64
            with open(first_image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            prompt = f"""
다음은 증권사 리포트의 첫 페이지 이미지입니다. 이미지에서 종목 정보를 추출해주세요.

**분석 요청사항:**
1. 종목명 (회사명)
2. 종목코드 (6자리 숫자)
3. 현재주가 (원 단위)
4. 목표주가 (원 단위)
5. 투자의견 (BUY/HOLD/SELL)
6. 증권사명
7. 애널리스트명
8. 리포트 발행일

**주의사항:**
- 숫자는 콤마 없이 숫자만 추출 (예: 50000)
- 종목코드는 6자리 숫자만 추출
- 날짜는 YYYY-MM-DD 형식으로 추출
- 찾을 수 없는 정보는 빈 문자열로 표시

JSON 형식으로 응답해주세요:
{{
    "stock_name": "종목명",
    "stock_code": "종목코드",
    "current_price": "현재주가",
    "target_price": "목표주가", 
    "investment_opinion": "투자의견",
    "securities_firm": "증권사명",
    "analyst": "애널리스트명",
    "report_date": "발행일"
}}
            """
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{encoded_image}"
                                }
                            }
                        ]
                    }
                ],
                "model": "llama3.1-70b-versatile",  # 이미지 분석 지원 모델로 변경
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # JSON 응답 파싱
                try:
                    import json
                    stock_info = json.loads(content)
                    print("✅ 이미지에서 종목 정보 추출 완료")
                    return stock_info
                except json.JSONDecodeError:
                    print("⚠️ 이미지 분석 결과 JSON 파싱 실패")
                    return {}
            elif response.status_code == 404:
                print("⚠️ 이미지 분석 모델을 찾을 수 없습니다. 텍스트 분석만 진행합니다.")
                return {}
            else:
                print(f"⚠️ 이미지 분석 API 오류: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"⚠️ 이미지 분석 중 오류: {e}")
            return {}
    
    def analyze_report(self, parsed_data: Dict) -> str:
        """파싱된 데이터를 Groq API로 분석 (Rate Limit 대응)"""
        if not self.api_key:
            return "Groq API 키가 설정되지 않아 분석을 수행할 수 없습니다."
        
        report_type = parsed_data.get('report_type', 'unknown')
        text_sample = parsed_data['text'][:3000]  # 토큰 사용량 줄이기
        
        if report_type == 'stock_report':
            stock_info = parsed_data.get('stock_info', {})
            prompt = f"""
다음은 증권사의 개별 종목 분석 리포트입니다. 간결하게 분석해주세요.

**종목 정보:**
{json.dumps(stock_info, ensure_ascii=False, indent=2)}

**리포트 내용 (일부):**
{text_sample[:2000]}

다음 관점에서 간결하게 분석해주세요:
1. 투자 의견 근거
2. 주요 투자 포인트
3. 리스크 요인
4. 향후 전망

한국어로 간결하게 분석해주세요.
            """
        else:
            market_info = parsed_data.get('market_info', {})
            prompt = f"""
다음은 증권사의 시장/산업 분석 리포트입니다. 간결하게 분석해주세요.

**시장 정보:**
{json.dumps(market_info, ensure_ascii=False, indent=2)}

**리포트 내용 (일부):**
{text_sample[:2000]}

다음 관점에서 간결하게 분석해주세요:
1. 주요 동향
2. 투자 기회
3. 리스크 요인
4. 향후 전망

한국어로 간결하게 분석해주세요.
            """
        
        return self._make_api_request(prompt)
    
    def _make_api_request(self, prompt: str, max_retries: int = 3) -> str:
        """API 요청 (재시도 및 Rate Limit 대응)"""
        
        for attempt in range(max_retries):
            try:
                # 요청 간격 조절 (지수 백오프)
                if attempt > 0:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"⏳ API 요청 재시도 대기 중... ({wait_time:.1f}초)")
                    time.sleep(wait_time)
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "messages": [{"role": "user", "content": prompt}],
                    "model": "llama3-8b-8192",
                    "temperature": 0.3,
                    "max_tokens": 800  # 토큰 사용량 줄이기
                }
                
                response = requests.post(
                    self.base_url, 
                    headers=headers, 
                    json=data,
                    timeout=30  # 타임아웃 설정
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result['choices'][0]['message']['content']
                    print("✅ Groq 분석 완료")
                    return analysis
                    
                elif response.status_code == 429:
                    # Rate Limit 오류 - 재시도
                    retry_after = response.headers.get('Retry-After', '60')
                    wait_time = min(int(retry_after), 180)  # 최대 3분 대기
                    
                    print(f"⚠️ API 요청 한도 초과 (429). {wait_time}초 후 재시도... ({attempt+1}/{max_retries})")
                    
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        return f"분석 실패: API 요청 한도 초과. 잠시 후 다시 시도해주세요."
                        
                elif response.status_code == 401:
                    return "API 키가 유효하지 않습니다."
                    
                else:
                    error_msg = f"API 오류 ({response.status_code})"
                    if attempt == max_retries - 1:
                        return f"분석 실패: {error_msg}"
                    else:
                        print(f"⚠️ {error_msg}, 재시도 중... ({attempt+1}/{max_retries})")
                        
            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    return "분석 실패: API 요청 시간 초과"
                else:
                    print(f"⚠️ API 요청 시간 초과, 재시도 중... ({attempt+1}/{max_retries})")
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    return f"분석 실패: {e}"
                else:
                    print(f"⚠️ API 요청 중 오류: {e}, 재시도 중... ({attempt+1}/{max_retries})")
        
        return "분석 실패: 최대 재시도 횟수 초과"

def main():
    parser = argparse.ArgumentParser(description='증권사 리포트 PDF 일괄 파싱 도구 V4 (Java 불필요)')
    
    # 필수 인수
    parser.add_argument('--input-folder', '-i', required=True, 
                       help='PDF 파일들이 있는 입력 폴더 경로')
    parser.add_argument('--output-folder', '-o', required=True,
                       help='파싱 결과를 저장할 출력 폴더 경로')
    
    # 선택적 인수
    parser.add_argument('--groq-key', help='Groq API 키 (코드 내 설정 덮어쓰기)')
    parser.add_argument('--no-ai', action='store_true', help='AI 분석 건너뛰기')
    parser.add_argument('--no-images', action='store_true', help='페이지 이미지 캡처 건너뛰기')
    parser.add_argument('--image-analysis', action='store_true', help='이미지에서 종목 정보 추출 활성화')
    
    args = parser.parse_args()
    
    # 입력 폴더 확인
    if not os.path.exists(args.input_folder):
        print(f"❌ 입력 폴더를 찾을 수 없습니다: {args.input_folder}")
        return
    
    if not os.path.isdir(args.input_folder):
        print(f"❌ 입력 경로가 폴더가 아닙니다: {args.input_folder}")
        return
    
    # 일괄 처리 실행
    print("📂 폴더 일괄 처리 모드 (Java 불필요)")
    batch_parser = BatchSecuritiesParser(args.input_folder, args.output_folder)
    
    # Groq API 키 설정 (명령줄 옵션이 있으면 우선 적용)
    if args.groq_key:
        global GROQ_API_KEY
        GROQ_API_KEY = args.groq_key
    
    batch_parser.process_all_pdfs(args.no_ai, args.no_images, args.image_analysis)

def download_file(url: str, output_path: str) -> bool:
    """URL에서 파일 다운로드"""
    try:
        print(f"📥 파일 다운로드 중: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ 다운로드 완료: {output_path}")
        return True
    except Exception as e:
        print(f"❌ 다운로드 실패: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(f"""
🚀 증권사 리포트 PDF 일괄 파싱 도구 V4 (Java 불필요)

🔑 API 키 설정 상태: {'✅ 설정됨' if GROQ_API_KEY and GROQ_API_KEY != "gsk_your_groq_api_key_here" else '❌ 미설정'}

✨ 주요 개선사항:
   - 📄 PDF 페이지 전체 캡처 (고해상도)
   - 🤖 이미지 AI 분석으로 종목 정보 추출
   - 📈 개선된 종목 정보 추출 (패턴 강화)
   - 🔍 더 정확한 리포트 타입 감지
   - 📊 더 나은 텍스트 및 구조 분석

📋 사용법:
    python enhanced_parser_v4.py --input-folder /path/to/pdf/folder --output-folder /path/to/output/folder
    python enhanced_parser_v4.py -i ./pdfs -o ./results
    python enhanced_parser_v4.py -i ./pdfs -o ./results --no-ai

🔧 주요 옵션:
    --input-folder, -i    입력 폴더 (필수)
    --output-folder, -o   출력 폴더 (필수)
    --groq-key           Groq API 키 덮어쓰기
    --no-ai              AI 분석 건너뛰기
    --no-images          페이지 이미지 캡처 건너뛰기
    --image-analysis     이미지에서 종목 정보 추출 활성화

📁 출력 구조:
    output_folder/
    ├── batch_summary_20250720_143022.json      # 전체 요약 (JSON)
    ├── batch_summary_20250720_143022.txt       # 전체 요약 (텍스트)
    ├── batch_summary_20250720_143022.xlsx      # 전체 요약 (Excel)
    ├── 파일명1_분석/
    │   ├── 종목명_analysis.json
    │   ├── 종목명_analysis_summary.txt
    │   ├── groq_analysis_stock_report.txt
    │   └── stock_page_*.png
    └── 파일명2_분석/
        └── ...

💡 예시:
    python enhanced_parser_v4.py -i ./증권리포트 -o ./파싱결과
    python enhanced_parser_v4.py -i "C:/Documents/Securities_Reports" -o "D:/Output"
    python enhanced_parser_v4.py -i ./pdfs -o ./results --no-images
    python enhanced_parser_v4.py -i ./pdfs -o ./results --image-analysis
    python enhanced_parser_v4.py -i ./pdfs -o ./results --no-ai --image-analysis
    
🔧 필요 라이브러리:
   - PyMuPDF (페이지 캡처, 텍스트)
   - pandas (데이터 처리)
   - requests (Groq API)
        """)
    else:
        main()
