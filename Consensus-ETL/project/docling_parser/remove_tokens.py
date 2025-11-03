import re

def preprocess_text_for_rag(text):
    """
    RAG용 텍스트를 전처리
    마크다운 구조는 보존하되, 분석에 불필요한 노이즈를 제거
    """
    
    # 1. 제거할 패턴 정의 (리포트 샘플 기반)
    patterns_to_remove = [
        # 이메일 주소
        r'\S+@\S+\.\S+',
        # 전화번호 (예: (02)2115-5148)
        r'\(?\d{2,3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}',
        # 저작권, 면책조항, 자료 출처 등
        r'Copyright.*',
        r'Disclaimer.*',
        r'Compliance.*',
        r'자료:.*',
        # 주소 (대부분 여의도에 집중)
        r'\d{5}\s+서울시.*',
        # KOSPI, 시가총액 등 (내용 분석에 불필요한 정보)
        r'KOSPI\s+\d+\.\d+',
        r'시가총액\s+\d+십억원',
        r'시가총액비중\s+\d+\.\d+%',
        r'52주\s+최고/최저.*',
        r'외국인지분율.*',
        r'주요주주.*'
    ]
    
    for pattern in patterns_to_remove:
        # re.IGNORECASE: 대소문자 무시
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # 2. 과도한 연속 줄바꿈을 2개로 축소
    text = re.sub(r'(\n\s*){3,}', '\n\n', text)
    
    # 3. 양 끝의 공백 제거
    text = text.strip()

    return text

# if __name__ == "__main__":
    # raw_text = extract_first_page_markdown(pdf_file)
    # processed_text = preprocess_text_for_rag(raw_text)
    # f.write(processed_text)