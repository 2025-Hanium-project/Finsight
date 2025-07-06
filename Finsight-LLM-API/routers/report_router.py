from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

# 표준화된 데이터 모델만 사용
from utils.data_models import StandardInput, StandardOutput, AgentType, ProcessingStatus
from error_handlers import BaseAnalysisError, handle_agent_error
from agents.summary_agent import summarize_report
from agents.analysis_agent import create_d_day_report, create_d_plus1_report
from agents.sentiment_agent import analyze_sentiment
from agents.risk_agent import analyze_risk
from agents.growth_agent import analyze_growth
from agents.supervisor_agent import review_agent_results
logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/summary", response_model=StandardOutput)
async def get_report_summary(request: StandardInput):
    """증권사 리포트 요약 API"""
    logger.info(f"리포트 요약 요청: {request.target_name}")
    
    try:
        # 첫 번째 리포트 내용 사용
        if not request.reports:
            raise HTTPException(status_code=400, detail="리포트 내용이 필요합니다")
        
        report_content = request.reports[0].get("content", "")
        report_info = request.reports[0].get("info", {})
        
        # 기존 함수 호출
        result = await summarize_report(report_content, report_info)
        
        # 표준화된 출력 형태로 변환
        return StandardOutput(
            agent_type=AgentType.SUMMARY,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result={
                "summary": result.get("summary", ""),
                "key_points": result.get("key_points", []),
                "report_info": result.get("report_info", {})
            }
        )
    
    except BaseAnalysisError as e:
        logger.error(f"리포트 요약 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"리포트 요약 처리 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류 발생: {str(e)}")

@router.post("/sentiment", response_model=StandardOutput)
async def get_sentiment_analysis(request: StandardInput):
    """리포트 감성 분석 API"""
    logger.info(f"감성 분석 요청: {request.target_name}")
    
    try:
        # 리포트 내용 추출
        if not request.reports:
            raise HTTPException(status_code=400, detail="리포트 내용이 필요합니다")
        
        report_contents = [report.get("content", "") for report in request.reports]
        
        # 기존 함수 호출
        result = await analyze_sentiment(report_contents, request.target_type, request.target_name)
        
        # 표준화된 출력 형태로 변환
        return StandardOutput(
            agent_type=AgentType.SENTIMENT,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result={
                "overall_sentiment": result.get("overall_sentiment", ""),
                "sentiment_score": result.get("sentiment_score", 0.0),
                "positive_factors": result.get("positive_factors", []),
                "negative_factors": result.get("negative_factors", []),
                "trend_analysis": result.get("trend_analysis", {})
            }
        )
    
    except BaseAnalysisError as e:
        logger.error(f"감성 분석 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"감성 분석 처리 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류 발생: {str(e)}")

@router.post("/risk", response_model=StandardOutput)
async def get_risk_analysis(request: StandardInput):
    """리포트 리스크 분석 API"""
    logger.info(f"리스크 분석 요청: {request.target_name}")
    
    try:
        # 리포트 내용 추출
        if not request.reports:
            raise HTTPException(status_code=400, detail="리포트 내용이 필요합니다")
        
        report_contents = [report.get("content", "") for report in request.reports]
        
        # 기존 함수 호출
        result = await analyze_risk(report_contents, request.target_type, request.target_name)
        
        # 표준화된 출력 형태로 변환
        return StandardOutput(
            agent_type=AgentType.RISK,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result={
                "risk_factors": result.get("risk_factors", []),
                "risk_score": result.get("risk_score", 0),
                "risk_trend": result.get("risk_trend", ""),
                "risk_level": result.get("risk_level", ""),
                "mitigation_strategies": result.get("mitigation_strategies", [])
            }
        )
    
    except BaseAnalysisError as e:
        logger.error(f"리스크 분석 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"리스크 분석 처리 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류 발생: {str(e)}")

@router.post("/growth", response_model=StandardOutput)
async def get_growth_analysis(request: StandardInput):
    """리포트 성장성 분석 API"""
    logger.info(f"성장성 분석 요청: {request.target_name}")
    
    try:
        # 리포트 내용 추출
        if not request.reports:
            raise HTTPException(status_code=400, detail="리포트 내용이 필요합니다")
        
        report_contents = [report.get("content", "") for report in request.reports]
        
        # 기존 함수 호출
        result = await analyze_growth(report_contents, request.target_type, request.target_name)
        
        # 표준화된 출력 형태로 변환
        return StandardOutput(
            agent_type=AgentType.GROWTH,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result={
                "growth_drivers": result.get("growth_drivers", []),
                "growth_score": result.get("growth_score", 0),
                "growth_potential": result.get("growth_potential", ""),
                "growth_timeline": result.get("growth_timeline", ""),
                "investment_opportunities": result.get("investment_opportunities", [])
            }
        )
    
    except BaseAnalysisError as e:
        logger.error(f"성장성 분석 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"성장성 분석 처리 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류 발생: {str(e)}")

@router.post("/analysis/d-day", response_model=StandardOutput)
async def get_d_day_analysis(request: StandardInput):
    """D-day 종합 보고서 생성 API"""
    logger.info(f"D-day 종합 보고서 생성 요청: {request.target_type} - {request.target_name}")
    
    try:
        # 필수 데이터 검증
        agent_results = request.context.get("agent_results", {})
        if not agent_results:
            raise HTTPException(status_code=400, detail="에이전트 결과 데이터가 필요합니다 (context.agent_results)")
        
        # 에이전트 결과에서 개별 분석 결과 추출
        summaries = []
        sentiment = {}
        risk = {}
        growth = {}
        
        for agent_type, result in agent_results.items():
            if agent_type == "summary":
                summaries.append(result)
            elif agent_type == "sentiment":
                sentiment = result
            elif agent_type == "risk":
                risk = result
            elif agent_type == "growth":
                growth = result
        
        # D-day 보고서 생성
        result = await create_d_day_report(summaries, sentiment, risk, growth, request.target_type, request.target_name)
        
        # 표준화된 출력 형태로 변환
        return StandardOutput(
            agent_type=AgentType.ANALYSIS,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"D-day 보고서 생성 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"D-day 보고서 생성 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류 발생: {str(e)}")

@router.post("/analysis/d-plus1", response_model=StandardOutput)
async def get_d_plus1_analysis(request: StandardInput):
    """D+1 종합 보고서 생성 API"""
    logger.info(f"D+1 종합 보고서 생성 요청: {request.target_type} - {request.target_name}")
    
    try:
        # 필수 데이터 검증
        agent_results = request.context.get("agent_results", {})
        if not agent_results or "d_day_report" not in agent_results:
            raise HTTPException(status_code=400, detail="D-day 보고서 데이터가 필요합니다 (context.agent_results.d_day_report)")
        
        d_day_report = agent_results["d_day_report"]
        market_result = agent_results.get("market_result", None)
        
        # D+1 보고서 생성
        result = await create_d_plus1_report(d_day_report, market_result)
        
        # 표준화된 출력 형태로 변환
        return StandardOutput(
            agent_type=AgentType.ANALYSIS,
            target_type=request.target_type,
            target_name=request.target_name,
            symbol=request.symbol,
            status=ProcessingStatus.COMPLETED,
            success=True,
            result=result
        )
    
    except BaseAnalysisError as e:
        logger.error(f"D+1 보고서 생성 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"D+1 보고서 생성 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류 발생: {str(e)}")

@router.post("/supervisor/review", response_model=StandardOutput)
async def review_agents_results(request: StandardInput):
    """Supervisor Agent - 에이전트 결과 품질 검토 API"""
    logger.info(f"에이전트 결과 검토 요청: {request.target_type} - {request.target_name}")
    
    try:
        # 필수 데이터 검증
        agent_results = request.context.get("agent_results", {})
        if not agent_results:
            raise HTTPException(status_code=400, detail="검토할 에이전트 결과 데이터가 필요합니다 (context.agent_results)")
        
        # Supervisor Agent 검토 실행
        result = await review_agent_results(agent_results, request.target_type, request.target_name)
        
        # 표준화된 출력 형태로 변환
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
        logger.error(f"에이전트 결과 검토 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"에이전트 결과 검토 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류 발생: {str(e)}")
