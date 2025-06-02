import pdfplumber
import os
from PIL import Image, ImageDraw

# 설정: 추출할 좌표 범위 (PDF 기준 좌표계, 단위: pt)
XMIN, YMIN = 50, 100     # 좌상단
XMAX, YMAX = 1000, 800    # 우하단

# 실행 예시
current_dir = os.path.dirname(os.path.abspath(__file__))
pdf_path = os.path.join(current_dir, "Consensus-ETL", "project", "consensus", "kiwoom", "2025-05-16_삼양식품_키움증권.pdf")

def is_within_box(x0, top, x1, bottom, xmin, ymin, xmax, ymax):
    return (x0 >= xmin and x1 <= xmax and top >= ymin and bottom <= ymax)

with pdfplumber.open(pdf_path) as pdf:
    for page_number, page in enumerate(pdf.pages):
        print(f"\n--- Page {page_number + 1} ---")

        words = page.extract_words()

        pil_image = page.to_image(resolution=150).original
        scale_x = pil_image.width / page.width
        scale_y = pil_image.height / page.height

        draw = ImageDraw.Draw(pil_image)

        for word in words:
            text = word["text"]
            x0, top, x1, bottom = word["x0"], word["top"], word["x1"], word["bottom"]

            # 특정 좌표 범위 내 텍스트만 필터링
            if not is_within_box(x0, top, x1, bottom, XMIN, YMIN, XMAX, YMAX):
                continue

            # 좌표계 변환
            left = x0 * scale_x
            right = x1 * scale_x
            top_img = top * scale_y
            bottom_img = bottom * scale_y

            print(f"Text: '{text}' at PDF ({x0:.1f}, {top:.1f}) → Image ({left:.1f}, {top_img:.1f})")
            draw.rectangle([left, top_img, right, bottom_img], outline="red", width=1)
        if page_number == 1:
            break
        img_path = os.path.join(current_dir, f"page_{page_number + 1}_clipped.png")
        pil_image.save(img_path)
        print(f"==> 시각화 이미지 저장됨: {img_path}")
