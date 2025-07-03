import easyocr
from PIL import Image
import os
import re
import uuid
from datetime import datetime
import pandas as pd
import glob
import numpy as np

class HeungkukConsensusParser:
    def __init__(self):
        self.data_list = []
        print("EasyOCR 리더를 초기화합니다. (최초 실행 시 시간이 소요될 수 있습니다)")
        # GPU 사용을 명시적으로 비활성화하려면 gpu=False 추가
        self.reader = easyocr.Reader(['ko', 'en'], gpu=False)
        print("EasyOCR 리더 초기화 완료.")

    def _clean_text(self, text):
        """추출된 텍스트에서 불필요한 공백과 줄바꿈을 제거합니다."""
        return ' '.join(text.split()).strip()

    def _parse_stock_info(self, text):
        """종목명과 종목코드를 파싱합니다."""
        # 종목명 (종목코드) 형식
        match = re.search(r'([가-힣\w\s]+)\s*\((\d{6})\)', text)
        if match:
            stock_name = self._clean_text(match.group(1))
            stock_code = match.group(2)
            # "BUY" 와 같은 단어가 종목명에 포함되는 경우 제거
            stock_name = stock_name.replace("BUY", "").strip()
            return stock_name, stock_code
        return 'Unknown', '000000'

    def _parse_report_date(self, text):
        """리포트 날짜를 파싱합니다."""
        # YYYY.MM.DD 또는 YYYY-MM-DD 형식
        match = re.search(r'(\d{4}[-./]\s?\d{1,2}[-./]\s?\d{1,2})', text)
        if match:
            date_str = match.group(1).replace('.', '-').replace('/', '-')
            return datetime.strptime(date_str.replace(" ", ""), '%Y-%m-%d').strftime('%Y-%m-%d')
        return datetime.now().strftime('%Y-%m-%d')

    def _parse_analyst_info(self, text):
        """애널리스트 이름과 증권사명을 파싱합니다."""
        company_name = '흥국증권'
        # "애널리스트" 또는 "연구원" 앞에 오는 이름 추출
        match = re.search(r'([가-힣]{2,4})\s*(?:연구원|애널리스트)', text)
        if match:
            return match.group(1), company_name
        
        # 하드코딩된 이름으로 폴백
        analyst_names = []
        if '정진수' in text:
            analyst_names.append('정진수')
        if '유준석' in text:
            analyst_names.append('유준석')
        
        analyst_name = ', '.join(analyst_names) if analyst_names else 'Unknown'
        return analyst_name, company_name

    def _parse_price_info(self, text):
        """목표주가, 현재주가, 상승여력을 파싱합니다."""
        target_price_match = re.search(r'목표주가\s*([\d,]+)원', text)
        target_price = int(target_price_match.group(1).replace(',', '')) if target_price_match else None

        # 현재주가 패턴을 좀 더 유연하게 수정 (날짜 괄호가 없을 수도 있음)
        current_price_match = re.search(r'현재주가\s*(?:\(.+?\))?\s*([\d,]+)원', text)
        current_price = int(current_price_match.group(1).replace(',', '')) if current_price_match else None
        
        upside_potential = None
        if target_price and current_price and current_price > 0:
            upside_potential = round(((target_price / current_price) - 1) * 100, 1)
            
        return target_price, current_price, upside_potential

    def _parse_rating_info(self, text):
        """투자의견과 의견 변경을 파싱합니다."""
        # 'BUY' 또는 '매수' 단어와 함께 괄호 안의 의견 변경 상태를 찾음
        rating_match = re.search(r'(?:BUY|매수)\s*\(?(\w+)\)?', text)
        if rating_match:
            rating = '매수'
            opinion_change = rating_match.group(1)
            # '유지', '상향', '하향' 등의 키워드가 없으면 '유지'로 간주
            if opinion_change not in ['유지', '상향', '하향', '신규']:
                 opinion_change = '유지'
            return rating, opinion_change
        return 'N/A', 'N/A' # Not Applicable

    def parse_image(self, image_path):
        """단일 이미지 파일을 파싱하여 리포트 정보를 추출합니다."""
        print(f"--- 이미지 파싱 시작: {os.path.basename(image_path)} ---")
        try:
            img = Image.open(image_path)
            img_np = np.array(img)

            # 전체 텍스트 추출
            results = self.reader.readtext(img_np)
            full_text = ' '.join([res[1] for res in results])
            
            # 정보 추출
            stock_name, stock_code = self._parse_stock_info(full_text)
            report_date = self._parse_report_date(full_text)
            analyst_name, company_name = self._parse_analyst_info(full_text)
            target_price, current_price, upside_potential = self._parse_price_info(full_text)
            rating, opinion_change = self._parse_rating_info(full_text)
            
            width, height = img.size
            
            # 제목 영역 (좌표는 이미지 레이아웃에 따라 조정 필요)
            # x1, y1, x2, y2
            title_bbox = (250, 150, width - 100, 250)
            title_results = self.reader.readtext(np.array(img.crop(title_bbox)))
            report_title = self._clean_text(' '.join([res[1] for res in title_results]))
            
            # 투자 근거 영역 (좌표는 이미지 레이아웃에 따라 조정 필요)
            rationale_bbox = (380, 280, width - 50, height - 50)
            rationale_results = self.reader.readtext(np.array(img.crop(rationale_bbox)))
            investment_rationale = self._clean_text(' '.join([res[1] for res in rationale_results]))

            data = {
                'report_id': str(uuid.uuid4()),
                'stock_code': stock_code,
                'stock_name': stock_name,
                'report_title': report_title or f"{stock_name} 분석리포트",
                'report_date': report_date,
                'report_type': '기업분석',
                'analyst_name': analyst_name,
                'company_name': company_name,
                'rating': rating,
                'opinion_change': opinion_change,
                'target_price': target_price,
                'current_price': current_price,
                'upside_potential': upside_potential,
                'investment_rationale': investment_rationale or '투자 근거 정보 없음',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.data_list.append(data)
            print(f"파싱 완료: {stock_name} ({stock_code})")
            return data
        except FileNotFoundError:
            print(f"[오류] 파일을 찾을 수 없습니다: {image_path}")
            return None
        except Exception as e:
            print(f"[오류] 이미지 파싱 중 예외 발생: {os.path.basename(image_path)}")
            print(f"  - 오류 타입: {type(e).__name__}")
            print(f"  - 오류 메시지: {e}")
            return None

    def process_all_images(self, image_folder_path):
        """지정된 폴더의 모든 PNG 파일을 처리합니다."""
        image_files = glob.glob(os.path.join(image_folder_path, '*.png'))
        if not image_files:
            print(f"경고: '{image_folder_path}' 폴더에 처리할 PNG 파일이 없습니다.")
            return
            
        for image_file in image_files:
            self.parse_image(image_file)
        print(f"\\n총 {len(image_files)}개의 이미지 파일 처리를 시도했습니다.")

    def save_to_csv(self, output_path):
        """파싱된 데이터를 CSV 파일로 저장합니다."""
        if not self.data_list:
            print("저장할 데이터가 없습니다.")
            return
        
        df = pd.DataFrame(self.data_list)
        # stock_code가 항상 6자리 문자열이 되도록 포맷팅 (앞을 0으로 채움)
        df['stock_code'] = df['stock_code'].astype(str).str.zfill(6)
        
        # CSV 저장 시 폴더가 없으면 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"CSV 파일 저장 완료: {output_path}")
        print(f"총 {len(self.data_list)}개 리포트 저장")

if __name__ == '__main__':
    # __file__을 기준으로 상대 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 상위 폴더로 이동 후 consensus/heungkuk 경로 설정
    heungkuk_folder = os.path.join(current_dir, '..', 'consensus', 'heungkuk')
    # 상위 폴더로 이동 후 consensus_parsed 경로 설정
    output_folder = os.path.join(current_dir, '..', 'consensus_parsed')
    
    # 출력 CSV 파일 경로
    output_csv_path = os.path.join(output_folder, 'heungkuk_consensus_reports.csv')
    
    # 절대 경로로 변환하여 출력
    print(f"이미지 소스 폴더: {os.path.abspath(heungkuk_folder)}")
    print(f"CSV 저장 경로: {os.path.abspath(output_csv_path)}")

    parser = HeungkukConsensusParser()
    parser.process_all_images(heungkuk_folder)
    parser.save_to_csv(output_csv_path)