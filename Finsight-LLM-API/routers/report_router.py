from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from models.schemas import (
    ReportSummaryRequest, ReportSummaryResponse,
    AnalysisRequest, AnalysisResponse,
    SentimentRequest, SentimentResponse
)
from agents.summary_agent import summarize_report
from agents.analysis_agent import analyze_reports
from agents.sentiment_agent import analyze_sentiment

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/summary", response_model=ReportSummaryResponse)
async def get_report_summary(request: ReportSummaryRequest):
    """증권사 리포트 요약 API"""
    logger.info("리포트 요약 요청")

    try:
        result = await summarize_report(request.report_content, request.report_info)
        return result
    except Exception as e:
        logger.error(f"리포트 요약 처리 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"리포트 요약 처리 중 오류 발생: {str(e)}")

@router.post("/analysis", response_model=AnalysisResponse)
async def get_integrated_analysis(request: AnalysisRequest):
    """리포트 통합 분석 API"""
    logger.info(f"리포트 통합 분석 요청: {request.target_type} - {request.target_name}")

    try:
        result = await analyze_reports(request.summaries, request.target_type, request.target_name)
        return result
    except Exception as e:
        logger.error(f"리포트 통합 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"리포트 통합 분석 중 오류 발생: {str(e)}")

@router.post("/sentiment", response_model=SentimentResponse)
async def get_sentiment_analysis(request: SentimentRequest):
    """리포트 감성 분석 API"""
    logger.info(f"리포트 감성 분석 요청: {request.target_type} - {request.target_name}")

    try:
        result = await analyze_sentiment(request.report_contents, request.target_type, request.target_name)
        return result
    except Exception as e:
        logger.error(f"리포트 감성 분석 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"리포트 감성 분석 중 오류 발생: {str(e)}")

# TO DO: Supervisor Agent 라우터 구현
