"""
종합 분석 에이전트
"""
from typing import Dict, Any, List
from datetime import datetime
import json

from models.schemas import AnalysisResponse
from utils.llm_client import generate_response
from error_handlers import AgentError
from utils.agent_base import BaseAgent


class AnalysisAgent(BaseAgent):
    """종합 분석 에이전트 클래스"""
    
    def __init__(self):
        super().__init__("analysis_agent")
    
    async def create_d_day_report(self, summaries: List[Dict[str, Any]], sentiment: Dict[str, Any], 
                                  risk: Dict[str, Any], growth: Dict[str, Any], 
                                  target_type: str, target_name: str) -> Dict[str, Any]:
        """D-day 보고서 생성 메인 함수"""
        return await create_d_day_report(summaries, sentiment, risk, growth, target_type, target_name)
    
    async def create_d_plus1_report(self, d_day_report: Dict[str, Any], market_result: Any) -> Dict[str, Any]:
        """D+1 보고서 생성 메인 함수"""
        return await create_d_plus1_report(d_day_report, market_result)


async def create_d_day_report(summaries: List[Dict[str, Any]], sentiment: Dict[str, Any], 
                              risk: Dict[str, Any], growth: Dict[str, Any], 
                              target_type: str, target_name: str) -> Dict[str, Any]:
    """
    D-day 보고서: 컨센서스 데이터 기반 투자 의견 종합
    """
    from utils.logging_config import get_agent_logger
    
    logger = get_agent_logger("analysis_agent")
    start_time = datetime.now()
    
    try:
        logger.log_start("D-day 보고서 생성", extra={
            'target_type': target_type,
            'target_name': target_name,
            'summaries_count': len(summaries) if summaries else 0
        })
        
        # 입력 검증
        _validate_d_day_inputs(summaries, sentiment, risk, growth, target_type, target_name)
        
        # 프롬프트 생성
        prompt = _create_d_day_prompt(summaries, sentiment, risk, growth, target_type, target_name)
        llm_response = await generate_response(prompt, agent_type="analysis_agent")
        
        # JSON 파싱
        parsed_data = json.loads(llm_response)
        
        # 메타데이터 추가
        parsed_data["generated_at"] = datetime.now().isoformat()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.log_completion("D-day 보고서 생성", processing_time, extra={
            'investment_opinion': parsed_data.get('consensus', {}).get('opinion', 'unknown'),
            'confidence': parsed_data.get('consensus', {}).get('confidence', 'unknown')
        })
        
        return parsed_data
        
    except json.JSONDecodeError as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.log_error("D-day 보고서 생성", e, extra={
            'processing_time': processing_time,
            'target_type': target_type,
            'target_name': target_name,
            'error_type': 'json_decode_error'
        })
        
        raise AgentError(
            agent_name="analysis_agent",
            message=f"D-day 보고서 응답 파싱 실패: {str(e)}",
            details={"target_type": target_type, "target_name": target_name}
        )
    except AgentError:
        # 이미 처리된 에러는 그대로 전파
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.log_error("D-day 보고서 생성", e, extra={
            'processing_time': processing_time,
            'target_type': target_type,
            'target_name': target_name
        })
        
        raise AgentError(
            agent_name="analysis_agent",
            message=f"D-day 보고서 생성 실패: {str(e)}",
            details={"target_type": target_type, "target_name": target_name}
        )


async def create_d_plus1_report(d_day_report: Dict[str, Any], market_result: Any) -> Dict[str, Any]:
    """
    D+1 보고서: D-day 보고서와 전날 장 결과 기반 해석
    """
    from utils.logging_config import get_agent_logger
    
    logger = get_agent_logger("analysis_agent")
    start_time = datetime.now()
    
    try:
        logger.log_start("D+1 보고서 생성", extra={
            'target_type': d_day_report.get('target_type', ''),
            'target_name': d_day_report.get('target_name', '')
        })
        
        # 입력 검증
        _validate_d_plus1_inputs(d_day_report, market_result)
        
        # 프롬프트 생성
        prompt = _create_d_plus1_prompt(d_day_report, market_result)
        llm_response = await generate_response(prompt, agent_type="analysis_agent")
        
        # JSON 파싱
        parsed_data = json.loads(llm_response)
        
        # 메타데이터 추가
        parsed_data["generated_at"] = datetime.now().isoformat()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.log_completion("D+1 보고서 생성", processing_time, extra={
            'investment_opinion': parsed_data.get('consensus', {}).get('opinion', 'unknown'),
            'confidence': parsed_data.get('consensus', {}).get('confidence', 'unknown')
        })
        
        return parsed_data
        
    except json.JSONDecodeError as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.log_error("D+1 보고서 생성", e, extra={
            'processing_time': processing_time,
            'target_type': d_day_report.get('target_type', ''),
            'target_name': d_day_report.get('target_name', ''),
            'error_type': 'json_decode_error'
        })
        
        raise AgentError(
            agent_name="analysis_agent",
            message=f"D+1 보고서 응답 파싱 실패: {str(e)}",
            details={
                "target_type": d_day_report.get('target_type', ''),
                "target_name": d_day_report.get('target_name', '')
            }
        )
    except AgentError:
        # 이미 처리된 에러는 그대로 전파
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.log_error("D+1 보고서 생성", e, extra={
            'processing_time': processing_time,
            'target_type': d_day_report.get('target_type', ''),
            'target_name': d_day_report.get('target_name', '')
        })
        
        raise AgentError(
            agent_name="analysis_agent",
            message=f"D+1 보고서 생성 실패: {str(e)}",
            details={
                "target_type": d_day_report.get('target_type', ''),
                "target_name": d_day_report.get('target_name', '')
            }
        )


def _validate_d_day_inputs(summaries: List[Dict[str, Any]], sentiment: Dict[str, Any], 
                           risk: Dict[str, Any], growth: Dict[str, Any], 
                           target_type: str, target_name: str) -> None:
    """D-day 보고서 입력 데이터 검증"""
    from error_handlers import ValidationError
    
    if not target_name or not target_name.strip():
        raise ValidationError(
            message="분석 대상명이 지정되지 않았습니다",
            field_name="target_name",
            invalid_value=target_name
        )
    
    if not target_type or target_type.lower() not in ['company', 'industry', 'sector']:
        raise ValidationError(
            message="올바르지 않은 분석 대상 타입입니다",
            field_name="target_type",
            invalid_value=target_type,
            details={"valid_types": ['company', 'industry', 'sector']}
        )
    
    if not summaries:
        raise AgentError(
            agent_name="analysis_agent",
            message="요약 데이터가 없습니다",
            details={"target_type": target_type, "target_name": target_name}
        )
    
    if not sentiment or not risk or not growth:
        raise AgentError(
            agent_name="analysis_agent",
            message="필수 분석 데이터가 없습니다",
            details={
                "target_type": target_type,
                "target_name": target_name,
                "missing_data": {
                    "sentiment": not sentiment,
                    "risk": not risk,
                    "growth": not growth
                }
            }
        )


def _validate_d_plus1_inputs(d_day_report: Dict[str, Any], market_result: Any) -> None:
    """D+1 보고서 입력 데이터 검증"""
    if not d_day_report:
        raise AgentError(
            agent_name="analysis_agent",
            message="D-day 보고서 데이터가 없습니다",
            details={}
        )
    
    if not market_result:
        raise AgentError(
            agent_name="analysis_agent",
            message="시장 결과 데이터가 없습니다",
            details={
                "target_type": d_day_report.get('target_type', ''),
                "target_name": d_day_report.get('target_name', '')
            }
        )


def _create_d_day_prompt(summaries, sentiment, risk, growth, target_type, target_name):
    """D-day 보고서 프롬프트 생성"""
    return f"""
너는 숙련된 증권 투자 전략가이며, 아래의 요약/감성/리스크/성장성 분석 결과를 종합해 투자 의견을 제시하는 D-day 보고서를 작성한다.

- 대상: {target_name} ({target_type})
- 요약: {summaries}
- 감성분석: {sentiment}
- 리스크분석: {risk}
- 성장성분석: {growth}

반드시 아래 구조의 JSON만 반환하라. (설명, 인사말, 기타 텍스트 절대 금지)
JSON 이외의 텍스트가 포함되면 시스템 오류가 발생한다.
모든 텍스트는 반드시 한국어로 작성하라.

JSON 형식:
{{
  "target_type": "{target_type}",
  "target_name": "{target_name}",
  "analysis_summary": "종합적인 분석 요약",
  "investment_points": ["투자 포인트들"],
  "risk_factors": ["리스크 요인들"],
  "consensus": {{"opinion": "투자의견", "target_price": "목표가", "confidence": "신뢰도"}}
}}
"""


def _create_d_plus1_prompt(d_day_report, market_result):
    """D+1 보고서 프롬프트 생성"""
    return f"""
너는 숙련된 증권 투자 전략가이며, 아래의 D-day 보고서와 전날 장 결과를 바탕으로 D+1 해석 보고서를 작성한다.

- D-day 보고서: {d_day_report}
- 전날 장 결과: {market_result}

반드시 아래 구조의 JSON만 반환하라. (설명, 인사말, 기타 텍스트 절대 금지)
JSON 이외의 텍스트가 포함되면 시스템 오류가 발생한다.
모든 텍스트는 반드시 한국어로 작성하라.

JSON 형식:
{{
  "target_type": "{d_day_report.get('target_type', '')}",
  "target_name": "{d_day_report.get('target_name', '')}",
  "analysis_summary": "전날 예측과 실제 결과를 종합한 해석",
  "investment_points": ["D+1 투자 포인트들"],
  "risk_factors": ["D+1 리스크 요인들"],
  "consensus": {{"opinion": "투자의견", "target_price": "목표가", "confidence": "신뢰도"}}
}}
"""