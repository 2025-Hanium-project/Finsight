"""
에이전트 기본 클래스
"""
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from utils.llm_client import generate_response
from error_handlers import AgentError, ParsingError, get_security_manager

logger = logging.getLogger(__name__)
security_manager = get_security_manager()


class BaseAgent:
    """모든 에이전트의 기본 클래스"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """에이전트 실행"""
        self.logger.info(f"{self.agent_name} 에이전트 시작")
        start_time = datetime.now()
        
        try:
            # 입력 검증
            self._validate_input(input_data)
            
            # 보안 처리
            safe_input = security_manager.sanitize_input(input_data)
            
            # 프롬프트 생성
            prompt = self._create_prompt(safe_input)
            
            # LLM 호출
            response = await generate_response(
                prompt=prompt,
                agent_type=self.agent_name,
                temperature=0.7
            )
            
            # 응답 파싱
            result = self._parse_response(response)
            
            # 후처리
            final_result = self._post_process(result, safe_input)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"{self.agent_name} 완료: {processing_time:.3f}s")
            
            return final_result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"{self.agent_name} 실패: {str(e)} ({processing_time:.3f}s)")
            raise AgentError(
                agent_name=self.agent_name,
                message=f"{self.agent_name} 에이전트 실행 실패: {str(e)}"
            )
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """입력 데이터 검증 (하위 클래스에서 구현)"""
        if not input_data:
            raise AgentError(
                agent_name=self.agent_name,
                message="입력 데이터가 비어있습니다"
            )
    
    def _create_prompt(self, input_data: Dict[str, Any]) -> str:
        """프롬프트 생성 (하위 클래스에서 구현)"""
        raise NotImplementedError("하위 클래스에서 구현해야 합니다")
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """LLM 응답 파싱"""
        try:
            # JSON 응답 파싱
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError as e:
            # JSON 파싱 실패 시 텍스트에서 JSON 추출 시도
            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return parsed
            except:
                pass
            
            raise ParsingError(
                message=f"{self.agent_name} 응답 파싱 실패",
                raw_response=response[:500],  # 처음 500자만 로깅
                expected_schema="JSON"
            )
    
    def _post_process(self, result: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """결과 후처리 (하위 클래스에서 선택적 구현)"""
        # 기본 메타데이터 추가
        result.update({
            "agent_name": self.agent_name,
            "generated_at": datetime.now().isoformat(),
            "target_type": input_data.get("target_type", ""),
            "target_name": input_data.get("target_name", "")
        })
        return result


class ReportAnalysisAgent(BaseAgent):
    """리포트 분석 전용 기본 클래스"""
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        super()._validate_input(input_data)
        
        if "report_contents" not in input_data:
            raise AgentError(
                agent_name=self.agent_name,
                message="리포트 내용이 필요합니다"
            )
        
        report_contents = input_data["report_contents"]
        if not report_contents or not isinstance(report_contents, list):
            raise AgentError(
                agent_name=self.agent_name,
                message="리포트 내용은 비어있지 않은 리스트여야 합니다"
            )
    
    def _get_combined_reports(self, report_contents: List[str]) -> str:
        """리포트들을 결합하여 하나의 텍스트로 만들기"""
        if not report_contents:
            return ""
        
        combined = ""
        for i, content in enumerate(report_contents, 1):
            if content and content.strip():
                combined += f"\n=== 리포트 {i} ===\n{content.strip()}\n"
        
        return combined.strip()


def create_standard_prompt_template(
    agent_name: str,
    task_description: str,
    output_schema: Dict[str, str]
) -> str:
    """표준 프롬프트 템플릿 생성"""
    
    schema_description = "\n".join([
        f'  "{field}": "{description}"'
        for field, description in output_schema.items()
    ])
    
    return f"""
당신은 전문적인 {agent_name}입니다.

**작업**: {task_description}

**분석 대상**: {{target_type}} - {{target_name}}

**리포트 내용**:
{{report_content}}

**출력 형식** (반드시 JSON 형식으로):
{{
{schema_description}
}}

**중요 사항**:
1. 모든 응답은 한국어로 작성
2. JSON 형식만 반환 (설명 불필요)
3. 객관적이고 전문적인 분석 제공
4. 근거가 불충분한 경우 "정보 부족"으로 표시
"""


def format_agent_response(
    agent_name: str,
    result: Dict[str, Any],
    target_type: str = "",
    target_name: str = ""
) -> Dict[str, Any]:
    """에이전트 응답 표준 형식"""
    return {
        "agent_type": agent_name,
        "target_type": target_type,
        "target_name": target_name,
        "success": True,
        "result": result,
        "generated_at": datetime.now().isoformat(),
        "processing_time": 0.0  # 실제 처리 시간은 호출하는 곳에서 설정
    } 