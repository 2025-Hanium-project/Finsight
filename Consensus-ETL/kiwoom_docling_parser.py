import os

from docling.document_converter import DocumentConverter
from pathlib import Path

def extract_first_page_text(pdf_path):
    converter = DocumentConverter()
    try:
        result = converter.convert(pdf_path)
        # docling의 document.chunks에서 첫 페이지에 해당하는 chunk만 추출
        # 대부분 chunk에 page_num이 있음
        first_page_chunks = []
        for chunk in getattr(result.document, 'chunks', []):
            if hasattr(chunk, 'page_num'):
                if chunk.page_num == 1:
                    first_page_chunks.append(chunk.text)
            else:
                # page_num이 없으면 앞부분만 추출 (백업)
                first_page_chunks.append(chunk.text)
        # 만약 page_num이 없는 경우, 전체 텍스트에서 앞부분만 자르기
        if not first_page_chunks:
            text = result.document.export_to_markdown()
            # 2000자까지만 자르기
            return text[:2000]
        return '\n\n'.join(first_page_chunks)
    except Exception as e:
        print(f"PDF 텍스트 추출 실패: {e}")
        return ""

def main():
    # PDF 파일 경로 지정 (사용자가 직접 지정)
    pdf_path = Path("2025-05-15_메리츠금융지주_키움증권.pdf")
    output_txt = Path("kiwoom_docling_debug.txt")
    if not pdf_path.exists():
        print(f"PDF 파일이 존재하지 않습니다: {pdf_path}")
        return
    text = extract_first_page_text(pdf_path)
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"첫 페이지 텍스트가 {output_txt}로 저장되었습니다.")

if __name__ == "__main__":
    main()
        