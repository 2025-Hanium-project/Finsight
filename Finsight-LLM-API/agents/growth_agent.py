"""
성장성 분석 에이전트
"""
from typing import Dict, Any, List, Union
from datetime import datetime

from models.schemas import GrowthResponse
from utils.llm_client import generate_structured_response
from error_handlers import AgentError
from utils.agent_base import ReportAnalysisAgent


class GrowthAgent(ReportAnalysisAgent):
    """성장성 분석 에이전트 클래스"""
    
    def __init__(self):
        super().__init__("growth_agent")
    
    async def process(self, report_contents: List[Any], target_type: str, target_name: str) -> Dict[str, Any]:
        """성장성 분석 처리 메인 함수"""
        return await analyze_growth(report_contents, target_type, target_name)


async def analyze_growth(report_contents: List[Any], target_type: str, target_name: str) -> Dict[str, Any]:
    """
    리포트의 성장성을 분석하는 에이전트
    """
    from utils.logging_config import get_agent_logger
    
    logger = get_agent_logger("growth_agent")
    start_time = datetime.now()
    
    try:
        logger.log_start("성장성 분석", extra={
            'target_type': target_type,
            'target_name': target_name,
            'reports_count': len(report_contents) if report_contents else 0
        })
        
        # 입력 검증
        validated_contents = _validate_and_prepare_inputs(report_contents, target_type, target_name)
        
        # 프롬프트 생성
        prompt = _create_growth_prompt(validated_contents, target_type, target_name)
        
        # Function Calling으로 구조화된 응답 생성
        structured_result = await generate_structured_response(
            prompt, 
            GrowthResponse,
            agent_type="growth_agent",
            temperature=0.1
        )
        result = structured_result.dict()
        
        # 메타데이터 추가
        result["generated_at"] = datetime.now().isoformat()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.log_completion("성장성 분석", processing_time, extra={
            'growth_score': result.get('growth_score', 0),
            'growth_potential': result.get('growth_potential', 'unknown'),
            'growth_drivers_count': len(result.get('growth_drivers', []))
        })
        
        return result
        
    except AgentError:
        # 이미 처리된 에러는 그대로 전파
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.log_error("성장성 분석", e, extra={
            'processing_time': processing_time,
            'target_type': target_type,
            'target_name': target_name
        })
        
        raise AgentError(
            agent_name="growth_agent",
            message=f"성장성 분석 중 오류 발생: {str(e)}",
            details={"target_type": target_type, "target_name": target_name}
        )


def _validate_and_prepare_inputs(
    report_contents: List[Any], 
    target_type: str, 
    target_name: str
) -> List[str]:
    """입력 데이터 검증 및 준비"""
    from config import MAX_REPORT_SIZE, MAX_REPORTS_PER_REQUEST
    from error_handlers import ValidationError
    
    # 필수 매개변수 검증
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
    
    # 리포트 내용 검증 및 변환
    if not report_contents:
        raise AgentError(
            agent_name="growth_agent",
            message="분석할 리포트 내용이 없습니다",
            details={"target_type": target_type, "target_name": target_name}
        )
    
    if len(report_contents) > MAX_REPORTS_PER_REQUEST:
        raise AgentError(
            agent_name="growth_agent",
            message=f"리포트 개수가 제한을 초과했습니다 ({len(report_contents)} > {MAX_REPORTS_PER_REQUEST})",
            details={"provided_count": len(report_contents), "max_allowed": MAX_REPORTS_PER_REQUEST}
        )
    
    # 문자열로 변환 및 크기 제한
    validated_contents = []
    for i, content in enumerate(report_contents):
        if isinstance(content, dict):
            # 딕셔너리인 경우 'content' 필드 추출
            text_content = content.get('content', str(content))
        else:
            # 문자열로 변환
            text_content = str(content)
        
        # 크기 제한
        if len(text_content) > MAX_REPORT_SIZE:
            text_content = text_content[:MAX_REPORT_SIZE] + "... (내용 생략)"
        
        if text_content.strip():  # 빈 내용 제외
            validated_contents.append(text_content.strip())
    
    if not validated_contents:
        raise AgentError(
            agent_name="growth_agent",
            message="유효한 리포트 내용이 없습니다",
            details={"original_count": len(report_contents)}
        )
    
    return validated_contents


def _create_growth_prompt(report_contents: List[Any], target_type: str, target_name: str) -> str:
    """성장성 분석 프롬프트 생성"""
    
    # 리포트 내용 문자열 생성
    reports_str = ""
    for i, report in enumerate(report_contents, 1):
        content = str(report)
        if isinstance(report, dict):
            content = report.get('content', str(report))
        content_preview = content[:1500] + "..." if len(content) > 1500 else content
        reports_str += f"### 리포트 {i}\n{content_preview}\n\n"
    
    target_description = {
        "company": "기업",
        "industry": "산업",
        "sector": "섹터"
    }.get(target_type.lower(), "대상")
    
    return f"""
너는 성장성 분석 전문가이며, 반드시 아래 예시와 동일한 JSON만 반환하는 API 역할을 한다.

**중요: 모든 응답은 반드시 한국어로 작성해야 한다. 영어 사용 절대 금지.**

분석 대상: {target_name} ({target_description})
분석할 리포트 내용:
{reports_str}

위 리포트들을 종합적으로 분석하여 {target_name}의 성장 잠재력을 분석하라:
- 성장 동력 요인들과 각각의 영향도, 지속가능성 - 한국어 필수
- 전체 성장 점수 (0-100)
- 성장 레벨 (high/medium/low)
- 성장 트렌드 (accelerating/stable/slowing)
- 핵심 성공 요인들 - 한국어 필수

반드시 아래 예시와 동일한 구조의 JSON만 반환하라. (설명, 인사말, 기타 텍스트 절대 금지)
JSON 이외의 텍스트가 포함되면 시스템 오류가 발생한다.

JSON 형식:
{{
  "target_type": "{target_type}",
  "target_name": "{target_name}",
  "growth_drivers": [
    {{
      "driver": "분석된 성장 동력",
      "description": "성장 동력 설명",
      "impact": "영향도",
      "sustainability": "지속가능성"
    }}
  ],
  "growth_score": 분석_점수,
  "growth_potential": "성장_잠재력",
  "growth_timeline": "성장_타임라인",
  "investment_opportunities": ["투자 기회들"]
}}

**다시 한 번 강조: 모든 텍스트는 한국어로 작성해야 합니다.**
""" 