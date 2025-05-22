from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 커스텀 예외 클래스 정의
class AnalysisError(Exception):
    """기본 에러 클래스"""
    pass

class LLMRequestError(AnalysisError):
    """LLM 요청 관련 오류"""
    pass

class InvalidRequestError(AnalysisError):
    """요청 형식이 올바르지 않을 때 발생하는 예외"""
    pass

# 오류 응답 포맷 함수
def format_error_response(error_code: int, error_msg: str, request: Request) -> Dict[str, Any]:
    return {
        "status": "error",
        "error_code": error_code,
        "message": error_msg,
        "timestamp": datetime.now().isoformat(),
        "path": request.url.path
    }

# 예외 핸들러 설정 함수
def setup_exception_handlers(app: FastAPI) -> None:
    """애플리케이션에 예외 핸들러 등록"""

    @app.exception_handler(LLMRequestError)
    async def llm_request_error_handler(request: Request, exc: LLMRequestError):
        return JSONResponse(
            status_code=503,
            content=format_error_response(503, f"LLM 요청 처리 중 오류 발생: {str(exc)}", request)
        )

    @app.exception_handler(InvalidRequestError)
    async def invalid_request_handler(request: Request, exc: InvalidRequestError):
        return JSONResponse(
            status_code=400,
            content=format_error_response(400, f"잘못된 요청: {str(exc)}", request)
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(exc.status_code, exc.detail, request)
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # 디버그를 위한 로그 추가
        logger.error(f"처리되지 않은 예외 발생: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content=format_error_response(500, "서버 내부 오류가 발생했습니다", request)
        )
