"""
FinsightAI LLM API
컨센서스 리포트 처리를 위한 FastAPI 애플리케이션
"""
import os
from dotenv import load_dotenv
from fastapi import FastAPI

from langsmith import Client

# API 라우터 임포트
from api.endpoints import router

# 환경변수 로드
load_dotenv()

# 환경 변수에서 API 키 확인
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT")
LANGSMITH_TRACING_V2 = os.getenv("LANGSMITH_TRACING_V2")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT")

# LangSmith 클라이언트 초기화
langsmith_client = Client(api_key=LANGSMITH_API_KEY)

# FastAPI 앱 생성
app = FastAPI(
    title="FinsightAI LLM API",
    description="LangGraph 기반의 지능형 멀티 에이전트 시스템",
    version="1.0.0"
)

# API 라우터 등록
app.include_router(router)

@app.get("/")
async def root():
    """루트 엔드포인트 - API 정보 제공"""
    return {
        "message": "FinsightAI LLM API에 오신 것을 환영합니다!",
        "version": "1.0.0",
        "service": "FinsightAI LLM API",
        "docs_url": "/docs",
        "health_check": "/health",
        "api_endpoints": {
            "consensus": "/api/v1/consensus"
        }
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트 - 서비스 상태 확인"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "FinsightAI LLM API",
        "environment": {
            "google_api_key_configured": bool(GOOGLE_API_KEY),
            "langsmith_api_key_configured": bool(LANGSMITH_API_KEY),
            "langsmith_tracing_enabled": bool("LANGCHAIN_TRACING_V2")
        }
    }

# 개발 서버 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=38000,
        reload=True,
        log_level="info"
    ) 