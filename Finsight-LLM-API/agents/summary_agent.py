"""
요약 에이전트
"""
from typing import Dict, Any, List, Union
from datetime import datetime

from models.schemas import ReportSummaryResponse
from utils.llm_client import generate_structured_response
from error_handlers import AgentError
from utils.agent_base import BaseAgent


class SummaryAgent(BaseAgent):
    """요약 에이전트 클래스"""
    
    def __init__(self):
        super().__init__("summary_agent")
    
    async def process(self, report_content: str, report_info: Dict[str, str]) -> Dict[str, Any]:
        """요약 처리 메인 함수"""
        return await summarize_report(report_content, report_info)


async def summarize_report(report_content: str, report_info: Dict[str, str]) -> Dict[str, Any]:
    """
    증권사 애널리스트 리포트를 요약하는 에이전트
    """
    from utils.logging_config import get_agent_logger
    
    logger = get_agent_logger("summary_agent")
    start_time = datetime.now()
    
    try:
        logger.log_start("리포트 요약", extra={
            'content_length': len(report_content) if report_content else 0,
            'report_info': report_info
        })
        
        # 입력 검증
        validated_content = _validate_and_prepare_input(report_content, report_info)
        
        # 프롬프트 생성
        prompt = _create_summary_prompt(validated_content, report_info)
        
        # Function Calling으로 구조화된 응답 생성
        structured_result = await generate_structured_response(
            prompt, 
            ReportSummaryResponse,
            agent_type="summary_agent",
            temperature=0.3
        )
        result = structured_result.dict()
        
        # 메타데이터 추가
        result["generated_at"] = datetime.now().isoformat()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.log_completion("리포트 요약", processing_time, extra={
            'summary_length': len(result.get('summary', '')),
            'key_points_count': len(result.get('key_points', []))
        })
        
        return result
        
    except AgentError:
        # 이미 처리된 에러는 그대로 전파
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.log_error("리포트 요약", e, extra={
            'processing_time': processing_time,
            'report_info': report_info
        })
        
        raise AgentError(
            agent_name="summary_agent",
            message=f"리포트 요약 중 오류 발생: {str(e)}",
            details={"report_info": report_info}
        )


def _validate_and_prepare_input(report_content: str, report_info: Dict[str, str]) -> str:
    """입력 데이터 검증 및 준비"""
    from config import MAX_REPORT_SIZE
    from error_handlers import ValidationError
    
    # 필수 매개변수 검증
    if not report_content or not report_content.strip():
        raise AgentError(
            agent_name="summary_agent",
            message="요약할 리포트 내용이 없습니다",
            details={"report_info": report_info}
        )
    
    # 리포트 크기 제한
    if len(report_content) > MAX_REPORT_SIZE:
        validated_content = report_content[:MAX_REPORT_SIZE] + "... (내용 생략)"
    else:
        validated_content = report_content.strip()
    
    return validated_content


def _create_summary_prompt(report_content: str, report_info: Dict[str, str]) -> str:
    """요약 프롬프트 생성"""
    
    # 리포트 내용 길이 제한
    content_preview = report_content[:3000] + "..." if len(report_content) > 3000 else report_content
    
    return f"""
너는 증권사 애널리스트 리포트 요약 전문가이며, 반드시 아래 형식의 JSON만 반환하는 API 역할을 한다.

**중요: 모든 응답은 반드시 한국어로 작성해야 한다.**

리포트 정보: {report_info}
리포트 내용:
{content_preview}

위 리포트를 다음 기준으로 요약하라:
- 핵심 내용 요약 (300자 이내)
- 주요 포인트 3-5개 추출
- 객관적이고 전문적인 톤 유지

반드시 아래 구조의 JSON만 반환하라. (설명, 인사말, 기타 텍스트 절대 금지)

JSON 형식:
{{
  "summary": "리포트 요약",
  "key_points": ["핵심 포인트들"],
  "report_info": 리포트_정보
}}

**모든 텍스트는 한국어로 작성해야 합니다.**
"""