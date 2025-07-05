import pdfplumber
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import io

class PDFCoordinateViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 좌표 확인 도구")
        self.root.geometry("1200x800")
        
        # 변수들
        self.pdf_path = None
        self.pdf_doc = None
        self.page_image = None
        self.canvas = None
        self.scale_factor = 1.0
        self.page_width = 0
        self.page_height = 0
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        # 상단 프레임 (파일 선택)
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="PDF 파일 선택", command=self.load_pdf).pack(side=tk.LEFT)
        self.file_label = ttk.Label(top_frame, text="파일이 선택되지 않음")
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # 정보 프레임
        info_frame = ttk.Frame(self.root)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.coord_label = ttk.Label(info_frame, text="좌표: x=0, y=0", font=("Arial", 12, "bold"))
        self.coord_label.pack(side=tk.LEFT)
        
        self.size_label = ttk.Label(info_frame, text="페이지 크기: 0 x 0")
        self.size_label.pack(side=tk.LEFT, padx=20)
        
        # 메인 프레임 (스크롤 가능한 캔버스)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 스크롤바
        v_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 캔버스
        self.canvas = tk.Canvas(main_frame, bg="white", 
                               yscrollcommand=v_scrollbar.set,
                               xscrollcommand=h_scrollbar.set)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        v_scrollbar.config(command=self.canvas.yview)
        h_scrollbar.config(command=self.canvas.xview)
        
        # 마우스 이벤트 바인딩
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        
        # 하단 정보 프레임
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.text_info = tk.Text(bottom_frame, height=5, wrap=tk.WORD)
        self.text_info.pack(fill=tk.BOTH, expand=True)
    
    def load_pdf(self):
        """PDF 파일 로드"""
        file_path = filedialog.askopenfilename(
            title="PDF 파일 선택",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialdir=os.path.join(os.path.dirname(__file__), "consensus", "kiwoom")
        )
        
        if file_path:
            try:
                self.pdf_path = file_path
                self.pdf_doc = fitz.open(file_path)
                self.display_pdf()
                self.file_label.config(text=os.path.basename(file_path))
                self.text_info.insert(tk.END, f"PDF 로드 완료: {os.path.basename(file_path)}\n")
            except Exception as e:
                messagebox.showerror("오류", f"PDF 로드 실패: {str(e)}")
    
    def display_pdf(self):
        """PDF를 캔버스에 표시"""
        if not self.pdf_doc:
            return
        
        try:
            # 첫 번째 페이지 가져오기
            page = self.pdf_doc[0]
            
            # 페이지 크기 정보
            rect = page.rect
            self.page_width = rect.width
            self.page_height = rect.height
            
            self.size_label.config(text=f"페이지 크기: {self.page_width:.1f} x {self.page_height:.1f}")
            
            # PDF를 이미지로 변환 (해상도 조정)
            mat = fitz.Matrix(2.0, 2.0)  # 2배 확대
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            
            # PIL Image로 변환
            img = Image.open(io.BytesIO(img_data))
            self.page_image = ImageTk.PhotoImage(img)
            
            # 스케일 팩터 계산
            self.scale_factor = 2.0
            
            # 캔버스 크기 설정
            canvas_width = int(self.page_width * self.scale_factor)
            canvas_height = int(self.page_height * self.scale_factor)
            
            self.canvas.config(scrollregion=(0, 0, canvas_width, canvas_height))
            
            # 이미지 표시
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.page_image)
            
            self.text_info.insert(tk.END, f"페이지 표시 완료 (스케일: {self.scale_factor})\n")
            
        except Exception as e:
            messagebox.showerror("오류", f"PDF 표시 실패: {str(e)}")
    
    def on_mouse_move(self, event):
        """마우스 움직임 시 좌표 표시"""
        if not self.page_image:
            return
        
        # 캔버스 좌표를 PDF 좌표로 변환
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # PDF 좌표 계산 (스케일 팩터 고려)
        pdf_x = canvas_x / self.scale_factor
        pdf_y = canvas_y / self.scale_factor
        
        # 좌표가 페이지 범위 내에 있는지 확인
        if 0 <= pdf_x <= self.page_width and 0 <= pdf_y <= self.page_height:
            self.coord_label.config(text=f"좌표: x={pdf_x:.1f}, y={pdf_y:.1f}")
            
            # 해당 위치의 텍스트 정보 가져오기
            self.get_text_at_position(pdf_x, pdf_y)
    
    def on_mouse_click(self, event):
        """마우스 클릭 시 상세 정보 표시"""
        if not self.page_image:
            return
        
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        pdf_x = canvas_x / self.scale_factor
        pdf_y = canvas_y / self.scale_factor
        
        if 0 <= pdf_x <= self.page_width and 0 <= pdf_y <= self.page_height:
            self.text_info.insert(tk.END, f"\n클릭 위치: x={pdf_x:.1f}, y={pdf_y:.1f}\n")
            
            # 주변 영역의 텍스트 추출
            margin = 50  # 주변 50포인트 영역
            bbox = (max(0, pdf_x - margin), 
                   max(0, pdf_y - margin),
                   min(self.page_width, pdf_x + margin),
                   min(self.page_height, pdf_y + margin))
            
            try:
                with pdfplumber.open(self.pdf_path) as pdf:
                    page = pdf.pages[0]
                    cropped = page.crop(bbox)
                    text = cropped.extract_text()
                    
                    if text:
                        self.text_info.insert(tk.END, f"주변 텍스트: {text.strip()}\n")
                    else:
                        self.text_info.insert(tk.END, "주변에 텍스트 없음\n")
            except Exception as e:
                self.text_info.insert(tk.END, f"텍스트 추출 오류: {str(e)}\n")
            
            # 자동 스크롤
            self.text_info.see(tk.END)
    
    def get_text_at_position(self, x, y):
        """특정 위치의 텍스트 정보 가져오기"""
        try:
            if not self.pdf_path:
                return
            
            with pdfplumber.open(self.pdf_path) as pdf:
                page = pdf.pages[0]
                words = page.extract_words()
                
                # 현재 위치에 있는 단어 찾기
                for word in words:
                    if (word['x0'] <= x <= word['x1'] and 
                        word['y0'] <= y <= word['y1']):
                        self.coord_label.config(
                            text=f"좌표: x={x:.1f}, y={y:.1f} | 텍스트: '{word['text']}'"
                        )
                        return
                
        except Exception:
            pass

def analyze_pdf_coordinates(pdf_path):
    """PDF의 좌표 정보를 분석하고 텍스트 위치를 확인하는 함수"""
    print(f"PDF 분석 시작: {pdf_path}")
    print("=" * 80)
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]  # 첫 번째 페이지
            
            # 페이지 기본 정보
            print(f"페이지 크기: {page.width} x {page.height}")
            print(f"페이지 bbox: {page.bbox}")
            print("=" * 80)
            
            # 모든 텍스트 요소의 좌표 정보 출력
            print("텍스트 요소별 좌표 정보:")
            print("-" * 80)
            
            chars = page.chars
            words = page.extract_words()
            
            # 단어별 좌표 정보 (처음 50개)
            print("\n=== 단어별 좌표 정보 (처음 50개) ===")
            for i, word in enumerate(words[:50]):
                print(f"{i+1:2d}. '{word['text']:<20}' x0:{word['x0']:6.1f} y0:{word['y0']:6.1f} x1:{word['x1']:6.1f} y1:{word['y1']:6.1f}")
            
            # Y좌표별로 그룹화하여 줄별 내용 확인
            print("\n=== Y좌표별 줄 분석 ===")
            lines_by_y = {}
            for word in words:
                y_key = round(word['y0'], 1)  # 소수점 1자리로 반올림
                if y_key not in lines_by_y:
                    lines_by_y[y_key] = []
                lines_by_y[y_key].append(word)
            
            # Y좌표 기준으로 정렬 (위에서 아래로)
            sorted_lines = sorted(lines_by_y.items(), key=lambda x: x[0])
            
            for i, (y_coord, line_words) in enumerate(sorted_lines[:30]):  # 처음 30줄만
                # X좌표 기준으로 정렬
                line_words.sort(key=lambda w: w['x0'])
                line_text = ' '.join([w['text'] for w in line_words])
                print(f"줄 {i+1:2d} (y={y_coord:6.1f}): '{line_text}'")
            
            # 특정 영역의 텍스트 추출 테스트
            print("\n=== 영역별 텍스트 추출 테스트 ===")
            
            # 테스트할 영역들
            test_areas = [
                {
                    'name': '상단_영역',
                    'bbox': (0, 0, page.width, page.height * 0.3)
                },
                {
                    'name': '중간_영역', 
                    'bbox': (0, page.height * 0.3, page.width, page.height * 0.7)
                },
                {
                    'name': '하단_영역',
                    'bbox': (0, page.height * 0.7, page.width, page.height)
                },
                {
                    'name': '좌측_영역',
                    'bbox': (0, 0, page.width * 0.5, page.height)
                },
                {
                    'name': '우측_영역',
                    'bbox': (page.width * 0.5, 0, page.width, page.height)
                },
                {
                    'name': '중앙_메인_영역',
                    'bbox': (page.width * 0.1, page.height * 0.2, page.width * 0.9, page.height * 0.8)
                }
            ]
            
            for area in test_areas:
                print(f"\n--- {area['name']} ---")
                print(f"bbox: {area['bbox']}")
                
                cropped = page.crop(area['bbox'])
                text = cropped.extract_text()
                
                if text:
                    lines = text.split('\n')[:10]  # 처음 10줄만
                    total_lines = len(text.split('\n'))
                    print(f"추출된 줄 수: {total_lines}")
                    for j, line in enumerate(lines):
                        if line.strip():
                            print(f"  {j+1}. {line.strip()}")
                else:
                    print("  텍스트 없음")
            
            # 투자 근거 관련 키워드 포함 영역 찾기
            print("\n=== 투자 근거 관련 키워드 위치 분석 ===")
            keywords = ['투자포인트', '투자의견', '핵심', '주요', '근거', '포인트', 'Point', 'Key']
            
            for keyword in keywords:
                found_words = [w for w in words if keyword.lower() in w['text'].lower()]
                if found_words:
                    print(f"\n'{keyword}' 키워드 발견:")
                    for word in found_words:
                        print(f"  위치: x={word['x0']:6.1f}-{word['x1']:6.1f}, y={word['y0']:6.1f}-{word['y1']:6.1f}")
                        print(f"  텍스트: '{word['text']}'")
            
            # 색상 정보 분석
            print("\n=== 색상 정보 분석 ===")
            color_chars = {}
            for char in chars[:100]:  # 처음 100개 문자만
                color = char.get('non_stroking_color', 'None')
                if color not in color_chars:
                    color_chars[color] = []
                color_chars[color].append(char)
            
            print("발견된 색상들:")
            for color, char_list in color_chars.items():
                print(f"  색상 {color}: {len(char_list)}개 문자")
                if len(char_list) > 0:
                    sample_text = ''.join([c['text'] for c in char_list[:20]])
                    print(f"    샘플: '{sample_text}'")
            
    except Exception as e:
        print(f"오류 발생: {e}")

def main():
    """메인 실행 함수 - GUI 실행"""
    try:
        root = tk.Tk()
        app = PDFCoordinateViewer(root)
        
        # 기본 PDF 파일이 있다면 자동 로드
        current_dir = os.path.dirname(os.path.abspath(__file__))
        kiwoom_folder = os.path.join(current_dir, "consensus", "kyobo")
        
        if os.path.exists(kiwoom_folder):
            pdf_files = [f for f in os.listdir(kiwoom_folder) if f.endswith('.pdf')]
            if pdf_files:
                # 디오 파일 우선 검색
                dio_files = [f for f in pdf_files if '공공부문 수요 정상화 예상_20250624' in f]
                if dio_files:
                    default_pdf = os.path.join(kiwoom_folder, dio_files[0])
                    app.pdf_path = default_pdf
                    try:
                        app.pdf_doc = fitz.open(default_pdf)
                        app.display_pdf()
                        app.file_label.config(text=os.path.basename(default_pdf))
                        app.text_info.insert(tk.END, f"기본 PDF 로드: {os.path.basename(default_pdf)}\n")
                    except Exception as e:
                        app.text_info.insert(tk.END, f"기본 PDF 로드 실패: {str(e)}\n")
        
        root.mainloop()
        
    except ImportError as e:
        print("필요한 패키지가 설치되지 않았습니다.")
        print("다음 명령어로 설치하세요:")
        print("pip install PyMuPDF pillow tkinter")
        print(f"오류: {e}")
    except Exception as e:
        print(f"GUI 실행 오류: {e}")

if __name__ == "__main__":
    main()
