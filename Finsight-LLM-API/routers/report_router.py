"""
리포트 분석 API 라우터

기능:
- 각 에이전트별 개별 분석 API
- 협업 시스템 API
- 워크플로우 API
- 대시보드 API
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import logging
import asyncio
from datetime import datetime

# 표준화된 데이터 모델
from utils.core.data_models import StandardInput, StandardOutput, ProcessingStatus
from utils.core.agent_base import AgentType, AgentConfig

# 새로운 에이전트 구조 import
from agents import (
    # 데이터 에이전트
    FinancialStatementAgent,
    NewsAnalysisAgent,
    SecuritiesReportAgent,
    MarketDataAgent,
    
    # 분석 에이전트
    RiskAssessmentAgent,
    GrowthAnalysisAgent,
    ValuationAgent,
    PeerComparisonAgent,
    
    # 리포트 에이전트
    DDayReportAgent,
    DPlus1ReportAgent,
    
    # 지원 에이전트
    SupervisorAgent,
    DataQualityAgent,
    DocumentProcessingAgent,
    
    # 에이전트 그룹
    ALL_AGENT_CLASSES,
    DATA_AGENTS,
    ANALYSIS_AGENTS,
    REPORT_AGENTS,
    SUPPORT_AGENTS
)

# 협업 시스템
from utils.collaboration import SimpleCollaborationManager
from utils.collaboration.performance import get_optimized_collaboration_manager
from utils.collaboration.dashboard import get_collaboration_dashboard

# 고급 협업 매니저는 별도로 구현 필요
def get_advanced_collaboration_manager():
    """고급 협업 매니저 반환 (임시 구현)"""
    from utils.collaboration import CollaborationManager
    return CollaborationManager()

# 에러 처리
from error_handlers import BaseAnalysisError, handle_agent_error

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# 에이전트 인스턴스 생성
# ============================================================================

# 데이터 에이전트
financial_agent = FinancialStatementAgent()
news_agent = NewsAnalysisAgent()
securities_agent = SecuritiesReportAgent()
market_agent = MarketDataAgent()

# 분석 에이전트
risk_config = AgentConfig(name="risk_assessment_agent", agent_type=AgentType.RISK_ASSESSMENT)
risk_agent = RiskAssessmentAgent(risk_config)

growth_config = AgentConfig(name="growth_analysis_agent", agent_type=AgentType.GROWTH_ANALYSIS)
growth_agent = GrowthAnalysisAgent(growth_config)

valuation_config = AgentConfig(name="valuation_agent", agent_type=AgentType.VALUATION)
valuation_agent = ValuationAgent(valuation_config)

peer_config = AgentConfig(name="peer_comparison_agent", agent_type=AgentType.PEER_COMPARISON)
peer_agent = PeerComparisonAgent(peer_config)

# 리포트 에이전트
dday_config = AgentConfig(name="dday_report_agent", agent_type=AgentType.DDAY_REPORT)
dday_agent = DDayReportAgent(dday_config)

dplus1_config = AgentConfig(name="dplus1_report_agent", agent_type=AgentType.DPLUS1_REPORT)
dplus1_agent = DPlus1ReportAgent(dplus1_config)

# 지원 에이전트
supervisor_agent = SupervisorAgent()  # 기본 설정으로 생성

data_quality_config = AgentConfig(name="data_quality_agent", agent_type=AgentType.DATA_QUALITY)
data_quality_agent = DataQualityAgent(data_quality_config)

document_config = AgentConfig(name="document_processing_agent", agent_type=AgentType.DOCUMENT_PROCESSING)
document_agent = DocumentProcessingAgent(document_config)

# 협업 매니저
collaboration_manager = SimpleCollaborationManager()
advanced_manager = get_advanced_collaboration_manager()
optimized_manager = get_optimized_collaboration_manager()

# ============================================================================
# 데이터 에이전트 API
# ============================================================================

@router.post("/agents/financial-statement", response_model=StandardOutput)
async def analyze_financial_statement(request: StandardInput):
    """재무제표 분석 API"""
    logger.info(f"재무제표 분석 요청: {request.target_name}")
    
    try:
        result = await financial_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        return StandardOutput(
            agent_type=AgentType.FINANCIAL_STATEMENT,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"재무제표 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"재무제표 분석 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.post("/agents/news-analysis", response_model=StandardOutput)
async def analyze_news(request: StandardInput):
    """뉴스 분석 API"""
    logger.info(f"뉴스 분석 요청: {request.target_name}")
    
    try:
        result = await news_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        return StandardOutput(
            agent_type=AgentType.NEWS_ANALYSIS,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"뉴스 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"뉴스 분석 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.post("/agents/securities-report", response_model=StandardOutput)
async def analyze_securities_report(request: StandardInput):
    """증권사 리포트 분석 API (텍스트)"""
    logger.info(f"증권사 리포트 분석 요청: {request.target_name}")
    
    try:
        result = await securities_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context,
            "data_type": "text"
        })
        
        return StandardOutput(
            agent_type=AgentType.SECURITIES_REPORT,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"증권사 리포트 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"증권사 리포트 분석 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@router.post("/agents/securities-report/image", response_model=StandardOutput)
async def analyze_securities_report_image(request: StandardInput):
    """증권사 리포트 이미지 분석 API"""
    logger.info(f"증권사 리포트 이미지 분석 요청: {request.target_name}")
    
    try:
        # 이미지 경로 확인
        image_path = request.context.get("image_path") if request.context else None
        if not image_path:
            raise HTTPException(status_code=400, detail="이미지 경로가 필요합니다")
        
        result = await securities_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "image_path": image_path,
            "data_type": "image"
        })
        
        return StandardOutput(
            agent_type=AgentType.SECURITIES_REPORT,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"증권사 리포트 이미지 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"증권사 리포트 이미지 분석 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@router.post("/agents/securities-report/batch", response_model=StandardOutput)
async def process_batch_securities_reports(request: StandardInput):
    """배치 증권사 리포트 이미지 처리 API"""
    logger.info(f"배치 증권사 리포트 이미지 처리 요청")
    
    try:
        # 이미지 경로 목록 확인
        image_paths = request.context.get("image_paths") if request.context else []
        if not image_paths:
            raise HTTPException(status_code=400, detail="이미지 경로 목록이 필요합니다")
        
        result = await securities_agent.process_batch_images(image_paths)
        
        return StandardOutput(
            agent_type=AgentType.SECURITIES_REPORT,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"배치 증권사 리포트 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"배치 증권사 리포트 처리 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@router.post("/agents/securities-report/validate-image", response_model=StandardOutput)
async def validate_image_quality(request: StandardInput):
    """이미지 품질 검증 API"""
    logger.info(f"이미지 품질 검증 요청")
    
    try:
        # 이미지 경로 확인
        image_path = request.context.get("image_path") if request.context else None
        if not image_path:
            raise HTTPException(status_code=400, detail="이미지 경로가 필요합니다")
        
        result = await securities_agent.validate_image_quality(image_path)
        
        return StandardOutput(
            agent_type=AgentType.SECURITIES_REPORT,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"이미지 품질 검증 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"이미지 품질 검증 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.post("/agents/market-data", response_model=StandardOutput)
async def analyze_market_data(request: StandardInput):
    """시장 데이터 분석 API"""
    logger.info(f"시장 데이터 분석 요청: {request.target_name}")
    
    try:
        result = await market_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        return StandardOutput(
            agent_type=AgentType.MARKET_DATA,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"시장 데이터 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"시장 데이터 분석 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

# ============================================================================
# 분석 에이전트 API
# ============================================================================

@router.post("/agents/risk-assessment", response_model=StandardOutput)
async def assess_risk(request: StandardInput):
    """리스크 평가 API"""
    logger.info(f"리스크 평가 요청: {request.target_name}")
    
    try:
        result = await risk_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        return StandardOutput(
            agent_type=AgentType.RISK_ASSESSMENT,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"리스크 평가 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"리스크 평가 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.post("/agents/growth-analysis", response_model=StandardOutput)
async def analyze_growth(request: StandardInput):
    """성장성 분석 API"""
    logger.info(f"성장성 분석 요청: {request.target_name}")
    
    try:
        result = await growth_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        return StandardOutput(
            agent_type=AgentType.GROWTH_ANALYSIS,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"성장성 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"성장성 분석 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.post("/agents/valuation", response_model=StandardOutput)
async def analyze_valuation(request: StandardInput):
    """밸류에이션 분석 API"""
    logger.info(f"밸류에이션 분석 요청: {request.target_name}")
    
    try:
        result = await valuation_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        return StandardOutput(
            agent_type=AgentType.VALUATION,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"밸류에이션 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"밸류에이션 분석 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.post("/agents/peer-comparison", response_model=StandardOutput)
async def compare_peers(request: StandardInput):
    """동종업계 비교 API"""
    logger.info(f"동종업계 비교 요청: {request.target_name}")
    
    try:
        result = await peer_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        return StandardOutput(
            agent_type=AgentType.PEER_COMPARISON,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"동종업계 비교 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"동종업계 비교 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

# ============================================================================
# 리포트 에이전트 API
# ============================================================================

@router.post("/agents/dday-report", response_model=StandardOutput)
async def generate_dday_report(request: StandardInput):
    """D-day 리포트 생성 API"""
    logger.info(f"D-day 리포트 생성 요청: {request.target_name}")
    
    try:
        result = await dday_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        return StandardOutput(
            agent_type=AgentType.DDAY_REPORT,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"D-day 리포트 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"D-day 리포트 생성 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.post("/agents/dplus1-report", response_model=StandardOutput)
async def generate_dplus1_report(request: StandardInput):
    """D+1 리포트 생성 API"""
    logger.info(f"D+1 리포트 생성 요청: {request.target_name}")
    
    try:
        result = await dplus1_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        return StandardOutput(
            agent_type=AgentType.DPLUS1_REPORT,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"D+1 리포트 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"D+1 리포트 생성 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

# ============================================================================
# 지원 에이전트 API
# ============================================================================

@router.post("/agents/document-processing", response_model=StandardOutput)
async def process_document(request: StandardInput):
    """문서 처리 API"""
    logger.info(f"문서 처리 요청: {request.target_name}")
    
    try:
        result = await document_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        return StandardOutput(
            agent_type=AgentType.DOCUMENT_PROCESSING,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"문서 처리 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"문서 처리 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.post("/agents/data-quality", response_model=StandardOutput)
async def assess_data_quality(request: StandardInput):
    """데이터 품질 평가 API"""
    logger.info(f"데이터 품질 평가 요청: {request.target_name}")
    
    try:
        result = await data_quality_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        return StandardOutput(
            agent_type=AgentType.DATA_QUALITY,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"데이터 품질 평가 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"데이터 품질 평가 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@router.post("/agents/supervisor", response_model=StandardOutput)
async def supervise_analysis(request: StandardInput):
    """Supervisor 분석 API"""
    logger.info(f"Supervisor 분석 요청: {request.target_name}")
    
    try:
        result = await supervisor_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        return StandardOutput(
            agent_type=AgentType.SUPERVISOR,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"Supervisor 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Supervisor 분석 예외: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

# ============================================================================
# 협업 시스템 API
# ============================================================================

@router.post("/collaboration/basic")
async def basic_collaboration(request: StandardInput):
    """기본 협업 API"""
    logger.info(f"기본 협업 요청: {request.target_name}")
    
    try:
        # 에이전트 등록
        collaboration_manager.register_agent(financial_agent)
        collaboration_manager.register_agent(news_agent)
        collaboration_manager.register_agent(risk_agent)
        collaboration_manager.register_agent(market_agent)
        
        # 협업 요청
        response = await collaboration_manager.request_collaboration(
            source_agent="risk_assessment_agent",
            target_agent="financial_statement_agent",
            request_type="financial_analysis",
            context={"target_name": request.target_name}
        )
        
        return {
            "success": True,
            "collaboration_response": response,
            "collaboration_status": collaboration_manager.get_collaboration_status()
        }
    
    except Exception as e:
        logger.error(f"기본 협업 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"협업 오류: {str(e)}")

@router.post("/collaboration/advanced")
async def advanced_collaboration(request: StandardInput):
    """고급 협업 API"""
    logger.info(f"고급 협업 요청: {request.target_name}")
    
    try:
        # 에이전트 등록
        advanced_manager.register_agent(financial_agent)
        advanced_manager.register_agent(news_agent)
        advanced_manager.register_agent(risk_agent)
        advanced_manager.register_agent(market_agent)
        
        # 지식 공유 및 워크플로우 실행
        knowledge_id = await advanced_manager.add_knowledge(
            "financial_analysis",
            {"target": request.target_name, "data": "재무 분석 결과"}
        )
        
        workflow_result = await advanced_manager.execute_workflow(
            "risk_assessment",
            {"target_name": request.target_name}
        )
        
        return {
            "success": True,
            "knowledge_id": knowledge_id,
            "workflow_result": workflow_result,
            "system_status": advanced_manager.get_system_status()
        }
    
    except Exception as e:
        logger.error(f"고급 협업 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"협업 오류: {str(e)}")

@router.post("/collaboration/optimized")
async def optimized_collaboration(request: StandardInput):
    """최적화된 협업 API"""
    logger.info(f"최적화된 협업 요청: {request.target_name}")
    
    try:
        # 에이전트 등록
        optimized_manager.register_agent(financial_agent)
        optimized_manager.register_agent(news_agent)
        optimized_manager.register_agent(risk_agent)
        optimized_manager.register_agent(market_agent)
        
        # 병렬 처리
        parallel_results = await optimized_manager.send_messages_parallel([
            {"source": "risk_assessment_agent", "target": "financial_statement_agent", "type": "financial_analysis"},
            {"source": "risk_assessment_agent", "target": "news_analysis_agent", "type": "sentiment_analysis"},
            {"source": "risk_assessment_agent", "target": "market_data_agent", "type": "market_analysis"}
        ])
        
        return {
            "success": True,
            "parallel_results": parallel_results,
            "optimization_status": optimized_manager.get_optimization_status()
        }
    
    except Exception as e:
        logger.error(f"최적화된 협업 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"협업 오류: {str(e)}")

# ============================================================================
# 대시보드 API
# ============================================================================

@router.get("/dashboard/summary")
async def get_dashboard_summary():
    """대시보드 요약 API"""
    try:
        dashboard = get_collaboration_dashboard()
        summary = dashboard.get_summary()
        return summary
    except Exception as e:
        logger.error(f"대시보드 요약 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"대시보드 오류: {str(e)}")

@router.get("/dashboard/agent/{agent_name}")
async def get_agent_details(agent_name: str):
    """에이전트 상세 정보 API"""
    try:
        dashboard = get_collaboration_dashboard()
        agent_details = dashboard.get_agent_details(agent_name)
        return agent_details
    except Exception as e:
        logger.error(f"에이전트 상세 정보 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"에이전트 정보 오류: {str(e)}")

@router.get("/dashboard/alerts")
async def get_system_alerts():
    """시스템 알림 API"""
    try:
        dashboard = get_collaboration_dashboard()
        alerts = dashboard.get_system_alerts()
        return alerts
    except Exception as e:
        logger.error(f"시스템 알림 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"알림 오류: {str(e)}")

@router.get("/dashboard/visualization")
async def get_visualization_data():
    """시각화 데이터 API"""
    try:
        dashboard = get_collaboration_dashboard()
        viz_data = dashboard.get_visualization_data()
        return viz_data
    except Exception as e:
        logger.error(f"시각화 데이터 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"시각화 오류: {str(e)}")

# ============================================================================
# 워크플로우 API
# ============================================================================

@router.post("/workflow/comprehensive")
async def execute_comprehensive_workflow(request: StandardInput):
    """종합 워크플로우 실행 API"""
    logger.info(f"종합 워크플로우 실행 요청: {request.target_name}")
    
    try:
        # 1단계: 재무 분석
        financial_result = await financial_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        # 2단계: 뉴스 분석
        news_result = await news_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        # 3단계: 시장 데이터 분석
        market_result = await market_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": request.context
        })
        
        # 4단계: 리스크 평가
        risk_result = await risk_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": {
                **request.context,
                "financial_result": financial_result,
                "news_result": news_result,
                "market_result": market_result
            }
        })
        
        # 5단계: D-day 리포트 생성
        dday_result = await dday_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": {
                **request.context,
                "financial_result": financial_result,
                "news_result": news_result,
                "market_result": market_result,
                "risk_result": risk_result
            }
        })
        
        # 6단계: Supervisor 검토
        supervisor_result = await supervisor_agent.analyze({
            "target_type": request.target_type,
            "target_name": request.target_name,
            "symbol": request.symbol,
            "reports": request.reports,
            "context": {
                **request.context,
                "agent_results": {
                    "financial": financial_result,
                    "news": news_result,
                    "market": market_result,
                    "risk": risk_result,
                    "dday": dday_result
                }
            }
        })
        
        return {
            "success": True,
            "workflow_results": {
                "financial_analysis": financial_result,
                "news_analysis": news_result,
                "market_analysis": market_result,
                "risk_assessment": risk_result,
                "dday_report": dday_result,
                "supervisor_review": supervisor_result
            },
            "execution_time": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"종합 워크플로우 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"워크플로우 오류: {str(e)}")

# ============================================================================
# 유틸리티 API
# ============================================================================

@router.get("/agents/list")
async def get_agents_list():
    """등록된 에이전트 목록 API"""
    try:
        return {
            "data_agents": list(DATA_AGENTS.keys()),
            "analysis_agents": list(ANALYSIS_AGENTS.keys()),
            "report_agents": list(REPORT_AGENTS.keys()),
            "support_agents": list(SUPPORT_AGENTS.keys()),
            "all_agents": list(ALL_AGENT_CLASSES.keys())
        }
    except Exception as e:
        logger.error(f"에이전트 목록 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"에이전트 목록 오류: {str(e)}")

@router.get("/health")
async def health_check():
    """시스템 건강도 확인 API"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "agents_count": len(ALL_AGENT_CLASSES)
        }
    except Exception as e:
        logger.error(f"건강도 확인 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"건강도 확인 오류: {str(e)}")
