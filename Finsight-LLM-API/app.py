from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# 내부 모듈 임포트
from config import API_VERSION, API_HOST, API_PORT, LOG_LEVEL
from routers.report_router import router as report_router
# TODO: 워크플로우 라우터 구현 필요시 추가
from error_handlers import setup_exception_handlers
from error_handlers import get_security_manager, get_input_validator

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 외부 라이브러리 로깅 레벨 조정 (스팸 메시지 방지)
logging.getLogger("watchfiles").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# 보안 관리자 초기화
security_manager = get_security_manager()
input_validator = get_input_validator()

# 애플리케이션 생명주기 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시 실행
    logger.info("AI 기반 증시 투자 분석 시스템 API 시작")
    yield
    # 종료 시 실행 (필요한 경우)
    logger.info("AI 기반 증시 투자 분석 시스템 API 종료")

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="AI 기반 증시 투자 분석 시스템 API",
    description="증권사 리포트 분석 및 투자 인사이트 제공 API",
    version="2.0.0",
    lifespan=lifespan,
    # 보안 헤더 추가
    docs_url="/docs" if LOG_LEVEL == "DEBUG" else None,  # 프로덕션에서는 docs 비활성화
    redoc_url="/redoc" if LOG_LEVEL == "DEBUG" else None
)

# 예외 핸들러 설정
setup_exception_handlers(app)

# 보안 미들웨어
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """보안 미들웨어"""
    start_time = datetime.now()
    
    # 클라이언트 IP 추출
    client_ip = request.client.host
    
    try:
        # IP 차단 확인
        if security_manager.is_ip_blocked(client_ip):
            logger.warning(f"차단된 IP에서 요청: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"error": "접근이 차단된 IP입니다"}
            )
        
        # Rate limiting 확인
        endpoint = request.url.path
        if not security_manager.check_rate_limit(client_ip, endpoint):
            security_manager.log_security_event("rate_limit_exceeded", {
                "client_ip": client_ip,
                "endpoint": endpoint
            })
            return JSONResponse(
                status_code=429,
                content={"error": "요청 빈도가 너무 높습니다. 잠시 후 다시 시도하세요"}
            )
        
        # Content-Type 검증
        if request.method == "POST":
            content_type = request.headers.get("content-type", "")
            if not security_manager.validate_content_type(content_type):
                security_manager.log_security_event("invalid_content_type", {
                    "client_ip": client_ip,
                    "content_type": content_type
                })
                return JSONResponse(
                    status_code=400,
                    content={"error": "지원하지 않는 Content-Type입니다"}
                )
        
        # 요청 처리
        response = await call_next(request)
        
        # 보안 헤더 추가
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
        
    except Exception as e:
        logger.error(f"보안 미들웨어 오류: {str(e)}")
        security_manager.log_security_event("middleware_error", {
            "client_ip": client_ip,
            "error": str(e)
        })
        raise

# API 라우터 등록
app.include_router(report_router, prefix=f"/{API_VERSION}/report", tags=["리포트 분석"])
# TODO: 워크플로우 라우터 등록 구현 필요시 추가

# 기본 상태 확인 엔드포인트
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "AI 기반 증시 투자 분석 시스템 API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "리포트 요약",
            "감성 분석", 
            "리스크 분석",
            "성장성 분석",
            "종합 분석",
            "품질 검토"
        ],
        "endpoints": {
            "report": f"/{API_VERSION}/report"
        }
    }

# 보안 상태 확인 엔드포인트
@app.get("/security/status")
async def security_status():
    """보안 상태 확인"""
    return {
        "status": "active",
        "features": [
            "입력 sanitization",
            "Rate limiting",
            "IP blocking",
            "Content-Type validation",
            "Error message sanitization"
        ],
        "timestamp": datetime.now().isoformat()
    }

# API 미들웨어 - 요청/응답 로깅
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    
    # 요청 ID 생성
    request_id = security_manager.generate_request_id()
    
    # 요청 처리
    try:
        response = await call_next(request)
        process_time = (datetime.now() - start_time).total_seconds()

        # 응답 시간 로깅
        logger.info(
            f"Method: {request.method}, Path: {request.url.path}, "
            f"Status: {response.status_code}, Process Time: {process_time:.3f}s, "
            f"Request ID: {request_id}"
        )

        return response
    except Exception as e:
        process_time = (datetime.now() - start_time).total_seconds()
        
        # 에러 메시지 sanitization
        safe_error_msg = security_manager.sanitize_error_message(str(e))
        
        logger.error(
            f"Method: {request.method}, Path: {request.url.path}, "
            f"Error: {safe_error_msg}, Process Time: {process_time:.3f}s, "
            f"Request ID: {request_id}"
        )
        raise

# UTF-8 인코딩 설정
@app.middleware("http")
async def add_encoding_header(request: Request, call_next):
    response = await call_next(request)
    
    # Swagger UI 관련 경로에는 헤더를 수정하지 않음
    if not request.url.path.startswith("/docs") and not request.url.path.startswith("/openapi.json"):
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    
    return response

if __name__ == "__main__":
    uvicorn.run("app:app", host=API_HOST, port=API_PORT, reload=True)
