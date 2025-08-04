from langchain_core.tools import tool
from langchain_community.document_loaders import PyPDFLoader

@tool
def extract_pdf(file_path: str) -> str:
    """PDF의 첫 번째 페이지 텍스트 추출

    Args:
        file_path (str): PDF 파일 경로

    Returns:
        str: 추출된 텍스트 (1페이지만)
    """
    # PyPDF 로더를 사용해 PDF 로드
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    if not docs:
        return "PDF 파일을 읽을 수 없습니다."
    
    # 첫 번째 페이지만 추출 (리포트 본문이 주로 1페이지에 있음)
    first_page = docs[0]
    page_text = first_page.page_content.strip()
    
    return page_text