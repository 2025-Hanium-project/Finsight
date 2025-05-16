import requests
import json
import os
import logging
from datetime import datetime
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='pdf_parser.log'
)
logger = logging.getLogger('pdf_parser')

class UpstageDocumentParser:
    def __init__(self):
        pass
    
    def parse_pdf(self, pdf_path):
        """PyMuPDF로 PDF 텍스트/이미지 추출 및 이미지 OCR"""
        try:
            doc = fitz.open(pdf_path)
            pages = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                images = []
                ocr_results = []
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    image = Image.open(io.BytesIO(image_bytes))
                    images.append({
                        "img_index": img_index,
                        "ext": image_ext,
                        "size": image.size
                    })
                    # OCR
                    try:
                        ocr_text = pytesseract.image_to_string(image, lang='eng+kor')
                    except Exception as e:
                        ocr_text = f"OCR 실패: {str(e)}"
                    ocr_results.append({
                        "img_index": img_index,
                        "ocr_text": ocr_text
                    })
                pages.append({
                    "page_num": page_num + 1,
                    "text": text,
                    "images": images,
                    "ocr_results": ocr_results
                })
            result = {
                "file": os.path.basename(pdf_path),
                "num_pages": len(doc),
                "pages": pages
            }
            logger.info(f"PDF 파싱 성공: {pdf_path}")
            return result
        except Exception as e:
            logger.error(f"PDF 파싱 중 오류: {str(e)}")
            return None
    
    def process_parsed_data(self, parsed_data, output_format="markdown"):
        """파싱된 데이터 처리"""
        try:
            if not parsed_data:
                return None
            
            # 마크다운 형식으로 변환
            if output_format.lower() == "markdown":
                markdown_content = parsed_data.get("markdown", "")
                return markdown_content
            
            # JSON 형식으로 반환
            elif output_format.lower() == "json":
                return parsed_data
            
            # HTML 형식으로 변환
            elif output_format.lower() == "html":
                html_content = parsed_data.get("html", "")
                return html_content
            
            # 텍스트 형식으로 변환
            elif output_format.lower() == "text":
                text_content = parsed_data.get("text", "")
                return text_content
            
            else:
                logger.warning(f"지원하지 않는 출력 형식: {output_format}")
                return parsed_data
                
        except Exception as e:
            logger.error(f"데이터 처리 중 오류: {str(e)}")
            return None
    
    def extract_structured_data(self, parsed_data):
        """구조화된 데이터 추출"""
        try:
            if not parsed_data:
                return None
            
            # 기본 정보 추출
            structured_data = {
                "parsed_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "document_type": "research_report",
                "tables": [],
                "charts": [],
                "paragraphs": [],
                "headings": []
            }
            
            # 요소별 데이터 추출
            if "elements" in parsed_data:
                for element in parsed_data["elements"]:
                    # 표 추출
                    if element.get("type") == "table":
                        structured_data["tables"].append({
                            "content": element.get("content", ""),
                            "position": element.get("position", {}),
                            "page": element.get("page", 1)
                        })
                    
                    # 차트 추출
                    elif element.get("type") == "figure" or element.get("type") == "chart":
                        structured_data["charts"].append({
                            "caption": element.get("caption", ""),
                            "position": element.get("position", {}),
                            "page": element.get("page", 1)
                        })
                    
                    # 문단 추출
                    elif element.get("type") == "paragraph":
                        structured_data["paragraphs"].append({
                            "content": element.get("content", ""),
                            "position": element.get("position", {}),
                            "page": element.get("page", 1)
                        })
                    
                    # 제목 추출
                    elif element.get("type").startswith("heading"):
                        structured_data["headings"].append({
                            "content": element.get("content", ""),
                            "level": element.get("type").replace("heading", ""),
                            "position": element.get("position", {}),
                            "page": element.get("page", 1)
                        })
            
            return structured_data
                
        except Exception as e:
            logger.error(f"구조화된 데이터 추출 중 오류: {str(e)}")
            return None
    
    def batch_process_pdfs(self, pdf_directory='./test/pdf_reports', output_directory='./test/parsed_reports', output_format="json"):
        """디렉토리 내 모든 PDF 파일 일괄 처리 (텍스트/이미지 저장 포함)"""
        try:
            if not os.path.exists(output_directory):
                os.makedirs(output_directory)
            images_dir = os.path.join(output_directory, 'images')
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)
            
            results = []
            pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith('.pdf')]
            
            for pdf_file in pdf_files:
                pdf_path = os.path.join(pdf_directory, pdf_file)
                logger.info(f"파싱 시작: {pdf_file}")
                
                # PDF 파싱
                parsed_data = self.parse_pdf(pdf_path)
                
                if parsed_data:
                    # 전체 텍스트 저장
                    all_text = '\n\n'.join([p['text'] for p in parsed_data['pages']])
                    text_file = os.path.join(output_directory, f"{pdf_file.replace('.pdf', '')}_full_text.txt")
                    with open(text_file, 'w', encoding='utf-8') as f:
                        f.write(all_text)
                    
                    # 이미지 저장
                    for page in parsed_data['pages']:
                        page_num = page['page_num']
                        for img_idx, img_info in enumerate(page['images']):
                            # 이미지 다시 추출
                            doc = fitz.open(pdf_path)
                            page_obj = doc[page_num-1]
                            img_list = page_obj.get_images(full=True)
                            if img_idx < len(img_list):
                                xref = img_list[img_idx][0]
                                base_image = doc.extract_image(xref)
                                image_bytes = base_image["image"]
                                image_ext = base_image["ext"]
                                img_filename = f"{pdf_file.replace('.pdf','')}_page{page_num}_img{img_idx+1}.{image_ext}"
                                img_path = os.path.join(images_dir, img_filename)
                                with open(img_path, 'wb') as img_f:
                                    img_f.write(image_bytes)
                    
                    # 구조화된 데이터 추출 및 메타데이터
                    structured_data = self.extract_structured_data(parsed_data)
                    file_parts = pdf_file.replace('.pdf', '').split('_')
                    if len(file_parts) >= 4:
                        structured_data["securities_firm"] = file_parts[0]
                        structured_data["stock_name"] = file_parts[1]
                        structured_data["report_date"] = file_parts[2]
                        structured_data["title"] = '_'.join(file_parts[3:])
                    else:
                        structured_data["filename_parse_warning"] = "파일명에서 메타데이터 추출 실패"
                    
                    # 결과 저장
                    output_file = os.path.join(output_directory, f"{pdf_file.replace('.pdf', '')}.json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(structured_data, f, ensure_ascii=False, indent=2)
                    
                    results.append({
                        "file": pdf_file,
                        "success": True,
                        "output": output_file,
                        "text_file": text_file
                    })
                else:
                    results.append({
                        "file": pdf_file,
                        "success": False,
                        "error": "파싱 실패"
                    })
            
            # 처리 결과 요약
            summary = {
                "total": len(pdf_files),
                "success": sum(1 for r in results if r["success"]),
                "failed": sum(1 for r in results if not r["success"]),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(os.path.join(output_directory, "processing_summary.json"), 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info(f"일괄 처리 완료: 총 {summary['total']}개 중 {summary['success']}개 성공, {summary['failed']}개 실패")
            return results
            
        except Exception as e:
            logger.error(f"일괄 처리 중 오류: {str(e)}")
            return None

# 사용 예시 (main)
if __name__ == "__main__":
    parser = UpstageDocumentParser()
    parser.batch_process_pdfs()  # 기본 경로 사용
