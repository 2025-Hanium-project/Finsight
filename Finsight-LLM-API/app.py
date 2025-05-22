from fastapi import FastAPI, Request
from datetime import datetime
import uvicorn
import logging

# 내부 모듈 임포트
from config import API_VERSION, API_HOST, API_PORT, LOG_LEVEL
from routers.report_router import router as report_router
from error_handlers import setup_exception_handlers

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="AI 기반 증시 투자 분석 시스템 API",
    description="증권사 리포트 분석 및 투자 인사이트 제공 API",
    version="0.1.0"
)

# 예외 핸들러 설정
setup_exception_handlers(app)

# API 라우터 등록
app.include_router(report_router, prefix=f"/{API_VERSION}/report", tags=["리포트 분석"])

# 기본 상태 확인 엔드포인트
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "AI 기반 증시 투자 분석 시스템 API",
        "version": API_VERSION,
        "timestamp": datetime.now().isoformat()
    }

# API 미들웨어 - 요청/응답 로깅
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()

    # 요청 처리
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()

        # 응답 시간 로깅
        logger.info(
            f"Method: {request.method}, Path: {request.url.path}, "
            f"Status: {response.status_code}, Process Time: {process_time:.3f}s"
        )

        return response
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        logger.error(
            f"Method: {request.method}, Path: {request.url.path}, "
            f"Error: {str(e)}, Process Time: {process_time:.3f}s"
        )
        raise

# UTF-8 인코딩 설정 - 수정된 버전
@app.middleware("http")
async def add_encoding_header(request: Request, call_next):
    response = await call_next(request)
    
    # Swagger UI 관련 경로에는 헤더를 수정하지 않음
    if not request.url.path.startswith("/docs") and not request.url.path.startswith("/openapi.json"):
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    
    return response

if __name__ == "__main__":
    # TO DO: Supervisor Agent 초기화
    # TO DO: RAG 시스템 초기화
    uvicorn.run("app:app", host=API_HOST, port=API_PORT, reload=True)
