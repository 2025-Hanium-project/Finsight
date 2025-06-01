import pdfplumber
from pydantic import BaseModel
from typing import List
from uuid import uuid4
import json

class Chunk(BaseModel):
    id: str
    text: str

class DoclingDocument(BaseModel):
    id: str
    chunks: List[Chunk]

def extract_text_chunks_with_pdfplumber(pdf_path, max_chunk_size=1000) -> DoclingDocument:
    full_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            try:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
            except:
                continue

    # 공백 정리
    full_text = " ".join(full_text.split())

    # 청크 단위로 분할
    chunks = []
    for i in range(0, len(full_text), max_chunk_size):
        chunk_text = full_text[i:i + max_chunk_size]
        chunks.append(Chunk(id=str(uuid4()), text=chunk_text))

    return DoclingDocument(id=str(uuid4()), chunks=chunks)

# 예시 실행
pdf_path = "2025-05-16_기업_대양전기공업(108380) 1Q25 Review_ 영업이익 고성장_정홍식_LS증권.pdf"
docling_document = extract_text_chunks_with_pdfplumber(pdf_path)

# JSON 문자열 출력 (ensure_ascii 지원을 위해 json.dumps 사용)
print(json.dumps(docling_document.dict(), indent=2, ensure_ascii=False))
