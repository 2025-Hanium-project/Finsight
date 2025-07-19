"""
새로운 Multi-Agent 설계에 따른 FastAPI 애플리케이션

기능:
- Multi-Agent 시스템 API
- 협업 시스템 API
- 워크플로우 API
- 대시보드 API
- 실시간 모니터링
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
import logging
from contextlib import asynccontextmanager
import asyncio
import time

# 내부 모듈 임포트
from config import (
    API_VERSION, API_HOST, API_PORT, LOG_LEVEL,
    LLM_PROVIDER, GEMINI_API_KEY
)
from routers.report_router import router as report_router

# 에러 처리 및 보안
from error_handlers import setup_exception_handlers
from error_handlers import get_security_manager, get_input_validator

# 협업 시스템
from utils.collaboration import SimpleCollaborationManager
from utils.collaboration.performance import get_optimized_collaboration_manager
from utils.collaboration.dashboard import get_collaboration_dashboard

# 고급 협업 매니저는 별도로 구현 필요
def get_advanced_collaboration_manager():
    """고급 협업 매니저 반환 (임시 구현)"""
    from utils.collaboration import CollaborationManager
    return CollaborationManager()

# 에이전트 시스템
from agents import (
    ALL_AGENT_CLASSES,
    DATA_AGENTS,
    ANALYSIS_AGENTS,
    REPORT_AGENTS,
    SUPPORT_AGENTS
)

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

# 협업 매니저 초기화
collaboration_manager = SimpleCollaborationManager()
advanced_manager = get_advanced_collaboration_manager()
optimized_manager = get_optimized_collaboration_manager()

# 시스템 시작 시간
startup_time = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global startup_time
    
    # 시작 시 실행
    startup_time = datetime.now()
    logger.info("🚀 FinsightAI 시스템 시작")
    logger.info(f"📊 등록된 에이전트 수: {len(ALL_AGENT_CLASSES)}")
    logger.info(f"🔧 LLM 제공자: {LLM_PROVIDER}")
    logger.info(f"🌐 API 서버: {API_HOST}:{API_PORT}")
    
    # 협업 시스템 초기화
    try:
        # 기본 협업 매니저 초기화
        logger.info("🤝 협업 시스템 초기화 중...")
        
        # 고급 협업 매니저 초기화
        logger.info("⚡ 고급 협업 시스템 초기화 중...")
        
        # 최적화된 협업 매니저 초기화
        logger.info("🚀 최적화된 협업 시스템 초기화 중...")
        
        # 대시보드 초기화
        logger.info("📊 대시보드 시스템 초기화 중...")
        
        logger.info("✅ 모든 시스템 초기화 완료")
        
    except Exception as e:
        logger.error(f"❌ 시스템 초기화 오류: {str(e)}")
        raise
    
    yield
    
    # 종료 시 실행
    logger.info("🛑 FinsightAI 시스템 종료")
    
    # 협업 시스템 정리
    try:
        collaboration_manager.cleanup()
        advanced_manager.cleanup()
        optimized_manager.cleanup()
        logger.info("🧹 협업 시스템 정리 완료")
    except Exception as e:
        logger.error(f"❌ 시스템 정리 오류: {str(e)}")

# FastAPI 애플리케이션 생성
app = FastAPI(
    title="FinsightAI Multi-Agent System",
    description="AI 기반 금융 분석 시스템",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(
    report_router,
    prefix=f"/api/{API_VERSION}",
    tags=["Multi-Agent Analysis"]
)

# 예외 핸들러 설정
setup_exception_handlers(app)

# ============================================================================
# 루트 엔드포인트
# ============================================================================

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "FinsightAI Multi-Agent System",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "uptime": str(datetime.now() - startup_time) if startup_time else "N/A"
    }

@app.get("/api")
async def api_info():
    """API 정보 엔드포인트"""
    return {
        "name": "FinsightAI Multi-Agent System",
        "version": "2.0.0",
        "description": "AI 기반 금융 분석 시스템",
        "endpoints": {
            "agents": f"/api/{API_VERSION}/agents/",
            "collaboration": f"/api/{API_VERSION}/collaboration/",
            "workflow": f"/api/{API_VERSION}/workflow/",
            "dashboard": f"/api/{API_VERSION}/dashboard/",
            "health": f"/api/{API_VERSION}/health"
        },
        "agent_categories": {
            "data_agents": len(DATA_AGENTS),
            "analysis_agents": len(ANALYSIS_AGENTS),
            "report_agents": len(REPORT_AGENTS),
            "support_agents": len(SUPPORT_AGENTS),
            "total_agents": len(ALL_AGENT_CLASSES)
        },
        "system_info": {
            "llm_provider": LLM_PROVIDER,
            "api_host": API_HOST,
            "api_port": API_PORT,
            "log_level": LOG_LEVEL
        }
    }

# ============================================================================
# 시스템 상태 엔드포인트
# ============================================================================

@app.get("/api/system/status")
async def system_status():
    """시스템 상태 확인"""
    try:
        # 협업 시스템 상태
        collaboration_status = collaboration_manager.get_collaboration_status()
        advanced_status = advanced_manager.get_system_status()
        optimized_status = optimized_manager.get_optimization_status()
        
        # 대시보드 정보
        dashboard = get_collaboration_dashboard()
        dashboard_summary = dashboard.get_summary()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": str(datetime.now() - startup_time) if startup_time else "N/A",
            "collaboration_systems": {
                "basic": collaboration_status,
                "advanced": advanced_status,
                "optimized": optimized_status
            },
            "dashboard": dashboard_summary,
            "agents": {
                "total": len(ALL_AGENT_CLASSES),
                "categories": {
                    "data": len(DATA_AGENTS),
                    "analysis": len(ANALYSIS_AGENTS),
                    "report": len(REPORT_AGENTS),
                    "support": len(SUPPORT_AGENTS)
                }
            },
            "llm_provider": LLM_PROVIDER,
            "api_version": API_VERSION
        }
    except Exception as e:
        logger.error(f"시스템 상태 확인 오류: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/system/agents")
async def list_all_agents():
    """등록된 모든 에이전트 목록"""
    try:
        return {
            "data_agents": list(DATA_AGENTS.keys()),
            "analysis_agents": list(ANALYSIS_AGENTS.keys()),
            "report_agents": list(REPORT_AGENTS.keys()),
            "support_agents": list(SUPPORT_AGENTS.keys()),
            "all_agents": list(ALL_AGENT_CLASSES.keys()),
            "total_count": len(ALL_AGENT_CLASSES)
        }
    except Exception as e:
        logger.error(f"에이전트 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"에이전트 목록 조회 오류: {str(e)}")

# ============================================================================
# 협업 시스템 엔드포인트
# ============================================================================

@app.get("/api/collaboration/status")
async def collaboration_status():
    """협업 시스템 상태 확인"""
    try:
        return {
            "basic_collaboration": collaboration_manager.get_collaboration_status(),
            "advanced_collaboration": advanced_manager.get_system_status(),
            "optimized_collaboration": optimized_manager.get_optimization_status(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"협업 시스템 상태 확인 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"협업 시스템 상태 확인 오류: {str(e)}")

@app.get("/api/collaboration/dashboard")
async def collaboration_dashboard():
    """협업 대시보드 정보"""
    try:
        dashboard = get_collaboration_dashboard()
        return {
            "summary": dashboard.get_summary(),
            "agent_activity": dashboard.get_agent_activity(),
            "system_alerts": dashboard.get_system_alerts(),
            "visualization_data": dashboard.get_visualization_data(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"협업 대시보드 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"협업 대시보드 조회 오류: {str(e)}")

# ============================================================================
# 모니터링 엔드포인트
# ============================================================================

@app.get("/api/monitoring/metrics")
async def get_system_metrics():
    """시스템 메트릭 조회"""
    try:
        dashboard = get_collaboration_dashboard()
        metrics = dashboard.get_summary()
        
        return {
            "metrics": metrics,
            "timestamp": datetime.now().isoformat(),
            "uptime": str(datetime.now() - startup_time) if startup_time else "N/A"
        }
    except Exception as e:
        logger.error(f"시스템 메트릭 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"시스템 메트릭 조회 오류: {str(e)}")

@app.get("/api/monitoring/alerts")
async def get_system_alerts():
    """시스템 알림 조회"""
    try:
        dashboard = get_collaboration_dashboard()
        alerts = dashboard.get_system_alerts()
        
        return {
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"시스템 알림 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"시스템 알림 조회 오류: {str(e)}")

# ============================================================================
# 에러 핸들링
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 핸들러"""
    logger.error(f"전역 예외 발생: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 핸들러"""
    logger.error(f"HTTP 예외 발생: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

# ============================================================================
# 메인 실행
# ============================================================================

if __name__ == "__main__":
    logger.info("🚀 FinsightAI Multi-Agent System 시작")
    logger.info(f"📊 등록된 에이전트: {len(ALL_AGENT_CLASSES)}개")
    logger.info(f"🔧 LLM 제공자: {LLM_PROVIDER}")
    logger.info(f"🌐 서버 주소: http://{API_HOST}:{API_PORT}")
    logger.info(f"📚 API 문서: http://{API_HOST}:{API_PORT}/docs")
    
    uvicorn.run(
        "app:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )
