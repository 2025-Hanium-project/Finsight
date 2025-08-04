import os
from pathlib import Path
import fitz  # PyMuPDF
import tempfile
from docling.document_converter import DocumentConverter

def extract_first_page_markdown(pdf_path):
    tmp_pdf_path = None
    try:
        # 첫 페이지만 포함된 임시 PDF 생성
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            tmp_pdf_path = Path(tmp_pdf.name)
            tmp_pdf.close()  # Windows 호환을 위해 닫기
            doc = fitz.open(pdf_path)
            first_page_doc = fitz.open()
            first_page_doc.insert_pdf(doc, from_page=0, to_page=0)
            first_page_doc.save(tmp_pdf_path)

        # Docling으로 파싱
        converter = DocumentConverter()
        result = converter.convert(tmp_pdf_path)
        return result.document.export_to_markdown()
    except Exception as e:
        print(f"{pdf_path.name} 첫 페이지 파싱 실패: {e}")
        return ""
    finally:
        try:
            if tmp_pdf_path and tmp_pdf_path.exists():
                tmp_pdf_path.unlink()
        except Exception as cleanup_error:
            print(f"임시 파일 삭제 실패: {cleanup_error}")

def parse_pdfs_to_txt(security):
    base_dir = Path(__file__).parent.parent
    pdf_dir = base_dir / "consensus" / security
    output_dir = base_dir / "consensus_to_txt" / security
    con_deleted_dir = base_dir / "con_deleted" / security
    output_dir.mkdir(parents=True, exist_ok=True)
    con_deleted_dir.mkdir(parents=True, exist_ok=True)

    for pdf_file in pdf_dir.glob("*.pdf"):
        try:
            text = extract_first_page_markdown(pdf_file)
            output_path = output_dir / (pdf_file.stem + ".txt")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"{pdf_file.name} -> {output_path.name} 저장 완료")
            # 변환 완료된 PDF를 con_deleted로 이동
            target_pdf_path = con_deleted_dir / pdf_file.name
            pdf_file.rename(target_pdf_path)
            print(f"{pdf_file.name} -> {target_pdf_path} 이동 완료")
        except Exception as e:
            print(f"{pdf_file.name} 변환 실패: {e}")

if __name__ == "__main__":
    target_list = ["bnk", "daishin"]
    parse_pdfs_to_txt("bnk")