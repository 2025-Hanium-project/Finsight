import pdfplumber
import logging
logging.getLogger("pdfminer").setLevel(logging.ERROR)

pdf_path = "2025-05-16_기업_대양전기공업(108380) 1Q25 Review_ 영업이익 고성장_정홍식_LS증권.pdf"

with pdfplumber.open(pdf_path) as pdf:
    full_text = ""
    for page in pdf.pages:
        full_text += page.extract_text() + "\n"

print(full_text[:2000])  # 앞 2000자만 미리 보기
